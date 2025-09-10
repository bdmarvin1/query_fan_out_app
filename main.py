from stages.stage1_expander import expand_query
from stages.stage2_router import route_subqueries
from stages.stage3_profiler import profile_content_competitively
from utils.file_logger import setup_logger, save_structured_data
from reporting.content_planner import generate_content_plan
import difflib

def get_validated_location(logger):
    # Simulated data for search locations based on typical Firecrawl format
    # In a real scenario, this would be loaded from firecrawl.dev/search_locations.json
    SEARCH_LOCATIONS = [
        {"name": "United States", "code": "us"},
        {"name": "United Kingdom", "code": "uk"},
        {"name": "Canada", "code": "ca"},
        {"name": "Australia", "code": "au"},
        {"name": "Germany", "code": "de"},
        {"name": "France", "code": "fr"},
        {"name": "India", "code": "in"},
        {"name": "Japan", "code": "jp"},
        {"name": "Brazil", "code": "br"},
        {"name": "Mexico", "code": "mx"},
        {"name": "Spain", "code": "es"},
        {"name": "Italy", "code": "it"},
        {"name": "Netherlands", "code": "nl"},
        {"name": "Singapore", "code": "sg"},
        {"name": "South Africa", "code": "za"},
        {"name": "Ireland", "code": "ie"},
        {"name": "New Zealand", "code": "nz"},
        {"name": "China", "code": "cn"},
        {"name": "Russia", "code": "ru"},
        {"name": "Argentina", "code": "ar"},
        {"name": "Austria", "code": "at"},
        {"name": "Belgium", "code": "be"},
        {"name": "Switzerland", "code": "ch"},
        {"name": "Denmark", "code": "dk"},
        {"name": "Finland", "code": "fi"},
        {"name": "Hong Kong", "code": "hk"},
        {"name": "Indonesia", "code": "id"},
        {"name": "Malaysia", "code": "my"},
        {"name": "Norway", "code": "no"},
        {"name": "Philippines", "code": "ph"},
        {"name": "Poland", "code": "pl"},
        {"name": "Portugal", "code": "pt"},
        {"name": "Sweden", "code": "se"},
        {"name": "Thailand", "code": "th"},
        {"name": "Turkey", "code": "tr"},
        {"name": "United Arab Emirates", "code": "ae"}
    ]
    
    location_names = [loc["name"].lower() for loc in SEARCH_LOCATIONS]
    location_codes = [loc["code"].lower() for loc in SEARCH_LOCATIONS]

    while True:
        user_location_input = input("Enter a target location (e.g., 'United States' or 'us'), or type 'skip' to proceed without a location: ").strip().lower()
        if user_location_input == 'skip':
            logger.info("User chose to skip location filtering.")
            return None

        found_location_code = None

        # Try exact match for name or code
        for loc in SEARCH_LOCATIONS:
            if user_location_input == loc["name"].lower() or user_location_input == loc["code"].lower():
                found_location_code = loc["code"]
                break

        if found_location_code:
            logger.info(f"Valid location selected: {found_location_code}")
            return found_location_code
        else:
            # Try nearest match
            all_location_terms = location_names + location_codes
            close_matches = difflib.get_close_matches(user_location_input, all_location_terms, n=3, cutoff=0.6)
            
            if close_matches:
                suggestions = []
                for match in close_matches:
                    # Find the original location object for the suggestion
                    for loc in SEARCH_LOCATIONS:
                        if loc["name"].lower() == match or loc["code"].lower() == match:
                            suggestions.append(f"{loc['name']} ({loc['code']})")
                            break
                logger.warning(f"Location not found. Did you mean one of these? {', '.join(suggestions)}")
            else:
                logger.warning(f"Location '{user_location_input}' not found and no close matches. Please try again or type 'skip'.")

def main():
    logger = setup_logger()
    logger.info("Starting Query Fan-Out Simulator.")

    # Get user input
    initial_query = input("Enter your query: ")
    logger.info(f"Initial query received: '{initial_query}'")
    
    # Get and validate location input
    selected_location = get_validated_location(logger)
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
    logger.info("--- Stage 3 Completed ---")
    
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