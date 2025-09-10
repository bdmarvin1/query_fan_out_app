from firecrawl.v2.types import SearchData, Document
import logging
import json
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
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
    """
    Wrapper for Firecrawl API calls with exponential backoff for rate limiting.
    """
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
                    raise e # Re-raise the exception after the last attempt
            else:
                # Re-raise other exceptions immediately
                raise e
    return None # Should not be reached, but as a fallback

def profile_content_competitively(stage2_output: List[Dict[str, Any]], cost_tracker: CostTracker, location: str = None) -> List[Dict[str, Any]]:
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
                item['ideal_content_profile'] = {"error": "No search results found to analyze."}
                continue

            if isinstance(search_results, SearchData):
                search_results = search_results.web
            
            if isinstance(search_results, dict) and 'results' in search_results:
                search_results = search_results['results']

            if not isinstance(search_results, list):
                logger.error(f"Unexpected data type for search results for '{sub_query}'. Expected a list, but got {type(search_results)}. Full response: {search_results}")
                item['ideal_content_profile'] = {"error": f"Unexpected data type from search API: {type(search_results)}"}
                continue

            top_urls = [result.url for result in search_results]
            logger.info(f"Found top URLs: {top_urls}")

            # 2. Scrape content iteratively
            scraped_content = []
            urls_to_scrape_count = INITIAL_SCRAPE_ATTEMPTS
            attempted_urls = set()

            while len(scraped_content) < MIN_SCRAPABLE_RESULTS and urls_to_scrape_count <= MAX_SEARCH_RESULTS:
                urls_for_this_attempt = top_urls[:urls_to_scrape_count]
                
                for url in urls_for_this_attempt:
                    if url in attempted_urls:
                        continue

                    attempted_urls.add(url)

                    try:
                        logger.info(f"Scraping {url} (attempting up to {urls_to_scrape_count} results)...")
                        scrape_data = _firecrawl_with_backoff(app.scrape, url=url, formats=['markdown'], only_main_content=True)
                        
                        if isinstance(scrape_data, Document) and scrape_data.markdown:
                            scraped_content.append({"url": url, "content": scrape_data.markdown[:12000]}) # Limit content to avoid token limits
                            if len(scraped_content) >= MIN_SCRAPABLE_RESULTS:
                                break
                        else:
                            logger.warning(f"Could not retrieve valid markdown from {url}. Got: {scrape_data}")
                    except Exception as e:
                        logger.error(f"Scraping {url} failed after retries: {e}")
                
                if len(scraped_content) < MIN_SCRAPABLE_RESULTS:
                    urls_to_scrape_count += 1
                    logger.info(f"Only {len(scraped_content)} scrapable results found. Increasing scrape attempts to {urls_to_scrape_count}.")
                else:
                    logger.info(f"Achieved {len(scraped_content)} successful scrapes for '{sub_query}'. Proceeding to analysis.")
                    break

            if not scraped_content:
                logger.warning("Could not scrape any top results for this sub-query after all attempts.")
                item['ideal_content_profile'] = {"error": "Could not scrape top search results."}
                continue

            # 3. Analyze the scraped content with Gemini
            logger.info("Analyzing scraped content with Gemini...")
            prompt = f"""
            You are a world-class SEO and Content Strategist. Your task is to analyze the provided search query and the content from the top-ranking pages to develop a strategic 'ideal content profile'. This profile will guide the creation of a new piece of content designed to outperform current competitors.

            Focus on identifying patterns, gaps, and opportunities within the competitive content.

            **Search Query:** {sub_query}

            **Location Context:** {location if location else 'Global'}

            **Analysis Context (Content from Top {len(scraped_content)} Ranking Pages):**
            ```json
            {json.dumps(scraped_content, indent=2)}
            ```

            **Instructions for 'ideal_content_profile' (Output ONLY in JSON format):**
            You MUST provide a JSON object with a single key 'ideal_content_profile'. The value of this key should be an object with the following nested keys, each providing a concise, actionable analysis based on the competitive content:

            - **`extractability` (Structure):** Describe the optimal content structure for easy extraction of key information by users and search engines. Consider headings, lists, tables, schema markup opportunities, interactive elements, etc. (e.g., 'The ideal format is a directory-style page. It should lead with a clear H1 tag like '24-Hour Access Storage Units in Overland Park, KS'. The core of the page should be a filterable and sortable list of individual storage facilities. Each list item must be a self-contained, structured block presenting key data: facility name, address, distance, a photo, available unit sizes with real-time pricing, current promotions, and unit availability.').

            - **`evidence_density` (Data):** Quantify and describe the type and density of data points and evidence needed to make the content authoritative and trustworthy. (e.g., 'Very high. The content must be rich with specific, dynamic data points. This includes exact dollar amounts for monthly rent per unit size, precise distances in miles from the search location, specific counts of remaining units ('2 left'), explicit promotional details ('50% Off First Month'), and aggregated statistics like the average monthly cost for storage in Overland Park.').

            - **`scope_clarity` (Audience/Intent):** Define the precise audience and user intent the content should address. Specify what the content should and should not cover to remain focused and highly relevant. (e.g., 'The scope is sharply defined and transactional. The content is explicitly for users looking to find and compare 24-hour access storage facilities in and around Overland Park, KS. The page should directly serve this intent without deviation.').

            - **`authority_signals` (Trust):** Identify the key signals that establish trust and authority for this topic. These could include expert citations, data sources, user reviews, brand mentions, certifications, etc. (e.g., 'Authority is built through the comprehensiveness and perceived accuracy of the marketplace data, rather than external citations. Key signals include a complete list of local providers, the integration of user-generated reviews and ratings (social proof), and the display of real-time pricing and availability data.').

            - **`freshness` (Recency):** Explain the required recency of the content to be competitive and relevant. Should it be real-time, updated quarterly, evergreen, etc.? How can freshness be signaled? (e.g., 'Extremely high. The content's utility depends on its recency. The ideal profile must feature data that is, or appears to be, real-time. This includes current rental prices, up-to-the-minute unit availability ('1 left'), and active promotions.').

            - **`target_keywords_and_phrasings` (Keywords):** List additional relevant keywords and key phrases (beyond the main sub-query) that should be naturally integrated into the content to capture a wider range of related user intents and improve SEO performance. These should be derived from the analysis of competitive content. Present as a list of strings.

            Ensure the output is a single, valid JSON object that can be directly parsed.
            """
            analysis_result = call_gemini_api(prompt, cost_tracker=cost_tracker)

            if analysis_result and 'ideal_content_profile' in analysis_result:
                item['ideal_content_profile'] = analysis_result['ideal_content_profile']
                logger.info(f"Successfully generated competitive profile for '{sub_query}'.")
            else:
                raise ValueError("Gemini API response was malformed or missing 'ideal_content_profile'.")

        except Exception as e:
            logger.error(f"An error occurred during competitive analysis for '{sub_query}': {e}")
            item['ideal_content_profile'] = {"error": str(e)}

    logger.info("Stage 3 (Competitive Analysis) completed.")
    return stage2_output
