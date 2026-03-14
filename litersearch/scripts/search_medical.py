#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医学文献多源检索引擎
整合 multi-source-litsearch 的检索架构到 evil-read-arxiv 工作流

核心功能：
1. 多数据源并行检索（PubMed、Semantic Scholar、OpenAlex）
2. 医学专业术语智能处理（MeSH映射）
3. 智能去重与优先级评分
4. 与原有工作流无缝集成
"""

import os
import sys
import json
import logging
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
import urllib.parse

try:
    import yaml
    import aiohttp
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# 导入高级评分系统
try:
    from advanced_scoring import batch_calculate_scores
    HAS_ADVANCED_SCORING = True
except ImportError:
    HAS_ADVANCED_SCORING = False
    logger.warning("高级评分系统未找到，将使用基础评分")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# 用户配置区 - 请在此处设置基本参数
# ============================================================================
DEFAULT_CONFIG = {
    "vault_path": "",  # Obsidian Vault路径，留空则使用环境变量
    "language": "zh",  # 输出语言：zh 或 en
    "max_results_per_source": 50,
    "default_date_range": "5y",
    "prioritize_pubmed_for_medical": True,
    "deduplication_strategy": "strict",
}

# ============================================================================
# 常量定义
# ============================================================================
MEDICAL_KEYWORDS = {
    'dementia', 'alzheimer', 'diabetes', 'cancer', 'cardiovascular',
    'hypertension', 'stroke', 'depression', 'anxiety', 'autism',
    'parkinson', 'multiple sclerosis', 'epilepsy', 'schizophrenia',
    'primary care', 'general practice', 'family medicine', 'clinical',
    'patient', 'therapy', 'treatment', 'diagnosis', 'prognosis',
    'hospital', 'nursing', 'healthcare', 'medication', 'drug',
    'health policy', 'public health', 'epidemiology', 'biomedical',
    '医学', '临床', '患者', '治疗', '诊断', '护理'
}

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
OPENALEX_URL = "https://api.openalex.org/works"
SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"

# ============================================================================
# 数据结构定义
# ============================================================================
@dataclass
class MedicalPaper:
    """医学论文数据结构"""
    title: str
    authors: List[str]
    journal: str
    year: Optional[int]
    doi: Optional[str]
    pmid: Optional[str]
    abstract: Optional[str]
    url: Optional[str]
    source_apis: List[str] = field(default_factory=list)
    priority_score: int = 0
    citation_count: Optional[int] = None
    mesh_terms: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    domain: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SearchConfig:
    """检索配置"""
    api_keys: Dict[str, str] = field(default_factory=dict)
    max_results_per_source: int = 50
    date_range: str = "5y"
    prioritize_pubmed: bool = True
    dedup_strategy: str = "strict"
    sources: List[str] = field(default_factory=lambda: ['pubmed', 'scopus', 'semantic_scholar', 'openalex'])


# ============================================================================
# 医学主题检测与查询构建
# ============================================================================
class MedicalQueryBuilder:
    """医学专业查询构建器"""
    
    # 常用MeSH术语映射
    MESH_MAPPINGS = {
        # 失智症相关
        'dementia': ['Dementia[mh]', 'Cognitive Dysfunction[mh]'],
        'dementia care': ['Dementia[mh]', '"dementia care"[tiab]'],
        'alzheimer': ['Alzheimer Disease[mh]'],
        'alzheimer disease': ['Alzheimer Disease[mh]'],
        'cognitive impairment': ['Cognitive Dysfunction[mh]'],
        'cognitive decline': ['Cognitive Dysfunction[mh]'],

        # 照护相关
        'primary care': ['Primary Health Care[mh]', 'General Practice[mh]'],
        'long-term care': ['Long-Term Care[mh]'],
        'nursing home': ['Nursing Homes[mh]'],
        'home care': ['Home Care Services[mh]'],
        'palliative care': ['Palliative Care[mh]'],
        'end-of-life care': ['Terminal Care[mh]', 'Palliative Care[mh]'],

        # 照护者相关
        'caregiver': ['Caregivers[mh]', 'Family Caregivers[mh]'],
        'family caregiver': ['Family Caregivers[mh]'],
        'caregiver burden': ['Caregiver Burden[mh]'],

        # 疾病相关
        'diabetes': ['Diabetes Mellitus[mh]'],
        'depression': ['Depression[mh]', 'Depressive Disorder[mh]'],
        'anxiety': ['Anxiety[mh]', 'Anxiety Disorders[mh]'],
        'stroke': ['Stroke[mh]'],
        'hypertension': ['Hypertension[mh]'],

        # 技术相关
        'artificial intelligence': ['Artificial Intelligence[mh]', 'Machine Learning[mh]'],
        'machine learning': ['Machine Learning[mh]'],
        'telemedicine': ['Telemedicine[mh]'],
        'telehealth': ['Telemedicine[mh]'],
        'mobile health': ['Telemedicine[mh]', 'Mobile Applications[mh]'],
        'mhealth': ['Telemedicine[mh]', 'Mobile Applications[mh]'],
        'virtual reality': ['Virtual Reality[mh]'],

        # 干预相关
        'intervention': ['Intervention Studies[mh]'],
        'randomized controlled trial': ['Randomized Controlled Trial[pt]'],
        'rct': ['Randomized Controlled Trial[pt]'],
        'systematic review': ['Systematic Review[pt]', 'Meta-Analysis[pt]'],
        'qualitative research': ['Qualitative Research[mh]'],

        # 健康政策
        'health policy': ['Health Policy[mh]'],
        'public health': ['Public Health[mh]'],
    }
    
    @classmethod
    def is_medical_topic(cls, query: str) -> bool:
        """检测是否为医学主题"""
        query_lower = query.lower()
        return any(kw in query_lower for kw in MEDICAL_KEYWORDS)
    
    @classmethod
    def build_pubmed_query(cls, query: str, date_range: str = "5y") -> str:
        """
        构建PubMed专业检索式

        策略：
        1. 检查是否包含NOT运算符，如果有则分别处理包含和排除部分
        2. 识别查询中的医学概念
        3. 映射到MeSH术语
        4. 组合文本词检索
        5. 添加日期限制
        """
        # 检查是否包含NOT运算符
        if ' NOT ' in query.upper():
            # 分割为包含部分和排除部分
            parts = query.split(' NOT ', 1)
            include_part = parts[0].strip()
            exclude_part = parts[1].strip() if len(parts) > 1 else ""

            # 构建包含部分的查询
            include_query = cls._build_query_part(include_part)

            # 构建排除部分的查询
            if exclude_part:
                # 处理排除部分的括号和OR运算符
                exclude_part = exclude_part.strip('()')
                exclude_terms = []

                # 分割OR运算符
                if ' OR ' in exclude_part.upper():
                    terms = [t.strip() for t in exclude_part.split(' OR ')]
                    for term in terms:
                        term = term.strip('()')
                        exclude_terms.append(f'{term}[tiab]')
                else:
                    exclude_terms.append(f'{exclude_part}[tiab]')

                exclude_query = ' OR '.join(exclude_terms)
                pubmed_query = f"({include_query}) NOT ({exclude_query})"
            else:
                pubmed_query = include_query
        else:
            # 没有NOT运算符，使用原有逻辑
            pubmed_query = cls._build_query_part(query)

        # 添加日期限制
        date_filter = cls._build_date_filter(date_range)
        if date_filter:
            pubmed_query = f"({pubmed_query}) AND {date_filter}"

        return pubmed_query

    @classmethod
    def _build_query_part(cls, query: str) -> str:
        """构建查询的一部分（不包含NOT运算符）"""
        concepts = cls._extract_concepts(query)
        query_parts = []

        for concept in concepts:
            mesh_terms = cls.MESH_MAPPINGS.get(concept.lower(), [])

            if mesh_terms:
                # 只使用MeSH术语，不重复添加文本词
                part = f"({' OR '.join(mesh_terms)})"
            else:
                # 没有MeSH映射的概念，使用文本词
                part = f'"{concept}"[tiab]'
            query_parts.append(part)

        # 组合所有概念
        if len(query_parts) > 1:
            return ' AND '.join(query_parts)
        elif query_parts:
            return query_parts[0]
        else:
            return f'"{query}"[tiab]'
    
    @classmethod
    def _extract_concepts(cls, query: str) -> List[str]:
        """从查询中提取概念"""
        query_lower = query.lower()
        concepts = []
        covered_ranges = []  # 记录已覆盖的字符范围

        # 首先检查多词概念（按长度降序，优先匹配长概念）
        mesh_keys_sorted = sorted(cls.MESH_MAPPINGS.keys(), key=len, reverse=True)
        for mesh_key in mesh_keys_sorted:
            start = query_lower.find(mesh_key)
            if start != -1:
                end = start + len(mesh_key)
                # 检查是否与已有概念重叠
                overlaps = False
                for covered_start, covered_end in covered_ranges:
                    if not (end <= covered_start or start >= covered_end):
                        overlaps = True
                        break

                if not overlaps:
                    concepts.append(mesh_key)
                    covered_ranges.append((start, end))

        # 如果没有匹配到任何MeSH概念，将整个查询作为一个概念
        if not concepts:
            # 检查是否是常见的医学短语模式
            if any(pattern in query_lower for pattern in ['care', 'treatment', 'management', 'intervention', 'therapy']):
                # 保持完整短语
                concepts.append(query.strip())
            else:
                # 分词处理
                words = query.split()
                for word in words:
                    if len(word) > 3:
                        concepts.append(word)

        return concepts[:5]  # 最多5个概念
    
    @classmethod
    def _build_date_filter(cls, date_range: str) -> Optional[str]:
        """构建日期过滤器"""
        from datetime import datetime, timedelta
        current_date = datetime.now()
        current_year = current_date.year

        if date_range.endswith('y'):
            # 年份格式：5y
            years = int(date_range[:-1])
            start_year = current_year - years
            return f"{start_year}:{current_year}[pdat]"
        elif date_range.endswith('d'):
            # 天数格式：90d
            days = int(date_range[:-1])
            start_date = current_date - timedelta(days=days)
            return f"{start_date.strftime('%Y/%m/%d')}:{current_date.strftime('%Y/%m/%d')}[pdat]"
        elif ':' in date_range and '/' in date_range:
            # 已经是正确格式：2026/01/01:2026/03/14
            return f"{date_range}[pdat]"
        elif date_range.isdigit():
            # 单个年份：2026
            return f"{date_range}[pdat]"

        return None


# ============================================================================
# 多源检索引擎
# ============================================================================
class MultiSourceMedicalSearch:
    """多源医学文献检索引擎"""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.query_builder = MedicalQueryBuilder()
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=5)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def search_all(self, query: str, domain: str = "") -> List[MedicalPaper]:
        """
        执行多源检索
        
        参数：
            query: 检索查询
            domain: 研究领域标签
        
        返回：
            去重后的论文列表
        """
        is_medical = self.query_builder.is_medical_topic(query)
        
        # 确定检索源顺序
        sources = self._get_source_order(is_medical)
        
        logger.info(f"检测到{'医学' if is_medical else '非医学'}主题")
        logger.info(f"检索源顺序: {sources}")
        
        # 并行检索
        all_results = []
        tasks = []
        
        for source in sources:
            if source == 'pubmed':
                tasks.append(self._search_pubmed(query, domain))
            elif source == 'scopus':
                tasks.append(self._search_scopus(query, domain))
            elif source == 'semantic_scholar':
                tasks.append(self._search_semantic_scholar(query, domain))
            elif source == 'openalex':
                tasks.append(self._search_openalex(query, domain))
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source, results in zip(sources, results_list):
            if isinstance(results, Exception):
                logger.error(f"{source} 检索失败: {results}")
            else:
                all_results.extend(results)
                logger.info(f"{source}: {len(results)} 条结果")
        
        # 去重
        deduplicated = self._deduplicate(all_results)
        logger.info(f"去重后: {len(deduplicated)} 条唯一结果")
        
        return deduplicated
    
    def _get_source_order(self, is_medical: bool) -> List[str]:
        """确定检索源顺序"""
        available = []
        
        for source in self.config.sources:
            if source in ['pubmed', 'scopus', 'semantic_scholar', 'openalex']:
                available.append(source)
        
        if is_medical and self.config.prioritize_pubmed and 'pubmed' in available:
            # 医学主题优先PubMed
            available.remove('pubmed')
            available.insert(0, 'pubmed')
        
        return available
    
    async def _search_pubmed(self, query: str, domain: str) -> List[MedicalPaper]:
        """PubMed检索"""
        results = []
        api_key = self.config.api_keys.get('pubmed', '')
        
        # 构建PubMed查询
        pubmed_query = self.query_builder.build_pubmed_query(query, self.config.date_range)
        logger.info(f"PubMed查询: {pubmed_query}")
        
        try:
            # ESearch获取PMID
            params = {
                'db': 'pubmed',
                'term': pubmed_query,
                'retmax': self.config.max_results_per_source,
                'retmode': 'json'
            }
            if api_key:
                params['api_key'] = api_key
            
            async with self.session.get(PUBMED_ESEARCH_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"PubMed ESearch失败: {resp.status}")
                    return results

                data = await resp.json()
                pmids = data.get('esearchresult', {}).get('idlist', [])
                total_count = data.get('esearchresult', {}).get('count', '0')

                logger.info(f"PubMed返回: {total_count}篇，获取前{len(pmids)}篇")

                if not pmids:
                    return results

                # EFetch获取详情（分批处理）
                # PubMed API限制：URL长度约8000字符，每个PMID约8字符
                # 安全批次大小：200篇（约1600字符的ID，加上其他参数不会超限）
                batch_size = 200
                delay = 0.1 if api_key else 0.34  # 有API key: 10次/秒，无API key: 3次/秒
                max_retries = 3  # 最大重试次数
                timeout = 30  # 超时时间（秒）

                for i in range(0, len(pmids), batch_size):
                    batch_pmids = pmids[i:i+batch_size]
                    batch_num = i//batch_size + 1
                    total_batches = (len(pmids)-1)//batch_size + 1

                    fetch_params = {
                        'db': 'pubmed',
                        'id': ','.join(batch_pmids),
                        'rettype': 'abstract',
                        'retmode': 'xml'
                    }
                    if api_key:
                        fetch_params['api_key'] = api_key

                    # 重试机制
                    for retry in range(max_retries):
                        try:
                            timeout_obj = aiohttp.ClientTimeout(total=timeout)
                            async with self.session.get(
                                PUBMED_EFETCH_URL,
                                params=fetch_params,
                                timeout=timeout_obj
                            ) as resp:
                                if resp.status == 200:
                                    xml_text = await resp.text()
                                    batch_results = self._parse_pubmed_xml(xml_text, batch_pmids, domain)
                                    results.extend(batch_results)
                                    logger.info(f"PubMed批次{batch_num}/{total_batches}: {len(batch_results)}篇成功")
                                    break  # 成功，跳出重试循环
                                else:
                                    logger.warning(f"PubMed批次{batch_num}失败(状态{resp.status})，重试{retry+1}/{max_retries}")
                                    if retry < max_retries - 1:
                                        await asyncio.sleep(2 ** retry)  # 指数退避：1s, 2s, 4s
                                    else:
                                        logger.error(f"PubMed批次{batch_num}失败: {resp.status}，已达最大重试次数")
                        except asyncio.TimeoutError:
                            logger.warning(f"PubMed批次{batch_num}超时({timeout}秒)，重试{retry+1}/{max_retries}")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry)
                            else:
                                logger.error(f"PubMed批次{batch_num}超时，已达最大重试次数，跳过该批次")
                        except Exception as e:
                            logger.warning(f"PubMed批次{batch_num}错误: {e}，重试{retry+1}/{max_retries}")
                            if retry < max_retries - 1:
                                await asyncio.sleep(2 ** retry)
                            else:
                                logger.error(f"PubMed批次{batch_num}失败: {e}，已达最大重试次数")

                    # 遵守API速率限制
                    if i + batch_size < len(pmids):
                        await asyncio.sleep(delay)
        
        except Exception as e:
            logger.error(f"PubMed检索错误: {e}")
        
        # 添加来源标记和优先级
        for r in results:
            r.source_apis.append('pubmed')
            r.priority_score += 100  # PubMed结果加分
        
        return results
    
    def _parse_pubmed_xml(self, xml_text: str, pmids: List[str], domain: str) -> List[MedicalPaper]:
        """解析PubMed XML响应"""
        import re
        results = []
        
        for pmid in pmids:
            try:
                # 提取文章部分
                pmid_pattern = rf'<PMID[^>]*>{pmid}</PMID>(.*?)(?=<PMID|$)'
                match = re.search(pmid_pattern, xml_text, re.DOTALL)
                
                if not match:
                    continue
                
                article_xml = match.group(1)
                
                # 提取字段
                title = self._extract_xml_field(article_xml, 'ArticleTitle') or "Unknown Title"
                abstract = self._extract_xml_field(article_xml, 'AbstractText')
                journal = self._extract_xml_field(article_xml, 'Title') or "Unknown Journal"
                year_str = self._extract_xml_field(article_xml, 'Year')
                year = int(year_str) if year_str and year_str.isdigit() else None
                doi = self._extract_doi(article_xml)
                authors = self._extract_authors(article_xml)
                
                paper = MedicalPaper(
                    title=title,
                    authors=authors,
                    journal=journal,
                    year=year,
                    doi=doi,
                    pmid=pmid,
                    abstract=abstract,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    domain=domain
                )
                results.append(paper)
            
            except Exception as e:
                logger.warning(f"解析PMID {pmid}失败: {e}")
        
        return results
    
    def _extract_xml_field(self, xml: str, field: str) -> Optional[str]:
        """提取XML字段"""
        import re
        pattern = rf'<{field}[^>]*>(.*?)</{field}>'
        match = re.search(pattern, xml, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def _extract_authors(self, xml: str) -> List[str]:
        """提取作者列表"""
        import re
        authors = []
        pattern = r'<Author[^>]*>.*?<LastName>(.*?)</LastName>.*?<ForeName>(.*?)</ForeName>.*?</Author>'
        for match in re.finditer(pattern, xml, re.DOTALL):
            authors.append(f"{match.group(2)} {match.group(1)}")
        return authors[:10]  # 最多10位作者
    
    def _extract_doi(self, xml: str) -> Optional[str]:
        """提取DOI"""
        import re
        patterns = [
            r'<ELocationId[^>]*EIdType="doi"[^>]*>(.*?)</ELocationId>',
            r'<ArticleId[^>]*IdType="doi"[^>]*>(.*?)</ArticleId>'
        ]
        for pattern in patterns:
            match = re.search(pattern, xml)
            if match:
                return match.group(1)
        return None
    
    async def _search_semantic_scholar(self, query: str, domain: str) -> List[MedicalPaper]:
        """Semantic Scholar检索"""
        results = []
        api_key = self.config.api_keys.get('semantic_scholar', '')
        
        try:
            headers = {}
            if api_key:
                headers['x-api-key'] = api_key
            
            params = {
                'query': query,
                'limit': self.config.max_results_per_source,
                'fields': 'title,authors,year,abstract,doi,url,citationCount,publicationDate,journal'
            }
            
            # 添加日期过滤
            if self.config.date_range != 'all':
                current_year = datetime.now().year
                if self.config.date_range.endswith('y'):
                    years = int(self.config.date_range[:-1])
                    params['year'] = f"{current_year-years}-{current_year}"
            
            async with self.session.get(SEMANTIC_SCHOLAR_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"Semantic Scholar失败: {resp.status}")
                    return results
                
                data = await resp.json()
                papers = data.get('data', [])
                
                for paper in papers:
                    authors = [a.get('name', '') for a in paper.get('authors', []) if a.get('name')]
                    
                    paper_obj = MedicalPaper(
                        title=paper.get('title', 'Unknown Title'),
                        authors=authors,
                        journal=paper.get('journal', {}).get('name', 'Unknown Journal'),
                        year=paper.get('year'),
                        doi=paper.get('doi'),
                        pmid=None,
                        abstract=paper.get('abstract'),
                        url=paper.get('url'),
                        citation_count=paper.get('citationCount'),
                        domain=domain
                    )
                    results.append(paper_obj)
        
        except Exception as e:
            logger.error(f"Semantic Scholar检索错误: {e}")
        
        for r in results:
            r.source_apis.append('semantic_scholar')
            r.priority_score += 60
        
        return results
    
    async def _search_openalex(self, query: str, domain: str) -> List[MedicalPaper]:
        """OpenAlex检索"""
        results = []
        
        try:
            params = {
                'search': query,
                'per_page': min(self.config.max_results_per_source, 200),
                'sort': 'relevance_score:desc'
            }
            
            # 日期过滤
            if self.config.date_range != 'all':
                current_year = datetime.now().year
                if self.config.date_range.endswith('y'):
                    years = int(self.config.date_range[:-1])
                    params['filter'] = f"publication_year:{current_year-years}-{current_year}"
            
            async with self.session.get(OPENALEX_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"OpenAlex失败: {resp.status}")
                    return results
                
                data = await resp.json()
                works = data.get('results', [])
                
                for work in works:
                    authors = []
                    for auth in work.get('authorships', []):
                        name = auth.get('author', {}).get('display_name', '')
                        if name:
                            authors.append(name)
                    
                    doi = work.get('doi', '')
                    if doi and doi.startswith('https://doi.org/'):
                        doi = doi[16:]
                    
                    paper = MedicalPaper(
                        title=work.get('display_name', 'Unknown Title'),
                        authors=authors,
                        journal=work.get('primary_location', {}).get('source', {}).get('display_name', 'Unknown Journal'),
                        year=work.get('publication_year'),
                        doi=doi,
                        pmid=None,
                        abstract=work.get('abstract'),
                        url=work.get('id'),
                        citation_count=work.get('cited_by_count'),
                        domain=domain
                    )
                    results.append(paper)
        
        except Exception as e:
            logger.error(f"OpenAlex检索错误: {e}")
        
        for r in results:
            r.source_apis.append('openalex')
            r.priority_score += 50

        return results

    async def _search_scopus(self, query: str, domain: str) -> List[MedicalPaper]:
        """Scopus检索"""
        results = []
        api_key = self.config.api_keys.get('scopus', '')

        if not api_key:
            logger.warning("Scopus API key 未配置，跳过检索")
            return results

        try:
            headers = {
                'X-ELS-APIKey': api_key,
                'Accept': 'application/json'
            }

            params = {
                'query': query,
                'count': min(self.config.max_results_per_source, 200),
                'sort': 'relevancy',
                'field': 'dc:title,dc:creator,prism:publicationName,prism:coverDate,prism:doi,dc:identifier,citedby-count,dc:description'
            }

            # 日期过滤
            if self.config.date_range != 'all':
                current_year = datetime.now().year
                if self.config.date_range.endswith('y'):
                    years = int(self.config.date_range[:-1])
                    start_year = current_year - years
                    params['date'] = f"{start_year}-{current_year}"
                elif self.config.date_range.endswith('d'):
                    days = int(self.config.date_range[:-1])
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                    params['date'] = f"{start_date}-{datetime.now().strftime('%Y-%m-%d')}"

            async with self.session.get(SCOPUS_SEARCH_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"Scopus失败: {resp.status}")
                    return results

                data = await resp.json()
                entries = data.get('search-results', {}).get('entry', [])

                for entry in entries:
                    # 提取作者
                    authors = []
                    creator = entry.get('dc:creator', '')
                    if creator:
                        authors = [creator]

                    # 提取年份
                    cover_date = entry.get('prism:coverDate', '')
                    year = None
                    if cover_date:
                        try:
                            year = int(cover_date.split('-')[0])
                        except:
                            pass

                    # 提取PMID（如果有）
                    pmid = None
                    identifiers = entry.get('dc:identifier', '')
                    if 'PUBMED_ID:' in identifiers:
                        pmid = identifiers.split('PUBMED_ID:')[1].split(';')[0].strip()

                    paper_obj = MedicalPaper(
                        title=entry.get('dc:title', 'Unknown Title'),
                        authors=authors,
                        journal=entry.get('prism:publicationName', 'Unknown Journal'),
                        year=year,
                        doi=entry.get('prism:doi'),
                        pmid=pmid,
                        abstract=entry.get('dc:description'),
                        url=entry.get('prism:url'),
                        citation_count=entry.get('citedby-count'),
                        domain=domain
                    )
                    results.append(paper_obj)

        except Exception as e:
            logger.error(f"Scopus检索错误: {e}")

        for r in results:
            r.source_apis.append('scopus')
            r.priority_score += 90  # Scopus高质量数据源

        return results

    def _deduplicate(self, papers: List[MedicalPaper]) -> List[MedicalPaper]:
        """去重"""
        if not papers:
            return []
        
        # 按DOI分组
        doi_groups: Dict[str, List[MedicalPaper]] = {}
        no_doi: List[MedicalPaper] = []
        
        for paper in papers:
            if paper.doi:
                doi_norm = paper.doi.lower().strip()
                if doi_norm not in doi_groups:
                    doi_groups[doi_norm] = []
                doi_groups[doi_norm].append(paper)
            else:
                no_doi.append(paper)
        
        # 合并DOI组
        merged: List[MedicalPaper] = []
        for doi, group in doi_groups.items():
            merged_result = self._merge_group(group)
            merged.append(merged_result)
        
        # 处理无DOI结果
        for paper in no_doi:
            is_dup = False
            for existing in merged:
                if self._is_similar(paper, existing):
                    self._merge_into(existing, paper)
                    is_dup = True
                    break
            if not is_dup:
                merged.append(paper)
        
        # 按优先级排序
        merged.sort(key=lambda x: x.priority_score, reverse=True)
        
        return merged
    
    def _merge_group(self, group: List[MedicalPaper]) -> MedicalPaper:
        """合并重复组"""
        base = group[0]
        for other in group[1:]:
            self._merge_into(base, other)
        return base
    
    def _merge_into(self, target: MedicalPaper, source: MedicalPaper):
        """合并到目标"""
        for api in source.source_apis:
            if api not in target.source_apis:
                target.source_apis.append(api)
        
        target.priority_score += source.priority_score // 2
        
        if not target.abstract and source.abstract:
            target.abstract = source.abstract
        if not target.doi and source.doi:
            target.doi = source.doi
        if not target.pmid and source.pmid:
            target.pmid = source.pmid
        if not target.url and source.url:
            target.url = source.url
        if not target.citation_count and source.citation_count:
            target.citation_count = source.citation_count
    
    def _is_similar(self, a: MedicalPaper, b: MedicalPaper) -> bool:
        """判断相似性"""
        # PMID匹配
        if a.pmid and b.pmid and a.pmid == b.pmid:
            return True
        
        # 标题相似度
        title_sim = SequenceMatcher(None, a.title.lower(), b.title.lower()).ratio()
        
        if self.config.dedup_strategy == "strict":
            if title_sim < 0.95:
                return False
            if a.year and b.year and a.year != b.year:
                return False
            return True
        else:
            return title_sim > 0.85


# ============================================================================
# 配置加载
# ============================================================================
def load_config(config_path: str = None) -> Dict:
    """
    加载配置文件
    
    优先级：
    1. 指定的配置文件路径
    2. 环境变量 OBSIDIAN_VAULT_PATH 下的 99_System/Config/research_interests.yaml
    3. 默认配置
    """
    config = DEFAULT_CONFIG.copy()
    
    # 尝试从环境变量获取Vault路径
    vault_path = os.environ.get('OBSIDIAN_VAULT_PATH', '')
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
            config.update(user_config)
    elif vault_path:
        config_file = Path(vault_path) / '99_System' / 'Config' / 'research_interests.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f) or {}
                config.update(user_config)
    
    # 设置vault路径
    if not config.get('vault_path') and vault_path:
        config['vault_path'] = vault_path
    
    return config


def get_search_config(config: Dict) -> SearchConfig:
    """从配置字典创建SearchConfig"""
    return SearchConfig(
        api_keys=config.get('api_keys', {}),
        max_results_per_source=config.get('preferences', {}).get('max_results_per_source', 50),
        date_range=config.get('preferences', {}).get('default_date_range', '5y'),
        prioritize_pubmed=config.get('preferences', {}).get('prioritize_pubmed_for_medical', True),
        dedup_strategy=config.get('preferences', {}).get('deduplication_strategy', 'strict'),
        sources=config.get('sources', ['pubmed', 'semantic_scholar', 'openalex'])
    )


# ============================================================================
# 主检索函数
# ============================================================================
async def search_medical_literature(
    query: str,
    domain: str = "",
    config_path: str = None,
    max_results: int = None,
    use_advanced_scoring: bool = True
) -> List[MedicalPaper]:
    """
    执行医学文献检索

    参数：
        query: 检索查询
        domain: 研究领域标签
        config_path: 配置文件路径
        max_results: 最大结果数
        use_advanced_scoring: 是否使用高级评分系统

    返回：
        论文列表
    """
    config = load_config(config_path)
    search_config = get_search_config(config)

    if max_results:
        search_config.max_results_per_source = max_results

    async with MultiSourceMedicalSearch(search_config) as engine:
        results = await engine.search_all(query, domain)

        # 应用高级评分系统
        if use_advanced_scoring and HAS_ADVANCED_SCORING:
            logger.info("应用高级评分系统...")
            results_dict = [asdict(r) for r in results]
            scored_results = batch_calculate_scores(results_dict)
            # 转换回MedicalPaper对象
            results = [MedicalPaper(**r) for r in scored_results]
            logger.info(f"评分完成，共 {len(results)} 篇论文")

        return results


def search_sync(query: str, domain: str = "", config_path: str = None) -> List[Dict]:
    """
    同步检索接口
    
    示例：
        results = search_sync("dementia care primary care")
        for paper in results:
            print(f"{paper['title']} - {paper['pmid']}")
    """
    results = asyncio.run(search_medical_literature(query, domain, config_path))
    return [r.to_dict() for r in results]


# ============================================================================
# 测试
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("医学文献多源检索引擎测试")
    print("=" * 60)
    
    test_query = "dementia care in primary care"
    print(f"\n测试查询: {test_query}")
    
    results = search_sync(test_query, domain="痴呆症照护")
    
    print(f"\n检索结果: {len(results)} 条")
    print("-" * 60)
    
    for i, paper in enumerate(results[:5], 1):
        print(f"\n[{i}] {paper['title']}")
        print(f"    作者: {', '.join(paper['authors'][:3])}...")
        print(f"    期刊: {paper['journal']} ({paper['year']})")
        print(f"    PMID: {paper['pmid']}")
        print(f"    DOI: {paper['doi']}")
        print(f"    来源: {', '.join(paper['source_apis'])}")
        print(f"    优先级: {paper['priority_score']}")
