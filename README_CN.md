# EndNote RIS 生成工具

一款强大的 AI 驱动工具，可从各种文档格式和目录结构生成 EndNote 和 Zotero 兼容的 RIS 文件。本工具远不止简单的元数据提取 - 它是文献管理、文档恢复和智能组织的综合解决方案。

## 本工具能做什么？

### 📂 通用文档处理
- **多格式支持**：处理 PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xls/.xlsx）和文本文件
- **灵活的输入结构**：
  - 从损坏的 EndNote 库中恢复记录（基于文件夹的导出）
  - 处理混合文档类型的扁平目录
  - 处理复杂的嵌套文件夹结构
  - 自动检测和处理根目录文件及文件夹

### 🔄 EndNote 库恢复
- **拯救损坏的库**：从损坏的 EndNote 导出中提取和重建记录
- **保留附件**：自动识别并链接所有相关文件（PDF、补充材料、演示文稿）
- **维护关系**：保持主文献和补充材料的正确关联

### 🤖 AI 驱动的元数据提取
- **智能内容分析**：LLM 阅读并理解文档内容以提取准确的元数据
- **文档类型识别**：自动识别期刊文章、书籍、会议论文、报告、学位论文、网页和演示文稿
- **DOI 检测**：扫描文档以查找和验证 DOI
- **多语言支持**：处理中文、英文和其他语言的文档

### 🔍 高级 OCR 功能
- **双 OCR 模式**：
  - **视觉 LLM 模式**（推荐）：GPU 加速，使用 qwen-vl-max 等模型，每页 1-3 秒
  - **Tesseract 模式**：传统 OCR，用于离线处理
- **智能自动触发**：当文本提取内容不足时自动启用 OCR
- **扫描文档支持**：从基于图像的 PDF 和扫描论文中提取元数据

### 🗂️ 智能自动分类
- **用户自定义类别**：指定您自己的研究类别（如"基因组学"、"药物筛选"、"AI医学"）
- **灵活的类别数量**：选择生成多少个类别（5、10、20 或更多）
- **两阶段分类**：确保 80%+ 的分类准确率
  - 第一阶段：AI 分析您的文献集并生成类别定义
  - 第二阶段：批量将文档分配到适当的类别
- **合并 RIS 输出**：每个类别一个 RIS 文件，便于批量导入
- **Smart Group 就绪**：包含关键词，可自动创建 EndNote Smart Group

### 🔗 智能补充材料检测与合并
- **自动补充材料识别**：
  - 文件名模式识别（-SE、-SM、-SI、-supplement、-supplementary）
  - 内容分析（标题、摘要包含补充材料关键词）
- **智能匹配**：AI 根据以下因素将补充材料匹配到主文献：
  - 标题相似度和作者重叠
  - 发表年份和内容关系
  - 置信度评分（高/中/低）
- **自动合并**：补充材料成为主文献的附件，消除重复记录
- **清洁的库**：不再有独立的补充材料条目混乱您的 EndNote 库

### 📎 智能附件管理
- **自动检测**：识别与每条记录相关的所有文件
- **绝对路径链接**：使用 `file:///` URL 实现可靠的附件访问
- **多文件支持**：链接 PDF、Word 文档、PowerPoint 演示文稿和其他格式
- **补充材料处理**：正确关联补充材料与主文献

### ⚡ 高性能处理
- **并发处理**：多线程支持（云 API 默认 10 个 worker）
- **断点续传**：状态管理允许失败重试和跳过已处理记录
- **批量处理**：高效处理数千篇文档
- **进度跟踪**：实时状态更新和详细日志记录

### 🎯 跨平台兼容性
- **EndNote 集成**：生成与所有 EndNote 版本兼容的标准 RIS 格式
- **Zotero 支持**：RIS 文件与 Zotero 无缝配合
- **通用格式**：与任何支持 RIS 格式的参考文献管理器兼容

## 主要特性

### 📚 智能元数据提取
- **多文件类型支持**：PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、Excel（.xls/.xlsx）、文本文件
- **智能主文件选择**：自动识别文件夹中的主要文献（vs 补充材料）
- **DOI 检测**：扫描 PDF 前 N 页查找 DOI，优先选择包含 DOI 的文件
- **文档类型识别**：LLM 自动识别文档类型（期刊文章、书籍、网页、报告等）
- **LLM 驱动**：使用大语言模型提取标题、作者、期刊、年份、摘要等元数据

### 🔍 OCR 支持
- **双模式 OCR**：
  - **Vision 模式**（推荐）：使用视觉大模型（如 qwen-vl-max），GPU 加速，1-3秒/页
  - **Tesseract 模式**：传统 OCR，CPU 处理，10-30秒/页
