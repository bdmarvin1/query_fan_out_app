import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from .cost_tracker import CostTracker

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("QueryFanOutSimulator")

# --- Configure the Gemini API using the new standard ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY":
        raise ValueError("GOOGLE_API_KEY not found or not set in .env file.")
    
    genai.configure(api_key=api_key)
    logger.info("Google Gemini API configured successfully with genai.configure().")
except Exception as e:
    logger.error(f"Failed to configure Gemini API client: {e}")

def call_gemini_api(
    prompt: str,
    cost_tracker: CostTracker,
    model_name: str = 'gemini-1.5-flash-latest',
    grounding_url: str = None,
    response_mime_type: str = 'text/plain',
):
    """
    Calls the Gemini API using the google.genai client, tracks token usage, and returns the parsed response.

    Args:
        prompt: The text prompt to send to the model. Assumes URL is part of prompt if grounding_url is used.
        cost_tracker: An instance of the CostTracker class.
        model_name: The ID of the Gemini model to use (e.g., "gemini-1.5-flash-latest").
        grounding_url: Optional URL string. If provided, enables the 'url_context' tool (unless JSON response is requested).
        response_mime_type: The expected MIME type of the response (e.g., 'application/json', 'text/plain').
    
    Returns:
        The processed response from the API, which can be a dictionary (for JSON)
        or a string (for plain text).
        
    Raises:
        Exception: For API-related errors.
    """
    try:
        # --- Initialize the model using the new genai.GenerativeModel pattern ---
        model = genai.GenerativeModel(model_name)

        contents = [prompt]
        
        # --- Build the generation_config and tools for the API call ---
        generation_config = {"response_mime_type": response_mime_type}
        tools_list = None
        
        if grounding_url and response_mime_type != 'application/json':
            # Note: The structure for tools might need adjustment based on specific library versions.
            # This reflects a common pattern.
            tools_list = [{"url_context": {}}]
            logger.info("URL context tool enabled for non-JSON response.")
        elif grounding_url and response_mime_type == 'application/json':
            logger.warning("Grounding URL provided, but URL context tool not enabled because JSON response was requested.")

        # --- Log the request for debugging ---
        log_prompt = (
            f"--- PROMPT SENT TO GEMINI ---\\n"
            f"Model: {model_name}\\n"
            f"Grounding URL (tool enabled if used): {grounding_url or 'None'}\\n"
            f"--- Prompt Content ---\\n{prompt}\\n"
            f"--- Generation Config ---\\n{json.dumps(generation_config, indent=2)}\\n"
            f"-----------------------------"
        )
        logger.info(log_prompt)

        # --- Generate Content using the updated method signature ---
        response = model.generate_content(
            contents=contents,
            generation_config=generation_config,
            tools=tools_list
        )

        # --- Cost and Token Tracking ---
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            cost_tracker.track_gemini_usage(model_name, input_tokens, output_tokens)
        else:
            logger.warning("Could not retrieve usage metadata from Gemini response.")

        raw_response_text = response.text
        logger.info(f"--- RAW RESPONSE FROM GEMINI ---\\n{raw_response_text}\\n------------------------------")
        
        # --- Process Response ---
        if response_mime_type == 'application/json':
            try:
                cleaned_text = raw_response_text.strip().removeprefix("```json").removesuffix("```")
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from Gemini response: {e}")
                logger.error(f"Raw response: {raw_response_text}")
                return {"error": "Failed to parse JSON", "raw_response": raw_response_text}
        else:
            return raw_response_text

    except Exception as e:
        logger.error(f"An unexpected error occurred while calling Gemini API: {e}")
        # Re-raise the exception to be caught by the calling function
        raise
