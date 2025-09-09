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

    Args:
        prompt: The prompt to send to the Gemini API.
        model_name: The specific model to use (e.g., 'gemini-2.5-pro').

    Returns:
        The parsed JSON response from the API (dict or list).
        Raises ConnectionError if the API is not configured or ValueError on response issue.
    """
    if not genai:
        raise ConnectionError("Gemini API is not configured.")

    try:
        model = genai.GenerativeModel(model_name)
        
        # Instruct the model to output JSON
        generation_config = {"response_mime_type": "application/json"}
            
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # The API returns a reparsed JSON object when using response_mime_type
        return json.loads(response.text)

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        # Re-raise the exception to be handled by the calling function
        raise
