import logging
import json
import os
import time
from typing import Dict, Any, List

from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from firecrawl.v2.types import SearchData, Document

from utils.gemini_client import call_gemini_api
from utils.cost_tracker import CostTracker

# Load environment variables
load_dotenv()
logger = logging.getLogger("QueryFanOutSimulator")

# Configure constants from environment variables
MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", 10))
MIN_SCRAPABLE_RESULTS = int(os.getenv("MIN_SCRAPABLE_RESULTS", 2))
INITIAL_SCRAPE_ATTEMPTS = int(os.getenv("INITIAL_SCRAPE_ATTEMPTS", 3))
INITIAL_DELAY = int(os.getenv("INITIAL_DELAY", 5))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 4))

# Initialize the FirecrawlApp client
try:
    firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_api_key or firecrawl_api_key == "YOUR_FIRECRAWL_API_KEY":
        raise ValueError("FIRECRAWL_API_KEY not found or not set in .env file.")
    app = FirecrawlApp(api_key=firecrawl_api_key)
    logger.info("Firecrawl client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Firecrawl client: {e}")
    app = None


def _firecrawl_with_backoff(crawl_function, **kwargs):
    """Wraps Firecrawl API calls with exponential backoff for rate limiting."""
    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            return crawl_function(**kwargs)
        except Exception as e:
            if "Rate Limit Exceeded" in str(e) or "rate limit" in str(e).lower():
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Rate limit hit. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error("Max retries reached. Aborting this call.")
                    raise e
            else:
                raise e
    return None


