#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiterSearch - 命令行文献检索工具
支持通过命令行参数自定义研究主题进行文献检索

使用方法：
    python litersearch.py "dementia care" --vault "D:/ObsidianFiles/paper-weekly" --max-results 50
    python litersearch.py "primary care qualitative research" --sources pubmed scopus --date-range 1y
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入模块
try:
    from search_medical import (
        search_medical_literature,
        MedicalPaper
    )
    from generate_medical_note import (
        generate_note,
        generate_daily_summary
    )
    from advanced_scoring import batch_calculate_scores
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入必要模块: {e}")
    MODULES_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def search_literature(
    query: str,
    vault_path: str,
    sources: List[str] = None,
    max_results: int = 50,
    date_range: str = "5y",
    language: str = "zh",
    top_n: int = 3,
    auto_translate: bool = True,
    translation_api: str = "claude",
    translation_api_key: Optional[str] = None,
    translation_api_url: Optional[str] = None,
    enable_scoring: bool = True,
    export_csv: bool = False
) -> Dict[str, Any]:
    """
    执行文献检索

    参数：
        query: 检索查询字符串
        vault_path: Obsidian Vault路径
        sources: 数据源列表
        max_results: 每个数据源的最大结果数
        date_range: 日期范围
        language: 语言设置
        top_n: 生成详细笔记的论文数量
        auto_translate: 是否自动翻译
        translation_api: 翻译API类型
        translation_api_key: 翻译API密钥
        translation_api_url: 自定义API URL
        enable_scoring: 是否启用高级评分系统
        export_csv: 是否导出CSV格式

    返回：
        检索结果摘要
    """
    logger.info("=" * 60)
    logger.info("LiterSearch 文献检索启动")
    logger.info("=" * 60)
    logger.info(f"检索主题: {query}")
    logger.info(f"Vault路径: {vault_path}")
    logger.info(f"数据源: {sources or ['pubmed', 'semantic_scholar', 'openalex']}")
    logger.info(f"日期范围: {date_range}")
    logger.info(f"语言设置: {language}")
    logger.info(f"自动翻译: {'开启' if auto_translate else '关闭'}")
    logger.info(f"高级评分: {'开启' if enable_scoring else '关闭'}")
    logger.info(f"导出CSV: {'是' if export_csv else '否'}")

    # 创建临时配置
    temp_config = {
        'vault_path': vault_path,
        'language': language,
        'sources': sources or ['pubmed', 'semantic_scholar', 'openalex'],  # 添加顶层sources字段
        'api_keys': {
            'pubmed': os.environ.get('PUBMED_API_KEY', ''),
            'scopus': os.environ.get('SCOPUS_API_KEY', ''),
            'semantic_scholar': os.environ.get('SEMANTIC_SCHOLAR_API_KEY', '')
        },
        'research_domains': {
            'Custom Search': {
                'keywords': query.split(),
                'sources': sources or ['pubmed', 'semantic_scholar', 'openalex'],
                'date_range': date_range,
                'priority': 5
            }
        },
        'preferences': {
            'max_results_per_source': max_results,
            'default_date_range': date_range
        },
        'translation': {
            'enabled': auto_translate,
            'api': translation_api,
            'api_key': translation_api_key or os.environ.get('ANTHROPIC_API_KEY', ''),
            'api_url': translation_api_url
        }
    }

    # 保存临时配置
    temp_config_path = SCRIPT_DIR / 'temp_config.json'
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump(temp_config, f, ensure_ascii=False, indent=2)

    logger.info(f"\n{'='*40}")
    logger.info(f"执行检索")
    logger.info(f"{'='*40}")

    try:
        # 执行检索
        papers = await search_medical_literature(
            query=query,
            domain='Custom Search',
            config_path=str(temp_config_path)
        )

        # 转换为字典
        papers_dict = [p.to_dict() if hasattr(p, 'to_dict') else p for p in papers]

        logger.info(f"检索结果: {len(papers_dict)} 篇论文")

        # 去重
        unique_papers = deduplicate_papers(papers_dict)
        logger.info(f"去重后: {len(unique_papers)} 篇")

        # 应用高级评分（可选）
        if enable_scoring:
            logger.info("应用高级评分系统...")
            unique_papers = batch_calculate_scores(unique_papers)
        else:
            logger.info("跳过高级评分系统（已禁用）")
            # 为未评分的论文设置默认优先级
            for paper in unique_papers:
                if 'priority_score' not in paper:
                    paper['priority_score'] = 50  # 默认中等优先级

        # 导出CSV（如果需要）
        csv_path = None
        if export_csv:
            logger.info(f"\n{'='*40}")
            logger.info("导出CSV格式")
            logger.info(f"{'='*40}")
            csv_path = export_to_csv(unique_papers, vault_path, query)
            logger.info(f"CSV文件: {csv_path}")

        # 生成每日摘要
        logger.info(f"\n{'='*40}")
        logger.info("生成检索摘要")
        logger.info(f"{'='*40}")

        search_queries = [{
            'domain': 'Custom Search',
            'query': query,
            'count': len(unique_papers)
        }]

        summary_path = generate_daily_summary(
            papers=unique_papers,
            vault_path=vault_path,
            queries=search_queries,
            language=language
        )
        logger.info(f"摘要文件: {summary_path}")

        # 为前N篇生成详细笔记
        logger.info(f"\n{'='*40}")
        logger.info(f"生成前 {top_n} 篇论文的详细笔记")
        logger.info(f"{'='*40}")

        generated_notes = []
        for i, paper in enumerate(unique_papers[:top_n], 1):
            title = paper.get('title', 'Unknown')
            logger.info(f"\n[{i}/{top_n}] {title[:50]}...")

            try:
                note_path = generate_note(
                    paper_data=paper,
                    vault_path=vault_path,
                    domain='Custom Search',
                    language=language,
                    auto_translate=auto_translate,
                    translation_api=translation_api,
                    translation_api_url=translation_api_url,
                    translation_api_key=translation_api_key
                )
                generated_notes.append(note_path)
                logger.info(f"生成笔记: {note_path}")
            except Exception as e:
                logger.error(f"生成笔记失败: {e}")

        # 清理临时配置
        temp_config_path.unlink(missing_ok=True)

        # 返回结果
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'vault_path': vault_path,
            'total_papers': len(papers_dict),
            'unique_papers': len(unique_papers),
            'summary_file': summary_path,
            'csv_file': csv_path,
            'notes_generated': len(generated_notes),
            'note_files': generated_notes,
            'scoring_enabled': enable_scoring
        }

        logger.info(f"\n{'='*60}")
        logger.info("检索完成摘要")
        logger.info(f"{'='*60}")
        logger.info(f"检索主题: {query}")
        logger.info(f"总结果数: {result['total_papers']}")
        logger.info(f"唯一论文: {result['unique_papers']}")
        logger.info(f"生成笔记: {result['notes_generated']}")
        logger.info(f"摘要文件: {result['summary_file']}")
        if csv_path:
            logger.info(f"CSV文件: {csv_path}")

        return result

    except Exception as e:
        logger.error(f"检索失败: {e}")
        import traceback
        traceback.print_exc()

        # 清理临时配置
        temp_config_path.unlink(missing_ok=True)

        return {
            'success': False,
            'error': str(e)
        }


