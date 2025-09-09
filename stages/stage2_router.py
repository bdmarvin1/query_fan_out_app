"""
Stage 2: Subquery Routing and Fan-Out Mapping.

This module uses the Gemini API to determine the best source types and 
modalities for each sub-query generated in Stage 1.
"""
import logging
import json  # <-- FIXED: Added missing import
from typing import Dict, Any, List
from utils.gemini_client import call_gemini_api

logger = logging.getLogger("QueryFanOutSimulator")

# Define the universe of possible source types and modalities, as per the document.
SOURCE_TYPES = ["Coaching blogs", "training websites", "expert-authored pages", "E-commerce sites", "product review sites", "affiliate blogs", "Instructional platforms", "fitness apps", "YouTube channels", "Knowledge bases", "encyclopedias", "government or academic sources", "financial data APIs", "bank product pages", "personal finance editorial sites"]
MODALITY_TYPES = ["Long-form text", "structured schedules", "tables", "Listicles", "bullet lists", "product comparison tables", "Video (with transcripts)", "step-by-step guides", "Concise explanatory text", "structured definitions"]

def route_subqueries(stage1_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Routes each sub-query to appropriate sources and modalities using the Gemini API.
    """
    logger.info("Executing Stage 2: Sub-query Routing.")
    
    # Consolidate all generated queries into one list for routing
    sub_queries = list(set(
        stage1_output.get("rewrites_and_diversifications", []) +
        stage1_output.get("speculative_sub_questions", []) +
        stage1_output.get("projected_latent_intents", [])
    ))
    
    if not sub_queries:
        logger.warning("No sub-queries found from Stage 1 to route.")
        return []

    # Prepare the prompt for the Gemini API
    prompt = f\"\"\"
    You are an expert in information retrieval and search algorithms. Your task is to analyze a list of sub-queries and determine the most appropriate source types and content modalities for finding the best answers, based on the principles of the "AI Search Manual".

    **Instructions:**
    1.  For each sub-query, select one or more source types from this exact list: {SOURCE_TYPES}
    2.  For each sub-query, select the single most appropriate modality from this exact list: {MODALITY_TYPES}
    3.  Return the output as a single, valid JSON object, which is a list of dictionaries. Each dictionary must have three keys: "sub_query", "predicted_source_types", and "predicted_modality".

    **List of Sub-Queries to Analyze:**
    {json.dumps(sub_queries, indent=2)}

    **Example Output Format:**
    [
        {{
            "sub_query": "16-week beginner half marathon training plan",
            "predicted_source_types": ["Coaching blogs", "training websites"],
            "predicted_modality": "structured schedules"
        }},
        {{
            "sub_query": "Half marathon gear checklist",
            "predicted_source_types": ["E-commerce sites", "product review sites"],
            "predicted_modality": "Listicles"
        }},
        {{
            "sub_query": "Stretch routine for runners",
            "predicted_source_types": ["Instructional platforms", "YouTube channels"],
            "predicted_modality": "Video (with transcripts)"
        }}
    ]
    \"\"\"

    logger.info(f"Sending {len(sub_queries)} unique sub-queries to Gemini for routing.")
    
    try:
        routed_queries = call_gemini_api(prompt)
        
        if not isinstance(routed_queries, list):
             raise ValueError("Gemini API did not return a list as expected.")

        logger.info(f"Successfully routed {len(routed_queries)} sub-queries.")
        return routed_queries
    except Exception as e:
        logger.error(f"An error occurred during Stage 2 routing: {e}")
        # Fallback to a simple structure on failure
        return [
            {"sub_query": sq, "predicted_source_types": ["unknown"], "predicted_modality": "unknown", "error": str(e)}
            for sq in sub_queries
        ]
