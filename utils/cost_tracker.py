import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("QueryFanOutSimulator")

class CostTracker:
    def __init__(self):
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.gemini_costs = {
            "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000}
            # Add other models here as needed
        }
        self.total_cost = 0.0
        self.gemini_token_usage = {"input": 0, "output": 0}
        self.firecrawl_credits_start = 0
        self.firecrawl_credits_end = 0

    def get_firecrawl_credits(self):
        """Fetches remaining Firecrawl credits."""
        if not self.firecrawl_api_key:
            logger.warning("FIRECRAWL_API_KEY not found. Skipping credit check.")
            return None
        try:
            response = requests.get(
                "https://api.firecrawl.dev/v2/team/credit-usage",
                headers={"Authorization": f"Bearer {self.firecrawl_api_key}"}
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("remainingCredits")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Firecrawl credits: {e}")
            return None

    def start_run(self):
        """Records the starting Firecrawl credits."""
        self.firecrawl_credits_start = self.get_firecrawl_credits()
        if self.firecrawl_credits_start is not None:
            logger.info(f"Starting Firecrawl credits: {self.firecrawl_credits_start}")

    def end_run(self):
        """Records ending credits and calculates the total run cost."""
        self.firecrawl_credits_end = self.get_firecrawl_credits()
        if self.firecrawl_credits_end is not None:
            logger.info(f"Ending Firecrawl credits: {self.firecrawl_credits_end}")
        
        self.calculate_total_cost()
        self.log_summary()

    def track_gemini_usage(self, model_name, input_tokens, output_tokens):
        """Tracks Gemini token usage and calculates cost."""
        self.gemini_token_usage["input"] += input_tokens
        self.gemini_token_usage["output"] += output_tokens
        
        if model_name in self.gemini_costs:
            cost_info = self.gemini_costs[model_name]
            cost = (input_tokens * cost_info["input"]) + (output_tokens * cost_info["output"])
            self.total_cost += cost
            logger.info(f"Gemini call cost: ${cost:.6f} ({input_tokens} in, {output_tokens} out)")
        else:
            logger.warning(f"Cost information for model '{model_name}' not found.")

    def calculate_total_cost(self):
        """Calculates the total cost of the run."""
        # Firecrawl cost is 1 credit per scrape/search, but we'll just show the difference
        pass # Gemini costs are already accumulated in self.total_cost

    def log_summary(self):
        """Logs a summary of the run's cost and usage."""
        print("\n--- Cost and Usage Summary ---")
        if self.firecrawl_credits_start is not None and self.firecrawl_credits_end is not None:
            credits_used = self.firecrawl_credits_start - self.firecrawl_credits_end
            print(f"Firecrawl Credits Used: {credits_used}")
        
        print(f"Gemini Total Input Tokens: {self.gemini_token_usage['input']}")
        print(f"Gemini Total Output Tokens: {self.gemini_token_usage['output']}")
        print(f"Estimated Gemini Cost: ${self.total_cost:.6f}")
        print("----------------------------\n")
