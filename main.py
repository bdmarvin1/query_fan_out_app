"""
Main entry point for the Query Fan-Out Simulator application.
"""
from stages.stage1_expander import expand_query
from stages.stage2_router import route_subqueries
from stages.stage3_profiler import profile_content_competitively # <-- UPDATED
from utils.file_logger import setup_logger, save_structured_data
from reporting.content_planner import generate_content_plan

def main():
    """
    Main function to run the query fan-out simulation.
    """
    logger = setup_logger()
    logger.info("Starting Query Fan-Out Simulator.")

    # Get user input
    initial_query = input("Enter your query: ")
    logger.info(f"Initial query received: '{initial_query}'")

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
    stage3_data = profile_content_competitively(stage2_data) # <-- UPDATED
    logger.info("--- Stage 3 Completed ---")
    
    # --- Data Persistence ---
    final_data = {
        "original_query": initial_query,
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
