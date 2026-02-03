from google import genai
from google.genai import types
from .config import Config
import json
import logging

logger = logging.getLogger(__name__)

TAG_HIERARCHY = {
    "Infrastructure & MLOps": {
        "desc": "AI 基础设施、训练推理与工程化工具",
        "children": {
            "Model Training": "预训练、微调框架、分布式训练 (e.g., DeepSpeed, Megatron)",
            "Inference & Serving": "推理引擎、模型服务、量化部署 (e.g., vLLM, TGI, llama.cpp)",
            "Quantization & Optimization": "模型压缩、量化工具、加速库 (e.g., AWQ, GPTQ)",
            "MLOps & Observability": "模型监控、日志、部署管理、Prompt管理",
            "Compute & Hardware": "GPU/NPU 管理、异构计算、算力调度",
        },
    },
    "Models & Architectures": {
        "desc": "基础模型权重、架构与算法",
        "children": {
            "LLM": "大语言模型基座、Chat模型 (e.g., Llama, Qwen, Mistral)",
            "Vision & Multimodal": "多模态大模型、视觉生成、OCR (e.g., Stable Diffusion, LLaVA)",
            "Audio & Speech": "语音识别(ASR)、语音合成(TTS)、音乐生成 (e.g., Whisper, CosyVoice)",
            "Small Language Model": "端侧模型、轻量化小模型",
            "Embedding & Rerank": "向量模型、重排序模型",
        },
    },
    "Application Frameworks": {
        "desc": "构建 AI 应用的开发框架与中间件",
        "children": {
            "Agent Framework": "智能体框架、多智能体协作 (e.g., LangChain, AutoGen)",
            "RAG & Knowledge": "检索增强生成、知识库管理、文档解析",
            "Vector Database": "向量数据库、向量检索引擎 (e.g., Milvus, Chroma)",
            "Workflow & Orchestration": "工作流编排、低代码/无代码 AI 流程 (e.g., Dify, Flowise)",
            "Interface & UI": "AI 应用前端、Chat UI (e.g., Streamlit, Gradio, Open WebUI)",
            "Plugin & Tools": "模型工具调用、MCP 协议、API 网关",
        },
    },
    "Applications & Products": {
        "desc": "直接面向用户的 AI 应用与产品",
        "children": {
            "Coding Assistant": "代码补全、编程助手、IDE 插件 (e.g., Copilot, Cursor)",
            "Chat & Messaging": "对话机器人、客服系统、社交伴侣",
            "Search & Research": "AI 搜索、深度研究助手 (e.g., Perplexity-like)",
            "Creative & Media": "图像/视频/音频创作工具、内容生成平台",
            "Marketing & SEO": "营销文案、SEO 优化、社媒运营",
            "Education & Learning": "教育辅导、语言学习、题库生成",
            "Productivity": "办公效率、写作助手、摘要工具、笔记",
            "Browser Use": "浏览器自动化、Web Agent",
            "Gaming & Entertainment": "游戏 AI、互动剧情、角色扮演",
        },
    },
    "Data & Evaluation": {
        "desc": "数据处理与模型评估",
        "children": {
            "Data Engineering": "数据清洗、合成数据生成、数据标注",
            "Datasets": "开源数据集、预训练语料",
            "Benchmark & Evaluation": "模型评测榜单、评估框架 (e.g., OpenCompass, LM-Harness)",
        },
    },
    "Domain Specific AI": {
        "desc": "特定领域的 AI 应用",
        "children": {
            "AI for Science": "生物医药、材料科学、数学物理",
            "Robotics & Embodied": "具身智能、机器人控制、自动驾驶",
            "Security & Safety": "AI 安全、内容风控、隐私保护",
            "FinTech & Legal": "金融与法律领域的 AI 应用",
        },
    },
    "Learning & Resources": {
        "desc": "学习资料与社区资源",
        "children": {
            "Tutorials & Courses": "教程、课程、最佳实践指南",
            "Papers & Research": "论文列表、学术研究资源",
        },
    },
    "Non-AI": {
        "desc": "与 AI/ML 无关的项目",
        "children": {},
    },
}

