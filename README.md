# LiterSearch - 医学与学术文献检索工具

> 整合PubMed、Scopus、Semantic Scholar、OpenAlex多数据源的智能文献检索系统

**当前版本**：v1.2.0 + 2026-03-14优化

## 核心特性

### 🔍 多源并行检索
- **PubMed**：医学文献权威数据库，支持MeSH术语映射
- **Scopus**：高质量引文数据库
- **Semantic Scholar**：AI驱动的学术搜索
- **OpenAlex**：开放学术图谱

### 📊 高级评分系统
多维度智能评分（2026-03-14优化）：
- **数据源权重**（30%）：PubMed 100, Scopus 90, Semantic Scholar 60, OpenAlex 50
- **期刊影响力**（35%）：内置100+顶级医学期刊评分（NEJM、Lancet、JAMA等）
- **研究类型**（20%）：RCT 100, 系统综述 95, 队列研究 85, 定性研究 75
- **引用量**（15%）：100+引用 50分，50+引用 40分
- **特殊加成**：中国相关 +50，定性研究 +40，多源验证 +30%

### 🧠 智能主题分析
基于Claude API的主题分析（2026-03-14新增）：
- 从摘要中提取研究内容（15-30字概括）
- 自动聚类相似研究到主��和研究焦点
- 为每条研究内容匹配最相关的3篇文献
- 生成带Obsidian内部链接的双层结构报告
- **按优先级筛选**：支持只分析前N%高质量论文

### 🌐 自动翻译
- 默认使用Claude API翻译英文摘要为中文
- 支持自定义OpenAI兼容API
- 可配置开关

### 📝 Obsidian集成
- 自动生成结构化笔记
- 支持内部链接格式 `[[论文标题|作者 年份]]`
- 按研究领域自动分类

### 📤 灵活导出
- **CSV格式**：适合Excel筛选和文献管理软件导入
- **Markdown格式**：每日推荐笔记和详细论文笔记
- **主题分析报告**：双层结构（主题 → 研究焦点 → 研究内容 → 文献链接）

## 快速开始

### 安装依赖

```bash
cd ~/.claude/skills/litersearch
pip install -r requirements.txt
```

### 环境配置

```bash
# 必需：Obsidian Vault路径
export OBSIDIAN_VAULT_PATH="/path/to/your/vault"

# 可选：API密钥（提高检索限额）
export PUBMED_API_KEY="your_key"
export SCOPUS_API_KEY="your_key"
export SEMANTIC_SCHOLAR_API_KEY="your_key"

# 可选：Claude API（用于翻译和主题分析）
export ANTHROPIC_API_KEY="your_key"
```

## 使用示例

### 场景1：快速检索高质量论文

```bash
python scripts/litersearch.py "dementia care primary care" \
  --max-results 50 \
  --date-range 5y
```

**输出**：
- 每日推荐笔记（按优先级评分排序）
- 前3篇论文的详细笔记
- 自动翻译的中文摘要

### 场景2：系统性文献综述

```bash
python scripts/litersearch.py "dementia interventions systematic review" \
  --sources pubmed scopus semantic_scholar \
  --max-results 200 \
  --date-range 10y \
  --export-csv \
  --no-translate
```

**输出**：
- CSV文件（便于Excel筛选）
- 不生成详细笔记（加快速度）
- 关闭自动翻译

### 场景3：主题分析（推荐）

```bash
# 第1步：检索文献
python scripts/litersearch.py "dementia care" \
  --max-results 500 \
  --export-csv

# 第2步：主题分析（前50%高质量论文）
python scripts/topic_analysis.py "result.csv" \
  --vault "$OBSIDIAN_VAULT_PATH" \
  --top-percent 0.5 \
  --max-papers 100
```

**输出**：
- 从500篇中自动筛选250篇高质量论文
- 限制处理前100篇进行主题分析
- 生成双层结构报告（主题 → 研究焦点 → 研究内容 → 文献链接）
- 为每篇论文创建Obsidian笔记

### 场景4：排除特定研究类型

```bash
python scripts/litersearch.py "dementia care NOT (animal OR mouse OR rat OR cell)" \
  --max-results 200
```

**说明**：使用NOT运算符排除动物研究、细胞研究等

## 命令行参数

