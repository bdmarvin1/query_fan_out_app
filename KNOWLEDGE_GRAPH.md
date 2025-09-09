
# Project Knowledge Graph: Query Fan-Out Simulator

This document outlines the nodes and relationships within the knowledge graph for the Query Fan-Out Simulator project.

## Nodes

### Project Core
- **qfo_project**: Query Fan-Out Simulator (Project) - The project node for the Query Fan-Out Simulator application.
- **qfo_main**: Main Application Runner (Module) - Main entry point for the application. Handles user input and orchestrates the workflow through all stages.

### Application Stages
- **qfo_stage1**: Stage 1: Query Expander (Module) - Handles Stage 1: Query Expansion and Latent Intent Mining.
- **qfo_stage2**: Stage 2: Subquery Router (Module) - Handles Stage 2: Subquery Routing and Fan-Out Mapping.
- **qfo_stage3**: Stage 3: Content Profiler (Module) - Handles Stage 3: Selection for Synthesis Simulation.

### Supporting Modules
- **qfo_utils**: Utilities (Logging & I/O) (Module) - Contains utility functions for robust logging and structured data persistence (JSON).
- **qfo_reporting**: Content Strategy Generator (Module) - Generates the final, human-readable content strategy plan from the structured JSON data.

### Artifacts & Outputs
- **qfo_json_output**: Structured JSON Output (Data Artifact) - A structured JSON file that stores all captured data from the three stages for a single application run.
- **qfo_report_output**: Content Plan Output (Report Artifact) - A human-readable text or markdown file containing the actionable content plan.
- **qfo_log_output**: Execution Log File (Log Artifact) - A log file created for each run, detailing the application's flow, timings, and any errors.
- **qfo_requirements**: requirements.txt (Configuration File) - Lists all Python library dependencies for the project.

### Conceptual Stages & Processes
- **query_expansion**: Query Expansion and Latent Intent Mining
- **subquery_routing**: Subquery Routing and Fan-Out Mapping
- **selection_for_synthesis**: Selection for Synthesis
- **rewrites_diversifications**: Rewrites and Diversifications
- **latent_intent_projection**: Latent Intent Projection
- **...and other conceptual nodes**

## Relationships

- **qfo_project** `CONTAINS` **qfo_main**
- **qfo_project** `CONTAINS` **qfo_stage1**
- **qfo_project** `CONTAINS` **qfo_stage2**
- **qfo_project** `CONTAINS` **qfo_stage3**
- **qfo_project** `CONTAINS` **qfo_utils**
- **qfo_project** `CONTAINS` **qfo_reporting**
- **qfo_project** `CONTAINS` **qfo_requirements**

- **qfo_main** `CALLS` **qfo_stage1**
- **qfo_main** `CALLS` **qfo_stage2**
- **qfo_main** `CALLS` **qfo_stage3**
- **qfo_main** `CALLS` **qfo_reporting**

- **qfo_main** `USES` **qfo_utils**
- **qfo_stage1** `USES` **qfo_utils**
- **qfo_stage2** `USES` **qfo_utils**
- **qfo_stage3** `USES` **qfo_utils**
- **qfo_reporting** `USES` **qfo_utils**

- **qfo_main** `PRODUCES` **qfo_json_output**
- **qfo_utils** `PRODUCES` **qfo_log_output**
- **qfo_reporting** `CONSUMES` **qfo_json_output**
- **qfo_reporting** `PRODUCES` **qfo_report_output**

- **query_expansion** `PRECEDES` **subquery_routing**
- **subquery_routing** `PRECEDES` **selection_for_synthesis**

- **query_expansion** `HAS_SUBPROCESS` **rewrites_diversifications**
- **...and other conceptual relationships**
