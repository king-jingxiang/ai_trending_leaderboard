# AI Trending Leaderboard

[中文版本 (Chinese Version)](./README_ZH.md)

[![Crawler Status](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/crawler.yml/badge.svg)](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/crawler.yml)
[![Deploy Web](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/deploy-web.yml/badge.svg)](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/deploy-web.yml)

A professional platform to track, analyze, and visualize trending AI-related GitHub projects. This project provides a curated leaderboard, detailed insights, and historical growth data for the rapidly evolving AI ecosystem.

🌐 **Live Demo:** [https://king-jingxiang.github.io/ai_trending_leaderboard/](https://king-jingxiang.github.io/ai_trending_leaderboard/)

## 🚀 Features

- **Daily Updates**: Data is automatically fetched and updated every day to ensure the latest trends are captured.
- **Smart Categorization**: Projects are automatically classified using the **Gemini 3 Flash Preview** model into granular categories (e.g., LLM, Agent Framework, MLOps).
- **Multi-Dimensional Ranking**: Projects are ranked not just by stars, but by a weighted score including forks and recent growth trends.
- **Interactive Visualization**:
  - **Star History**: Visualize the growth trajectory of projects over time.
  - **Category Explorer**: Filter and explore projects by specific domains.
- **Detailed Insights**: View 90-day growth metrics, weekly trends, and more.

## 📊 Star History

Track the growth of this project itself:

[![Star History Chart](https://api.star-history.com/svg?repos=king-jingxiang/ai_trending_leaderboard&type=Date)](https://star-history.com/#king-jingxiang/ai_trending_leaderboard&Date)

## 🏷️ Category Management

We maintain a strict and organized categorization system to help users find relevant tools easily.

- **View Categories**: All project category mappings are maintained in [PROJECT_CATEGORIES.md](./PROJECT_CATEGORIES.md).
- **Classification Model**: We use **Gemini 3 Flash Preview** as the default model for intelligent tagging and categorization.

### How to Contribute to Categories

We welcome community contributions to improve the accuracy of our project classifications!

1.  **Check Existing Categories**: Refer to [PROJECT_CATEGORIES.md](./PROJECT_CATEGORIES.md) to see current mappings.
2.  **Submit Changes**:
    - **Pull Request (PR)**: Directly edit `PROJECT_CATEGORIES.md` and submit a PR.
    - **Issue**: Open an issue describing the project and the suggested category change.

## 🛠️ Project Structure

- `crawler/`: Python-based data collection engine. Fetches data from GitHub, analyzes it with Gemini, and stores it in S3/R2.
- `web/`: React + Vite frontend application for visualizing the leaderboard and insights.
- `.github/workflows/`: Automated CI/CD pipelines for daily crawling and frontend deployment.

## ⚙️ Setup & Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Cloudflare R2 or S3 compatible storage
- GitHub Token
- Gemini API Key

### Crawler (Data Collection)

1.  Navigate to `crawler/`:
    ```bash
    cd crawler
    pip install -r requirements.txt
    ```

2.  Set up environment variables (`.env`):
    ```env
    GITHUB_TOKEN=your_github_token
    GEMINI_API_KEY=your_gemini_key
    S3_ENDPOINT_URL=...
    S3_ACCESS_KEY_ID=...
    S3_SECRET_ACCESS_KEY=...
    S3_BUCKET_NAME=ai-trending-data
    ```

3.  Run the crawler:
    ```bash
    python -m crawler.main
    ```

### Web UI (Visualization)

1.  Navigate to `web/`:
    ```bash
    cd web
    npm install
    ```

2.  Run development server:
    ```bash
    npm run dev
    ```

3.  Build for production:
    ```bash
    npm run build
    ```

## 📦 Deployment

- **Data**: Automatically runs daily via GitHub Actions (`.github/workflows/crawler.yml`) and saves JSON to S3/R2.
- **Frontend**: Automatically deploys to GitHub Pages on push to main (`.github/workflows/deploy-web.yml`).

## 🔧 Configuration

Configure the S3 bucket URL in `web/src/lib/api.ts` or via `VITE_DATA_URL` environment variable during build.

## 🔮 Future Roadmap

We are expanding beyond just tracking GitHub projects. Our goal is to provide comprehensive support for AI development scenarios.

### 1. Technical Stack Selection Reference

We plan to provide hierarchical open-source project recommendations based on different development scenarios. The architecture is layered as follows:

| Architecture Layer | Core Function/Description |
| :--- | :--- |
| **Application Interaction Layer** | Responsible for interaction with users or external systems, providing RESTful API, Web/Mobile UI, IM connectors, etc. |
| **Business Layer** | Core agent logic, responsible for implementing various business requirements. |
| **Engine Layer** | Agent orchestration and workflow engines, coordinating workflows between components. |
| **Memory & Knowledge Layer** | Long-term memory (RAG), short-term working memory (Session), and state persistence. |
| **Skill Layer** | Records methods/experiences for completing specific tasks; "Soft Assets" (SOP/Prompt). |
| **Tool Layer** | External tools connecting systems or databases; "Hard Assets" (API/Code). |
| **Observability Layer (Vertical)** | Monitoring, logging, metrics for recording system status and issue resolution. |
| **Data Storage Layer** | Provides storage services like vector DBs, relational DBs, object storage, etc. |
| **AI Gateway Layer** | Unified OpenAI-compatible API interface, shielding model provider differences. |
| **Model Foundation Layer** | Inference frameworks providing LLM, VLM, Embedding model inference APIs. |

### 2. Conversational Recommendation

We will introduce a conversational interface that recommends reasonable open-source projects based on specific user requirements.

### 3. High-Growth Project Analysis & Trend Prediction

By analyzing high-growth projects over specific periods, we will:
- Identify technical development trends.
- Track user and media movements.
- Predict future technical directions to help you stay ahead of the next generation of technology.

### 4. Agent Skill for Technical Selection Support

We will provide a dedicated Agent Skill. Users can describe their requirements in natural language, and the Skill will automatically analyze and recommend suitable technology stacks and open-source project combinations, providing personalized technical selection references.

