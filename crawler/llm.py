import os
import json
import logging
import time
import random
from typing import List, Dict, Set, Optional

import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

TAG_HIERARCHY = {
    "Infrastructure & MLOps": {
        "desc": "专注于 AI 模型的底层基础设施、全生命周期管理与性能优化。包括模型预训练/微调框架、推理服务引擎、模型压缩与量化、MLOps 监控与部署平台、以及 GPU/算力资源管理工具。旨在支持模型的开发、训练、部署和运维。",
        "children": {
            "Model Training": "预训练、微调框架、分布式训练 (e.g., DeepSpeed, Megatron-LM, Axolotl, LLaMA-Factory, Torchtune)",
            "Inference & Serving": "推理引擎、模型服务、量化部署 (e.g., vLLM, TGI, llama.cpp, TensorRT-LLM, SGLang)",
            "Quantization & Optimization": "模型压缩、量化工具、加速库 (e.g., AutoGPTQ, bitsandbytes, AWQ, GGUF)",
            "MLOps & Observability": "模型监控、日志、部署管理、Prompt管理 (e.g., LangFuse, Arize Phoenix, Weights & Biases, MLflow)",
            "AI Gateway": "API 网关、模型路由、流量管理 (e.g., One API, LiteLLM, RouteLLM, Gateway)",
            "Compute & Hardware": "GPU/NPU 管理、异构计算、算力调度 (e.g., SkyPilot, dstack, K8s Device Plugins)",
        },
    },
    "Models & Architectures": {
        "desc": "核心 AI 模型权重、网络架构设计与算法研究。涵盖大型语言模型 (LLM)、多模态/视觉模型、音频/语音模型、轻量化端侧模型 (SLM)、Embedding 向量模型以及 OCR 等特定任务模型。侧重于模型本身的能力与结构。",
        "children": {
            "LLM": "大语言模型基座、Chat模型 (e.g., Llama 3, Qwen 2.5, Mistral, Gemma, DeepSeek)",
            "Vision & Multimodal": "多模态大模型、视觉生成、OCR (e.g., Stable Diffusion, Flux, LLaVA, Qwen-VL, Midjourney-API)",
            "Audio & Speech": "语音识别(ASR)、语音合成(TTS)、音乐生成 (e.g., Whisper, CosyVoice, ChatTTS, Fish Speech, F5-TTS)",
            "Small Language Model": "端侧模型、轻量化小模型 (e.g., Phi-3, Qwen-1.5-1.8B, Gemma-2B, MobileLLM)",
            "Embedding & Rerank": "向量模型、重排序模型 (e.g., BGE, Jina Embeddings, Nomic Embed, Cohere Rerank)",
            "OCR & Document Processing": "光学字符识别、文档解析、OCR 工具 (e.g., PaddleOCR, MinerU, OmniParser, Marker, GeneralOCR)",
        },
    },
    "Application Frameworks": {
        "desc": "用于构建、编排和集成 AI 应用的中间件与开发框架。包括 Agent 智能体开发框架、RAG 检索增强生成套件、向量数据库、工作流编排工具 (Workflow) 以及 AI 应用的前端交互界面 (UI)。侧重于将模型转化为实际应用。",
        "children": {
            "Agent Framework": "智能体框架、多智能体协作 (e.g., LangChain, AutoGen, CrewAI, LangGraph, PydanticAI)",
            "RAG & Knowledge": "检索增强生成、知识库管理、文档解析 (e.g., LlamaIndex, Haystack, R2R, GraphRAG, Kotaemon)",
            "Vector Database": "向量数据库、向量检索引擎 (e.g., Milvus, Chroma, Qdrant, Weaviate, Pgvector)",
            "Workflow & Orchestration": "工作流编排、低代码/无代码 AI 流程 (e.g., Dify, Flowise, LangFlow, n8n, Bisheng)",
            "Interface & UI": "AI 应用前端、Chat UI (e.g., Streamlit, Gradio, Open WebUI, Chainlit, Lobe Chat)",
            
        },
    },
    "Tools": {
        "desc": "供大模型调用的工具集、插件与扩展能力。包括 Model Context Protocol (MCP) 服务器、Agent Skills（智能体技能）、代码解释器接口及其他辅助 AI 模型交互的工具。",
        "children": {
            "Plugin & Tools": "供大模型调用的工具服务、MCP 服务，以及其他辅助工具等 (e.g., Model Context Protocol (MCP) Servers, Code Interpreter API)",
            "Agent Skill": "智能体技能、自主智能体有关的skill和经验 (e.g., anthropics/skills, obra/superpowers, Community Agent Skills)",
        },
    },
    "Applications & Products": {
        "desc": "面向最终用户的成品级 AI 应用与软件产品。包括代码助手、聊天机器人、AI 搜索工具、内容创作平台 (图像/视频/音频)、教育/办公效率工具、浏览器 Agent 以及游戏娱乐应用。强调开箱即用的产品体验。",
        "children": {
            "Coding Assistant": "代码补全、编程助手、IDE 插件 (e.g., Copilot, Cursor, Continue, Aider, Twinny)",
            "Chat & Messaging": "对话机器人、客服系统、社交伴侣 (e.g., LibreChat, ChatGPT-Next-Web, Jan, Hollama)",
            "Search & Research": "AI 搜索、深度研究助手 (e.g., Perplexica, GPT Researcher, Open Perplex, Search1API)",
            "Creative & Media": "图像/视频/音频创作工具、内容生成平台 (e.g., ComfyUI, Fooocus, InvokeAI, Diffusers-WebUI)",
            "Marketing & SEO": "营销文案、SEO 优化、社媒运营 (e.g., SEO.AI, Content generation scripts)",
            "Education & Learning": "教育辅导、语言学习、题库生成 (e.g., Open LMS, Coursebox, Quiz generators)",
            "Productivity": "办公效率、写作助手、摘要工具、笔记 (e.g., AFFiNE, AppFlowy, Obsidian AI plugins)",
            "Browser Use": "浏览器自动化、Web Agent (e.g., Browser Use, LaVague, OpenAdapt)",
            "Gaming & Entertainment": "游戏 AI、互动剧情、角色扮演 (e.g., Open AI Games, NPC generators)",
        },
    },
    "Data & Evaluation": {
        "desc": "围绕 AI 数据的全链路处理与模型能力评测。包括数据清洗/合成/标注工具、开源数据集仓库、以及模型性能评估榜单与测试框架。侧重于数据质量与模型效果验证。",
        "children": {
            "Data Engineering": "数据清洗、合成数据生成、数据标注 (e.g., Unstructured, Label Studio, Argilla, Distilabel)",
            "Datasets": "开源数据集、预训练语料 (e.g., HuggingFace Datasets, FineWeb, RedPajama, Common Crawl)",
            "Benchmark & Evaluation": "模型评测榜单、评估框架 (e.g., OpenCompass, LM-Evaluation-Harness, Ragas, DeepEval)",
        },
    },
    "Domain Specific AI": {
        "desc": "针对特定垂直领域的 AI 解决方案与应用。涵盖 AI for Science (生物/化学/物理)、具身智能与机器人 (Robotics)、网络安全与风控 (Security)、以及金融 (FinTech) 和法律 (Legal) 等专业领域的 AI 落地。",
        "children": {
            "AI for Science": "生物医药、材料科学、数学物理 (e.g., AlphaFold, BioNeMo, DeepChem, OpenFold)",
            "Robotics & Embodied": "具身智能、机器人控制、自动驾驶 (e.g., Open X-Embodiment, Aloha, LeRobot, Octo)",
            "Security & Safety": "AI 安全、内容风控、隐私保护 (e.g., Guardrails AI, LlamaGuard, Presidio, LlamaFirewall)",
            "FinTech & Legal": "金融与法律领域的 AI 应用 (e.g., FinGPT, LawGPT)",
        },
    },
    "Learning & Resources": {
        "desc": "AI 领域的学习资源、学术研究与社区资料。包括教程课程、最佳实践指南 (Awesome Lists)、学术论文集合与研究资源。侧重于知识传播与教育。",
        "children": {
            "Tutorials & Courses": "教程、课程、最佳实践指南，项目名称包含awesome的项目 (e.g., Andrew Ng Courses, Fast.ai, Awesome-LLM)",
            "Papers & Research": "论文列表、学术研究资源 (e.g., Arxiv Sanity, Papers with Code)",
        },
    },
    "Non-AI": {
        "desc": "与人工智能、机器学习或大模型无直接关联的项目。例如纯前端 UI 库（非 AI 专用）、通用后端框架、区块链、硬件驱动（非 AI 加速卡）等。",
        "children": {},
    },
}

