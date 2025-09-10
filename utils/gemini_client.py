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
except Exception as e:\n    logger.error(f"Failed to configure Gemini API: {e}")
    genai = None

# Added default_response_mime_type to allow flexibility in output, default to markdown
def call_gemini_api(prompt: str, cost_tracker: CostTracker, model_name: str = 'gemini-2.0-flash', grounding_url: str = None, default_response_mime_type: str = 'text/markdown'):
    """
    Calls the Gemini API, tracks token usage, and returns the parsed JSON/Markdown response.
    Optionally uses a URL for native model grounding.
    """
    if not genai:\n        raise ConnectionError("Gemini API is not configured.")

    contents = [{"text": prompt}]
    generation_config = {"response_mime_type": default_response_mime_type} # Use default_response_mime_type

    if grounding_url:\n        contents.insert(0, {"url_context": {"url": grounding_url}})
        generation_config["tools"] = [{"url_context": {}}] # Enable the url_context tool

    try:\n        # For logging, we still want to see the main prompt clearly\n        log_prompt = f"--- PROMPT SENT TO GEMINI ---\n{prompt}\n"
        if grounding_url:\n            log_prompt += f"--- WITH GROUNDING URL: {grounding_url} ---\n"
        log_prompt += "-----------------------------"
        logger.info(log_prompt)

        model = genai.GenerativeModel(model_name)\n        response = model.generate_content(contents=contents, generation_config=generation_config)

        # --- COST TRACKING ---\n        if response.usage_metadata:\n            input_tokens = response.usage_metadata.prompt_token_count\n            output_tokens = response.usage_metadata.candidates_token_count\n            cost_tracker.track_gemini_usage(model_name, input_tokens, output_tokens)\n        else:\n            logger.warning("Could not retrieve usage metadata from Gemini response.")\n        
        raw_response_text = response.text\n        logger.info(f"--- RAW RESPONSE FROM GEMINI ---\n{raw_response_text}\n------------------------------")
        
        # Return raw_response_text if markdown is expected, otherwise attempt json.loads
        if default_response_mime_type == 'text/markdown':
            return raw_response_text
        else:\n            return json.loads(raw_response_text)

    except json.JSONDecodeError as e:\n        logger.error(f"Error parsing JSON from Gemini response (expected JSON, got markdown/text): {e}")\n        logger.error(f"Raw response: {raw_response_text}")\n        return raw_response_text # Fallback to returning raw text if JSON parsing fails
    except Exception as e:\n        logger.error(f"Error calling Gemini API or processing response: {e}")\n        raise