#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级评分系统 - 医学文献优先级评估
整合多维度评分标准：
1. 期刊影响力
2. 研究类型（RCT > Cohort > Review）
3. 中国作者和研究场景
4. 定性研究标记
5. 引用量（如果可用）
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# 高影响力期刊列表（医学领域）
# ============================================================================
HIGH_IMPACT_JOURNALS = {
    # 顶级综合医学期刊
    'new england journal of medicine': 100,
    'nejm': 100,
    'lancet': 100,
    'the lancet': 100,
    'jama': 95,
    'journal of the american medical association': 95,
    'bmj': 90,
    'british medical journal': 90,
    'plos medicine': 85,

    # 专科高影响力期刊
    'nature medicine': 100,
    'cell': 100,
    'science': 100,
    'nature': 100,
    'jama internal medicine': 90,
    'jama neurology': 90,
    'jama psychiatry': 90,
    'annals of internal medicine': 90,

    # 老年医学和痴呆症
    'alzheimer\'s & dementia': 95,
    'journal of alzheimer\'s disease': 80,
    'neurology': 90,
    'brain': 95,
    'journal of neurology neurosurgery and psychiatry': 85,

    # 初级卫生保健
    'annals of family medicine': 80,
    'british journal of general practice': 75,
    'family practice': 70,
    'bmc family practice': 70,

    # 健康政策
    'health affairs': 85,
    'health policy': 75,
    'milbank quarterly': 80,
    'health services research': 75,

    # 定性研究
    'qualitative health research': 75,
    'bmc qualitative research': 70,
    'international journal of qualitative studies on health and well-being': 70,
}

# ============================================================================
# 研究类型权重
# ============================================================================
STUDY_TYPE_WEIGHTS = {
    'rct': 100,  # 随机对照试验
    'randomized controlled trial': 100,
    'randomised controlled trial': 100,
    'systematic review': 95,  # 系统综述
    'meta-analysis': 95,  # Meta分析
    'cohort': 85,  # 队列研究
    'cohort study': 85,
    'prospective': 80,  # 前瞻性研究
    'case-control': 70,  # 病例对照
    'cross-sectional': 60,  # 横断面研究
    'qualitative': 75,  # 定性研究
    'qualitative study': 75,
    'mixed methods': 80,  # 混合方法
    'review': 65,  # 一般综述
    'case report': 40,  # 病例报告
    'case series': 45,  # 病例系列
}

# ============================================================================
# 中国相关关键词
# ============================================================================
CHINA_KEYWORDS = {
    'china', 'chinese', 'beijing', 'shanghai', 'guangzhou', 'shenzhen',
    'hong kong', 'taiwan', 'mainland china', 'prc',
    '中国', '中华', '北京', '上海', '广州', '深圳', '香港', '台湾'
}

CHINA_AUTHOR_PATTERNS = [
    r'\b(wang|zhang|li|liu|chen|yang|huang|zhao|wu|zhou|xu|sun|ma|zhu|hu|guo|he|gao|lin|luo|zheng|liang|song|tang|xu|han|feng|yu|dong|xiao|cheng|cao|yuan|deng|xie|pan|peng|jiang|dai|tian|fan|ren|wei|jin|shi|jiang|qin|cui|lu|gu|ye|su|lv|ding|xia|mao|qian|yin|yao|shao|wan|lei|qiu|kong|bai|cui|tan|xiong|lu|chang|meng|qin|yan|zou|xiang|duan|zhong|xiong|luo|jiang|tao|jiang|mei|mo|fang|ren|long|gong|wen|xiong|cai|tian|du|lan|min|cui|shi|fu|shen|yu|lu|jiang|hong|jiang|xue|lei|bo|tao|miao|shao|wan|xi|jiang|jiang|jiang)\b',
]

# ============================================================================
# 定性研究关键词
# ============================================================================
QUALITATIVE_KEYWORDS = {
    'qualitative', 'interview', 'focus group', 'thematic analysis',
    'grounded theory', 'phenomenology', 'ethnography', 'narrative',
    'content analysis', 'discourse analysis', 'lived experience',
    'participant observation', 'case study', 'mixed methods',
    '定性', '访谈', '焦点小组', '主题分析'
}


def calculate_journal_score(journal: str) -> int:
    """
    计算期刊影响力评分

    参数：
        journal: 期刊名称

    返回：
        评分 (0-100)
    """
    if not journal:
        return 0

    journal_lower = journal.lower().strip()

    # 精确匹配
    if journal_lower in HIGH_IMPACT_JOURNALS:
        return HIGH_IMPACT_JOURNALS[journal_lower]

    # 模糊匹配
    for key, score in HIGH_IMPACT_JOURNALS.items():
        if key in journal_lower or journal_lower in key:
            return score

    # 默认评分
    return 30


def detect_study_type(title: str, abstract: str) -> Tuple[str, int]:
    """
    检测研究类型并返回权重

    参数：
        title: 论文标题
        abstract: 摘要

    返回：
        (研究类型, 权重)
    """
    text = (title + ' ' + abstract).lower()

    # 按优先级检测
    detected_types = []

    for study_type, weight in STUDY_TYPE_WEIGHTS.items():
        if study_type in text:
            detected_types.append((study_type, weight))

    if detected_types:
        # 返回权重最高的类型
        detected_types.sort(key=lambda x: x[1], reverse=True)
        return detected_types[0]

    return ('unknown', 50)


