import os
import pprint
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# Load environment variables from .env file
load_dotenv()

def test_scrape():
    """
    Initializes the FirecrawlApp client and scrapes a single URL,
    then prints the entire response for inspection.
    """
    print("--- Starting Firecrawl Scrape Test ---")
    
    # Initialize the FirecrawlApp client
    try:
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        if not firecrawl_api_key or firecrawl_api_key == "YOUR_FIRECRAWL_API_KEY":
            raise ValueError("FIRECRAWL_API_KEY not found or not set in .env file.")
        
        app = FirecrawlApp(api_key=firecrawl_api_key)
        print("Firecrawl client initialized successfully.")
    
    except Exception as e:
        print(f"Failed to initialize Firecrawl client: {e}")
        return

    # URL to scrape
    test_url = "https://golocalinteractive.com"
    print(f"Scraping URL: {test_url}")

    # Perform the scrape
    try:
        # Scrape the URL and request markdown format
        scrape_result = app.scrape(
            url=test_url,
            formats=['markdown'],
            only_main_content=True
        )

        # Pretty-print the entire response dictionary
        print("\n--- Full Scrape Response ---")
        pprint.pprint(scrape_result)
        print("--------------------------\n")

    except Exception as e:
        print(f"An error occurred during the scrape operation: {e}")
    
    finally:
        print("--- Scrape Test Finished ---")

if __name__ == "__main__":
    test_scrape()
