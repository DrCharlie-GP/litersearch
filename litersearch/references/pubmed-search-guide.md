# PubMed 检索规范指南

## 目录
- [基础检索语法](#基础检索语法)
- [字段标签](#字段标签)
- [布尔运算符](#布尔运算符)
- [MeSH术语检索](#mesh术语检索)
- [日期过滤](#日期过滤)
- [高级检索技巧](#高级检索技巧)
- [常见检索模式](#常见检索模式)

---

## 基础检索语法

### 1. 文本词检索 (Text Word)

使用 `[tiab]` 标签在标题和摘要中检索：

```
"dementia care"[tiab]
```

### 2. 标题检索 (Title)

使用 `[ti]` 标签仅在标题中检索：

```
"alzheimer disease"[ti]
```

### 3. 摘要检索 (Abstract)

使用 `[ab]` 标签仅在摘要中检索：

```
"cognitive impairment"[ab]
```

---

## 字段标签

| 标签 | 含义 | 示例 |
|------|------|------|
| `[tiab]` | 标题或摘要 | `dementia[tiab]` |
| `[ti]` | 标题 | `alzheimer[ti]` |
| `[ab]` | 摘要 | `treatment[ab]` |
| `[au]` | 作者 | `Smith J[au]` |
| `[mh]` | MeSH主题词 | `Dementia[mh]` |
| `[majr]` | MeSH主要主题 | `Dementia[majr]` |
| `[tw]` | 文本词（全文） | `care[tw]` |
| `[pt]` | 出版类型 | `Review[pt]` |
| `[dp]` | 出版日期 | `2020:2024[dp]` |
| `[la]` | 语言 | `english[la]` |
| `[journal]` | 期刊名 | `Lancet[journal]` |

---

## 布尔运算符

### AND - 交集

要求所有词都出现：

```
dementia[tiab] AND care[tiab]
```

### OR - 并集

任一词出现即可：

```
dementia[tiab] OR alzheimer[tiab]
```

### NOT - 排除

排除特定词：

```
dementia[tiab] NOT animal[tiab]
```

### 优先级

使用括号控制运算顺序：

```
(dementia[tiab] OR alzheimer[tiab]) AND (care[tiab] OR treatment[tiab])
```

---

## MeSH术语检索

### 什么是MeSH？

MeSH (Medical Subject Headings) 是美国国家医学图书馆的受控词表，用于标准化医学术语。

### MeSH检索优势

1. **标准化**：统一不同表达方式
2. **层级结构**：自动包含下位词
3. **精确性**：减少无关结果

### MeSH检索语法

#### 基础MeSH检索

```
Dementia[mh]
```

自动包含所有下位词（如 Alzheimer Disease, Vascular Dementia等）

#### 不展开下位词

使用 `:noexp` 修饰符：

```
Dementia[mh:noexp]
```

#### MeSH主要主题

使用 `[majr]` 标签：

```
Dementia[majr]
```

仅检索以该MeSH词为主要主题的文献。

### MeSH + 文本词组合

推荐模式：MeSH OR 文本词

```
(Dementia[mh] OR "dementia"[tiab])
```

这样可以：
- 捕获已标引的文献（MeSH）
- 捕获新发表的未标引文献（文本词）

---

## 日期过滤

### 年份范围

```
2020:2024[dp]
```

### 最近N年

med-start-my-day 自动转换：
- `5y` → `2019:2024[dp]`
- `1y` → `2023:2024[dp]`

### 最近N天

med-start-my-day 自动转换：
- `30d` → 最近30天的日期范围

---

## 高级检索技巧

### 1. 短语检索

使用引号进行精确短语匹配：

```
"primary health care"[tiab]
```

### 2. 截词检索

使用 `*` 进行词干检索：

```
nurs*[tiab]
```

匹配：nurse, nurses, nursing

### 3. 出版类型过滤

#### 仅检索RCT

```
"Randomized Controlled Trial"[pt]
```

#### 仅检索综述

```
"Review"[pt] OR "Systematic Review"[pt]
```

#### 排除病例报告

```
NOT "Case Reports"[pt]
```

### 4. 语言过滤

```
english[la]
```

### 5. 人类研究

```
humans[mh]
```

---

## 常见检索模式

### 模式1：疾病 + 干预

```
(Dementia[mh] OR "dementia"[tiab])
AND
(Caregivers[mh] OR "caregiver"[tiab])
```

### 模式2：疾病 + 结局

```
(Alzheimer Disease[mh] OR "alzheimer"[tiab])
AND
(Mortality[mh] OR "mortality"[tiab])
```

### 模式3：人群 + 干预 + 结局

```
(Aged[mh] OR "elderly"[tiab])
AND
(Exercise[mh] OR "exercise"[tiab])
AND
(Cognition[mh] OR "cognitive function"[tiab])
```

### 模式4：定性研究检索

```
(Dementia[mh] OR "dementia"[tiab])
AND
("qualitative"[tiab] OR "interview"[tiab] OR "focus group"[tiab])
```

### 模式5：中国研究检索

```
(Dementia[mh] OR "dementia"[tiab])
AND
("China"[mh] OR "China"[tiab] OR "Chinese"[tiab])
```

---

## Med-Start-My-Day 检索式构建逻辑

### 步骤1：医学主题检测

检查关键词是否包含医学术语（如 dementia, diabetes, care等）

### 步骤2：MeSH映射

从配置文件的 `mesh_terms` 字段获取MeSH术语：

```yaml
mesh_terms:
  - "Dementia"
  - "Alzheimer Disease"
  - "Cognitive Dysfunction"
```

### 步骤3：构建检索式

```python
# 伪代码
for concept in concepts:
    mesh_terms = get_mesh_terms(concept)
    textword = f'"{concept}"[tiab]'

    if mesh_terms:
        part = f"({' OR '.join(mesh_terms)} OR {textword})"
    else:
        part = textword

    query_parts.append(part)

final_query = ' AND '.join(query_parts)
```

### 步骤4：添加日期过滤

```python
date_filter = build_date_filter(date_range)
final_query = f"({final_query}) AND {date_filter}"
```

### 示例输出

输入配置：
```yaml
keywords:
  - "dementia care"
  - "alzheimer disease"
mesh_terms:
  - "Dementia"
  - "Alzheimer Disease"
date_range: "5y"
```

生成检索式：
```
(Dementia[mh] OR "dementia"[tiab])
AND
(Alzheimer Disease[mh] OR "alzheimer"[tiab])
AND
"care"[tiab]
AND
2019:2024[dp]
```

---

## 检索优化建议

### 1. 平衡敏感性和特异性

- **高敏感性**（宽泛检索）：使用 OR，包含同义词
- **高特异性**（精确检索）：使用 AND，限制字段

### 2. 迭代优化

1. 初始检索：宽泛策略
2. 查看结果：识别相关和不相关文献
3. 调整检索式：添加/排除关键词
4. 重新检索：验证改进

### 3. 使用PubMed高级检索构建器

访问：https://pubmed.ncbi.nlm.nih.gov/advanced/

可视化构建复杂检索式。

### 4. 保存检索历史

PubMed允许保存检索式，便于重复使用和更新。

---

## 参考资源

- **PubMed用户指南**：https://pubmed.ncbi.nlm.nih.gov/help/
- **MeSH数据库**：https://www.ncbi.nlm.nih.gov/mesh/
- **PubMed高级检索**：https://pubmed.ncbi.nlm.nih.gov/advanced/
- **检索式构建器**：https://pubmed.ncbi.nlm.nih.gov/advanced/

---

*本指南由 med-start-my-day v1.1.0 提供*