def is_china_related(title: str, abstract: str, authors: List[str]) -> bool:
    """
    检测是否与中国相关

    参数：
        title: 论文标题
        abstract: 摘要
        authors: 作者列表

    返回：
        是否中国相关
    """
    # 检查标题和摘要
    title = title or ""
    abstract = abstract or ""
    text = (title + ' ' + abstract).lower()
    if any(keyword in text for keyword in CHINA_KEYWORDS):
        return True

    # 检查作者姓名
    authors_text = ' '.join(authors).lower() if authors else ""
    for pattern in CHINA_AUTHOR_PATTERNS:
        if re.search(pattern, authors_text, re.IGNORECASE):
            return True

    return False


def is_qualitative_research(title: str, abstract: str) -> bool:
    """
    检测是否为定性研究

    参数：
        title: 论文标题
        abstract: 摘要

    返回：
        是否定性研究
    """
    title = title or ""
    abstract = abstract or ""
    text = (title + ' ' + abstract).lower()
    return any(keyword in text for keyword in QUALITATIVE_KEYWORDS)


def calculate_advanced_priority_score(paper: Dict) -> Dict:
    """
    计算高级优先级评分

    参数：
        paper: 论文数据字典

    返回：
        更新后的论文数据（包含详细评分信息）
    """
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    journal = paper.get('journal', '')
    authors = paper.get('authors', [])
    citation_count = paper.get('citation_count', 0)
    source_apis = paper.get('source_apis', [])

    # 基础评分（数据源）
    base_score = 0
    if 'pubmed' in source_apis:
        base_score += 100
    if 'scopus' in source_apis:
        base_score += 90
    if 'wos' in source_apis:
        base_score += 90
    if 'semantic_scholar' in source_apis:
        base_score += 60
    if 'openalex' in source_apis:
        base_score += 50

    # 多源加成
    if len(source_apis) > 1:
        base_score = int(base_score * 1.3)

    # 期刊影响力评分
    journal_score = calculate_journal_score(journal)

    # 研究类型评分
    study_type, study_score = detect_study_type(title, abstract)

    # 中国相关加成
    china_related = is_china_related(title, abstract, authors)
    china_bonus = 50 if china_related else 0

    # 定性研究加成
    qualitative = is_qualitative_research(title, abstract)
    qualitative_bonus = 40 if qualitative else 0

    # 引用量评分（如果可用）
    citation_score = 0
    if citation_count:
        if citation_count >= 100:
            citation_score = 50
        elif citation_count >= 50:
            citation_score = 40
        elif citation_count >= 20:
            citation_score = 30
        elif citation_count >= 10:
            citation_score = 20
        elif citation_count >= 5:
            citation_score = 10

    # 综合评分
    total_score = (
        base_score * 0.3 +  # 数据源权重 30%
        journal_score * 0.35 +  # 期刊影响力 35%
        study_score * 0.20 +  # 研究类型 20%
        citation_score * 0.15 +  # 引用量 15%
        china_bonus +  # 中国相关加成
        qualitative_bonus  # 定性研究加成
    )

    # 更新论文数据
    paper['priority_score'] = int(total_score)
    paper['scoring_details'] = {
        'base_score': base_score,
        'journal_score': journal_score,
        'journal_name': journal,
        'study_type': study_type,
        'study_score': study_score,
        'citation_score': citation_score,
        'citation_count': citation_count,
        'china_related': china_related,
        'china_bonus': china_bonus,
        'qualitative': qualitative,
        'qualitative_bonus': qualitative_bonus,
        'total_score': int(total_score)
    }

    logger.debug(f"评分详情 - {title[:50]}...")
    logger.debug(f"  期刊: {journal} ({journal_score})")
    logger.debug(f"  研究类型: {study_type} ({study_score})")
    logger.debug(f"  中国相关: {china_related} (+{china_bonus})")
    logger.debug(f"  定性研究: {qualitative} (+{qualitative_bonus})")
    logger.debug(f"  总分: {int(total_score)}")

    return paper


def batch_calculate_scores(papers: List[Dict]) -> List[Dict]:
    """
    批量计算论文评分

    参数：
        papers: 论文列表

    返回：
        评分后的论文列表
    """
    scored_papers = []

    for paper in papers:
        try:
            scored_paper = calculate_advanced_priority_score(paper)
            scored_papers.append(scored_paper)
        except Exception as e:
            logger.error(f"评分失败: {e}")
            # 保留原始评分
            scored_papers.append(paper)

    # 按评分排序
    scored_papers.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

    return scored_papers


# ============================================================================
# 测试
# ============================================================================
if __name__ == "__main__":
    # 测试用例
    test_paper = {
        'title': 'A randomized controlled trial of dementia care in primary care settings in China',
        'abstract': 'Background: Dementia care in primary care is challenging. Methods: We conducted a qualitative study using interviews with caregivers in Beijing. Results: Significant improvements were observed.',
        'journal': 'The Lancet',
        'authors': ['Wang L', 'Zhang H', 'Smith J'],
        'citation_count': 45,
        'source_apis': ['pubmed', 'semantic_scholar']
    }

    scored = calculate_advanced_priority_score(test_paper)

    print("=" * 60)
    print("高级评分系统测试")
    print("=" * 60)
    print(f"\n论文: {scored['title']}")
    print(f"\n评分详情:")
    for key, value in scored['scoring_details'].items():
        print(f"  {key}: {value}")
