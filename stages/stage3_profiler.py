from firecrawl.v2.types import SearchData, Document
import logging
import json
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from utils.gemini_client import call_gemini_api

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

def profile_content_competitively(stage2_output: List[Dict[str, Any]], location: str = None) -> List[Dict[str, Any]]:
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

            # Handle the case where the API returns a SearchData object
            if isinstance(search_results, SearchData):
                search_results = search_results.web
            
            # Handle the case where the API returns a dictionary
            if isinstance(search_results, dict) and 'results' in search_results:
                search_results = search_results['results']

            # Add a robust check to ensure search_results is a list before proceeding
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
                        continue # Skip already attempted URLs in this or previous rounds

                    attempted_urls.add(url) # Mark as attempted

                    try:
                        logger.info(f"Scraping {url} (attempting up to {urls_to_scrape_count} results)...")
                        scrape_data = _firecrawl_with_backoff(app.scrape, url=url, formats=['markdown'], only_main_content=True)
                        
                        if isinstance(scrape_data, Document) and scrape_data.markdown:
                            scraped_content.append({"url": url, "content": scrape_data.markdown[:12000]})
                            if len(scraped_content) >= MIN_SCRAPABLE_RESULTS:
                                break # Achieved minimum required scrapes
                        else:
                            logger.warning(f"Could not retrieve valid markdown from {url}. Got: {scrape_data}")
                    except Exception as e:
                        logger.error(f"Scraping {url} failed after retries: {e}")
                
                if len(scraped_content) < MIN_SCRAPABLE_RESULTS:
                    urls_to_scrape_count += 1 # Try one more URL in the next iteration
                    logger.info(f"Only {len(scraped_content)} scrapable results found. Increasing scrape attempts to {urls_to_scrape_count}.")
                else:
                    logger.info(f"Achieved {len(scraped_content)} successful scrapes for '{sub_query}'. Proceeding to analysis.")
                    break # Exit loop if minimum met

            if not scraped_content:
                logger.warning("Could not scrape any top results for this sub-query after all attempts.")
                item['ideal_content_profile'] = {"error": "Could not scrape top search results."}
                continue

            # 3. Analyze the scraped content with Gemini
            logger.info("Analyzing scraped content with Gemini...")
            prompt = f\"\"\"
            You are a world-class SEO and Content Strategist specializing in Generative Engine Optimization (GEO). Your task is to analyze the content of the top-ranking web pages for a given search query and synthesize an \"ideal content profile\" that would be competitive and likely to rank.

            **Search Query:** {sub_query}\n
            **Location Context:** {location if location else 'Global'}

            **Analysis Context (Content from Top {len(scraped_content)} Ranking Pages):**
            ```json
            {json.dumps(scraped_content, indent=2)}
            ```

            **Your Task:**
            Based *only* on the provided context from the top-ranking pages, identify their common strengths and define the ideal content profile for a new piece of content intended to outperform them. The profile must be based on these five criteria:

            1.  **Extractability**: Based on the successful structures in the context, what is the best format? (e.g., \"A mix of H2/H3 sections for key questions, a data table comparing features, and a final summary checklist.\").\n
            2.  **Evidence Density**: What kind of specific, fact-rich information do these pages provide? (e.g., \"High. They consistently cite specific statistics, include dollar amounts, and reference named experts.\").\n
            3.  **Scope Clarity**: How do the top pages define their audience and applicability? (e.g., \"They all explicitly state 'for beginners' and include a 'who this is for' section.\").\n
            4.  **Authority Signals**: What common sources, experts, or data points do they reference to build trust? (e.g., \"Frequent mentions of government sources, university studies, and named industry professionals.\").\n
            5.  **Freshness**: What is the required recency of the information based on the content? (e.g., \"The content includes market data and product models from the current year, indicating high freshness is required.\").\n

            **Instructions:**
            - You MUST return the output as a single, valid JSON object.
            - The object should contain a single key: \"ideal_content_profile\".
            - The value of this key should be an object with the five criteria as keys.
            \"\"\"
            analysis_result = call_gemini_api(prompt)

            if analysis_result and 'ideal_content_profile' in analysis_result:
                item['ideal_content_profile'] = analysis_result['ideal_content_profile']
                logger.info(f"Successfully generated competitive profile for '{sub_query}'.")
            else:
                raise ValueError("Gemini API response was malformed.")

        except Exception as e:
            logger.error(f"An error occurred during competitive analysis for '{sub_query}': {e}")
            item['ideal_content_profile'] = {"error": str(e)}

    logger.info("Stage 3 (Competitive Analysis) completed.")
    return stage2_output
