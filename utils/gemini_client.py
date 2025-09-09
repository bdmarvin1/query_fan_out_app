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

def call_gemini_api(prompt: str, is_json_output: bool = True):
    """
    Calls the Gemini API with a given prompt and returns the response.

    Args:
        prompt: The prompt to send to the Gemini API.
        is_json_output: If True, expects and parses a JSON string from the model.

    Returns:
        The parsed response from the API (dict or list if json, else string).
        Returns None if the API call fails.
    """
    if not genai:
        logger.error("Gemini API is not configured. Cannot make API call.")
        raise ConnectionError("Gemini API is not configured.")

    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        generation_config = {}
        if is_json_output:
            # Instruct the model to output JSON
            generation_config["response_mime_type"] = "application/json"
            
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if is_json_output:
            # The API should already return parsed JSON when using response_mime_type
            return json.loads(response.text)
        else:
            return response.text

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        # In case of an API error, you might want to return a specific error message
        # or re-raise the exception depending on how you want to handle it upstream.
        raise e
