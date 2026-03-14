# 文献处理参考配置

本文件用于自定义文献评分和处理的各项参数。

## 目录
- [高影响力期刊列表](#高影响力期刊列表)
- [研究类型权重](#研究类型权重)
- [评分权重配置](#评分权重配置)
- [特殊加成配置](#特殊加成配置)
- [如何使用本配置](#如何使用本配置)

---

## 高影响力期刊列表

### 使用说明

在此处自定义你认为的高影响力期刊及其评分（0-100分）。评分越高，该期刊发表的论文优先级越高。

### 综合医学期刊（顶级）

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| New England Journal of Medicine | 100 | 医学顶刊 |
| NEJM | 100 | 同上（缩写） |
| The Lancet | 100 | 医学顶刊 |
| Lancet | 100 | 同上（简写） |
| JAMA | 95 | 美国医学会杂志 |
| Journal of the American Medical Association | 95 | 同上（全称） |
| BMJ | 90 | 英国医学杂志 |
| British Medical Journal | 90 | 同上（全称） |
| PLoS Medicine | 85 | 开放获取高质量期刊 |

### 综合科学期刊

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Nature | 100 | 顶级科学期刊 |
| Science | 100 | 顶级科学期刊 |
| Cell | 100 | 顶级生命科学期刊 |
| Nature Medicine | 100 | Nature子刊-医学 |

### 专科期刊 - 神经科学与痴呆症

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Alzheimer's & Dementia | 95 | 痴呆症研究顶刊 |
| Alzheimer's and Dementia | 95 | 同上（不同写法） |
| Brain | 95 | 神经科学顶刊 |
| Neurology | 90 | 神经病学权威期刊 |
| Journal of Alzheimer's Disease | 80 | 阿尔茨海默病专业期刊 |
| Journal of Neurology Neurosurgery and Psychiatry | 85 | 神经精神病学 |
| JNNP | 85 | 同上（缩写） |
| Dementia | 75 | 痴呆症专业期刊 |
| International Psychogeriatrics | 75 | 老年精神病学 |

### 专科期刊 - 初级卫生保健

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Annals of Family Medicine | 80 | 家庭医学顶刊 |
| British Journal of General Practice | 75 | 英国全科医学 |
| BJGP | 75 | 同上（缩写） |
| Family Practice | 70 | 家庭医学实践 |
| BMC Primary Care | 70 | BMC家庭医学 |
| Journal of General Internal Medicine | 75 | 综合内科医学 |
| Primary Care | 65 | 初级保健 |

### 专科期刊 - 健康政策与公共卫生

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Health Affairs | 85 | 健康政策顶刊 |
| Milbank Quarterly | 80 | 健康政策研究 |
| Health Policy | 75 | 健康政策 |
| Health Services Research | 75 | 卫生服务研究 |
| Social Science & Medicine | 80 | 社会医学 |
| Journal of Health Politics Policy and Law | 75 | 健康政治与政策 |
| International Journal of Health Services | 70 | 国际卫生服务 |

### 专科期刊 - 定性研究

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Qualitative Health Research | 75 | 定性健康研究顶刊 |
| BMC Qualitative Research | 70 | BMC定性研究 |
| International Journal of Qualitative Studies on Health and Well-being | 70 | 定性研究 |
| Qualitative Research | 70 | 定性研究方法 |

### 专科期刊 - 老年医学

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Journal of the American Geriatrics Society | 85 | 美国老年医学会 |
| JAGS | 85 | 同上（缩写） |
| Age and Ageing | 80 | 年龄与衰老 |
| Journals of Gerontology | 75 | 老年学系列期刊 |
| Geriatrics | 70 | 老年医学 |

### 开放获取期刊（高质量）

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| BMJ Open | 75 | BMJ开放获取 |
| PLOS ONE | 65 | 综合开放获取 |
| Frontiers in Aging Neuroscience | 70 | Frontiers衰老神经科学 |
| Frontiers in Public Health | 70 | Frontiers公共卫生 |

### 中国期刊（英文）

| 期刊名称 | 评分 | 说明 |
|---------|------|------|
| Chinese Medical Journal | 70 | 中华医学杂志英文版 |
| Journal of Geriatric Cardiology | 65 | 老年心脏病学 |

---

## 研究类型权重

### 使用说明

定义不同研究类型的权重（0-100分）。权重越高，该类型研究的优先级越高。

### 研究类型评分表

| 研究类型 | 评分 | 说明 |
|---------|------|------|
| Randomized Controlled Trial | 100 | 随机对照试验（金标准） |
| RCT | 100 | 同上（缩写） |
| Systematic Review | 95 | 系统综述 |
| Meta-Analysis | 95 | Meta分析 |
| Cohort Study | 85 | 队列研究 |
| Cohort | 85 | 同上（简写） |
| Prospective Study | 80 | 前瞻性研究 |
| Prospective | 80 | 同上（简写） |
| Qualitative Study | 75 | 定性研究 |
| Qualitative | 75 | 同上（简写） |
| Mixed Methods | 80 | 混合方法研究 |
| Case-Control Study | 70 | 病例对照研究 |
| Case-Control | 70 | 同上（简写） |
| Cross-Sectional Study | 60 | 横断面研究 |
| Cross-Sectional | 60 | 同上（简写） |
| Review | 65 | 一般综述 |
| Case Series | 45 | 病例系列 |
| Case Report | 40 | 病例报告 |

### 定性研究方法关键词

以下关键词用于识别定性研究：

- qualitative
- interview
- focus group
- thematic analysis
- grounded theory
- phenomenology
- ethnography
- narrative
- content analysis
- discourse analysis
- lived experience
- participant observation
- case study
- 定性
- 访谈
- 焦点小组
- 主题分析

---

## 评分权重配置

### 总评分公式

```
总分 = 数据源评分 × 20%
     + 期刊影响力评分 × 35%
     + 研究类型评分 × 25%
     + 引用量评分 × 20%
     + 特殊加成
```

### 权重说明

| 维度 | 权重 | 说明 |
|------|------|------|
| 数据源 | 30% | 论文来源的可靠性 |
| 期刊影响力 | 35% | 发表期刊的质量（最重要） |
| 研究类型 | 20% | 研究设计的严谨性 |
| 引用量 | 15% | 学术影响力 |

### 数据源基础评分

| 数据源 | 评分 | 说明 |
|--------|------|------|
| PubMed | 100 | 医学文献权威数据库 |
| Scopus | 90 | 高质量引文数据库 |
| Web of Science | 80 | 科学引文索引 |
| Semantic Scholar | 60 | AI驱动的学术搜索 |
| OpenAlex | 50 | 开放学术图谱 |

### 引用量评分标准

| 引用次数 | 评分 | 说明 |
|---------|------|------|
| 100+ | 50 | 高影响力论文 |
| 50-99 | 40 | 较高影响力 |
| 20-49 | 30 | 中等影响力 |
| 10-19 | 20 | 一般影响力 |
| 5-9 | 10 | 较低影响力 |
| 0-4 | 0 | 新发表或低影响力 |

---

## 特殊加成配置

### 中国相关研究加成

**加成分数**: +40

**识别条件**（满足任一即可）：
1. 标题或摘要包含中国相关关键词
2. 作者姓名符合中国姓氏模式

**中国关键词列表**：
- China
- Chinese
- Beijing
- Shanghai
- Guangzhou
- Shenzhen
- Hong Kong
- Taiwan
- Mainland China
- PRC
- 中国
- 中华
- 北京
- 上海
- 广州
- 深圳
- 香港
- 台湾

**中国姓氏模式**（正则表达式）：
```
Wang, Zhang, Li, Liu, Chen, Yang, Huang, Zhao, Wu, Zhou,
Xu, Sun, Ma, Zhu, Hu, Guo, He, Gao, Lin, Luo, Zheng,
Liang, Song, Tang, Xu, Han, Feng, Yu, Dong, Xiao, Cheng,
Cao, Yuan, Deng, Xie, Pan, Peng, Jiang, Dai, Tian, Fan,
Ren, Wei, Jin, Shi, Jiang, Qin, Cui, Lu, Gu, Ye, Su, Lv,
Ding, Xia, Mao, Qian, Yin, Yao, Shao, Wan, Lei, Qiu,
Kong, Bai, Cui, Tan, Xiong, Lu, Chang, Meng, Qin, Yan,
Zou, Xiang, Duan, Zhong
```

### 定性研究加成

**加成分数**: +35

**识别条件**：
标题或摘要包含定性研究关键词（见"研究类型权重"部分）

### 多源验证加成

**加成计算**: 原分值 × 10%

**说明**：
- 如果论文同时出现在多个数据源中，说明其质量较高
- 例如：同时在PubMed和Scopus中检索到的论文，会获得额外加成

---

## 如何使用本配置

### 方法1：直接编辑本文件

1. 在上述表格中添加、删除或修改期刊
2. 调整评分（0-100）
3. 保存文件
4. 重新运行 `start my day`

### 方法2：通过代码加载

本配置文件会被 `advanced_scoring.py` 自动读取。如果你修改了本文件，评分系统会自动使用新的配置。

### 示例：添加新期刊

```markdown
| Journal of My Research | 85 | 我的研究领域顶刊 |
```

### 示例：调整权重

修改"评分权重配置"部分的百分比，例如：

```
总分 = 数据源评分 × 20%    # 降低数据源权重
     + 期刊影响力评分 × 45%  # 提高期刊权重
     + 研究类型评分 × 20%
     + 引用量评分 × 15%
```

然后在 `advanced_scoring.py` 中相应修改代码。

### 示例：添加新的特殊加成

在"特殊加成配置"部分添加新的加成规则，例如：

```markdown
### 欧洲研究加成

**加成分数**: +30

**识别条件**：
标题或摘要包含欧洲国家名称
```

然后在 `advanced_scoring.py` 中实现相应逻辑。

---

## 配置更新日志

### v1.1.0 (2026-03-14)
- 初始版本
- 包含100+医学期刊
- 定义研究类型权重
- 配置中国相关和定性研究加成

### 如何贡献

如果你发现遗漏的重要期刊或有更好的评分建议，请：
1. 编辑本文件
2. 在"配置更新日志"中记录你的修改
3. 重新测试评分效果

---

## 参考资源

- **期刊影响因子查询**: https://www.scimagojr.com/
- **中科院期刊分区**: http://www.fenqubiao.com/
- **PubMed期刊列表**: https://www.ncbi.nlm.nih.gov/nlmcatalog/journals/
- **Scopus期刊列表**: https://www.scopus.com/sources

---

*本配置文件由 med-start-my-day v1.1.0 提供*
*最后更新：2026-03-14*