def _build_secondary_to_primary(tag_hierarchy: dict) -> dict[str, str]:
    mapping = {}
    for primary_tag, info in tag_hierarchy.items():
        for secondary_tag in info.get("children", {}):
            mapping[secondary_tag] = primary_tag
    return mapping

PRIMARY_TAGS = set(TAG_HIERARCHY.keys())
SECONDARY_TO_PRIMARY = _build_secondary_to_primary(TAG_HIERARCHY)

def _dedupe_list(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def _normalize_primary_tags(tags: list[str], allowed_primary: set[str]) -> list[str]:
    normalized = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    filtered = [t for t in normalized if t in allowed_primary]
    return _dedupe_list(filtered)

def _normalize_secondary_tags(
    tags: list[str],
    primary_tags: list[str],
    secondary_to_primary: dict[str, str],
) -> list[str]:
    normalized = [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    allowed_secondary = {tag for tag, p in secondary_to_primary.items() if p in primary_tags}
    filtered = [t for t in normalized if t in allowed_secondary]
    return _dedupe_list(filtered)

def _format_tag_hierarchy(tag_hierarchy: dict) -> str:
    lines = []
    for primary_tag, info in tag_hierarchy.items():
        lines.append(f"- {primary_tag}：{info['desc']}")
        for secondary_tag, desc in info.get("children", {}).items():
            lines.append(f"  - {secondary_tag}：{desc}")
    return "\n".join(lines)

def _limit_tags(tags: list[str], max_count: int) -> list[str]:
    return tags[:max_count]

class LLMClient:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model_name = "gemini-3-flash-preview"

    def generate_tags(self, repo_data: dict) -> dict[str, list[str]]:
        """
        Generates tags for a repository based on its description and readme.
        Returns a dictionary with 'primary_tags' and 'secondary_tags'.
        """
        if not Config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Skipping tagging.")
            return {"primary_tags": [], "secondary_tags": []}

        description = repo_data.get("description", "")
        readme = repo_data.get("readme", "")[:20000]
        topics = repo_data.get("topics", [])
        full_name = repo_data.get("full_name", "")

        tags_desc = _format_tag_hierarchy(TAG_HIERARCHY)

        prompt = f"""
仓库：{full_name}
简介：{description}
Topics：{topics}
README片段：{readme}

你是专业的开源项目分类助手。请基于仓库信息为项目打两级标签（一级=大类，二级=子类）。

规则：
1. 一级标签只有 1 个，按重要性排序，优先选择最重要，最接近的类别。
2. 二级标签通常 1~3 个，必须从所选一级标签对应的子类中选择，按重要性排序。
3. 如果项目与 AI/ML 无关，primary_tags 返回 ["Non-AI"]，secondary_tags 返回 []。
4. 尽量选择最确定的类别，避免泛化。

标签体系与含义：
{tags_desc}

Please return a JSON object with this structure:
{{
  "primary_tags": ["tag1", ...],
  "secondary_tags": ["tag2", ...]
}}
Only return the JSON.
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            data = json.loads(response.text)
            
            primary_tags = data.get("primary_tags", [])
            secondary_tags = data.get("secondary_tags", [])
            
            # Post-processing
            allowed_primary = set(TAG_HIERARCHY.keys())
            allowed_secondary_to_primary = {
                tag: primary for tag, primary in SECONDARY_TO_PRIMARY.items() if primary in allowed_primary
            }

            primary_tags = _normalize_primary_tags(primary_tags, allowed_primary)
            
            # Non-AI logic
            if "Non-AI" in primary_tags:
                primary_tags = ["Non-AI"]
                secondary_tags = []
            else:
                primary_tags = _limit_tags(primary_tags, 1)
                secondary_tags = _normalize_secondary_tags(
                    secondary_tags,
                    primary_tags,
                    allowed_secondary_to_primary,
                )
                secondary_tags = _limit_tags(secondary_tags, 3)
            
            return {"primary_tags": primary_tags, "secondary_tags": secondary_tags}
            
        except Exception as e:
            logger.error(f"Failed to generate tags for {full_name}: {e}")
            return {"primary_tags": [], "secondary_tags": []}
