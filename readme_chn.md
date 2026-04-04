# literature-to-protocols

面向化学实验文献的 **Literature-to-Protocols** 工具仓库。
本项目结合**知识图谱（KG）**与**大语言模型（LLM）**，从论文中提取实验相关信息，并生成结构化、可审阅、可追溯的实验 protocol 模板，用于实验设计参考、结果整理，以及后续向实验室平台代码转换的探索。


---

## 项目简介

科学文献中的实验流程通常以自由文本形式分散在论文中，不便于复现、比较和自动化执行。
本项目的目标是：

* 从论文中抽取实验相关实体、条件、操作和关系
* 构建论文级知识图谱
* 结合模板化提示词与图谱检索生成结构化 protocol
* 对生成结果进行事实性、文本质量和问卷式实用性评估

从论文定位上看，本项目生成的是一种**适合人工审阅和下游转换的 protocol 中间表示**，而不是面向某个具体机器人平台的最终执行语言。

---

## 项目特点

* **知识图谱驱动**：将论文中的实验信息组织为结构化图谱，便于检索与追溯
* **LLM 协同生成**：结合模板提示词与图谱问答生成结构化实验 protocol
* **面向论文实验流程**：适合化学/材料方向实验文献解析
* **支持案例分析**：仓库中包含生成样例、top-k 检索差异、实体差异讨论等内容
* **支持后续转换探索**：提供 protocol 到实验室平台代码的示例

---

## 仓库中哪些内容能直接运行

当前仓库的**主流程入口**是：

* `graph_search.py`：项目主程序入口
* `graph_utils/`：知识图谱构建、检索与生成的核心代码
* `graph_utils/chatgpt/config/config.yaml`：模型/API/代理等参数配置
* `graph_utils/chatgpt/config/prompts_config.json`：提示词配置文件
* `template/FT/ft.md`：FT 场景模板
* `origin_paper/more_paper/`：待解析论文目录
* `papersavings/`：生成结果输出目录

通常只需要完成环境配置、模型参数配置、Neo4j 启动和 PDF 解析服务启动后，运行：

```bash
python graph_search.py
```

即可开始主流程。

---

## 环境安装

### 1. 主代码环境

```bash
conda env create -f freeze.yml
conda activate ftpack
```

安装完成后，先修改模型配置文件：

```bash
vi graph_utils/chatgpt/config/config.yaml
```

需要填写你自己的：

* API Key
* base URL
* proxy（如需要）

---

### 2. Neo4j 知识图谱数据库

项目使用 Neo4j 进行知识图谱存储与检索。
请先安装并启动 Neo4j（推荐 5.10+）。

然后修改数据库连接参数。当前仓库中可参考：

```python
# 路径示例：graph_utils/graph_generate_bak.py
os.environ["NEO4J_USERNAME"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
```

请替换成你自己的用户名和密码。

---

### 3. PDF 文献解析服务

项目依赖 `marker_server` 进行 PDF 文献解析。

```bash
conda create -n marker python=3.10.0
conda activate marker

pip install marker-pdf
pip install -U uvicorn fastapi python-multipart
```

启动解析服务：

```bash
marker_server --port 2675
```

启动后可通过本地接口访问。

---

## 快速开始

### 第一步：准备论文

将待处理论文放入：

```bash
origin_paper/more_paper/
```

---

### 第二步：启动 PDF 解析服务

```bash
marker_server --port 2675
```

---

### 第三步：运行主程序

```bash
python graph_search.py
```

---

### 输出结果

生成结果默认保存在：

```bash
papersavings/
```

这里保存的是模型生成的 protocol 模板结果。

---

## 目录说明

### 主流程相关

#### `graph_search.py`

项目主入口。
负责组织论文解析、知识图谱检索、分章节生成与结果保存。

#### `graph_utils/`

核心代码目录，包含知识图谱构建、文件加载、样例加载、审阅等模块，例如：

* `graph_generate_bak.py`
* `graph_generate_optimized.py`
* `load_example.py`
* `load_files.py`
* `review.py`

#### `graph_utils/chatgpt/config/config.yaml`

运行参数配置文件，包括 API、base URL、proxy 等模型调用相关参数。

#### `graph_utils/chatgpt/config/prompts_config.json`

