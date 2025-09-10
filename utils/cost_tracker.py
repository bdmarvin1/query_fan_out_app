import os
import requests
import logging
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
logger = logging.getLogger("QueryFanOutSimulator")

class CostTracker:
    def __init__(self, run_timestamp):
        self.run_timestamp = run_timestamp
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        self.gemini_costs = {
            "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
            "gemini-2.5-pro": {"input": 1.25 / 1_000_000, "output": 10.00 / 1_000_000}
        }
        self.total_cost = 0.0
        self.gemini_token_usage = {"input": 0, "output": 0}
        self.firecrawl_credits_start = 0
        self.firecrawl_credits_end = 0

    def get_firecrawl_credits(self):
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
        self.firecrawl_credits_start = self.get_firecrawl_credits()
        if self.firecrawl_credits_start is not None:
            logger.info(f"Starting Firecrawl credits: {self.firecrawl_credits_start}")

    def end_run(self):
        self.firecrawl_credits_end = self.get_firecrawl_credits()
        if self.firecrawl_credits_end is not None:
            logger.info(f"Ending Firecrawl credits: {self.firecrawl_credits_end}")
        
        self.log_summary()
        self.save_summary_to_file()

    def track_gemini_usage(self, model_name, input_tokens, output_tokens):
        self.gemini_token_usage["input"] += input_tokens
        self.gemini_token_usage["output"] += output_tokens
        
        if model_name in self.gemini_costs:
            cost_info = self.gemini_costs[model_name]
            cost = (input_tokens * cost_info["input"]) + (output_tokens * cost_info["output"])
            self.total_cost += cost
            logger.info(f"Gemini call cost: ${cost:.6f} ({input_tokens} in, {output_tokens} out)")
        else:
            logger.warning(f"Cost information for model '{model_name}' not found.")

    def get_summary(self):
        summary = "--- Cost and Usage Summary ---\n" # Removed leading newline
        if self.firecrawl_credits_start is not None and self.firecrawl_credits_end is not None:
            credits_used = self.firecrawl_credits_start - self.firecrawl_credits_end
            summary += f"Firecrawl Credits Used: {credits_used}\n"
        
        summary += f"Gemini Total Input Tokens: {self.gemini_token_usage['input']}\n"
        summary += f"Gemini Total Output Tokens: {self.gemini_token_usage['output']}\n"
        summary += f"Estimated Gemini Cost: ${self.total_cost:.6f}\n"
        summary += "----------------------------\n"
        return summary

    def log_summary(self):
        print(self.get_summary())

    def save_summary_to_file(self):
        summary = self.get_summary()
        output_dir = Path('outputs')
        output_dir.mkdir(exist_ok=True)
        filename = output_dir / f"costs_{self.run_timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        logger.info(f"Cost summary saved to {filename}")