def export_to_csv(papers: List[Dict], vault_path: str, query: str) -> str:
    """
    导出论文列表为CSV格式

    参数：
        papers: 论文列表
        vault_path: Obsidian Vault路径
        query: 检索查询

    返回：
        CSV文件路径
    """
    import csv
    from datetime import datetime

    # 确定保存目录
    daily_dir = Path(vault_path) / "10_Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    today = datetime.now()
    filename = today.strftime('%Y-%m-%d') + "-文献检索结果.csv"
    filepath = daily_dir / filename

    # CSV字段
    fieldnames = [
        '序号',
        '标题',
        '作者',
        '期刊',
        '年份',
        'PMID',
        'DOI',
        '数据源',
        '优先级评分',
        '摘要',
        'PubMed链接',
        'DOI链接'
    ]

    # 写入CSV
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, paper in enumerate(papers, 1):
            # 格式化作者
            authors = paper.get('authors', [])
            if isinstance(authors, list):
                if len(authors) > 3:
                    authors_str = f"{authors[0]} et al."
                else:
                    authors_str = ', '.join(authors)
            else:
                authors_str = str(authors)

            # 格式化数据源
            sources = paper.get('source_apis', [])
            sources_str = ', '.join(sources) if sources else 'Unknown'

            # 构建链接
            pmid = paper.get('pmid', '')
            doi = paper.get('doi', '')
            pmid_link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            doi_link = f"https://doi.org/{doi}" if doi else ""

            # 摘要（限制长度）
            abstract = paper.get('abstract', '')
            if abstract and len(abstract) > 500:
                abstract = abstract[:500] + "..."

            writer.writerow({
                '序号': i,
                '标题': paper.get('title', 'Unknown Title'),
                '作者': authors_str,
                '期刊': paper.get('journal', 'Unknown Journal'),
                '年份': paper.get('year', 'Unknown'),
                'PMID': pmid,
                'DOI': doi,
                '数据源': sources_str,
                '优先级评分': paper.get('priority_score', 0),
                '摘要': abstract,
                'PubMed链接': pmid_link,
                'DOI链接': doi_link
            })

    logger.info(f"导出CSV: {filepath}")
    return str(filepath)