# --- Helper Functions ---

def _format_primary_tags_desc() -> str:
    lines = []
    for tag, info in TAG_HIERARCHY.items():
        lines.append(f"- {tag}: {info['desc']}")
    return "\n".join(lines)

def _format_secondary_tags_desc(primary_tag: str) -> str:
    info = TAG_HIERARCHY.get(primary_tag)
    if not info or not info.get("children"):
        return ""
    lines = []
    for tag, desc in info["children"].items():
        lines.append(f"- {tag}: {desc}")
    return "\n".join(lines)

def _dedupe_list(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

class LLMClient:
    def __init__(self):
        # Configuration from environment variables with defaults matching update_project_tags_v2.py
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-Empty")
        self.base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:3000/v1")
        self.model_name = os.getenv("OPENAI_MODEL", "Qwen3-235B-A22B")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def _call_openai_with_retry(self, messages: List[Dict[str, str]], retries: int = 3) -> Optional[str]:
        """
        Calls OpenAI API with exponential backoff retry.
        """
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"OpenAI API call failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    sleep_time = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Max retries reached. Error: {e}")
                    return None
        return None

    def generate_tags(self, repo_data: dict) -> dict:
        """
        Generates tags for a repository based on its description and readme.
        Returns a dictionary with 'primary_tags' and 'secondary_tags'.
        Uses a two-step classification process.
        """
        full_name = repo_data.get("full_name", "")
        description = repo_data.get("description", "")
        readme = repo_data.get("readme", "")[:8000] # Truncate to avoid context limit
        topics = repo_data.get("topics", [])

        repo_context = f"""
**Repository**: {full_name}
**Description**: {description}
Topics: {topics}
README Snippet: 
---
{readme}
---
"""

        # --- Step 1: Primary Classification ---
        primary_options = _format_primary_tags_desc()
        
        # Note: We append JSON instructions to match the structured output behavior of the original script
        primary_system_prompt = """You are a professional open-source project classifier. 
Your task is to classify the project into ONE primary category based on its description and README.

**Constraint: Single Best Match**
You must select exactly one primary category that is most relevant to the project's core function. If a project seems to fit multiple categories, choose the one that represents its main value proposition or architectural focus.

Before providing the final tag, output a brief thinking process (max 50 words) analyzing the project's key features and why the chosen category is the best fit compared to others.

Please return a valid JSON object with the following structure:
{
    "thinking_process": "Brief thinking process...",
    "primary_tag": "The single most appropriate primary category",
    "reason": "Brief reason for the choice"
}
"""
        primary_user_prompt = f"""
{repo_context}

Please classify this project into ONE of the following primary categories:
{primary_options}

Note: If the project is clearly not related to AI/ML, choose 'Non-AI'.
"""
        
        logger.info(f"Running primary classification for {full_name}")
        
        primary_response_text = self._call_openai_with_retry([
            {"role": "system", "content": primary_system_prompt},
            {"role": "user", "content": primary_user_prompt}
        ])

        primary_tag = ""
        if primary_response_text:
            try:
                p_data = json.loads(primary_response_text)
                primary_tag = p_data.get("primary_tag", "").strip()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode primary classification JSON for {full_name}")
        
        # Validation
        if primary_tag not in TAG_HIERARCHY:
            logger.warning(f"Invalid primary tag returned for {full_name}: {primary_tag}. Fallback to Non-AI.")
            # Simple strict check as per original script logic
            if "Non-AI" in TAG_HIERARCHY:
                primary_tag = "Non-AI"
            else:
                return {"primary_tags": [], "secondary_tags": []}

        # If Non-AI, we are done
        if primary_tag == "Non-AI":
            return {"primary_tags": ["Non-AI"], "secondary_tags": []}

        # --- Step 2: Secondary Classification ---
        secondary_options = _format_secondary_tags_desc(primary_tag)
        
        # If no secondary options, return early
        if not secondary_options:
             return {"primary_tags": [primary_tag], "secondary_tags": []}

        secondary_system_prompt = """You are a professional open-source project classifier.
Your task is to select appropriate secondary tags (sub-categories) for the project, given its assigned primary category.

**DEFAULT STRATEGY: A project usually corresponds to only one most relevant secondary tag.**
This is the preferred rule. You must strictly follow this unless there is a special justification.

**EXCEPTION CLAUSE:**
Only in rare cases, when a project objectively spans multiple distinct secondary categories and each category significantly matches the project's core content, is it allowed to assign multiple secondary tags (up to 3).
**Judgment Criteria:** The secondary categories must have comparable importance and relevance to the project. If one category is clearly dominant, select only that one.

Before selecting tags, you must output a brief thinking process (max 50 words) to justify your decision, specifically weighing the "one tag default" against the "multi-tag exception".

Please return a valid JSON object with the following structure:
{
    "thinking_process": "Brief thinking process...",
    "secondary_tags": ["tag1", "tag2"]
}
"""

        secondary_user_prompt = f"""
{repo_context}

The project has been classified as Primary Category: "{primary_tag}".
Please select 1 to 3 Secondary Tags from the following list that apply to this project:
{secondary_options}
"""

        logger.info(f"Running secondary classification for {full_name}")
        
        secondary_response_text = self._call_openai_with_retry([
            {"role": "system", "content": secondary_system_prompt},
            {"role": "user", "content": secondary_user_prompt}
        ])

        secondary_tags = []
        if secondary_response_text:
            try:
                s_data = json.loads(secondary_response_text)
                secondary_tags = s_data.get("secondary_tags", [])
            except json.JSONDecodeError:
                logger.error(f"Failed to decode secondary classification JSON for {full_name}")
        
        # Validation: Ensure tags are valid children
        valid_children = TAG_HIERARCHY[primary_tag].get("children", {}).keys()
        valid_secondary = [t for t in secondary_tags if t in valid_children]
        valid_secondary = _dedupe_list(valid_secondary)[:3] # Limit to 3

        return {"primary_tags": [primary_tag], "secondary_tags": valid_secondary}
