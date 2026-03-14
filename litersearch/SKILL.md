---
name: litersearch
description: 医学与学术文献检索工具，支持命令行自定义检索主题。整合PubMed、Scopus、Semantic Scholar、OpenAlex多数据源，支持高级评分系统（可开关）、CSV导出、Obsidian笔记生成、自动翻译。特别适用于系统性文献综述、大规模文献检索、医学研究、健康政策等领域。当用户提到"文献检索"、"literature search"、"系统性综述"、"systematic review"、"检索论文"、"search papers"、"文献综述"或需要查找学术文献时使用此skill。
license: MIT
---

# LiterSearch - 医学与学术文献检索

## 目标

帮助用户进行医学和学术文献检索，支持：
- 自定义检索主题（通过命令行参数）
- 多数据源并行检索
- 高级评分系统（可选）
- CSV导出（适合文献综述）
- Obsidian笔记生成
- 自动翻译
- **主题分析与关键词图谱**（新功能）

## 何时使用此 Skill

当用户需要：
- 检索医学或学术文献
- 进行系统性文献综述
- 查找特定主题的论文
- 导出文献列表到CSV
- 生成Obsidian格式的文献笔记

**触发关键词**：
- "检索文献"、"search literature"
- "系统性综述"、"systematic review"
- "查找论文"、"find papers"
- "文献综述"、"literature review"
- "检索 [主题]"

## 工作流程

### 步骤1：理解用户需求

从用户输入中提取：
1. **检索主题** - 关键词或研究问题
2. **检索模式** - 快速筛选 vs 大规模综述
3. **输出需求** - Obsidian笔记 vs CSV导出
4. **特殊要求** - 数据源、时间范围、结果数量等

### 步骤2：确定检索参数

根据用户需求选择合适的参数：

**快速筛选模式**（默认）：
- 启用高级评分系统
- 生成详细笔记（3-5篇）
- 自动翻译
- 适合：日常文献跟踪、快速筛选高质量论文

**文献综述模式**：
- 关闭评分系统（`--no-scoring`）
- 导出CSV（`--export-csv`）
- 关闭翻译（`--no-translate`）
- 不生成详细笔记（`--top-n 0`）
- 大量结果（`--max-results 200`）
- 适合：系统性文献综述、大规模检索

### 步骤3：执行检索

切换到skill目录并执行Python脚本：

```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "[检索主题]" [参数]
```

**基础检索**：
```bash
python scripts/litersearch.py "dementia care primary care"
```

**文献综述模式**：
```bash
python scripts/litersearch.py "systematic review dementia interventions" \
  --max-results 200 \
  --no-scoring \
  --export-csv \
  --no-translate \
  --top-n 0
```

**精细化检索**：
```bash
python scripts/litersearch.py "dementia care qualitative research China" \
  --sources pubmed scopus \
  --max-results 100 \
  --date-range 5y \
  --top-n 5
```

### 步骤4：处理结果

检索完成后，告知用户：
1. **生成的文件位置**
   - Markdown摘要：`{vault}/10_Daily/YYYY-MM-DD-文献推荐.md`
   - CSV文件（如果导出）：`{vault}/10_Daily/YYYY-MM-DD-文献检索结果.csv`
   - 详细笔记：`{vault}/20_Research/Papers/Custom Search/`

2. **检索统计**
   - 总结果数
   - 唯一论文数
   - 生成笔记数

3. **下一步建议**
   - 如果是文献综述：建议在Excel中打开CSV进行筛选
   - 如果是快速筛选：建议查看生成的详细笔记

## 命令行参数

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `query` | 检索主题（关键词） | `"dementia care"` |

### 可选参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--vault` | `-v` | Obsidian Vault路径 | 环境变量 |
| `--sources` | `-s` | 数据源列表 | pubmed semantic_scholar openalex |
| `--max-results` | `-m` | 每个数据源最大结果数 | 50 |
| `--date-range` | `-d` | 日期范围（1y, 5y, 30d） | 5y |
| `--language` | `-l` | 输出语言（zh/en） | zh |
| `--top-n` | `-n` | 生成详细笔记数量 | 3 |
| `--no-translate` | - | 关闭自动翻译 | False |
| `--no-scoring` | - | 关闭高级评分系统 | False |
| `--export-csv` | - | 导出CSV格式 | False |
| `--topic-analysis` | - | 生成主题分析报告（含关键词图谱） | False |

### 数据源选项

- `pubmed` - PubMed（医学文献首选）
- `scopus` - Scopus（高质量引文数据库）
- `semantic_scholar` - Semantic Scholar（AI驱动）
- `openalex` - OpenAlex（开放学术图谱）

## 使用场景

### 场景1：快速查找高质量论文

**用户输入**：
> "帮我检索一下痴呆症照护的最新研究"

**执行**：
```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "dementia care" \
  --max-results 50 \
  --top-n 5
```

**特点**：
- 启用评分系统，优先显示高质量论文
- 生成5篇详细笔记
- 自动翻译摘要

### 场景2：系统性文献综述

