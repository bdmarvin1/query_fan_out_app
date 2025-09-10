"""
Gemini API Client Utility.

This module abstracts the interaction with the Google Gemini API.
"""
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from .cost_tracker import CostTracker

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("QueryFanOutSimulator")

# Configure the Gemini API key
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY":
        raise ValueError("GOOGLE_API_KEY not found or not set in .env file.")
    genai.configure(api_key=api_key)
    logger.info("Google Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    genai = None

def call_gemini_api(prompt: str, cost_tracker: CostTracker, model_name: str = 'gemini-2.0-flash'):
    """
    Calls the Gemini API, tracks token usage, and returns the parsed JSON response.
    """
    if not genai:
        raise ConnectionError("Gemini API is not configured.")

    try:
        logger.info(f"--- PROMPT SENT TO GEMINI ---\\n{prompt}\\n-----------------------------")

        model = genai.GenerativeModel(model_name)
        generation_config = {"response_mime_type": "application/json"}
        response = model.generate_content(prompt, generation_config=generation_config)

        # --- COST TRACKING ---
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            cost_tracker.track_gemini_usage(model_name, input_tokens, output_tokens)
        else:
            logger.warning("Could not retrieve usage metadata from Gemini response.")
        
        raw_response_text = response.text
        logger.info(f"--- RAW RESPONSE FROM GEMINI ---\\n{raw_response_text}\\n------------------------------")
        
        return json.loads(raw_response_text)

    except Exception as e:
        logger.error(f"Error calling Gemini API or parsing response: {e}")
        raise
