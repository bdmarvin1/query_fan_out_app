"""
Gemini API Client Utility.

This module abstracts the interaction with the Google Gemini API.
"""
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

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

def call_gemini_api(prompt: str, model_name: str = 'gemini-2.5-pro'):
    """
    Calls the Gemini API with a given prompt and returns the parsed JSON response.
    Logs the full prompt and raw response for complete transparency.
    """
    if not genai:
        raise ConnectionError("Gemini API is not configured.")

    try:
        # --- VERBOSE LOGGING: Log the full prompt ---
        logger.info(f"--- PROMPT SENT TO GEMINI ---\n{prompt}\n-----------------------------")

        model = genai.GenerativeModel(model_name)
        generation_config = {"response_mime_type": "application/json"}
        response = model.generate_content(prompt, generation_config=generation_config)

        # --- VERBOSE LOGGING: Log the full raw response ---
        raw_response_text = response.text
        logger.info(f"--- RAW RESPONSE FROM GEMINI ---\n{raw_response_text}\n------------------------------")
        
        return json.loads(raw_response_text)

    except Exception as e:
        logger.error(f"Error calling Gemini API or parsing response: {e}")
        raise