- **灵活配置**：OCR 可使用与主 LLM 相同或不同的提供商/模型
- **自动触发**：当 PDF 文本提取过少时自动启用 OCR

### 🗂️ 智能自动分类
- **两阶段分类**：确保至少 80% 的文献被正确分类
  - 第一阶段：LLM 生成类别定义
  - 第二阶段：批量分配文献到类别
- **用户指定类别**：可预定义已知类别（如"基因组学"、"药物筛选"、"AI生物医学"）
- **合并 RIS 文件**：每个类别生成一个 RIS 文件，包含该类别所有文献
- **便捷导入**：
  - 一次性导入所有 RIS 文件到 EndNote
  - 使用 Smart Groups 自动分组（基于关键词）
  - 附件使用绝对路径，确保正确链接

### 🔗 智能补充材料合并
- **双重检测机制**：
  - **文件名模式识别**：自动识别 -SE、-SM、-SI、-supplement、-supplementary 等后缀
  - **内容分析识别**：LLM 分析标题、摘要内容，识别补充材料关键词和关系
- **智能匹配**：LLM 根据标题相似度、作者重叠、年份、内容关系匹配补充材料到主文献
- **自动合并**：
  - 将补充材料作为附件添加到主文献
  - 更新主文献的 RIS 文件
  - 删除独立的补充材料 RIS 记录
- **减少重复**：避免补充材料作为独立记录出现在 EndNote 中

### ⚡ 高性能处理
- **并发处理**：支持多线程处理（云 API 默认 10 workers）
- **断点续传**：状态管理支持失败重试和跳过已处理记录
- **批量处理**：适合处理数千篇文献

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

**必需依赖**：
- PyMuPDF (PDF 处理)
- python-docx (Word 文档)
- python-pptx (PowerPoint)
- openai + httpx (LLM API)
- requests (HTTP 客户端)
- Pillow (图像处理)

