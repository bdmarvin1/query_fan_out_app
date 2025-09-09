"""
Content Strategy Generation.

This module processes the final JSON output to create a human-readable,
strategic, and actionable content plan in a markdown file.
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
import re
import logging  # Ensure logger is imported

logger = logging.getLogger("QueryFanOutSimulator")

def _cluster_subqueries(sub_query_profiles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Groups sub-queries into logical clusters based on common keywords.
    """
    logger.info("Clustering sub-queries into strategic groups.")
    clusters = defaultdict(list)
    
    # Define keywords that identify a cluster. Order matters, more specific first.
    cluster_keywords = {
        "Cost & Sizing": ['cost', 'price', 'cheap', 'size', 'how much', 'pricing'],
        "How-To & Logistics": ['how to', 'pack', 'tips', 'guide', 'organize', 'rules', 'checklist', 'plan'],
        "Comparison & Alternatives": ['vs', 'versus', 'or', 'best', 'alternative', 'compare', 'review'],
        "Benefits & Reasons": ['why', 'benefit', 'advantage', 'should i'],
        "Definitions & Concepts": ['what is', 'what are', 'define', 'meaning'],
        "Problem & Solution": ['prevent', 'avoid', 'solution', 'issue', 'fix', 'rules', 'not keep'],
    }

    # Assign each sub-query to the first cluster it matches
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
    """
    Synthesizes a single, actionable brief from a cluster of profiles.
    """
    if not cluster_profiles:
        return "No profiles to analyze."

    # --- KEYWORD ENRICHMENT ---
    # Extract all sub-queries to be listed as target keywords
    target_keywords = [p['sub_query'] for p in cluster_profiles]
    
    # Use the profile of the first sub-query as a base for synthesis
    base_profile = cluster_profiles[0].get('ideal_content_profile', {})
    if 'error' in base_profile:
        brief = f"- **Note:** Competitive analysis could not be performed for this cluster: {base_profile['error']}\n"
    else:
        # Synthesize by taking the most common or representative elements
        extractability = base_profile.get('extractability', 'N/A')
        evidence = base_profile.get('evidence_density', 'N/A')
        scope = base_profile.get('scope_clarity', 'N/A')
        authority = base_profile.get('authority_signals', 'N/A')
        freshness = base_profile.get('freshness', 'N/A')
        brief = (
            f"- **Content Brief (based on competitive analysis):**\n"
            f"  - **Structure (Extractability):** {extractability}\n"
            f"  - **Data (Evidence Density):** {evidence}\n"
            f"  - **Audience (Scope Clarity):** {scope}\n"
            f"  - **Trust (Authority Signals):** {authority}\n"
            f"  - **Recency (Freshness):** {freshness}\n"
        )

    # --- KEYWORD ENRICHMENT ---
    # Add the target keywords section to the brief
    keyword_section = "\n- **Target Keywords & Phrasings to Include:**\n"
    for kw in target_keywords:
        keyword_section += f"  - `{kw}`\n"
    
    return brief + keyword_section

def generate_content_plan(json_filepath: Path):
    """
    Processes the fan-out data to generate a clustered, strategic content plan.
    """
    logger.info(f"Starting final content plan generation from {json_filepath}...")
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        original_query = data.get("original_query", "unknown_query")
        sub_query_profiles = data.get("final_sub_query_profiles", [])

        if not sub_query_profiles:
            logger.warning("JSON data contains no sub-query profiles to process.")
            return

        clusters = _cluster_subqueries(sub_query_profiles)

        plan = f"# 🚀 Content Strategy Plan for \"{original_query}\"\n\n"
        plan += "This plan outlines content pillars based on clustered user intents. Each cluster brief is derived from a competitive analysis of top-ranking content, designed to guide the creation of material that can outperform them.\n\n---\n\n"

        for cluster_name, profiles in clusters.items():
            plan += f"## 🎯 Content Pillar: {cluster_name}\n\n"
            brief = _synthesize_brief(cluster_name, profiles)
            plan += brief
            plan += "\n---\n\n"

        # Save the report to a markdown file
        safe_query_name = re.sub(r'[\W_]+', '_', original_query)
        plan_filename = json_filepath.parent / f"content-plan-{safe_query_name}.md"
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(plan)
            
        logger.info(f"✅ Content strategy plan successfully saved to {plan_filename}")

    except Exception as e:
        logger.error(f"Failed to generate content plan: {e}", exc_info=True)
        error_filename = json_filepath.parent / "content-plan-ERROR.txt"
        with open(error_filename, 'w', encoding='utf-8') as f:
            f.write(f"An error occurred during content plan generation: {e}")
