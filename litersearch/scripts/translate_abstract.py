#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摘要翻译模块
支持使用 Claude API 或自定义 LLM API 自动翻译医学论文摘要

使用方法：
    python translate_abstract.py --text "摘要内容" --api claude
    python translate_abstract.py --text "摘要内容" --api custom --url "https://api.example.com/v1/chat/completions"
"""

import os
import sys
import json
import logging
import argparse
from typing import Optional, Dict

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# 翻译提示词模板
# ============================================================================
TRANSLATION_PROMPT = """请将以下医学论文摘要翻译成中文，要求：

1. 保持医学术语的准确性和规范性
2. 保留关键专业名词的英文原文（如研究方法、统计指标等）
3. 使用学术化的中文表达
4. 保持原文的逻辑结构（背景-方法-结果-结论）
5. 对于疾病名称，使用中国大陆的标准译名（如 dementia → 痴呆症）

摘要：
{abstract}

请直接输出中文翻译，不要包含任何解释或额外内容。"""


# ============================================================================
# Claude API 翻译
# ============================================================================
def translate_with_claude(
    text: str,
    api_key: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022"
) -> Optional[str]:
    """
    使用 Claude API 翻译摘要

    参数：
        text: 待翻译的英文摘要
        api_key: Claude API Key（如果为空则从环境变量读取）
        model: Claude 模型名称

    返回：
        中文翻译，失败返回 None
    """
    if not HAS_REQUESTS:
        logger.error("requests 库未安装，请运行: pip install requests")
        return None

    # 获取 API Key
    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        logger.error("未找到 Claude API Key。请设置 ANTHROPIC_API_KEY 环境变量或通过参数传入。")
        return None

    # 构建请求
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    prompt = TRANSLATION_PROMPT.format(abstract=text)

    payload = {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        logger.info("正在调用 Claude API 进行翻译...")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            logger.error(f"Claude API 请求失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None

        result = response.json()
        translation = result.get('content', [{}])[0].get('text', '')

        if translation:
            logger.info("翻译成功")
            return translation.strip()
        else:
            logger.error("API 返回为空")
            return None

    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return None


# ============================================================================
# 自定义 LLM API 翻译（OpenAI 兼容格式）
# ============================================================================
def translate_with_custom_api(
    text: str,
    api_url: str,
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo"
) -> Optional[str]:
    """
    使用自定义 LLM API 翻译摘要（OpenAI 兼容格式）

    参数：
        text: 待翻译的英文摘要
        api_url: API 端点 URL
        api_key: API Key（可选）
        model: 模型名称

    返回：
        中文翻译，失败返回 None
    """
    if not HAS_REQUESTS:
        logger.error("requests 库未安装，请运行: pip install requests")
        return None

    # 构建请求
    headers = {
        "Content-Type": "application/json"
    }

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    prompt = TRANSLATION_PROMPT.format(abstract=text)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }

    try:
        logger.info(f"正在调用自定义 API 进行翻译: {api_url}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            logger.error(f"API 请求失败: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return None

        result = response.json()

        # 尝试解析 OpenAI 格式
        translation = result.get('choices', [{}])[0].get('message', {}).get('content', '')

        if translation:
            logger.info("翻译成功")
            return translation.strip()
        else:
            logger.error("API 返回为空")
            return None

    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return None


# ============================================================================
# 批量翻译笔记中的摘要
# ============================================================================
def translate_note_abstract(
    note_path: str,
    api_type: str = "claude",
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> bool:
    """
    翻译笔记文件中的摘要

    参数：
        note_path: 笔记文件路径
        api_type: API 类型（claude 或 custom）
        api_url: 自定义 API URL（仅当 api_type=custom 时需要）
        api_key: API Key
        model: 模型名称

    返回：
        是否成功
    """
    try:
        # 读取笔记
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取摘要
        import re
        abstract_match = re.search(r'## 摘要\n\n(.*?)\n\n## 摘要翻译', content, re.DOTALL)

        if not abstract_match:
            logger.warning(f"未找到摘要部分: {note_path}")
            return False

        abstract = abstract_match.group(1).strip()

        if not abstract or abstract == "[摘要不可用]":
            logger.warning(f"摘要为空: {note_path}")
            return False

        # 检查是否已翻译
        if re.search(r'## 摘要翻译\n\n(?!\[待补充)', content):
            logger.info(f"摘要已翻译，跳过: {note_path}")
            return True

        # 翻译
        if api_type == "claude":
            translation = translate_with_claude(abstract, api_key, model or "claude-3-5-sonnet-20241022")
        elif api_type == "custom":
            if not api_url:
                logger.error("使用自定义 API 时必须提供 --url 参数")
                return False
            translation = translate_with_custom_api(abstract, api_url, api_key, model or "gpt-3.5-turbo")
        else:
            logger.error(f"不支持的 API 类型: {api_type}")
            return False

        if not translation:
            return False

        # 替换翻译部分
        new_content = re.sub(
            r'## 摘要翻译\n\n\[待补充：中文翻译\].*?(?=\n\n##)',
            f'## 摘要翻译\n\n{translation}',
            content,
            flags=re.DOTALL
        )

        # 写回文件
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        logger.info(f"翻译完成: {note_path}")
        return True

    except Exception as e:
        logger.error(f"处理笔记失败: {e}")
        return False


# ============================================================================
# 命令行接口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description='医学论文摘要翻译工具'
    )

    parser.add_argument(
        '--text',
        type=str,
        help='待翻译的英文摘要'
    )

    parser.add_argument(
        '--note',
        type=str,
        help='笔记文件路径（自动提取并翻译摘要）'
    )

    parser.add_argument(
        '--api',
        type=str,
        default='claude',
        choices=['claude', 'custom'],
        help='API 类型（默认: claude）'
    )

    parser.add_argument(
        '--url',
        type=str,
        help='自定义 API URL（仅当 --api=custom 时需要）'
    )

    parser.add_argument(
        '--key',
        type=str,
        help='API Key（如果不提供则从环境变量读取）'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='模型名称（Claude: claude-3-5-sonnet-20241022, Custom: gpt-3.5-turbo）'
    )

    args = parser.parse_args()

    if not args.text and not args.note:
        parser.error("必须提供 --text 或 --note 参数")

    # 翻译文本
    if args.text:
        if args.api == 'claude':
            translation = translate_with_claude(args.text, args.key, args.model or "claude-3-5-sonnet-20241022")
        else:
            if not args.url:
                parser.error("使用自定义 API 时必须提供 --url 参数")
            translation = translate_with_custom_api(args.text, args.url, args.key, args.model or "gpt-3.5-turbo")

        if translation:
            print("\n" + "="*60)
            print("翻译结果:")
            print("="*60)
            print(translation)
            print("="*60)
        else:
            print("翻译失败")
            sys.exit(1)

    # 翻译笔记
    if args.note:
        success = translate_note_abstract(args.note, args.api, args.url, args.key, args.model)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