**可选依赖**：
- OCR (Tesseract)：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- 旧版 Office 转换：`sudo apt install libreoffice` 或 `brew install libreoffice`
- Ollama（本地 LLM）：从 [ollama.com](https://ollama.com) 下载
- pywin32（EndNote COM 自动导入）：`pip install pywin32`

### 基础用法

```bash
# 使用默认配置（需要 .env 文件）
python endnote_cli.py create --enable_ocr --ocr_lang eng+chi_sim

# 指定 PDF 目录和输出目录
python endnote_cli.py create \
  --root_dir "./pdf" \
  --out_dir "./output" \
  --enable_ocr \
  --ocr_lang eng+chi_sim
```

### 使用阿里云 API（推荐）

## 使用.env
```bash
python endnote_cli.py create --dotenv .env2.txt --enable_ocr --ocr_lang eng+chi_sim \
  --max_workers 10 \
  --merge_supplements \
  --auto_classify \
  --num_categories 12 \
  --predefined_categories "multiple-omics,High-Altitude-Adaptation,Echolocation,Genetic-Evolution,large-models,drug-screening,virtual-cell,WORD,PPT,others"
```

```bash
python endnote_cli.py create \
  --provider openai_sdk \
  --base_url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus \
  --api_key_env LLM_API_KEY \
  --enable_ocr \
  --ocr_method vision \
  --ocr_model qwen-vl-max \
  --max_workers 10
```

### 使用 Ollama（本地 GPU）

```bash
# 推荐配置：RTX 3080 10GB
python endnote_cli.py create \
  --provider ollama_native \
  --base_url http://localhost:11434 \
  --model "qwen2.5:7b" \
  --enable_ocr \
  --ocr_method vision \
  --ocr_provider ollama_native \
  --ocr_model qwen2-vl:7b
```

### 自动分类

```bash
# 基础分类：自动生成 5 个类别
python endnote_cli.py create \
  --enable_ocr \
  --auto_classify \
  --num_categories 5

# 高级分类：指定已知类别
python endnote_cli.py create \
  --enable_ocr \
  --auto_classify \
  --num_categories 10 \
  --predefined_categories "基因组学,AI生物医学,药物筛选,多组学,演示文稿"
```

### 补充材料智能合并

```bash
# 启用补充材料检测和合并
python endnote_cli.py create \
  --enable_ocr \
  --merge_supplements

# 与自动分类一起使用（推荐）
python endnote_cli.py create \
  --enable_ocr \
  --merge_supplements \
  --auto_classify \
  --num_categories 5
```

**补充材料检测示例**：
- 文件名模式：`paper-SE.pdf`, `study-SM.pdf`, `data-SI.pdf`, `results-supplement.pdf`
- 内容模式：标题包含"Supplementary Information"、"Supporting Data"等
- 自动匹配：根据作者、标题相似度、年份匹配到主文献
- 合并结果：补充材料作为附件添加到主文献，不再作为独立记录

**分类输出示例**：
```
output/out_ris_class/
├── Genomics_and_Transcriptomics.ris    # 55篇
├── AI_in_Biomedicine.ris               # 52篇
├── Drug_Discovery.ris                  # 21篇
├── Multiomics_and_Disease.ris          # 22篇
├── Presentation_Slides.ris             # 4篇
├── Uncategorized.ris                   # 15篇
├── classification_report.json          # 分类报告
├── IMPORT_INSTRUCTIONS.txt             # 导入说明
└── EndNote_Import_Guide.txt            # 详细导入指南
```

## 配置文件

创建 `.env` 文件配置默认参数：

```ini
# LLM 配置（用于元数据提取）
LLM_API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-plus
PROVIDER=openai_sdk

# OCR 配置（使用阿里云视觉模型）
OCR_METHOD=vision
OCR_PROVIDER=openai_sdk
OCR_MODEL=qwen-vl-max
OCR_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OCR_API_KEY_ENV=LLM_API_KEY

# 路径配置
ROOT_DIR=./pdf
OUT_DIR=./output
```

## 目录结构

### 输入结构

支持三种目录结构：

**1. 文件夹记录（EndNote 导出结构）**
```
pdf/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── folder2/
│   └── presentation.pptx
└── folder3/
    └── document.docx
```
结果：3 条记录（每个文件夹一条）

**2. 混合结构（文件夹 + 根目录文件）**
```
pdf/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── paper2.pdf
├── presentation.pptx
└── notes.docx
```
结果：4 条记录（1 个文件夹 + 3 个根文件）

**3. 扁平结构（仅文件）**
```
pdf/
├── paper1.pdf
├── paper2.pdf
├── presentation.pptx
├── document.docx
└── data.xlsx
```
结果：5 条记录（所有根文件）

### 输出结构

```
output/
├── out_ris/              # 最终 RIS 文件（每条记录一个）
│   ├── paper1_abc123.ris
│   ├── paper2_def456.ris
│   └── ...
├── out_ris_class/        # 分类后的合并 RIS 文件（每个类别一个）
│   ├── Genomics.ris
│   ├── AI_Biomedicine.ris
│   ├── classification_report.json
│   ├── IMPORT_INSTRUCTIONS.txt
│   └── EndNote_Import_Guide.txt
├── pdf/                  # 所有附件（复制到此处，使用绝对路径）
│   ├── paper1.pdf
│   ├── paper2.pdf
│   └── ...
├── out_intermediate/     # 中间 JSON 元数据（调试用）
│   └── paper1_abc123.json
├── logs/                 # 应用日志和原始 LLM 响应
└── state.jsonl          # 处理状态（ok/fail）
```

## 命令行参数

### 基础参数
- `--root_dir`：PDF 根目录（默认从 .env 读取 ROOT_DIR）
- `--out_dir`：输出目录（默认：`./output`）
- `--dotenv`：.env 文件路径（默认：`./.env`）

### LLM 配置
- `--provider`：LLM 提供商（`ollama_native` 或 `openai_sdk`）
- `--model`：模型名称（如 `qwen-plus`、`gpt-4`）
- `--base_url`：API 基础 URL
- `--api_key_env`：API 密钥环境变量名（默认：`LLM_API_KEY`）
- `--timeout`：HTTP 超时（秒，默认：600）
- `--num_ctx`：上下文窗口大小（默认：16384）

### OCR 配置
- `--enable_ocr`：启用 OCR
- `--ocr_method`：OCR 方法（`vision` 或 `tesseract`）
- `--ocr_provider`：OCR 提供商（vision 模式，默认使用主 LLM 提供商）
- `--ocr_model`：OCR 模型名称（vision 模式，如 `qwen-vl-max`）
- `--ocr_base_url`：OCR API URL（vision 模式）
- `--ocr_api_key_env`：OCR API 密钥环境变量名
- `--ocr_lang`：OCR 语言（tesseract 模式，如 `eng+chi_sim`）
- `--ocr_force`：强制对所有 PDF 执行 OCR

### 处理控制
- `--max_records`：限制处理记录数（测试用，0=全部）
- `--max_workers`：并发 worker 数（0=自动检测：云 API 10，本地 GPU 1）
- `--only_failed`：仅重试失败记录
- `--skip_ok`：跳过已成功记录（默认：True）
- `--max_pages`：PDF 提取最大页数（默认：20）
- `--scan_doi_pages`：DOI 扫描页数（默认：20）

### 自动分类
- `--auto_classify`：启用自动分类
- `--num_categories`：目标类别数（默认：20）
- `--predefined_categories`：用户指定类别（逗号分隔）

### 补充材料合并
- `--merge_supplements`：启用补充材料智能检测和合并

## 工作原理

### 处理流程

1. **记录扫描**：发现目录结构下的记录（文件夹或文件）
2. **主文件选择**：智能选择主要文件
   - 扫描所有 PDF 检测 DOI
   - 如有多个 DOI PDF，LLM 选择主文献（vs 补充材料）
   - 回退：文件名启发式 + 文件大小
3. **文本提取**：从主文件提取文本
   - PDF：前 N 页文本
   - Word：文档属性 + 前 200 段落
   - PowerPoint：前 20 张幻灯片内容
   - Excel/TXT：直接读取
4. **OCR 处理**（可选）：如文本过少，触发 OCR
5. **元数据提取**：LLM 从文本提取书目信息
   - 标题、作者、年份、期刊、DOI、摘要
   - **文档类型识别**：JOUR（期刊）、BOOK（书籍）、WEB（网页）、RPRT（报告）等
6. **RIS 导出**：生成 RIS 文件
   - 主文件 + 所有附件
   - 附件使用绝对路径（`file:///C:/path/to/file.pdf`）
7. **补充材料合并**（可选）：智能检测和合并补充材料
   - 基于文件名和内容识别补充材料
   - LLM 匹配补充材料到主文献
   - 自动合并为附件，删除重复记录
8. **自动分类**（可选）：将文献分类并合并 RIS 文件
   - 每个 RIS 记录添加 `Category: XXX` 关键词
   - 生成导入指南

### 文档类型识别

LLM 会根据内容自动识别文档类型：

| 类型 | RIS 代码 | 识别特征 |
|------|---------|---------|
| 期刊文章 | JOUR | 有期刊名、卷号、期号、DOI、摘要 |
| 书籍 | BOOK | 书名、出版社、ISBN、章节 |
| 书籍章节 | CHAP | 有书名和章节标题 |
| 会议论文 | CONF | 会议论文集 |
| 报告 | RPRT | 技术报告、白皮书 |
| 学位论文 | THES | 硕士或博士论文 |
| 网页 | WEB | 有 URL，无期刊/出版社 |
| 通用 | GEN | 演示文稿、笔记等 |

### 主文件选择策略

**多文件文件夹的关键逻辑**：

1. **DOI 检测阶段**：扫描每个 PDF 的前 N 页（默认 20 页）
2. **LLM 选择**（多个 DOI PDF）：
   - 提取每个 DOI PDF 的前几页
   - LLM 根据内容选择"主文献"vs"补充材料"
3. **回退启发式**：
   - 检查文件名关键词（"supplement"、"supporting"、"SI" 等）
   - 优先选择非补充材料和较大文件

### 自动分类策略

**两阶段方法确保 80%+ 分类率**：

**第一阶段：类别生成**
- 从所有文档抽样最多 500 篇
- LLM 分析样本生成 N 个类别定义
- 包含用户指定类别（如果有）
- 类别设计为广泛且包容性强

**第二阶段：文档分配**
- 批量处理所有文档（每批 50 篇）
- LLM 将每篇文档分配到最佳类别
- 明确指示：至少 80% 必须分类（不是"其他"）
- 使用宽松匹配标准最大化分类率

### 补充材料合并策略

**双重检测机制**：

**1. 文件名模式检测**
识别以下文件名模式：
- `-SE`、`-SM`、`-SI`（常见补充材料后缀）
- `-supplement`、`-supplementary`、`-supporting`
- `-supp`、`-appendix`
- 包含 `supplement`、`supplementary`、`supporting` 等关键词

**2. 内容分析检测**
LLM 分析文档内容，识别：
- 标题中的补充材料关键词（"Supplementary Information"、"Supporting Data"等）
- 摘要中描述补充数据、额外材料的内容
- 与其他文档的引用关系

**3. 智能匹配**
LLM 根据以下因素匹配补充材料到主文献：
- **标题相似度**：补充材料通常引用或包含主文献标题
- **作者重叠**：相同的作者列表
- **发表年份**：相同年份
- **内容关系**：补充材料描述主文献的额外数据

**4. 置信度评估**
- **High**：标题、作者、年份完全匹配
- **Medium**：部分匹配（如作者重叠 + 年份相同）
- **Low**：仅弱关联（不会合并）

只有 high 和 medium 置信度的匹配会被执行。

## EndNote 导入指南

### 方法1：一次性导入所有文件（推荐）

1. **打开 EndNote**
2. **File → Import → File**
3. **按住 Ctrl 键**，选择 `out_ris_class/` 目录下的所有 .ris 文件
4. **Import Option**: 选择 "RefMan (RIS)"
5. **点击 Import**

✅ 所有文献会被导入，每篇都带有 `Category: XXX` 关键词

### 方法2：创建 Smart Groups 自动分组

导入后，为每个类别创建 Smart Group：

1. **Groups → Create Smart Group**
2. **名称**：输入类别名（如 `Genomics_and_Transcriptomics`）
3. **搜索条件**：
   - Field: **Keywords**
   - Condition: **Contains**
   - Value: `Category: Genomics_and_Transcriptomics`
4. **点击 Create**

重复以上步骤，为每个类别创建 Smart Group。

### 附件说明

- ✅ 附件使用绝对路径（`file:///C:/path/to/file.pdf`）
- ✅ EndNote 会自动识别并链接附件
- ⚠️ 不要移动 `output/pdf/` 目录，否则附件链接会失效

## 性能优化

### 并发处理

- **云 API**（`openai_sdk`）：默认 10 workers，可处理 10-50+ 并发请求
- **本地 GPU**（`ollama_native`）：默认 1 worker（VRAM 限制）

**性能对比**：
- 单线程：~1-2 条记录/分钟
- 10 workers（云）：~10-20 条记录/分钟（5-10倍加速）
- 20 workers（云）：~15-30 条记录/分钟（10-15倍加速）

### 推荐配置

**阿里云 API（高吞吐量）**：
```bash
python endnote_cli.py create \
  --provider openai_sdk \
  --base_url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus \
  --max_workers 10 \
  --enable_ocr \
  --ocr_method vision \
  --ocr_model qwen-vl-max
```

**RTX 3080 10GB（本地 GPU）**：
```bash
python endnote_cli.py create \
  --provider ollama_native \
  --model qwen2.5:7b \
  --max_workers 1 \
  --enable_ocr \
  --ocr_method vision \
  --ocr_model qwen2-vl:7b
```

## 故障排除

### 常见问题

**1. JSON 解析错误**
- 工具包含强大的 JSON 修复逻辑（3 次重试）
- 原始 LLM 响应记录在 `logs/openai_raw_*.txt`
- 检查日志了解详情

**2. OCR 失败**
- Vision 模式：确保 API 可用且模型支持
- Tesseract 模式：确保已安装 tesseract-ocr
- 检查日志中的 OCR 相关信息

**3. 分类率低于 80%**
- 增加 `--num_categories` 使类别更广泛
- 使用 `--predefined_categories` 指定已知类别
- 检查 `classification_report.json` 了解详情

**4. 内存不足（本地 GPU）**
- 使用 `--max_workers 1` 单线程模式
- 使用较小模型（如 `qwen2.5:3b`）
- 减少 `--num_ctx`（默认 16384）

**5. Word/PowerPoint 提取失败**
- 确保已安装：`pip install python-docx python-pptx`
- 旧格式（.doc/.ppt）需要 LibreOffice 转换

**6. EndNote COM 自动导入失败**
- 确保已安装：`pip install pywin32`
- EndNote 需要支持 COM 接口
- 回退到手动导入方法（见导入指南）

## 依赖项

### Python 包（必需）
```bash
PyMuPDF>=1.23.0              # PDF 文本提取
python-docx>=1.0.0           # Word 文档
python-pptx>=0.6.21          # PowerPoint
openai>=1.0.0                # OpenAI SDK
httpx>=0.24.0                # HTTP 客户端
requests>=2.31.0             # HTTP 客户端
Pillow>=10.0.0               # 图像处理
```

### Python 包（可选）
```bash
pywin32>=306                 # EndNote COM 自动导入
ocrmypdf>=14.0.0            # Tesseract OCR
pytesseract>=0.3.10         # Tesseract 包装器
```

### 外部工具（可选）
- **Tesseract OCR**：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- **LibreOffice**：`sudo apt install libreoffice` 或 `brew install libreoffice`
- **Ollama**：从 [ollama.com](https://ollama.com) 下载

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

本工具使用大语言模型技术，支持多种 LLM 提供商（OpenAI、阿里云、Ollama 等）。
