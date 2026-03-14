#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献主题分析工具（基于Claude API）
功能：
1. 使用Claude API从摘要中提取研究内容
2. 聚类相似的研究内容到研究焦点
3. 为每条研究内容匹配最相关的文献
4. 生成双层结构的主题分析报告
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Set
from datetime import datetime
import anthropic

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class TopicAnalyzer:
    """主题分析器"""

    def __init__(self, csv_path: str, vault_path: str):
        self.csv_path = csv_path
        self.vault_path = Path(vault_path)
        self.papers = []
        self.research_items = []  # 提取的研究内容列表
        self.theme_structure = defaultdict(lambda: defaultdict(list))  # 主题 -> 研究焦点 -> 研究内容列表
        self.papers_folder = self.vault_path / '20_Research' / 'Papers' / 'Custom Search'
        self.papers_folder.mkdir(parents=True, exist_ok=True)
        self.graph_folder = self.vault_path / '20_Research' / 'PaperGraph'
        self.graph_folder.mkdir(parents=True, exist_ok=True)

        # 初始化Claude客户端
        api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')
        if not api_key:
            raise ValueError("未找到ANTHROPIC_API_KEY或ANTHROPIC_AUTH_TOKEN环境变量")

        # 获取base_url和model（如果有）
        base_url = os.environ.get('ANTHROPIC_BASE_URL')
        self.model = os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')

        if base_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

    def load_papers(self, top_percent: float = 1.0):
        """
        加载CSV文件中的论文

        参数：
            top_percent: 按优先级评分选择的百分比（0.5表示前50%）
        """
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                abstract = row.get('摘要', '')
                title = row.get('标题', '')

                if title:
                    self.papers.append({
                        'id': i + 1,
                        'title': title,
                        'authors': row.get('作者', ''),
                        'journal': row.get('期刊', ''),
                        'year': row.get('年份', ''),
                        'pmid': row.get('PMID', ''),
                        'doi': row.get('DOI', ''),
                        'abstract': abstract if abstract else '',
                        'priority': row.get('优先级评分', '50'),
                        'pubmed_link': row.get('PubMed链接', ''),
                        'doi_link': row.get('DOI链接', '')
                    })

        # 按优先级评分排序
        self.papers.sort(key=lambda x: int(x.get('priority', 50)), reverse=True)

        # 选择前N%
        if top_percent < 1.0:
            cutoff = int(len(self.papers) * top_percent)
            self.papers = self.papers[:cutoff]
            print(f"按优先级评分选择前 {int(top_percent*100)}%，共 {len(self.papers)} 篇论文")
        else:
            print(f"加载了 {len(self.papers)} 篇论文")

    def extract_research_content_batch(self, max_papers=None):
        """第一步：使用Claude API批量提取研究内容"""
        print("正在使用Claude API提取研究内容...")

        # 只处理有摘要的论文
        papers_with_abstract = [p for p in self.papers if p['abstract']]

        # 限制处理数量
        if max_papers and max_papers < len(papers_with_abstract):
            papers_with_abstract = papers_with_abstract[:max_papers]
            print(f"限制处理前 {max_papers} 篇论文")

        # 分批处理（每批20篇）
        batch_size = 20
        total_batches = (len(papers_with_abstract) + batch_size - 1) // batch_size

        for i in range(0, len(papers_with_abstract), batch_size):
            batch = papers_with_abstract[i:i+batch_size]
            batch_num = i // batch_size + 1

            # 构建prompt
            papers_text = ""
            for idx, paper in enumerate(batch, 1):
                papers_text += f"\n论文{idx}:\n标题: {paper['title']}\n摘要: {paper['abstract'][:500]}\n"

            prompt = f"""请分析以下失智症照护相关论文，为每篇论文提取一句话的核心研究内容描述。

要求：
1. 用一句话（15-30字）概括论文的核心研究内容
2. 描述要具体、可操作，突出研究的创新点或关键发现
3. 使用中文
4. 格式：论文X: [研究内容描述]

{papers_text}

请按格式输出每篇论文的研究内容："""

            try:
                print(f"正在处理批次 {batch_num}/{total_batches}...", flush=True)
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = message.content[0].text

                # 解析响应
                for idx, paper in enumerate(batch, 1):
                    pattern = rf"论文{idx}[:：]\s*(.+?)(?=\n论文\d+|$)"
                    match = re.search(pattern, response_text, re.DOTALL)
                    if match:
                        content = match.group(1).strip()
                        self.research_items.append({
                            'content': content,
                            'paper': paper,
                            'paper_id': paper['id']
                        })
                    else:
                        # 如果提取失败，使用标题作为fallback
                        self.research_items.append({
                            'content': paper['title'],
                            'paper': paper,
                            'paper_id': paper['id']
                        })

                print(f"[OK] 批次 {batch_num}/{total_batches} 完成，已处理 {min(i+batch_size, len(papers_with_abstract))}/{len(papers_with_abstract)} 篇", flush=True)

            except Exception as e:
                print(f"[FAIL] 批次 {batch_num}/{total_batches} 处理失败: {e}", flush=True)
                # 失败时使用标题作为fallback
                for paper in batch:
                    self.research_items.append({
                        'content': paper['title'],
                        'paper': paper,
                        'paper_id': paper['id']
                    })

    def cluster_research_items(self):
        """第二步：使用Claude API聚类研究内容"""
        print("正在聚类研究内容...")

        # 构建所有研究内容的列表
        items_text = ""
        for idx, item in enumerate(self.research_items, 1):
            items_text += f"{idx}. {item['content']}\n"

        prompt = f"""请分析以下失智症照护研究内容，将它们归类到合适的主题和研究焦点下。

研究内容列表：
{items_text}

请按以下JSON格式输出分类结果：
{{
  "主题名称1": {{
    "研究焦点1": [1, 3, 5],  // 研究内容的编号
    "研究焦点2": [2, 4]
  }},
  "主题名称2": {{
    "研究焦点1": [6, 7]
  }}
}}

主题示例：照护者支持与负担、技术与数字化干预、临床评估与诊断、干预措施与治疗、照护质量与政策等
研究焦点示例：照护者负担评估、移动健康应用、生物标志物研究、非药物干预等

要求：
1. 主题要宽泛，研究焦点要具体
2. 每个研究内容只归到最相关的一个焦点
3. 使用中文
4. 只输出JSON，不要其他文字"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                clustering = json.loads(json_match.group())

                # 构建主题结构
                for theme, focuses in clustering.items():
                    for focus, item_indices in focuses.items():
                        for idx in item_indices:
                            if 1 <= idx <= len(self.research_items):
                                item = self.research_items[idx - 1]
                                self.theme_structure[theme][focus].append(item)

                print(f"聚类完成，识别出 {len(self.theme_structure)} 个主题")
            else:
                print("聚类失败，使用默认分类")
                self._fallback_clustering()

        except Exception as e:
            print(f"聚类失败: {e}，使用默认分类")
            self._fallback_clustering()

    def _fallback_clustering(self):
        """备用聚类方法（基于关键词）"""
        keyword_mapping = {
            '照护者支持与负担': {
                '照护者负担': ['caregiver', 'burden', 'stress', 'family care'],
                '照护者支持': ['support', 'assistance', 'help']
            },
            '技术与数字化干预': {
                '移动健康': ['mobile', 'app', 'mhealth'],
                '人工智能': ['ai', 'artificial intelligence', 'machine learning']
            },
            '临床评估与诊断': {
                '生物标志物': ['biomarker', 'amyloid', 'tau'],
                '认知评估': ['assessment', 'screening', 'diagnosis']
            }
        }

        for item in self.research_items:
            text = (item['paper']['title'] + ' ' + item['paper']['abstract']).lower()
            matched = False

            for theme, focuses in keyword_mapping.items():
                for focus, keywords in focuses.items():
                    if any(kw in text for kw in keywords):
                        self.theme_structure[theme][focus].append(item)
                        matched = True
                        break
                if matched:
                    break

            if not matched:
                self.theme_structure['其他研究']['未分类'].append(item)

    def find_related_papers(self, research_content: str, paper_id: int, top_k: int = 3) -> List[Dict]:
        """第三步：为研究内容找到最相关的文献"""
        # 简化版：返回该研究内容对应的原始论文，以及同一焦点下优先级最高的其他论文
        related = []

        # 首先添加原始论文
        original_paper = next((p for p in self.papers if p['id'] == paper_id), None)
        if original_paper:
            related.append(original_paper)

        # 然后从同一研究焦点中找其他高优先级论文
        for theme, focuses in self.theme_structure.items():
            for focus, items in focuses.items():
                # 检查当前研究内容是否在这个焦点中
                if any(item['paper_id'] == paper_id for item in items):
                    # 找到同焦点的其他论文
                    other_papers = [
                        item['paper'] for item in items
                        if item['paper_id'] != paper_id
                    ]
                    # 按优先级排序
                    other_papers.sort(key=lambda p: int(p.get('priority', 50)), reverse=True)
                    related.extend(other_papers[:top_k-1])
                    break

        return related[:top_k]

    def create_paper_note(self, paper: Dict) -> str:
        """创建单篇论文的完整笔记"""
        title = paper['title']
        note_filename = self._sanitize_filename(title) + '.md'
        note_path = self.papers_folder / note_filename

        if note_path.exists():
            return note_filename[:-3]

        note_content = [
            f"# {title}",
            "",
            "## 基本信息",
            "",
            f"- **作者**: {paper['authors']}",
            f"- **期刊**: {paper['journal']}",
            f"- **年份**: {paper['year']}",
        ]

        if paper['pmid']:
            note_content.append(f"- **PMID**: [{paper['pmid']}]({paper['pubmed_link']})")

        if paper['doi']:
            note_content.append(f"- **DOI**: [{paper['doi']}]({paper['doi_link']})")

        note_content.extend([
            "",
            "## 摘要",
            "",
            paper['abstract'] if paper['abstract'] else "（无摘要）",
            "",
            "## 研究笔记",
            "",
            "### 研究目的",
            "",
            "",
            "### 研究方法",
            "",
            "",
            "### 主要发现",
            "",
            "",
            "### 研究意义",
            "",
            "",
            "### 局限性",
            "",
            "",
            "## 个人评论",
            "",
            "",
            "## 相关文献",
            "",
            "",
            "---",
            "",
            f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**优先级评分**: {paper['priority']}"
        ])

        with open(note_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(note_content))

        return note_filename[:-3]

    def generate_report(self, output_path: str):
        """生成主题分析报告"""
        date_str = datetime.now().strftime('%Y-%m-%d')

        print("正在生成主题分析报告...")

        report = [
            f"# 失智症照护文献主题分析报告",
            "",
            f"**检索日期**: {date_str}",
            f"**文献总数**: {len(self.papers)}篇",
            f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            ""
        ]

        # 执行摘要
        total_themes = len(self.theme_structure)
        theme_counts = [(theme, sum(len(items) for items in focuses.values()))
                       for theme, focuses in self.theme_structure.items()]
        theme_counts.sort(key=lambda x: x[1], reverse=True)

        report.extend([
            "## 执行摘要",
            "",
            f"本次检索共纳入 **{len(self.papers)}** 篇文献，识别出 **{total_themes}** 个主要研究领域。",
            "",
            "**研究热点领域**：",
            ""
        ])

        for i, (theme, count) in enumerate(theme_counts[:3], 1):
            report.append(f"{i}. **{theme}**（{count}篇相关研究）")

        report.extend([
            "",
            "---",
            "",
            "## 研究焦点",
            "",
            "以下按主题分类展示具体研究内容。每条研究内容后列出最相关的文献。",
            "",
            "---",
            ""
        ])

        # 生成各主题内容
        for theme, focuses in sorted(self.theme_structure.items(),
                                     key=lambda x: sum(len(items) for items in x[1].values()),
                                     reverse=True):
            total_count = sum(len(items) for items in focuses.values())
            report.append(f"### {theme} ({total_count}篇)")
            report.append("")

            # 关键发现
            report.append("#### 关键发现")
            report.append("")
            for focus, items in sorted(focuses.items(), key=lambda x: len(x[1]), reverse=True):
                report.append(f"- **{focus}**: {len(items)}篇")
            report.append("")

            # 研究焦点
            report.append("#### 研究焦点")
            report.append("")

            for focus_idx, (focus, items) in enumerate(sorted(focuses.items(),
                                                              key=lambda x: len(x[1]),
                                                              reverse=True), 1):
                report.append(f"##### {focus_idx}. {focus}")
                report.append("")

                # 按优先级排序
                sorted_items = sorted(items,
                                    key=lambda x: int(x['paper'].get('priority', 50)),
                                    reverse=True)[:10]

                for item in sorted_items:
                    content = item['content']
                    paper_id = item['paper_id']

                    # 找到相关文献
                    related_papers = self.find_related_papers(content, paper_id, top_k=3)

                    # 创建文献笔记
                    paper_links = []
                    for paper in related_papers:
                        note_name = self.create_paper_note(paper)
                        # 使用第一作者+年份作为简短显示
                        first_author = paper['authors'].split(' et al.')[0] if ' et al.' in paper['authors'] else paper['authors'].split(',')[0]
                        short_ref = f"{first_author} {paper['year']}"
                        paper_links.append(f"[[{note_name}|{short_ref}]]")

                    # 生成条目：研究内容 → 文献链接
                    links_str = " ".join(paper_links)
                    report.append(f"- {content} → {links_str}")

                if len(items) > 10:
                    report.append(f"- *（还有 {len(items) - 10} 条相关研究未列出）*")

                report.append("")

            report.append("---")
            report.append("")

        # 写入报告
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"[OK] 主题分析报告已生成: {output_path}")
        print(f"[OK] 文献笔记已保存至: {self.papers_folder}")

    def _sanitize_filename(self, title: str) -> str:
        """清理文件名"""
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            title = title.replace(char, '')
        if len(title) > 100:
            title = title[:100]
        return title.strip()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='文献主题分析工具（基于Claude API）')
    parser.add_argument('csv_file', help='CSV文件路径')
    parser.add_argument('--vault', help='Obsidian Vault路径', required=True)
    parser.add_argument('--output', help='输出文件路径', default=None)
    parser.add_argument('--max-papers', type=int, help='限制处理的论文数量', default=None)
    parser.add_argument('--top-percent', type=float, help='按优先级选择前N%%的论文（0.5表示前50%%）', default=0.5)

    args = parser.parse_args()

    if args.output is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        args.output = str(Path(args.vault) / '10_Daily' / f'{date_str}-主题分析报告.md')

    # 创建分析器
    analyzer = TopicAnalyzer(args.csv_file, args.vault)

    # 执行分析
    analyzer.load_papers(top_percent=args.top_percent)
    print(f"加载了 {len(analyzer.papers)} 篇论文")
    if args.max_papers:
        print(f"将限制处理前 {args.max_papers} 篇")

    analyzer.extract_research_content_batch(max_papers=args.max_papers)  # 第一步：提取研究内容
    print(f"提取了 {len(analyzer.research_items)} 条研究内容")

    analyzer.cluster_research_items()          # 第二步：聚类
    print(f"识别出 {len(analyzer.theme_structure)} 个主题")

    analyzer.generate_report(args.output)      # 第三步：生成报告（包含匹配文献）


if __name__ == '__main__':
    main()
