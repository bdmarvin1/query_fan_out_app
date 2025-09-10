
# Query Fan-Out App

## Overview

The Query Fan-Out App is a powerful tool designed to simulate and automate the process of expanding a single user query into a comprehensive content strategy. It leverages Google's Gemini Pro API to explore latent intents, route subqueries, and perform competitive analysis, ultimately generating a detailed content plan. This app is ideal for content strategists, SEO specialists, and marketing professionals looking to create data-driven content that covers a topic exhaustively.

## Features

- **Query Expansion:** Expands a single user query into a set of related subqueries, uncovering latent intents and diversifying the topic area.
- **Subquery Routing:** Categorizes and routes expanded subqueries to the most appropriate search engines or platforms for analysis.
- **Competitive Analysis:** Profiles the top-ranking content for each subquery, extracting valuable insights into what makes them successful.
- **Content Strategy Generation:** Creates a comprehensive content plan based on the analysis, providing actionable recommendations for creating new content.
- **Cost Tracking:** Monitors and reports the costs associated with API usage, helping you manage your budget effectively.
- **Detailed Logging:** Captures every step of the process in detailed logs, making it easy to debug and understand the app's behavior.

## Workflow

The application operates in a sequential, multi-stage workflow:

1. **Initialization:** The app starts by loading necessary configurations, including search locations and API keys.
2. **User Input:** The user provides an initial query and an optional target location for the analysis.
3. **Stage 1: Query Expansion:** The initial query is sent to the Gemini Pro API, which returns a set of expanded and diversified subqueries.
4. **Stage 2: Subquery Routing:** The subqueries are routed to the most appropriate search engines or platforms for analysis.
5. **Stage 3: Competitive Analysis:** The app scrapes the top-ranking content for each subquery and uses the Gemini Pro API to generate a competitive analysis.
6. **Content Plan Generation:** A final content plan is generated based on the collected data, providing a roadmap for content creation.
7. **Output:** The app saves all the data in a structured JSON file and generates a human-readable content plan.

## Project Structure

```
.
├── .env.example
├── .gitignore
├── KNOWLEDGE_GRAPH.md
├── README.md
├── locations.json
├── main.py
├── reporting
│   └── content_planner.py
├── requirements.txt
├── stages
│   ├── stage1_expander.py
│   ├── stage2_router.py
│   └── stage3_profiler.py
├── test_gemini.py
├── test_scraper.py
└── utils
    ├── cost_tracker.py
    ├── file_logger.py
    └── gemini_client.py
```

- **`main.py`**: The main entry point of the application.
- **`stages/`**: Contains the core logic for each stage of the workflow.
- **`utils/`**: Contains utility functions for logging, cost tracking, and interacting with the Gemini Pro API.
- **`reporting/`**: Contains the logic for generating the final content plan.
- **`locations.json`**: A large JSON file containing a list of possible search locations.
- **`KNOWLEDGE_GRAPH.md`**: A detailed document outlining the project's knowledge graph, including nodes and relationships.

## Setup and Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bdmarvin1/query_fan_out_app.git
   cd query_fan_out_app
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file:**
   - Copy the `.env.example` file to a new file named `.env`.
   - Add your Google API key to the `.env` file:
     ```
     GOOGLE_API_KEY="your_api_key_here"
     ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Follow the prompts:**
   - The app will prompt you to enter your query and an optional target location.
   - The app will then run through the workflow and save the results in the `output` directory.

## Deep Dive into the Stages

### Stage 1: Query Expander

The `stage1_expander.py` module is responsible for taking the initial user query and expanding it into a set of related subqueries. It uses the Gemini Pro API to brainstorm and generate a diverse range of questions and topics related to the initial query.

### Stage 2: Subquery Router

The `stage2_router.py` module takes the expanded subqueries and routes them to the most appropriate search engines or platforms. This allows for a more targeted and efficient analysis in the next stage.

### Stage 3: Competitive Analysis

The `stage3_profiler.py` module performs a deep dive into the top-ranking content for each subquery. It uses a scraper to fetch the content and then uses the Gemini Pro API to analyze it, extracting key information such as:

- The main topics covered
- The tone and style of the content
- The target audience
- The key takeaways and conclusions

## Knowledge Graph

For a deeper understanding of the project's architecture and the relationships between its different components, refer to the `KNOWLEDGE_GRAPH.md` file. This document provides a visual representation of the project's knowledge graph, which can be a valuable resource for developers and contributors.
