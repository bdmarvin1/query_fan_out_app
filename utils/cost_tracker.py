import os
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("QueryFanOutSimulator")


class CostTracker:
    """A class to track the cost and usage of API calls."""

    def __init__(self, run_timestamp):
        self.run_timestamp = run_timestamp
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.gemini_costs = {
            "gemini-1.5-flash-latest": {
                "input": 0.35 / 1_000_000, 
                "output": 1.05 / 1_000_000
            },
            "gemini-1.5-pro-latest": {
                "cutoff": 200000,
                "input_short": 0.625 / 1_000_000,
                "input_long": 1.25 / 1_000_000,
                "output_short": 5.00 / 1_000_000,
                "output_long": 7.50 / 1_000_000,
            },
        }
        self.total_cost = 0.0
        self.gemini_token_usage = {"input": 0, "output": 0}
        self.firecrawl_credits_start = 0
        self.firecrawl_credits_end = 0

    def get_firecrawl_credits(self):
        """Fetches the remaining Firecrawl credits from the API."""
        if not self.firecrawl_api_key:
            logger.warning("FIRECRAWL_API_KEY not found. Skipping credit check.")
            return None
        try:
            response = requests.get(
                "https://api.firecrawl.dev/v2/team/credit-usage",
                headers={"Authorization": f"Bearer {self.firecrawl_api_key}"},
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("remainingCredits")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Firecrawl credits: {e}")
            return None

    def start_run(self):
        """Initializes the run by fetching starting Firecrawl credits."""
        self.firecrawl_credits_start = self.get_firecrawl_credits()
        if self.firecrawl_credits_start is not None:
            logger.info(f"Starting Firecrawl credits: {self.firecrawl_credits_start}")

    def end_run(self):
        """Finalizes the run, logs the summary, and saves it to a file."""
        self.firecrawl_credits_end = self.get_firecrawl_credits()
        if self.firecrawl_credits_end is not None:
            logger.info(f"Ending Firecrawl credits: {self.firecrawl_credits_end}")

        self.log_summary()
        self.save_summary_to_file()

    def track_gemini_usage(self, model_name, input_tokens, output_tokens):
        """Tracks the token usage and cost for each Gemini API call."""
        self.gemini_token_usage["input"] += input_tokens
        self.gemini_token_usage["output"] += output_tokens

        if model_name in self.gemini_costs:
            cost_info = self.gemini_costs[model_name]
            
            # Check if the model has a tiered pricing structure
            if "cutoff" in cost_info:
                if input_tokens <= cost_info["cutoff"]:
                    input_cost = input_tokens * cost_info["input_short"]
                    output_cost = output_tokens * cost_info["output_short"]
                else:
                    input_cost = input_tokens * cost_info["input_long"]
                    output_cost = output_tokens * cost_info["output_long"]
            else:
                # Fallback to simple pricing for other models
                input_cost = input_tokens * cost_info["input"]
                output_cost = output_tokens * cost_info["output"]

            cost = input_cost + output_cost
            self.total_cost += cost
            logger.info(
                f"Gemini call cost: ${cost:.6f} ({input_tokens} in, {output_tokens} out)"
            )
        else:
            logger.warning(f"Cost information for model '{model_name}' not found.")

    def get_summary(self):
        """Generates a summary of the cost and usage for the run."""
        summary = (
            f"--- Cost and Usage Summary ---\\n"
            f"Gemini Total Input Tokens: {self.gemini_token_usage['input']}\\n"
            f"Gemini Total Output Tokens: {self.gemini_token_usage['output']}\\n"
            f"Estimated Gemini Cost: ${self.total_cost:.6f}\\n"
        )
        if self.firecrawl_credits_start is not None and self.firecrawl_credits_end is not None:
            credits_used = self.firecrawl_credits_start - self.firecrawl_credits_end
            summary += f"Firecrawl Credits Used: {credits_used}\\n"
        summary += "----------------------------\\n"
        return summary

    def log_summary(self):
        """Prints the summary to the console."""
        print(self.get_summary())

    def save_summary_to_file(self):
        """Saves the summary to a text file."""
        summary = self.get_summary()
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"costs_{self.run_timestamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(summary)
        logger.info(f"Cost summary saved to {filename}")