### litersearch.py（文献检索）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 检索关键词（必需） | - |
| `--vault` | Obsidian Vault路径 | 环境变量 |
| `--sources` | 数据源列表 | pubmed semantic_scholar openalex |
| `--max-results` | 每个数据源最大结果数 | 50 |
| `--date-range` | 日期范围（1y, 5y, 30d, 2026/01/01:2026/03/14） | 5y |
| `--language` | 输出语言（zh/en） | zh |
| `--top-n` | 生成详细笔记数量 | 3 |
| `--no-translate` | 关闭自动翻译 | False |
| `--export-csv` | 导出CSV格式 | False |

### topic_analysis.py（主题分析）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `csv_file` | CSV文件路径（必需） | - |
| `--vault` | Obsidian Vault路径（必需） | - |
| `--output` | 输出文件路径 | vault/10_Daily/日期-主题分析报告.md |
| `--top-percent` | 按优先级选择前N%（0.5=前50%） | 0.5 |
| `--max-papers` | 限制处理的论文数量 | None |

## 高级功能

### 1. PubMed专业检索

自动构建专业检索式：
- **MeSH术语映射**：40+医学概念自动映射到MeSH术语
- **布尔运算符**：支持AND、OR、NOT
- **日期过滤**：使用 `[pdat]` 字段
- **字段标签**：`[mh]` MeSH术语，`[tiab]` 标题/摘要

示例检索式：
```
((Dementia[mh] OR "dementia care"[tiab]))
NOT (animal[tiab] OR mouse[tiab] OR rat[tiab])
AND 2026/01/01:2026/03/14[pdat]
```

详见：`references/pubmed-search-guide.md`

### 2. 自定义期刊评分

编辑 `references/literature-processing-config.md` 自定义：
- 高影响力期刊列表
- 研究类型权重
- 评分公式权重

### 3. 批量翻译现有笔记

```bash
python scripts/translate_abstract.py \
  --note "path/to/note.md" \
  --api claude
```

## 输出文件

### 1. 每日推荐笔记
**位置**：`{vault}/10_Daily/YYYY-MM-DD-文献推荐.md`

**内容**：
- 检索概览
- 推荐论文列表（按优先级排序）
- 摘要预览

### 2. 详细论文笔记
**位置**：`{vault}/20_Research/Papers/Custom Search/{论文标题}.md`

**内容**：
- 论文元数据（作者、期刊、年份、PMID、DOI）
- 摘要（英文 + 中文翻译）
- 结构化笔记模板（研究目的、方法、发现、意义、局限性）
- 个人评论区
- 相关文献

### 3. CSV文件（可选）
**位置**：`{vault}/10_Daily/YYYY-MM-DD-文献检索结果.csv`

**字段**：序号、标题、作者、期刊、年份、PMID、DOI、数据源、优先级评分、摘要、链接

### 4. 主题分析报告（可选）
**位置**：`{vault}/10_Daily/YYYY-MM-DD-主题分析报告.md`

**结构**：
```
执行摘要
  └─ 研究热点领域

主题1 (N篇)
  ├─ 关键发现
  └─ 研究焦点1
      ├─ 研究内容1 → [[论文1|作者 年份]] [[论文2|作者 年份]]
      ├─ 研究内容2 → [[论文3|作者 年份]] [[论文4|作者 年份]]
      └─ ...
```

## 故障排除

### 问题1：无结果返回
- 检查网络连接
- 验证API密钥配置
- 简化关键词
- 调整日期范围（`--date-range 10y`）

### 问题2：翻译失败
- 检查 `ANTHROPIC_API_KEY` 环境变量
- 验证API密钥有效性
- 临时关闭翻译：`--no-translate`

### 问题3：处理速度慢
- 使用 `--export-csv` 导出CSV而非生成笔记
- 减少 `--max-results` 参数
- 减少 `--top-n` 参数

### 问题4：CSV中文乱码
- CSV使用UTF-8-BOM编码，Excel应能正确显示
- 如仍有问题，用记事本打开CSV，另存为UTF-8编码

### 问题5：主题分析中文乱码
- 已修复（2026-03-14）
- 自动设置Windows控制台UTF-8编码

### 问题6：Scopus检索失败
**原因**：Scopus API需要密钥才能访问

