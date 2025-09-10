import os
from datetime import datetime # Import datetime
from dotenv import load_dotenv
from query_fan_out_app.utils.gemini_client import call_gemini_api
from query_fan_out_app.utils.cost_tracker import CostTracker

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":
    # Ensure your GOOGLE_API_KEY is set as an environment variable.
    # For example, in your shell: export GOOGLE_API_KEY="your_api_key_here"
    # Or in a .env file loaded by dotenv.
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "YOUR_GOOGLE_API_KEY":
        print("Error: GOOGLE_API_KEY environment variable not set or is a placeholder.")
        print("Please set GOOGLE_API_KEY in your .env file or as an environment variable.")
    else:
        test_prompt = "What is the capital of France, and what are the current pricing details for Gemini API usage?"
        print(f"Sending test prompt to Gemini: {test_prompt}")

        # Generate a timestamp for the run
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Initialize CostTracker with the timestamp
        cost_tracker = CostTracker(run_timestamp=current_timestamp)

        try:
            full_response = call_gemini_api(
                prompt=test_prompt,
                cost_tracker=cost_tracker,
                model_name='gemini-1.5-flash-latest', # Or your preferred model
                response_mime_type='text/plain' # Or 'application/json' if expecting structured data
            )
            print("\n--- ENTIRE GEMINI RESPONSE ---")
            print(full_response)
            print("------------------------------")

            # You can also print the cost summary if needed
            print("\n--- COST SUMMARY ---")
            cost_tracker.log_summary() # Use log_summary instead of print_cost_summary
            print("--------------------")

        except Exception as e:
            print(f"An error occurred during the Gemini API call: {e}")
