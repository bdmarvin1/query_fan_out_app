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
    grounding_url: str = None,
    response_mime_type: str = 'text/plain',
):
    """
    Calls the Gemini API, tracks token usage, and returns the parsed response.

    Args:
        prompt: The text prompt to send to the model. Assumes URL is part of prompt if grounding_url is used.
        cost_tracker: An instance of the CostTracker class.
        model_name: The name of the Gemini model to use.
        grounding_url: Optional URL string. If provided, enables the 'url_context' tool.
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

    contents = [prompt]
    
    # Initialize generation_config and add tools if grounding_url is provided
    generation_config_with_tools = {"response_mime_type": response_mime_type}
    if grounding_url:
        generation_config_with_tools["tools"] = [{"url_context": {}}]
    
    # Initialize model without tools parameter, as tools are in generation_config
    model = genai.GenerativeModel(model_name=model_name)

    try:
        # --- Log the request for debugging ---
        log_prompt = (
            f"--- PROMPT SENT TO GEMINI ---\n"
            f"Model: {model_name}\n"
            f"Grounding URL (tool enabled if used): {grounding_url or 'None'}\n"
            f"Response MIME Type: {response_mime_type}\n"
            f"--- Prompt Content ---\n{prompt}\n"
            f"--- Generation Config (with tools) ---\n{json.dumps(generation_config_with_tools, indent=2)}\n"
            f"-----------------------------"
        )
        logger.info(log_prompt)

        # --- Generate Content ---
        response = model.generate_content(
            contents=contents,
            generation_config=generation_config_with_tools
        )

        # --- Cost and Token Tracking ---
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            cost_tracker.track_gemini_usage(model_name, input_tokens, output_tokens)
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
