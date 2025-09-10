import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from .cost_tracker import CostTracker

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("QueryFanOutSimulator")

# --- Configure the Gemini API ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY":
        raise ValueError("GOOGLE_API_KEY not found or not set in .env file.")
    genai.configure(api_key=api_key)
    logger.info("Google Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    genai = None


def call_gemini_api(
    prompt: str,
    cost_tracker: CostTracker,
    model_name: str = 'gemini-1.5-flash-latest',
    grounding_url: str = None, # grounding_url is still passed as a parameter
    response_mime_type: str = 'text/plain',
):
    """
    Calls the Gemini API, tracks token usage, and returns the parsed response.

    Args:
        prompt: The text prompt to send to the model.
        cost_tracker: An instance of the CostTracker class.
        model_name: The name of the Gemini model to use.
        grounding_url: Optional URL to include in the prompt for contextual grounding.
        response_mime_type: The expected MIME type of the response (e.g., 'application/json', 'text/plain').
    
    Returns:
        The processed response from the API, which can be a dictionary (for JSON)
        or a string (for plain text).
        
    Raises:
        ConnectionError: If the Gemini API is not configured.
        Exception: For other API-related errors.
    """
    if not genai:
        raise ConnectionError("Gemini API is not configured.")

    # Augment the prompt with the grounding_url if provided
    if grounding_url:
        full_prompt = f"Contextual URL: {grounding_url}\n\n{prompt}"
    else:
        full_prompt = prompt

    contents = [{"text": full_prompt}]
    generation_config = {"response_mime_type": response_mime_type}

    # Removed explicit tool enabling for GoogleSearchRetrieval
    # as per user's request not to enable the 'search tool'.
    # The 'URLs tool' as a distinct genai.protos.Tool for direct URL content
    # grounding is not available in the current library. The URL is provided
    # as part of the prompt for context.
    model = genai.GenerativeModel(model_name=model_name)

    try:
        # --- Log the request for debugging ---
        log_prompt = (
            f"--- PROMPT SENT TO GEMINI ---\n"
            f"Model: {model_name}\n"
            f"Grounding URL (if used): {grounding_url or 'None'}\n"
            f"Response MIME Type: {response_mime_type}\n"
            f"--- Prompt Content ---\n{full_prompt}\n"
            f"-----------------------------"
        )
        logger.info(log_prompt)

        # --- Generate Content ---
        response = model.generate_content(
            contents=contents,
            generation_config=generation_config
        )

        # --- Cost and Token Tracking ---
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count\n            output_tokens = response.usage_metadata.candidates_token_count\n            cost_tracker.track_gemini_usage(model_name, input_tokens, output_tokens)
        else:
            logger.warning("Could not retrieve usage metadata from Gemini response.")

        raw_response_text = response.text
        logger.info(f"--- RAW RESPONSE FROM GEMINI ---\n{raw_response_text}\n------------------------------")
        
        # --- Process Response ---
        if response_mime_type == 'application/json':
            try:
                # Attempt to parse JSON and clean up markdown artifacts
                cleaned_text = raw_response_text.strip().removeprefix("```json").removesuffix("```")
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from Gemini response: {e}")
                logger.error(f"Raw response: {raw_response_text}")
                # Fallback to returning raw text if JSON parsing fails
                return {"error": "Failed to parse JSON", "raw_response": raw_response_text}
        else:
            # For 'text/plain' or other types, return the raw text
            return raw_response_text

    except Exception as e:
        logger.error(f"An unexpected error occurred while calling Gemini API: {e}")
        raise
