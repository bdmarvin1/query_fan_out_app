# Query Fan-Out Simulator for Content Strategy

This Python application is an expert tool designed to reverse-engineer the "Query Fan-Out" process used by modern AI-powered search engines. Its primary goal is not to generate answers, but to simulate the entire query expansion, routing, and selection pipeline to discover the full spectrum of sub-queries, latent intents, and content characteristics that AI systems use to build their responses.

This data is then used to generate a highly actionable, data-driven content strategy, enabling creators to build content that is perfectly optimized for visibility in generative search results.

## Core Concepts

The application is built around the three core stages of the Query Fan-Out process, using a sophisticated, data-driven approach:

1.  **Stage 1: Query Expansion & Latent Intent Mining:** The initial user query is sent to the Google Gemini 2.5 Pro model, which performs a complete deconstruction. It identifies user intent, finds explicit and implicit slots, projects latent concepts, generates dozens of rewrites and diversifications, and speculates on likely follow-up questions.

2.  **Stage 2: Subquery Routing & Fan-Out Mapping:** Each of the sub-queries generated in Stage 1 is then analyzed by Gemini. The model determines the most appropriate source types (e.g., blogs, forums, e-commerce sites) and content modalities (e.g., text, table, video) for finding the best answer to that specific sub-query.

3.  **Stage 3: Content Profiling via Competitive Analysis:** This is the data-driven core of the application. For each sub-query, the system performs a live web search to find the top-ranking competitors. It scrapes their content and feeds it to Gemini for analysis. The model then synthesizes a detailed "ideal content profile" with a brief on how to create a new piece of content that can outperform the current winners based on five key criteria: Extractability, Evidence Density, Scope Clarity, Authority Signals, and Freshness.

## Features

-   **AI-Powered Simulation:** Uses Google's Gemini 2.5 Pro model for sophisticated, human-like analysis and generation at every stage.
-   **Data-Driven Competitive Analysis:** Goes beyond pure simulation by searching and scraping top-ranking content to ground its strategic recommendations in real-world data.
-   **Strategic Content Clustering:** The final report groups dozens of sub-queries into logical "Content Pillars," preventing content cannibalization and promoting the creation of comprehensive topic hubs.
-   **Actionable Markdown Reports:** Generates a clean, human-readable markdown file with detailed briefs for each content pillar, including target keywords and competitive insights.
-   **Verbose Logging:** Creates a detailed log for every run, including the full prompts sent to the AI and the raw responses received, providing complete transparency for analysis and debugging.
-   **Structured Data Output:** Saves all generated data in a hierarchical JSON file for further analysis or integration with other tools.

## Technology Stack

-   **Backend:** Python 3
-   **AI Model:** Google Gemini 2.5 Pro
-   **Web Scraping/Searching:** Firecrawl API
-   **Dependencies:** `google-generativeai`, `python-dotenv`

---

## Installation & Setup

Follow these steps to get the application running on your local machine.

### Prerequisites

-   Python 3.8 or higher
-   A Google AI API Key

### 1. Clone the Repository

Clone this repository to your local machine:
```bash
git clone https://github.com/bdmarvin1/query_fan_out_app.git
cd query_fan_out_app
```

### 2. Install Dependencies

Install the required Python libraries using pip:
```bash
pip install -r requirements.txt
```

### 3. Configure Your API Key

The application uses a `.env` file to securely manage your API key.

1.  Find the `.env` file in the root of the project.
2.  Open it and replace `YOUR_GOOGLE_API_KEY` with your actual key from Google AI Studio.

    ```
    # .env
    GOOGLE_API_KEY="aIzaSy..."
    ```

## How to Run

Once the setup is complete, you can run the application with a single command:

```bash
python main.py
```

The script will then prompt you to enter your initial query. The full simulation will run, providing progress updates in the console.

## Understanding the Output

After a successful run, you will find new files in the `logs/` and `output/` directories.

### Logs (`logs/`)

-   A file named `query-fan-out-run-YYYYMMDD-HHMMSS.log`.
-   This file is crucial for debugging and analysis. It contains a step-by-step log of the application's flow, including the **full prompts** sent to the Gemini API and the **raw JSON responses** received at each stage.

### Output (`output/`)

-   **Raw Data File (`fan-out-data-YYYYMMDD-HHMMSS.json`):**
    -   This is a structured JSON file containing *all* the data generated during the simulation. It has a hierarchical structure that includes the Stage 1 expansion, Stage 2 routing, and Stage 3 competitive profiles.

-   **Content Strategy Plan (`content-plan-your_query.md`):**
    -   This is the final, human-readable output. It is a single markdown file that presents the complete content strategy.
    -   It is organized into **Content Pillars**, where each pillar represents a strategic piece of content to create.
    -   Each pillar includes a detailed **Content Brief** based on competitive analysis and a list of **Target Keywords & Phrasings** that the content should address.
