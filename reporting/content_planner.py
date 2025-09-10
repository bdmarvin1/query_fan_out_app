"""
Content Strategy Generation.
"""
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
            if any(re.search(r'\\b' + keyword.replace(' ', r'\\s') + r'\\b', query_lower) for keyword in keywords):
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

    target_keywords = [p['sub_query'] for p in cluster_profiles]
    
    base_profile = cluster_profiles[0].get('ideal_content_profile', {})
    if 'error' in base_profile:
        brief = f"- **Note:** Competitive analysis could not be performed: {base_profile['error']}\\n"
    else:
        brief = (
            f"- **Content Brief (based on competitive analysis):**\\n"
            f"  - **Structure:** {base_profile.get('extractability', 'N/A')}\\n"
            f"  - **Data:** {base_profile.get('evidence_density', 'N/A')}\\n"
            f"  - **Audience:** {base_profile.get('scope_clarity', 'N/A')}\\n"
            f"  - **Trust:** {base_profile.get('authority_signals', 'N/A')}\\n"
            f"  - **Recency:** {base_profile.get('freshness', 'N/A')}\\n"
        )

    keyword_section = "\\n- **Target Keywords:**\\n"
    for kw in target_keywords:
        keyword_section += f"  - `{kw}`\\n"
    
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

        plan = f"# Content Strategy Plan for \\\"{original_query}\\\"\\n\\n"
        plan += "This plan outlines content pillars based on clustered user intents...\\n\\n---\\n\\n"

        for cluster_name, profiles in clusters.items():
            plan += f"## Content Pillar: {cluster_name}\\n\\n"
            brief = _synthesize_brief(cluster_name, profiles)
            plan += brief
            plan += "\\n---\\n\\n"

        safe_query_name = re.sub(r'[\\W_]+', '_', original_query)
        plan_filename = json_filepath.parent / f"content-plan-{safe_query_name}-{run_timestamp}.md"
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(plan)
            
        logger.info(f"Content strategy plan saved to {plan_filename}")

    except Exception as e:
        logger.error(f"Failed to generate content plan: {e}", exc_info=True)
