# AI Trending Leaderboard

[English Version](./README.md)

[![Crawler Status](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/crawler.yml/badge.svg)](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/crawler.yml)
[![Deploy Web](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/deploy-web.yml/badge.svg)](https://github.com/king-jingxiang/ai_trending_leaderboard/actions/workflows/deploy-web.yml)

一个用于追踪、分析和可视化 AI 领域 GitHub 热门项目的专业平台。本项目提供经过精心策划的排行榜、详细的数据洞察以及 AI 生态系统的历史增长趋势。

🌐 **在线访问:** [https://king-jingxiang.github.io/ai_trending_leaderboard/](https://king-jingxiang.github.io/ai_trending_leaderboard/)

## 🚀 功能特性

- **每日更新**: 每天自动抓取并更新数据，确保捕捉到最新的趋势。
- **智能分类**: 使用 **Gemini 3 Flash Preview** 模型自动将项目分类到细粒度的领域（如 LLM, Agent Framework, MLOps 等）。
- **多维度排行**: 不仅依据 Star 数量，还综合考虑 Fork 数量和近期增长趋势进行加权评分。
- **交互式可视化**:
  - **Star History**: 可视化项目随时间变化的增长轨迹。
  - **类别探索**: 按特定领域筛选和探索项目。
- **深度洞察**: 查看 90 天增长指标、周趋势等详细数据。

## 📊 Star History

查看本项目自身的增长趋势：

[![Star History Chart](https://api.star-history.com/svg?repos=king-jingxiang/ai_trending_leaderboard&type=Date)](https://star-history.com/#king-jingxiang/ai_trending_leaderboard&Date)

## 🏷️ 类别管理

我们要维护一个严谨且有组织的分类系统，帮助用户轻松找到相关工具。

- **查看类别**: 所有项目的分类映射关系都维护在 [PROJECT_CATEGORIES.md](./PROJECT_CATEGORIES.md) 文件中。
- **分类模型**: 我们默认使用 **Gemini 3 Flash Preview** 模型进行智能打标和分类。

### 如何参与类别更新

我们欢迎社区贡献，以提高项目分类的准确性！

1.  **检查现有类别**: 参考 [PROJECT_CATEGORIES.md](./PROJECT_CATEGORIES.md) 查看当前的映射关系。
2.  **提交更改**:
    - **Pull Request (PR)**: 直接编辑 `PROJECT_CATEGORIES.md` 文件并提交 PR。
    - **Issue**: 提交 Issue 描述项目以及建议的类别更改。

## 🛠️ 项目结构

- `crawler/`: 基于 Python 的数据采集引擎。从 GitHub 获取数据，使用 Gemini 进行分析，并存储到 S3/R2。
- `web/`: React + Vite 前端应用，用于可视化排行榜和数据洞察。
- `.github/workflows/`: 用于每日爬取和前端部署的自动化 CI/CD 流程。

## ⚙️ 安装与开发

### 前置要求

- Python 3.11+
- Node.js 20+
- Cloudflare R2 或兼容 S3 的存储服务
- GitHub Token
- Gemini API Key

### Crawler (数据采集)

1.  进入 `crawler/` 目录:
    ```bash
    cd crawler
    pip install -r requirements.txt
    ```

2.  设置环境变量 (`.env`):
    ```env
    GITHUB_TOKEN=your_github_token
    GEMINI_API_KEY=your_gemini_key
    S3_ENDPOINT_URL=...
    S3_ACCESS_KEY_ID=...
    S3_SECRET_ACCESS_KEY=...
    S3_BUCKET_NAME=ai-trending-data
    ```

3.  运行爬虫:
    ```bash
    python -m crawler.main
    ```

### Web UI (可视化)

1.  进入 `web/` 目录:
    ```bash
    cd web
    npm install
    ```

2.  运行开发服务器:
    ```bash
    npm run dev
    ```

3.  构建生产版本:
    ```bash
    npm run build
    ```

## 📦 部署

- **数据**: 通过 GitHub Actions (`.github/workflows/crawler.yml`) 每日自动运行，并将 JSON 数据保存到 S3/R2。
- **前端**: 推送到 main 分支时自动部署到 GitHub Pages (`.github/workflows/deploy-web.yml`)。

## 🔧 配置

在 `web/src/lib/api.ts` 中配置 S3 存储桶 URL，或在构建期间通过 `VITE_DATA_URL` 环境变量进行配置。

## 🔮 未来规划

除了提供 GitHub 项目追踪，我们将在后续版本中支持更多重要场景，旨在打造全方位的 AI 开发生态指南。

### 1. 技术选型参考

我们将按照分层架构提供不同层级的开源项目选型推荐，以满足不同开发场景的需求。整体架构技术分层如下：

| 架构分层 | 核心功能/描述 |
| :--- | :--- |
| **应用交互层** | 主要是负责与用户或外部系统交互，提供 RESTful API、Web/Mobile UI、IM 连接器等。 |
| **业务层** | 主要以智能体为核心，负责实现各种业务逻辑。 |
| **引擎层** | 主要以智能体编排引擎和工作流编排引擎为核心，负责协调不同组件之间的工作流。 |
| **记忆与知识层** | 主要以长期记忆 (RAG)、短期工作记忆 (Session)、状态持久化等为核心，负责管理智能体的记忆和状态。 |
| **技能层** | 主要以提供完成某个工作的各种方法经验的记录；“软资产”（SOP/Prompt）。 |
| **工具层** | 主要以各种外部工具，连接各个系统或数据库的工具服务；“硬资产”（API/Code）。 |
| **可观测层（纵向）** | 主要是监控、日志、指标等，用于记录和分析系统运行状态，及时发现和解决问题。 |
| **数据存储层** | 主要是提供各种存储服务，如向量数据库、关系型数据库、对象存储服务等。 |
| **AI网关层** | 以 AI Gateway 统一提供 OpenAI-compatible 规范的 API 接口，屏蔽不同模型供应商之间的差异，方便切换不同模型供应商。 |
| **模型基座层** | 以推理框架为主，提供 LLM、VLM、Embedding 等模型推理 API。 |

### 2. 对话式推荐

我们将提供对话功能，基于用户的具体需求（如“我想搭建一个 RAG 系统”），智能给出合理的开源项目组合推荐。

### 3. 高增长项目分析与趋势预测

通过深入分析一段时间内的高增长项目，我们将：
- 剖析该时间段内的技术发展趋势。
- 追踪相关用户、媒体的关注动向。
- 进行深度研究和分析，预测下一阶段的技术走向，帮助开发者提前关注下一代技术。

### 4. Agent Skill 技术选型支持

我们将提供专门的 Agent Skill，用户可以通过自然语言描述需求，Skill 将自动分析并推荐合适的技术栈和开源项目组合，实现个性化的技术选型参考。