**用户输入**：
> "我要做一个关于痴呆症干预措施的系统性综述，帮我检索相关文献"

**执行**：
```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "dementia interventions systematic review" \
  --sources pubmed scopus semantic_scholar \
  --max-results 200 \
  --date-range 10y \
  --no-scoring \
  --export-csv \
  --no-translate \
  --top-n 0
```

**特点**：
- 大规模检索（200篇/数据源）
- 关闭评分系统（加快速度）
- 导出CSV（便于Excel筛选）
- 不生成详细笔记（减少处理时间）

### 场景3：特定主题深入检索

**用户输入**：
> "检索中国的痴呆症定性研究，最近5年的"

**执行**：
```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "dementia care qualitative research China" \
  --sources pubmed \
  --max-results 100 \
  --date-range 5y \
  --top-n 10
```

**特点**：
- 针对性检索
- 生成10篇详细笔记
- 启用评分系统

### 场景4：仅导出CSV列表

**用户输入**：
> "帮我检索健康政策相关的文献，导出成CSV"

**执行**：
```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "health policy reform" \
  --export-csv \
  --max-results 100 \
  --top-n 0
```

### 场景5：主题分析与关键词图谱（新功能）

**用户输入**：
> "帮我检索失智症照护最近2年的文献，至少200篇，并对摘要进行主题分析"

**执行**：
```bash
cd "$SKILL_DIR"
python scripts/litersearch.py "dementia care" \
  --date-range 2y \
  --max-results 200 \
  --export-csv \
  --no-translate \
  --top-n 0 \
  --topic-analysis
```

**特点**：
- 生成关键词共现网络图（Mermaid格式，在Obsidian中可视化）
- 自动识别研究主题（照护者、干预措施、技术应用等）
- 每个主题显示代表性研究，并生成Obsidian内部链接
- 显示主题之间的关联关系和共现强度
- 适合：快速了解研究领域全貌、识别研究热点、发现跨学科关联

**生成文件**：
- CSV文件：`{vault}/10_Daily/YYYY-MM-DD-文献检索结果.csv`
- 主题分析报告：`{vault}/10_Daily/YYYY-MM-DD-主题分析报告.md`
  - 包含关键词共现网络图
  - 每个主题的代表性研究（带Obsidian链接）
  - 主题之间的关联分析

## 环境要求

### 必需环境变量

```bash
# Obsidian Vault路径（必填）
export OBSIDIAN_VAULT_PATH="D:/ObsidianFiles/paper-weekly"
```

### 可选环境变量（提高API限额）

```bash
# PubMed API Key
export PUBMED_API_KEY="your_key"

# Scopus API Key
export SCOPUS_API_KEY="your_key"

# Semantic Scholar API Key
export SEMANTIC_SCHOLAR_API_KEY="your_key"

# Claude API Key（用于自动翻译）
export ANTHROPIC_API_KEY="your_key"
```

### Python依赖

skill目录包含 `requirements.txt`：
```
PyYAML>=6.0
aiohttp>=3.8.0
requests>=2.28.0
```

如果用户首次使用，提示安装：
```bash
cd "$SKILL_DIR"
pip install -r requirements.txt
```

## 输出文件

### 1. Markdown摘要

**位置**：`{vault}/10_Daily/YYYY-MM-DD-文献推荐.md`

**内容**：
- 检索概览
- 检索详情
- 推荐论文列表（按优先级排序）

### 2. CSV文件（可选）

**位置**：`{vault}/10_Daily/YYYY-MM-DD-文献检索结果.csv`

**字段**：
- 序号、标题、作者、期刊、年份
- PMID、DOI、数据源
- 优先级评分
- 摘要、链接

**用途**：
- 在Excel中筛选和管理
- 团队协作共享
- 导入文献管理软件

### 3. 详细笔记（可选）

**位置**：`{vault}/20_Research/Papers/Custom Search/{论文标题}.md`

**内容**：
- 论文元数据
- 摘要（英文 + 中文翻译）
- 结构化笔记模板

## 高级评分系统

### 何时启用（默认）

- 需要快速筛选高质量论文
- 关注特定类型研究（RCT、定性研究）
- 关注高影响力期刊
- 关注中国相关研究

### 何时关闭（`--no-scoring`）

- 进行大规模文献综述（200+篇）
- 需要保持原始检索顺序
- 评分系统处理速度较慢
- 只需要快速获取文献列表

### 评分维度

```
总分 = 数据源评分 × 30%
     + 期刊影响力评分 × 35%
     + 研究类型评分 × 20%
     + 引用量评分 × 15%
     + 特殊加成
```

**特殊加成**：
- 中国相关研究：+50
- 定性研究：+40
- 多源验证：+原分值的30%

## 参考文档

skill包含以下参考文档（位于 `references/` 目录）：

### 1. PubMed检索规范

**文件**：`references/pubmed-search-guide.md`

**内容**：
- 基础检索语法
- MeSH术语检索
- 日期过滤技巧
- 常见检索模式

### 2. MeSH术语参考

**文件**：`references/mesh-terms-reference.md`

