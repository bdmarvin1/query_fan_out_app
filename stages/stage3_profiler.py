"""
Stage 3: Selection for Synthesis (Competitive Analysis).

This module uses a data-driven approach to define the ideal content profile.
For each sub-query, it searches the web, scrapes the top results, and uses
Gemini to analyze the content and generate a competitive brief.
"""
import logging
import json
from typing import Dict, Any, List
from utils.gemini_client import call_gemini_api
from firecrawl_search import search as firecrawl_search
from firecrawl_scrape import scrape as firecrawl_scrape

logger = logging.getLogger("QueryFanOutSimulator")

# Configure the number of top search results to analyze for each sub-query
TOP_N_RESULTS = 3

def profile_content_competitively(stage2_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Creates a data-driven, ideal content profile for each sub-query by
    searching, scraping, and analyzing the top-ranking web content.
    """
    logger.info("Executing Stage 3 (Competitive Analysis): Defining Ideal Content Profiles.")

    if not stage2_output:
        logger.warning("No routed sub-queries from Stage 2 to profile.")
        return []

    # Process each sub-query item from Stage 2
    for item in stage2_output:
        sub_query = item.get('sub_query')
        if not sub_query:
            continue

        logger.info(f"--- Starting competitive analysis for sub-query: '{sub_query}' ---")
        
        try:
            # 1. Search for the sub-query to find top competitors
            logger.info(f"Searching for top {TOP_N_RESULTS} results...")
            search_results = firecrawl_search(query=f"'{sub_query}'", limit=TOP_N_RESULTS)
            
            if not search_results or 'web' not in search_results or not search_results['web']:
                logger.warning(f"No web search results found for '{sub_query}'. Skipping analysis.")
                item['ideal_content_profile'] = {"error": "No search results found to analyze."}
                continue

            top_urls = [result['url'] for result in search_results['web'][:TOP_N_RESULTS]]
            logger.info(f"Found top URLs: {top_urls}")

            # 2. Scrape the content of the top URLs
            scraped_content = []
            for url in top_urls:
                try:
                    logger.info(f"Scraping {url}...")
                    # We specify markdown for a clean, text-based representation
                    scrape_data = firecrawl_scrape(url=url, formats=['markdown'])
                    if scrape_data and isinstance(scrape_data, list) and scrape_data[0].get('markdown'):
                        scraped_content.append({
                            "url": url,
                            "content": scrape_data[0]['markdown'][:10000] # Truncate to manage context window size
                        })
                    else:
                         logger.warning(f"Could not retrieve markdown content from {url}.")
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
            
            if not scraped_content:
                logger.warning(f"Failed to scrape any content for '{sub_query}'. Skipping analysis.")
                item['ideal_content_profile'] = {"error": "Could not scrape top search results."}
                continue

            # 3. Analyze the scraped content with Gemini to generate the profile
            logger.info("Analyzing scraped content with Gemini to define ideal profile...")
            
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

            # This call expects a dictionary back, not a list
            analysis_result = call_gemini_api(prompt)

            if analysis_result and 'ideal_content_profile' in analysis_result:
                item['ideal_content_profile'] = analysis_result['ideal_content_profile']
                logger.info(f"Successfully generated competitive profile for '{sub_query}'.")
            else:
                 raise ValueError("Gemini API response did not contain the expected 'ideal_content_profile' key.")

        except Exception as e:
            logger.error(f"An error occurred during the competitive analysis for '{sub_query}': {e}")
            item['ideal_content_profile'] = {"error": str(e)}

    logger.info("Stage 3 (Competitive Analysis) completed.")
    return stage2_output

# In main.py, you would replace the call to `profile_content` with this new function.
# from stages.stage3_profiler import profile_content_competitively
# ...
# stage3_data = profile_content_competitively(stage2_data)