**解决方案**：
1. 获取Scopus API密钥：访问 https://dev.elsevier.com/
2. 配置密钥：`export SCOPUS_API_KEY="your_key"`
3. 或移除Scopus数据源：`--sources pubmed semantic_scholar openalex`

## 参考文档

- `references/pubmed-search-guide.md` - PubMed检索规范指南
- `references/mesh-terms-reference.md` - MeSH术语参考表
- `references/literature-processing-config.md` - 文献处理配置

---

## 更新日志

### v1.2.0 + 2026-03-14优化

#### 新增功能

**1. 集成高级评分系统**
- 多维度智能评分（数据源30% + 期刊35% + 研究类型20% + 引用量15%）
- 自动识别高影响力期刊（100+顶级医学期刊）
- 研究类型识别（RCT、系统综述、队列研究、定性研究等）
- 中国相关研究和定性研究特殊加成
- 测试结果：NEJM的RCT研究得分141分（而不是100分）

**2. 主题分析按优先级筛选**
- 新增 `--top-percent` 参数（默认0.5，即前50%）
- 按优先级评分排序后自动筛选高质量论文
- 从500篇中筛选250篇，大幅减少处理时间
- 提高主题分析的质量和效率

**3. 基于Claude API的智能主题分析**
- 从摘要中提取研究内容（15-30字概括）
- 自动聚类相似研究到主题和研究焦点
- 为每条研究内容匹配最相关的3篇文献
- 生成带Obsidian内部链接的双层结构报告
- 支持 `--max-papers` 参数限制处理数量

**4. Obsidian内部链接支持**
- 自动生成 `[[论文标题|作者 年份]]` 格式链接
- 点击链接快速跳转到相关文献笔记
- 双层结构报告（主题 → 研究焦点 → 研究内容 → 文献链接）

**5. 自动翻译功能**
- 默认使用Claude API翻译英文摘要为中文
- 支持自定义OpenAI兼容API
- 可通过 `--no-translate` 关闭

#### 改进

**1. 修复PubMed检索问题**
- 修复日期过滤：使用 `[pdat]` 替代 `[dp]`
- 修复NOT运算符支持
- 支持多种日期格式（5y、90d、2026/01/01:2026/03/14）

**2. 优化批处理性能**
- 批处理大小优化为200篇/批
- 添加重试机制（最多3次，指数退避）
- 添加30秒超时控制
- API调用延迟优化为0.1秒（有API key时）

**3. 修复Windows控制台乱码**
- 自动设置UTF-8编码（仅Windows平台）
- 所有中文输出正常显示
- 进度信息清晰可读

#### 新增参考文档

- `references/pubmed-search-guide.md` - PubMed检索规范指南
- `references/mesh-terms-reference.md` - MeSH术语参考表
- `references/literature-processing-config.md` - 文献处理配置

#### 文件修改

1. `scripts/search_medical.py`
   - 导入 `advanced_scoring.py`
   - 添加 `use_advanced_scoring` 参数
   - 修复PubMed日期过滤和NOT运算符

2. `scripts/topic_analysis.py`
   - 添加UTF-8编码设置
   - 添加 `--top-percent` 参数
   - 按优先级排序和筛选逻辑
   - 基于Claude API的智能分析

3. `scripts/advanced_scoring.py`
   - 无修改（已存在且功能完整）

### v1.1.0 (2026-03-14)

#### 新增功能

**1. 评分系统开关控制**
- 新增 `--no-scoring` 参数
- 适用于大规模文献综述场景
- 关闭评分后保持原始检索顺序，处理速度更快

**2. CSV格式导出**
- 新增 `--export-csv` 参数
- 导出完整的论文元数据
- 便于在Excel中筛选和管理
- 适合团队协作和文献综述

### v1.0.0 (2026-03-14)

#### 初始版本

- 基于 med-start-my-day 创建
- 命令行驱动的文献检索
- 多源检索（PubMed、Scopus、Semantic Scholar、OpenAlex）
- 高级评分系统
- Obsidian笔记生成
- 自动翻译功能

---

## 致谢

本项目的核心架构和设计理念深受 [evil-read-arxiv](https://github.com/yourusername/evil-read-arxiv) 项目的启发。在其基础上，针对医学文献的特点进行了深度定制和优化。

详见：`ACKNOWLEDGE.md`

## 许可证

本项目遵循与 evil-read-arxiv 相同的开源许可证。
