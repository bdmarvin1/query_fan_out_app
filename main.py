import json
import difflib
from datetime import datetime
from stages.stage1_expander import expand_query
from stages.stage2_router import route_subqueries
from stages.stage3_profiler import profile_content_competitively
from utils.file_logger import setup_logger, save_structured_data
from reporting.content_planner import generate_content_plan
from utils.cost_tracker import CostTracker

def load_search_locations(logger):
    """Loads search locations from the locations.json file."""
    try:
        with open('locations.json', 'r', encoding='utf-8') as f:
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
    """Gets and validates the user's target location with interactive confirmation."""
    if not search_locations:
        logger.warning("No search locations loaded. Skipping location validation.")
        return None

    while True:
        user_location_input = input("Enter a target location (e.g., 'San Jose' or 'ca-us'), or type 'skip' to proceed: ").strip().lower()
        if user_location_input == 'skip':
            logger.info("User chose to skip location filtering.")
            return None

        matches = [
            loc for loc in search_locations 
            if user_location_input in loc["name"].lower() or 
               user_location_input in loc["canonicalName"].lower() or
               (loc.get("countryCode") and user_location_input in loc["countryCode"].lower())
        ]

        if len(matches) == 1:
            match = matches[0]
            confirm = input(f"Found one match: {match['canonicalName']}. Is this correct? (yes/no): ").strip().lower()
            if confirm in ['y', 'yes']:
                logger.info(f"Location confirmed: {match['canonicalName']}")
                return match['canonicalName']
            else:
                print("Confirmation denied. Please try again.")
                continue

        elif len(matches) > 1:
            display_limit = 10
            print(f"Found {len(matches)} possible locations. Showing top {min(len(matches), display_limit)}. Please choose one:")
            for i, match in enumerate(matches[:display_limit]):
                print(f"{i + 1}: {match['canonicalName']}")
            if len(matches) > display_limit:
                print("   ... and many more.")
            
            try:
                choice = int(input(f"Enter the number (1-{min(len(matches), display_limit)}): ")) - 1
                if 0 <= choice < min(len(matches), display_limit):
                    selected = matches[choice]
                    logger.info(f"Location selected by user: {selected['canonicalName']}")
                    return selected['canonicalName']
                else:
                    logger.warning("Invalid number selected. Please try again.")
            except ValueError:
                logger.warning("Invalid input. Please enter a number.")
            continue
            
        else:
            all_location_terms = [loc["canonicalName"].lower() for loc in search_locations]
            close_matches = difflib.get_close_matches(user_location_input, all_location_terms, n=3, cutoff=0.7)
            
            if close_matches:
                logger.warning(f"Location not found. Did you mean one of these? {', '.join(close_matches)}")
            else:
                logger.warning(f"Location '{user_location_input}' not found. No close matches. Please try again.")


def main():
    run_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    logger = setup_logger(run_timestamp)
    cost_tracker = CostTracker(run_timestamp)
    cost_tracker.start_run()
    
    logger.info("Starting Query Fan-Out Simulator.")

    search_locations = load_search_locations(logger)

    initial_query = input("Enter your query: ")
    logger.info(f"Initial query received: '{initial_query}'")

    selected_location = get_validated_location(logger, search_locations)
    logger.info(f"Selected location for search: {selected_location if selected_location else 'None'}")

    logger.info("--- Starting Stage 1: Query Expansion ---")
    stage1_data = expand_query(initial_query)
    logger.info(f"--- Stage 1 Completed ---")

    logger.info("--- Starting Stage 2: Subquery Routing ---")
    stage2_data = route_subqueries(stage1_data)
    logger.info(f"--- Stage 2 Completed ---")

    logger.info("--- Starting Stage 3: Competitive Analysis ---")
    stage3_data = profile_content_competitively(stage2_data, location=selected_location, cost_tracker=cost_tracker)
    logger.info(f"--- Stage 3 Completed ---")

    final_data = {
        "original_query": initial_query,
        "location": selected_location,
        "stage1_output": stage1_data,
        "final_sub_query_profiles": stage3_data,
    }

    json_filepath = save_structured_data(final_data, run_timestamp)
    logger.info(f"All captured data saved to {json_filepath}")

    logger.info("--- Starting Final Step: Content Strategy Generation ---")
    generate_content_plan(json_filepath, cost_tracker=cost_tracker, run_timestamp=run_timestamp)
    logger.info(f"--- Content strategy generation complete ---")
    
    logger.info("Query Fan-Out Simulation finished successfully.")
    cost_tracker.end_run()

if __name__ == "__main__":
    main()