主提示词配置文件。
问题分解、章节生成、内容过滤、目录生成等 prompt 都集中维护在这里。

#### `change_prompt.py`

用于批量替换提示词的辅助脚本。
如果你需要替换模板、切换主题或统一修改 prompt，可以从这里入手。

---

### 模板与评测相关

#### `template/`

费托合成（FT）场景下的模板目录。

其中主要包括：

* `template/ft.md`：FT 场景下使用的模板，也是我们的 **L2 提示词模板**
* `template/all_paper_en.md`：论文中问卷式评测的重要提示词文件之一

#### `evaluation` 相关说明

`evaluation` 中的内容主要用于展示：

* 评测提示词设计
* 评价问题构成
* 评测代码逻辑
* 论文中评估思路的实现方式

需要注意的是：
由于仓库中**没有提供可直接对齐运行的全部 baseline 及完整评测配套环境**，因此这里的 evaluation code **不能直接当作一个完整开箱即用的 baseline 对比评测系统**。更适合用于阅读提示词和理解代码逻辑。

---

### 数据与样例相关

#### `origin_paper/`

原始论文输入目录。
主流程会从这里读取论文内容并进行解析。

#### `origin_paper/more_paper/`

待处理论文存放目录。

#### `papersavings/`

我们方法生成的 protocol 模板输出目录。
仓库中已经包含一系列 `Paper_*.md` 文件，可作为生成结果示例。

#### `originpaper`

从原始论文中提取和整理得到的原型内容，用于和最终生成模板进行对照理解。

#### `example`

一系列对比例子，用来展示不同生成方式、不同组织方式之间的差异。

#### `entities_discussion`

用于讨论不同方法生成实体时的差别，重点关注实体提取结果，而不是完整主流程运行。

#### `papersavings-topk`

论文中的一个检索设置分析目录。
主要展示在**不同 Top-K 检索参数**下，最终生成模板的差异。

#### `protocols2commands`

这是一个将生成的 protocol 转换为实验室平台代码的示例。
由于该方向目前还不够成熟，且实验室平台本身是中文环境，因此这一部分当前**全部为中文内容**，更适合作为概念验证示例。

---

## 提示词与模板

本项目的生成过程高度依赖模板与提示词设计。

### 核心提示词配置

```bash
graph_utils/chatgpt/config/prompts_config.json
```

### FT 模板

```bash
template/ft.md
```

### 评测问卷提示词

```bash
template/all_paper_en.md
```

### 批量替换提示词

```bash
python change_prompt.py
```

---

## 模型配置说明

如果你需要更换使用的 LLM，可以重点关注图谱生成、推理和轻量调用相关配置。
例如当前项目中常见的分工包括：

* 主生成模型：用于 protocol 章节生成与整合
* 推理模型：用于问题分解、复杂检索推理
* 轻量模型：用于部分抽取、筛选和辅助任务

具体参数配置请以代码与 `config.yaml` 为准。

---

## 使用建议

首次运行前建议检查：

1. Neo4j 服务是否已启动
2. `config.yaml` 中 API 配置是否正确
3. `marker_server` 是否已启动
4. 待解析论文是否已放入 `origin_paper/more_paper/`

如果 PDF 解析失败，可以尝试升级：

```bash
pip install marker-pdf --upgrade
```

如果需要代理访问模型服务，可在 `config.yaml` 中配置 `proxy`。

---

## 项目定位与限制

这个仓库更适合被理解为一个**研究型方法仓库**，而不是完整工业级产品。

### 当前适合做的事

* 从化学/材料论文中抽取实验流程信息
* 构建论文级知识图谱
* 生成结构化实验 protocol 模板
* 分析不同 prompt / 检索设置对生成效果的影响
* 研究 protocol 到实验平台代码转换的可能路径

---

## 建议阅读顺序

如果你想从论文和代码对应关系来理解这个仓库，建议按下面顺序阅读：

1. `readme.md`
2. `graph_search.py`
3. `graph_utils/`
4. `template/ft.md`
5. `template/all_paper_en.md`
6. `change_prompt.py`
7. `papersavings/` 中的输出样例
8. `example`、`entities_discussion`、`papersavings-topk`、`protocols2commands`

---

## 引用

如果你使用了本仓库中的代码、模板或提示词设计，请引用对应论文与仓库。