def profile_content_competitively(
    stage2_output: List[Dict[str, Any]],
    cost_tracker: CostTracker,
    location: str = None,
    grounding_url: str = None,
) -> List[Dict[str, Any]]:
    """
    Creates a data-driven, ideal content profile for each sub-query by
    searching, scraping, and analyzing top content with robust error handling.
    """
    if not app:
        raise ConnectionError("Firecrawl client is not initialized.")

    logger.info("Executing Stage 3 (Competitive Analysis)...")
    if not stage2_output:
        logger.warning("No routed sub-queries from Stage 2 to profile.")
        return []

    for item in stage2_output:
        sub_query = item.get('sub_query')
        if not sub_query:
            continue

        logger.info(f"--- Analyzing sub-query: '{sub_query}' ---")

        try:
            # 1. Search for top URLs with exponential backoff
            logger.info(f"Searching for top {MAX_SEARCH_RESULTS} results...")
            search_params = {
                'query': f"'{sub_query}'",
                'limit': MAX_SEARCH_RESULTS
            }
            if location:
                search_params['location'] = location
                logger.info(f"Applying location filter: {location}")

            search_results = _firecrawl_with_backoff(app.search, **search_params)

            if not search_results:
                logger.warning("No search results found after retries.")
                item['ideal_content_profile'] = {
                    "error": "No search results found to analyze."
                }
                continue

            # Process search results
            if isinstance(search_results, SearchData):
                search_results = search_results.web
            if isinstance(search_results, dict) and 'results' in search_results:
                search_results = search_results['results']

            if not isinstance(search_results, list):
                logger.error(
                    f"Unexpected data type for search results for '{sub_query}'. "
                    f"Expected a list, but got {type(search_results)}. "
                    f"Full response: {search_results}"
                )
                item['ideal_content_profile'] = {
                    "error": f"Unexpected data type from search API: {type(search_results)}"
                }
                continue

            top_urls = [result.url for result in search_results]
            logger.info(f"Found top URLs: {top_urls}")

            # 2. Scrape content iteratively
            scraped_content = []
            urls_to_scrape_count = INITIAL_SCRAPE_ATTEMPTS
            attempted_urls = set()

            while (
                len(scraped_content) < MIN_SCRAPABLE_RESULTS
                and urls_to_scrape_count <= MAX_SEARCH_RESULTS
            ):
                urls_for_this_attempt = top_urls[:urls_to_scrape_count]
                for url in urls_for_this_attempt:
                    if url in attempted_urls:
                        continue
                    attempted_urls.add(url)

                    try:
                        logger.info(
                            f"Scraping {url} (attempting up to {urls_to_scrape_count} results)..."
                        )
                        scrape_data = _firecrawl_with_backoff(
                            app.scrape,
                            url=url,
                            formats=['markdown'],
                            only_main_content=True
                        )

                        if isinstance(scrape_data, Document) and scrape_data.markdown:
                            scraped_content.append(
                                {"url": url, "content": scrape_data.markdown[:12000]}
                            )
                            if len(scraped_content) >= MIN_SCRAPABLE_RESULTS:
                                break
                        else:
                            logger.warning(
                                f"Could not retrieve valid markdown from {url}. "
                                f"Got: {scrape_data}"
                            )
                    except Exception as e:
                        logger.error(f"Scraping {url} failed after retries: {e}")

                if len(scraped_content) < MIN_SCRAPABLE_RESULTS:
                    urls_to_scrape_count += 1
                    logger.info(
                        f"Only {len(scraped_content)} scrapable results found. "
                        f"Increasing scrape attempts to {urls_to_scrape_count}."
                    )
                else:
                    logger.info(
                        f"Achieved {len(scraped_content)} successful scrapes for "
                        f"'{sub_query}'. Proceeding to analysis."
                    )
                    break

            if not scraped_content:
                logger.warning(
                    "Could not scrape any top results for this sub-query."
                )
                item['ideal_content_profile'] = {
                    "error": "Could not scrape top search results."
                }
                continue

            # 3. Analyze the scraped content with Gemini
            logger.info("Analyzing scraped content with Gemini...")
            prompt = (
                f"You are a world-class SEO and Content Strategist. Your task is to analyze the "
                f"provided search query and the content from the top-ranking pages to develop a "
                f"strategic 'ideal content profile'. This profile will guide the creation of a "
                f"new piece of content designed to outperform current competitors.\n\n"
                f"**CRUCIAL INSTRUCTION FOR GROUNDING:** Utilize the comprehensive context provided "
                f"by the URL: {grounding_url} for all aspects of your analysis and response, "
                f'especially for understanding the principles of "Query Fan-Out".\n\n'
                f"Focus on identifying patterns, gaps, and opportunities within the competitive content.\n\n"
                f"**Search Query:** {sub_query}\n"
                f"**Location Context:** {location if location else 'Global'}\n\n"
                f"**Analysis Context (Content from Top {len(scraped_content)} Ranking Pages):**\n"
                f"```json\n{json.dumps(scraped_content, indent=2)}\n```\n\n"
                f"**Instructions for 'ideal_content_profile' (Output ONLY in JSON format):**\n"
                f"You MUST provide a JSON object with a single key 'ideal_content_profile'. The value "
                f"of this key should be an object with the following nested keys, each providing a "
                f"concise, actionable analysis based on the competitive content:\n\n"
                f"- **`extractability` (Structure):** Describe the optimal content structure.\n"
                f"- **`evidence_density` (Data):** Quantify and describe the type and density of data points.\n"
                f"- **`scope_clarity` (Audience/Intent):** Define the precise audience and user intent.\n"
                f"- **`authority_signals` (Trust):** Identify the key signals that establish trust.\n"
                f"- **`freshness` (Recency):** Explain the required recency of the content.\n"
                f"- **`target_keywords_and_phrasings` (Keywords):** List additional relevant keywords.\n\n"
                f"Ensure the output is a single, valid JSON object that can be directly parsed."
            )

            analysis_result = call_gemini_api(
                prompt,
                cost_tracker=cost_tracker,
                grounding_url=grounding_url,
                response_mime_type='application/json'
            )

            if analysis_result and 'ideal_content_profile' in analysis_result:
                item['ideal_content_profile'] = analysis_result['ideal_content_profile']
                logger.info(
                    f"Successfully generated competitive profile for '{sub_query}'."
                )
            else:
                raise ValueError(
                    "Gemini API response was malformed or missing 'ideal_content_profile'."
                )

        except Exception as e:
            logger.error(
                f"An error occurred during competitive analysis for '{sub_query}': {e}"
            )
            item['ideal_content_profile'] = {"error": str(e)}

    logger.info("Stage 3 (Competitive Analysis) completed.")
    return stage2_output
