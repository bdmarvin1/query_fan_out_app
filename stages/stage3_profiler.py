"""
Stage 3: Selection for Synthesis (Competitive Analysis).

This module uses a data-driven approach to define the ideal content profile.
For each sub-query, it searches the web, scrapes the top results, and uses
Gemini to analyze the content and generate a competitive brief.
"""
import logging
import json
import os
import time  # <-- RATE LIMITING: Import time module
from typing import Dict, Any, List
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from utils.gemini_client import call_gemini_api

# Load environment variables
load_dotenv()
logger = logging.getLogger("QueryFanOutSimulator")

# Configure the number of top search results to analyze for each sub-query
TOP_N_RESULTS = 3
# --- RATE LIMITING: Add a delay in seconds between processing each sub-query ---
REQUEST_DELAY = 5  # 5 seconds delay to stay within typical free-tier limits

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

def profile_content_competitively(stage2_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Creates a data-driven, ideal content profile for each sub-query by
    searching, scraping, and analyzing the top-ranking web content.
    """
    if not app:
        raise ConnectionError("Firecrawl client is not initialized. Please check your API key.")
        
    logger.info("Executing Stage 3 (Competitive Analysis): Defining Ideal Content Profiles.")
    if not stage2_output:
        logger.warning("No routed sub-queries from Stage 2 to profile.")
        return []

    for item in stage2_output:
        sub_query = item.get('sub_query')
        if not sub_query:
            continue

        logger.info(f"--- Starting competitive analysis for sub-query: '{sub_query}' ---")
        
        try:
            # 1. Use the FirecrawlApp instance to search
            logger.info(f"Searching for top {TOP_N_RESULTS} results...")
            search_results = app.search(query=f"'{sub_query}'", limit=TOP_N_RESULTS)
            
            if not search_results:
                logger.warning(f"No search results found for '{sub_query}'. Skipping analysis.")
                item['ideal_content_profile'] = {"error": "No search results found to analyze."}
                continue

            top_urls = [result['url'] for result in search_results]
            logger.info(f"Found top URLs: {top_urls}")

            # 2. Use the FirecrawlApp instance to scrape
            scraped_content = []
            for url in top_urls:
                try:
                    logger.info(f"Scraping {url}...")
                    scrape_params = {'pageOptions': {'onlyMainContent': True}}
                    scrape_data = app.scrape(url=url, params=scrape_params)
                    
                    # --- TYPEERROR FIX: Check if scrape_data is a dictionary before accessing keys ---
                    if isinstance(scrape_data, dict) and scrape_data.get('markdown'):
                        scraped_content.append({
                            "url": url,
                            "content": scrape_data['markdown'][:12000]
                        })
                    else:
                        logger.warning(f"Could not retrieve valid markdown content from {url}. Got: {scrape_data}")
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
            
            if not scraped_content:
                logger.warning(f"Failed to scrape any content for '{sub_query}'. Skipping analysis.")
                item['ideal_content_profile'] = {"error": "Could not scrape top search results."}
                continue

            # 3. Analyze the scraped content with Gemini
            logger.info("Analyzing scraped content with Gemini to define ideal profile...")
            
            # --- SYNTAX FIX: Corrected f-string declaration ---
            prompt = f"""
            You are a world-class SEO and Content Strategist specializing in Generative Engine Optimization (GEO). Your task is to analyze the content of the top-ranking web pages for a given search query and synthesize an "ideal content profile" that would be competitive and likely to rank.

            **Search Query:** "{sub_query}"

            **Analysis Context (Content from Top {len(scraped_content)} Ranking Pages):**
            ```json
            {json.dumps(scraped_content, indent=2)}
            ```

            **Your Task:**
            Based *only* on the provided context from the top-ranking pages, identify their common strengths and define the ideal content profile for a new piece of content intended to outperform them. The profile must be based on these five criteria:

            1.  **Extractability**: Based on the successful structures in the context, what is the best format? (e.g., "A mix of H2/H3 sections for key questions, a data table comparing features, and a final summary checklist.").
            2.  **Evidence Density**: What kind of specific, fact-rich information do these pages provide? (e.g., "High. They consistently cite specific statistics, include dollar amounts, and reference named experts.").
            3.  **Scope Clarity**: How do the top pages define their audience and applicability? (e.g., "They all explicitly state 'for beginners' and include a 'who this is for' section.").
            4.  **Authority Signals**: What common sources, experts, or data points do they reference to build trust? (e.g., "Frequent mentions of government sources, university studies, and named industry professionals.").
            5.  **Freshness**: What is the required recency of the information based on the content? (e.g., "The content includes market data and product models from the current year, indicating high freshness is required.").

            **Instructions:**
            - You MUST return the output as a single, valid JSON object.
            - The object should contain a single key: "ideal_content_profile".
            - The value of this key should be an object with the five criteria as keys.
            """
            analysis_result = call_gemini_api(prompt)

            if analysis_result and 'ideal_content_profile' in analysis_result:
                item['ideal_content_profile'] = analysis_result['ideal_content_profile']
                logger.info(f"Successfully generated competitive profile for '{sub_query}'.")
            else:
                raise ValueError("Gemini API response was malformed.")

        except Exception as e:
            logger.error(f"An error occurred during competitive analysis for '{sub_query}': {e}")
            item['ideal_content_profile'] = {"error": str(e)}

        # --- RATE LIMITING: Pause between processing each sub-query ---
        logger.info(f"Pausing for {REQUEST_DELAY} seconds to respect API rate limits.")
        time.sleep(REQUEST_DELAY)

    logger.info("Stage 3 (Competitive Analysis) completed.")
    return stage2_output
