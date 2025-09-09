"""
Content Strategy Generation.

This module processes the final JSON output to create a human-readable,
strategic, and actionable content plan in a markdown file.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict
import re

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
        "Problem & Solution": ['prevent', 'avoid', 'solution', 'issue', 'fix'],
    }

    # Assign each sub-query to the first cluster it matches
    for profile in sub_query_profiles:
        query_lower = profile['sub_query'].lower()
        assigned = False
        for cluster_name, keywords in cluster_keywords.items():
            if any(re.search(r'\b' + keyword + r'\b', query_lower) for keyword in keywords):
                clusters[cluster_name].append(profile)
                assigned = True
                break
        if not assigned:
            clusters["General Information"].append(profile)
            
    logger.info(f"Identified {len(clusters)} content clusters.")
    return clusters

def _synthesize_brief(cluster_profiles: List[Dict[str, Any]]) -> str:
    """
    Synthesizes a single, actionable brief from a cluster of profiles.
    """
    if not cluster_profiles:
        return "No profiles to analyze."

    # Use the profile of the first sub-query as a base for synthesis
    base_profile = cluster_profiles[0].get('ideal_content_profile', {})
    if 'error' in base_profile:
        return "- **Note:** Analysis could not be performed for this cluster due to an earlier error."

    # Synthesize by taking the most common or representative elements
    extractability = base_profile.get('extractability', 'N/A')
    evidence = base_profile.get('evidence_density', 'N/A')
    scope = base_profile.get('scope_clarity', 'N/A')
    authority = base_profile.get('authority_signals', 'N/A')
    freshness = base_profile.get('freshness', 'N/A')

    # Get all unique modalities and source types from the cluster
    modalities = list(set([p.get('predicted_modality', 'N/A') for p in cluster_profiles]))
    sources = list(set([st for p in cluster_profiles for st in p.get('predicted_source_types', ['N/A'])]))

    brief = (
        f"- **Recommended Title/Theme:** A comprehensive guide covering '{cluster_profiles[0]['sub_query']}' and related questions.\n"
        f"- **Ideal Modalities:** {', '.join(modalities)}\n"
        f"- **Target Source Types:** {', '.join(sources)}\n\n"
        f"- **Content Brief Insights (based on competitive analysis):**\n"
        f"  - **Structure (Extractability):** {extractability}\n"
        f"  - **Data (Evidence Density):** {evidence}\n"
        f"  - **Audience (Scope Clarity):** {scope}\n"
        f"  - **Trust (Authority Signals):** {authority}\n"
        f"  - **Recency (Freshness):** {freshness}\n"
    )
    return brief

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

        # 1. Cluster the sub-queries
        clusters = _cluster_subqueries(sub_query_profiles)

        # 2. Build the markdown report string
        plan = f"# 🚀 Content Strategy Plan for \"{original_query}\"\n\n"
        plan += "This plan outlines a series of content clusters designed to capture the full range of user intents discovered during the Query Fan-Out simulation. Each cluster represents a pillar piece of content.\n\n"

        for cluster_name, profiles in clusters.items():
            plan += f"## 🎯 Content Cluster: {cluster_name}\n\n"
            
            # 3. Synthesize a brief for the cluster
            brief = _synthesize_brief(profiles)
            plan += brief
            
            # 4. List the specific sub-queries this content pillar will address
            plan += "\n- **Sub-Queries Covered by This Pillar:**\n"
            for p in profiles:
                plan += f"  - `{p['sub_query']}`\n"
            plan += "\n---\n\n"

        # 3. Save the report to a markdown file
        plan_filename = json_filepath.parent / f"content-plan-{original_query.replace(' ', '_')}.md"
        with open(plan_filename, 'w', encoding='utf-8') as f:
            f.write(plan)
            
        logger.info(f"✅ Content strategy plan successfully saved to {plan_filename}")

    except Exception as e:
        logger.error(f"Failed to generate content plan: {e}")
        # Create a simple error file if generation fails
        error_filename = json_filepath.parent / "content-plan-ERROR.txt"
        with open(error_filename, 'w', encoding='utf-8') as f:
            f.write(f"An error occurred during content plan generation: {e}")