**内容**：
- 痴呆症与认知障碍
- 初级卫生保健
- 健康政策
- 研究方法

### 3. 文献处理配置

**文件**：`references/literature-processing-config.md`

**内容**：
- 高影响力期刊列表（可自定义）
- 研究类型权重
- 评分公式权重

## 故障排除

### 问题1：无结果返回

**原因**：
- 网络连接问题
- API限制
- 关键词过于具体

**解决**：
1. 检查网络连接
2. 简化关键词
3. 调整日期范围（`--date-range 10y`）
4. 增加最大结果数（`--max-results 100`）

### 问题2：翻译失败

**原因**：
- 未设置 `ANTHROPIC_API_KEY`
- API密钥无效

**解决**：
1. 设置环境变量：`export ANTHROPIC_API_KEY="your_key"`
2. 或临时关闭翻译：`--no-translate`

### 问题3：处理速度慢

**原因**：
- 大规模检索 + 启用评分系统

**解决**：
- 使用 `--no-scoring` 关闭评分系统
- 减少 `--max-results` 参数
- 减少 `--top-n` 参数

### 问题4：CSV中文乱码

**原因**：
- Excel编码问题

**解决**：
- CSV使用UTF-8-BOM编码，Excel应能正确显示
- 如仍有问题，用记事本打开CSV，另存为UTF-8编码

## 最佳实践

### 1. 文献综述工作流

**第1步：大规模初步检索**
```bash
python scripts/litersearch.py "your topic" \
  --max-results 200 \
  --no-scoring \
  --export-csv \
  --no-translate \
  --top-n 0
```

**第2步：Excel筛选**
- 打开CSV文件
- 根据标题、摘要、期刊筛选
- 标记感兴趣的论文

**第3步：精细化检索**
```bash
python scripts/litersearch.py "refined topic" \
  --max-results 50 \
  --top-n 10
```

### 2. 日常文献跟踪

**每周检索最新文献**：
```bash
python scripts/litersearch.py "your topic" \
  --date-range 7d \
  --max-results 30 \
  --top-n 5
```

### 3. 多角度检索

**不同关键词组合**：
```bash
# 检索1：广泛主题
python scripts/litersearch.py "dementia care"

# 检索2：特定研究类型
python scripts/litersearch.py "dementia care RCT"

# 检索3：特定地区
python scripts/litersearch.py "dementia care China"
```

## 与用户交互

### 询问关键信息

如果用户请求不够具体，询问：

1. **检索主题**
   - "你想检索什么主题的文献？"
   - "有具体的关键词吗？"

2. **检索目的**
   - "是快速查找几篇高质量论文，还是做系统性文献综述？"
   - "需要多少篇文献？"

3. **输出格式**
   - "需要生成Obsidian笔记吗？"
   - "需要导出CSV格式吗？"

4. **特殊要求**
   - "有时间范围要求吗？（如最近1年、5年）"
   - "有特定的数据源偏好吗？（如只用PubMed）"

### 提供建议

根据用户需求提供建议：

**如果用户说"文献综述"**：
> "建议使用文献综述模式：大规模检索（200篇/数据源）+ 关闭评分系统 + 导出CSV。这样你可以在Excel中进行初步筛选。"

**如果用户说"查找几篇论文"**：
> "建议使用快速筛选模式：启用评分系统，生成3-5篇详细笔记，自动翻译摘要。"

**如果用户说"最新研究"**：
> "建议设置时间范围为最近1年（--date-range 1y）或最近30天（--date-range 30d）。"

## 注意事项

1. **首次使用**
   - 检查Python依赖是否安装
   - 检查环境变量是否设置
   - 提示用户配置API密钥（可选但推荐）

2. **大规模检索**
   - 提醒用户可能需要较长时间
   - 建议关闭评分系统和翻译
   - 建议导出CSV而非生成大量笔记

3. **API限制**
   - 提醒用户注意API限制
   - 建议配置API密钥提高限额
   - 如遇限制，建议减少结果数或等待

4. **文件位置**
   - 明确告知生成文件的位置
   - 提供完整路径
   - 建议下一步操作

## 示例对话

**用户**：帮我检索一下痴呆症照护的文献

**回复**：
好的，我来帮你检索痴呆症照护的文献。请问：
1. 你是想快速查找几篇高质量论文，还是要做系统性文献综述？
2. 有时间范围要求吗？（如最近1年、5年）
3. 需要导出CSV格式吗？

**用户**：快速查找几篇高质量的，最近5年的

**回复**：
明白了，我会使用快速筛选模式，检索最近5年的痴呆症照护文献，生成5篇详细笔记并自动翻译摘要。

[执行检索]

检索完成！
- 总结果数：87篇
- 唯一论文：85篇
- 生成笔记：5篇

生成的文件：
- 摘要：D:/ObsidianFiles/paper-weekly/10_Daily/2026-03-14-文献推荐.md
- 详细笔记：D:/ObsidianFiles/paper-weekly/20_Research/Papers/Custom Search/

建议你先查看摘要文件，了解所有检索结果，然后阅读生成的5篇详细笔记。
