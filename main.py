import json
from stages.stage1_expander import expand_query
from stages.stage2_router import route_subqueries
from stages.stage3_profiler import profile_content_competitively
from utils.file_logger import setup_logger, save_structured_data
from reporting.content_planner import generate_content_plan
import difflib

def load_search_locations(logger):
    """Loads search locations from the locations.json file."""
    try:
        with open('locations.json', 'r') as f:
            locations = json.load(f)
        logger.info("Successfully loaded locations from locations.json.")
        return locations
    except FileNotFoundError:
        logger.error("locations.json not found. Please ensure the file is in the root directory.")
        return []
    except json.JSONDecodeError:
        logger.error("Error decoding locations.json. Please check the file for valid JSON format.")
        return []

def get_validated_location(logger, search_locations):
    """Gets and validates the user's target location."""
    if not search_locations:
        logger.warning("No search locations loaded. Skipping location validation.")
        return None

    location_names = [loc["name"].lower() for loc in search_locations]
    country_codes = [loc["countryCode"].lower() for loc in search_locations]
    canonical_names = [loc["canonicalName"].lower() for loc in search_locations]


    while True:
        user_location_input = input("Enter a target location (e.g., 'United States' or 'us'), or type 'skip' to proceed: ").strip().lower()
        if user_location_input == 'skip':
            logger.info("User chose to skip location filtering.")
            return None

        found_country_code = None

        # Try exact match for name or slug
        for loc in search_locations:
            if user_location_input == loc["name"].lower() or user_location_input == loc["countryCode"].lower():
                found_country_code = loc["countryCode"]
                break

        if found_country_code:
            logger.info(f"Valid location selected: {found_country_code}")
            return found_country_code
        else:
            # Try nearest match
            all_location_terms = location_names + country_codes + canonical_names
            close_matches = difflib.get_close_matches(user_location_input, all_location_terms, n=3, cutoff=0.6)

            if close_matches:
                suggestions = []
                for match in close_matches:
                    for loc in search_locations:
                        if loc["name"].lower() == match or loc["countryCode"].lower() == match:
                            suggestions.append(f"{loc['name']} ({loc['countryCode']})")
                            break
                logger.warning(f"Location not found. Did you mean one of these? {', '.join(suggestions)}")
            else:
                logger.warning(f"Location '{user_location_input}' not found. No close matches. Please try again or type 'skip'.")


def main():
    logger = setup_logger()
    logger.info("Starting Query Fan-Out Simulator.")

    # Load locations
    search_locations = load_search_locations(logger)

    # Get user input
    initial_query = input("Enter your query: ")
    logger.info(f"Initial query received: '{initial_query}'")

    # Get and validate location input
    selected_location = get_validated_location(logger, search_locations)
    logger.info(f"Selected location for search: {selected_location if selected_location else 'None'}")

    # --- Stage 1: Query Expansion ---
    logger.info("--- Starting Stage 1: Query Expansion and Latent Intent Mining ---")
    stage1_data = expand_query(initial_query)
    logger.info(f"--- Stage 1 Completed ---")

    # --- Stage 2: Subquery Routing ---
    logger.info("--- Starting Stage 2: Subquery Routing and Fan-Out Mapping ---")
    stage2_data = route_subqueries(stage1_data)
    logger.info(f"--- Stage 2 Completed ---")

    # --- Stage 3: Content Profiling (Competitive Analysis) ---
    logger.info("--- Starting Stage 3: Selection for Synthesis (Competitive) ---")
    stage3_data = profile_content_competitively(stage2_data, location=selected_location)
    logger.info(f"--- Stage 3 Completed ---")

    # --- Data Persistence ---
    final_data = {
        "original_query": initial_query,
        "location": selected_location,
        "stage1_output": stage1_data,
        "final_sub_query_profiles": stage3_data,
    }

    json_filepath = save_structured_data(final_data)
    logger.info(f"All captured data saved to {json_filepath}")

    # --- Content Strategy Generation ---
    logger.info("--- Starting Final Step: Content Strategy Generation ---")
    generate_content_plan(json_filepath)
    logger.info("--- Content strategy generation complete ---")

    logger.info("Query Fan-Out Simulation finished successfully.")

if __name__ == "__main__":
    main()