def deduplicate_papers(papers: List[Dict]) -> List[Dict]:
    """
    全局去重

    参数：
        papers: 论文列表

    返回：
        去重后的论文列表
    """
    from difflib import SequenceMatcher

    # 按DOI分组
    doi_groups: Dict[str, List[Dict]] = {}
    no_doi: List[Dict] = []

    for paper in papers:
        doi = paper.get('doi', '')
        if doi:
            doi_norm = doi.lower().strip()
            if doi_norm not in doi_groups:
                doi_groups[doi_norm] = []
            doi_groups[doi_norm].append(paper)
        else:
            no_doi.append(paper)

    # 合并DOI组
    merged: List[Dict] = []

    for doi, group in doi_groups.items():
        base = group[0]
        for other in group[1:]:
            # 合并来源
            for api in other.get('source_apis', []):
                if api not in base.get('source_apis', []):
                    base.setdefault('source_apis', []).append(api)
            # 合并优先级
            base['priority_score'] = base.get('priority_score', 0) + other.get('priority_score', 0) // 2
        merged.append(base)

    # 处理无DOI结果
    for paper in no_doi:
        is_dup = False
        for existing in merged:
            # PMID匹配
            if paper.get('pmid') and existing.get('pmid') and paper['pmid'] == existing['pmid']:
                is_dup = True
                break
            # 标题相似度
            title_sim = SequenceMatcher(
                None,
                paper.get('title', '').lower(),
                existing.get('title', '').lower()
            ).ratio()
            if title_sim > 0.95:
                is_dup = True
                break

        if not is_dup:
            merged.append(paper)

    return merged


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='LiterSearch: 命令行文献检索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础检索
  python litersearch.py "dementia care primary care"

  # 指定Vault路径
  python litersearch.py "qualitative research" --vault "D:/ObsidianFiles/paper-weekly"

  # 指定数据源和日期范围
  python litersearch.py "health policy" --sources pubmed scopus --date-range 1y

  # 指定最大结果数和详细笔记数量
  python litersearch.py "alzheimer disease" --max-results 100 --top-n 5

  # 关闭自动翻译
  python litersearch.py "cognitive impairment" --no-translate
        """
    )

    parser.add_argument(
        'query',
        type=str,
        help='检索查询字符串（关键词用空格分隔）'
    )

    parser.add_argument(
        '--vault', '-v',
        type=str,
        default=None,
        help='Obsidian Vault路径（默认从环境变量 OBSIDIAN_VAULT_PATH 读取）'
    )

    parser.add_argument(
        '--sources', '-s',
        nargs='+',
        choices=['pubmed', 'scopus', 'semantic_scholar', 'openalex'],
        default=None,
        help='数据源列表（默认: pubmed semantic_scholar openalex）'
    )

    parser.add_argument(
        '--max-results', '-m',
        type=int,
        default=50,
        help='每个数据源的最大结果数（默认: 50）'
    )

    parser.add_argument(
        '--date-range', '-d',
        type=str,
        default='5y',
        help='日期范围（如: 1y, 5y, 10y, 30d）（默认: 5y）'
    )

    parser.add_argument(
        '--language', '-l',
        type=str,
        choices=['zh', 'en'],
        default='zh',
        help='输出语言（默认: zh）'
    )

    parser.add_argument(
        '--top-n', '-n',
        type=int,
        default=3,
        help='生成详细笔记的论文数量（默认: 3）'
    )

    parser.add_argument(
        '--no-translate',
        action='store_true',
        help='关闭自动翻译'
    )

    parser.add_argument(
        '--no-scoring',
        action='store_true',
        help='关闭高级评分系统（适用于大规模文献综述）'
    )

    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='导出CSV格式的检索结果'
    )

    parser.add_argument(
        '--translation-api',
        type=str,
        choices=['claude', 'custom'],
        default='claude',
        help='翻译API类型（默认: claude）'
    )

    parser.add_argument(
        '--translation-api-url',
        type=str,
        default=None,
        help='自定义翻译API URL（仅当 --translation-api=custom 时需要）'
    )

    parser.add_argument(
        '--translation-api-key',
        type=str,
        default=None,
        help='翻译API密钥（默认从环境变量读取）'
    )

    parser.add_argument(
        '--topic-analysis',
        action='store_true',
        help='生成主题分析报告（包含关键词图谱和文献链接）'
    )

    args = parser.parse_args()

    if not MODULES_AVAILABLE:
        print("错误: 必要模块不可用，请检查依赖安装")
        sys.exit(1)

    # 获取Vault路径
    vault_path = args.vault or os.environ.get('OBSIDIAN_VAULT_PATH')
    if not vault_path:
        print("错误: 未指定Vault路径。请通过 --vault 参数或 OBSIDIAN_VAULT_PATH 环境变量设置。")
        sys.exit(1)

    # 运行检索
    result = asyncio.run(search_literature(
        query=args.query,
        vault_path=vault_path,
        sources=args.sources,
        max_results=args.max_results,
        date_range=args.date_range,
        language=args.language,
        top_n=args.top_n,
        auto_translate=not args.no_translate,
        translation_api=args.translation_api,
        translation_api_key=args.translation_api_key,
        translation_api_url=args.translation_api_url,
        enable_scoring=not args.no_scoring,
        export_csv=args.export_csv
    ))

    # 输出结果
    if result.get('success'):
        print(f"\n检索执行成功!")
        print(f"  摘要文件: {result.get('summary_file')}")
        if result.get('csv_file'):
            print(f"  CSV文件: {result.get('csv_file')}")
        print(f"  生成笔记: {result.get('notes_generated')} 篇")
        if not result.get('scoring_enabled'):
            print(f"  注意: 高级评分系统已禁用")

        # 主题分析
        if args.topic_analysis and result.get('csv_file'):
            print(f"\n========================================")
            print(f"生成主题分析报告")
            print(f"========================================")
            try:
                from topic_analysis import TopicAnalyzer

                date_str = datetime.now().strftime('%Y-%m-%d')
                analysis_output = str(Path(vault_path) / '10_Daily' / f'{date_str}-主题分析报告.md')

                analyzer = TopicAnalyzer(result.get('csv_file'), vault_path)
                analyzer.load_papers()
                analyzer.extract_keywords()
                analyzer.generate_report(analysis_output)

                print(f"  主题分析报告: {analysis_output}")
            except Exception as e:
                logger.error(f"主题分析失败: {e}")
                print(f"  警告: 主题分析失败 - {e}")
    else:
        print(f"\n检索执行失败")
        print(f"  错误: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
