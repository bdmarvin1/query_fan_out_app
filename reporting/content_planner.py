import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import re
import logging
from utils.cost_tracker import CostTracker
from utils.gemini_client import call_gemini_api

logger = logging.getLogger("QueryFanOutSimulator")

def _cluster_subqueries(sub_query_profiles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups sub-queries into logical clusters."""
    logger.info("Clustering sub-queries into strategic groups.")
    clusters = defaultdict(list)
    
    cluster_keywords = {
        "Cost & Sizing": ['cost', 'price', 'cheap', 'size', 'how much', 'pricing'],
        "How-To & Logistics": ['how to', 'pack', 'tips', 'guide', 'organize', 'rules', 'checklist', 'plan'],
        "Comparison & Alternatives": ['vs', 'versus', 'or', 'best', 'alternative', 'compare', 'review'],
        "Benefits & Reasons": ['why', 'benefit', 'advantage', 'should i'],
        "Definitions & Concepts": ['what is', 'what are', 'define', 'meaning'],
        "Problem & Solution": ['prevent', 'avoid', 'solution', 'issue', 'fix', 'rules', 'not keep'],
    }

    for profile in sub_query_profiles:
        query_lower = profile['sub_query'].lower()
        assigned = False
        for cluster_name, keywords in cluster_keywords.items():
            if any(re.search(r'\b' + keyword.replace(' ', r'\s') + r'\b', query_lower) for keyword in keywords):
                clusters[cluster_name].append(profile)
                assigned = True
                break
        if not assigned:
            clusters["General Information"].append(profile)
            
    logger.info(f"Identified {len(clusters)} content clusters.")
    return clusters

def _synthesize_brief(cluster_name: str, cluster_profiles: List[Dict[str, Any]]) -> str:
    """Synthesizes a single, actionable brief from a cluster of profiles."""
    if not cluster_profiles:
        return "No profiles to analyze."

    target_keywords = []
    # Use a set to store unique keywords
    unique_keywords = set() 
    
    # Collect keywords from all profiles in the cluster
    for profile in cluster_profiles:
        target_keywords.append(profile['sub_query'])
        # Add keywords from the 'ideal_content_profile' if available
        ideal_profile = profile.get('ideal_content_profile', {})
        if 'target_keywords_and_phrasings' in ideal_profile:
            for kw in ideal_profile['target_keywords_and_phrasings']:
                unique_keywords.add(kw)

    # Convert the set back to a list for output, sorting for consistency
    target_keywords.extend(sorted(list(unique_keywords)))
    
    # Aggregate brief details from all profiles in the cluster
    aggregated_brief_details = defaultdict(list)
    has_valid_profile = False

    for profile in cluster_profiles:
        ideal_profile = profile.get('ideal_content_profile', {})
        if 'error' in ideal_profile:
            # If there's an error, just note it for this specific profile, but continue processing others
            logger.warning(f"Error in ideal_content_profile for sub_query '{profile.get('sub_query', 'N/A')}': {ideal_profile['error']}")
        else:
            has_valid_profile = True
            for key in ['extractability', 'evidence_density', 'scope_clarity', 'authority_signals', 'freshness']:
                if ideal_profile.get(key) and ideal_profile.get(key) != 'N/A':
                    aggregated_brief_details[key].append(ideal_profile[key])

    brief = f"- **Content Brief (based on competitive analysis):**\n"
    if not has_valid_profile:
        brief += f"  - **Note:** Competitive analysis could not be performed for any profiles in this cluster.  All briefs were N/A or contained errors.\n"
    else:
        for key in ['structure', 'data', 'audience', 'trust', 'recency']:
            # Map the key names from the brief back to the aggregated_brief_details keys
            detail_key = key.replace('structure', 'extractability').replace('data', 'evidence_density').replace('audience', 'scope_clarity').replace('trust', 'authority_signals').replace('recency', 'freshness')
            
            combined_value = "; ".join(aggregated_brief_details[detail_key]) if aggregated_brief_details[detail_key] else 'N/A'
            brief += f"  - **{key.capitalize()}:** {combined_value}\n"
        
    keyword_section = "\n- **Target Keywords & Phrasings to Include:**\n"
    # Ensure unique keywords and order them
    for kw in sorted(list(set(target_keywords))):
        keyword_section += f"  - `{kw}`\n"
    
    return brief + keyword_section

def generate_content_plan(json_filepath: Path, cost_tracker: CostTracker, run_timestamp: str):
    """Processes fan-out data to generate a strategic content plan."""
    logger.info(f"Generating content plan from {json_filepath}...")
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        original_query = data.get("original_query", "unknown_query")
        sub_query_profiles = data.get("final_sub_query_profiles", [])

        if not sub_query_profiles:
            logger.warning("No sub-query profiles to process.")
            return

        clusters = _cluster_subqueries(sub_query_profiles)

        plan = f"# \U0001f680 Content Strategy Plan for "{original_query}"\n\n"
        plan += "This plan outlines content pillars based on clustered user intents. Each cluster brief is derived from a competitive analysis of top-ranking content, designed to guide the creation of material that can outperform them.\n\n---\n\n"

        for cluster_name, profiles in clusters.items():
            plan += f"## \U0001f3af Content Pillar: {cluster_name}\n\n"
            brief = _synthesize_brief(cluster_name, profiles)
            plan += brief
            plan += "\n---\n\n"


        safe_query_name = re.sub(r'[\W_]+', '_', original_query)
        plan_filename = json_filepath.parent / f"content-plan-{safe_query_name}-{run_timestamp}.md"
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(plan)
            
        logger.info(f"Content strategy plan saved to {plan_filename}")

    except Exception as e:
        logger.error(f"Failed to generate content plan: {e}", exc_info=True)