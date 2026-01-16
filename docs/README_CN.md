# Zotero 文献恢复工具

从 EndNote PDF 目录结构恢复 Zotero 文献库的智能工具。使用大语言模型（LLM）自动提取文献元数据，支持 OCR 识别扫描版 PDF，并提供智能分类功能。

## 主要特性

### 📚 智能元数据提取
- **多文件类型支持**：PDF、Word（.doc/.docx）、PowerPoint（.ppt/.pptx）、文本文件
- **智能主文件选择**：自动识别文件夹中的主要文献（vs 补充材料）
- **DOI 检测**：扫描 PDF 前 N 页查找 DOI，优先选择包含 DOI 的文件
- **LLM 驱动**：使用大语言模型提取标题、作者、期刊、年份、摘要等元数据

### 🔍 OCR 支持
- **双模式 OCR**：
  - **Vision 模式**（推荐）：使用视觉大模型（如 qwen2-vl:7b），GPU 加速，1-3秒/页
  - **Tesseract 模式**：传统 OCR，CPU 处理，10-30秒/页
- **灵活配置**：OCR 可使用与主 LLM 相同或不同的提供商/模型
- **自动触发**：当 PDF 文本提取过少时自动启用 OCR

### 🗂️ 智能自动分类
- **两阶段分类**：确保至少 80% 的文献被正确分类
  - 第一阶段：LLM 生成类别定义
  - 第二阶段：批量分配文献到类别
- **用户指定类别**：可预定义已知类别（如"非编码RNA"、"高原适应"、"回声定位"）
- **合并 RIS 文件**：每个类别生成一个 RIS 文件，包含该类别所有文献
- **便捷导入**：直接拖放 RIS 文件到 Zotero，无需逐个导入

### ⚡ 高性能处理
- **并发处理**：支持多线程处理（云 API 默认 10 workers）
- **断点续传**：状态管理支持失败重试和跳过已处理记录
- **批量处理**：适合处理数千篇文献

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

**可选依赖**：
- OCR (Tesseract)：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- 旧版 Office 转换：`sudo apt install libreoffice` 或 `brew install libreoffice`
- Ollama（本地 LLM）：从 [ollama.com](https://ollama.com) 下载

### 基础用法

```bash
# 使用默认配置（需要 .env 文件）
python zotero_restore_from_endnote_pdf_directories.py --enable_ocr

# 指定 PDF 目录和输出目录
python zotero_restore_from_endnote_pdf_directories.py \
  --root_dir "C:/Users/你的用户名/Desktop/PDF" \
  --out_dir "./outputs" \
  --enable_ocr
```

### 使用 Ollama（本地 GPU）

```bash
# 推荐配置：RTX 3080 10GB
python zotero_restore_from_endnote_pdf_directories.py \
  --provider ollama_native \
  --base_url http://localhost:11434 \
  --model "qwen2.5:7b" \
  --enable_ocr \
  --ocr_method vision \
  --ocr_provider ollama_native \
  --ocr_model qwen2-vl:7b
```

### 使用云 API（OpenAI 兼容）

```bash
python zotero_restore_from_endnote_pdf_directories.py \
  --provider openai_sdk \
  --base_url https://api.openai.com/v1 \
  --model gpt-4 \
  --api_key_env OPENAI_API_KEY \
  --max_workers 20 \
  --enable_ocr
```

### 自动分类

```bash
# 基础分类：自动生成 15 个类别
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify \
  --num_categories 15

# 高级分类：指定已知类别
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify \
  --num_categories 10 \
  --predefined_categories "多组学omic,遗传进化,药物筛选,虚拟细胞，综述，生物大模型"
```

**分类输出示例**：
```
outputs/out_ris_class/
├── Non-coding_RNA.ris              # 用户指定（50篇）
├── High_Altitude_Adaptation.ris    # 用户指定（30篇）
├── Echolocation.ris                # 用户指定（25篇）
├── Cancer_Genomics.ris             # 用户指定（80篇）
├── Genomics.ris                    # LLM 生成（200篇）
├── Evolution.ris                   # LLM 生成（150篇）
├── Neuroscience.ris                # LLM 生成（120篇）
├── Uncategorized.ris               # 未分类（<20%）
└── classification_report.json
```

## 配置文件

创建 `.env` 文件配置默认参数：

```ini
# LLM 配置
PROVIDER=openai_sdk
MODEL=gpt-4
BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here

# 目录配置
PDF_DIR=C:/Users/你的用户名/Desktop/PDF
OUT_DIR=./outputs

# OCR 配置（可选）
OCR_METHOD=vision
OCR_PROVIDER=ollama_native
OCR_MODEL=qwen2-vl:7b
OCR_BASE_URL=http://localhost:11434
```

## 目录结构

### 输入结构

支持三种 EndNote 导出结构：

**1. 文件夹记录（原始 EndNote 结构）**
```
PDF/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── folder2/
│   └── presentation.ppt
└── folder3/
    └── document.docx
```
结果：3 条记录（每个文件夹一条）

**2. 混合结构（文件夹 + 根目录文件）**
```
PDF/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── paper2.pdf
├── presentation.ppt
└── notes.docx
```
结果：4 条记录（1 个文件夹 + 3 个根文件）

**3. 扁平结构（仅文件）**
```
PDF/
├── paper1.pdf
├── paper2.pdf
├── presentation.ppt
└── notes.docx
```
结果：4 条记录（所有根文件）

### 输出结构

```
outputs/
├── out_ris/              # 最终 RIS 文件（每条记录一个）
├── out_ris_class/        # 分类后的合并 RIS 文件（每个类别一个）
├── out_intermediate/     # 中间 JSON 元数据（调试用）
│   └── ocr_pdfs/        # OCR 处理后的 PDF（如果启用）
├── logs/                 # 应用日志和原始 LLM 响应
└── state.jsonl          # 处理状态（ok/fail）
```

## 命令行参数

### 基础参数
- `--root_dir`：EndNote PDF 根目录
- `--out_dir`：输出目录（默认：`./outputs`）
- `--include_root_files`：包含根目录文件作为单独记录（默认：True）

### LLM 配置
- `--provider`：LLM 提供商（`ollama_native` 或 `openai_sdk`）
- `--model`：模型名称
- `--base_url`：API 基础 URL
- `--api_key_env`：API 密钥环境变量名
- `--timeout`：HTTP 超时（秒，默认：600）

### OCR 配置
- `--enable_ocr`：启用 OCR
- `--ocr_method`：OCR 方法（`vision` 或 `tesseract`）
- `--ocr_provider`：OCR 提供商（vision 模式）
- `--ocr_model`：OCR 模型名称（vision 模式）
- `--ocr_lang`：OCR 语言（tesseract 模式，如 `eng+chi_sim`）

### 处理控制
- `--max_records`：限制处理记录数（测试用，0=全部）
- `--max_workers`：并发 worker 数（0=自动检测）
- `--only_failed`：仅重试失败记录
- `--skip_ok`：跳过已成功记录（默认：True）

### 自动分类
- `--auto_classify`：启用自动分类
- `--num_categories`：目标类别数（默认：20）
- `--predefined_categories`：用户指定类别（逗号分隔）

## 工作原理

### 处理流程

1. **记录扫描**：发现 EndNote `PDF/XXX/*` 结构下的记录
2. **主文件选择**：智能选择主要文件
   - 扫描所有 PDF 检测 DOI
   - 如有多个 DOI PDF，LLM 选择主文献（vs 补充材料）
   - 回退：文件名启发式 + 文件大小
3. **文本提取**：从主文件提取文本（PDF 前 N 页）
4. **OCR 处理**（可选）：如文本过少，触发 OCR
5. **元数据提取**：LLM 从文本提取书目信息
6. **RIS 导出**：生成 RIS 文件（主文件 + 所有附件）
7. **自动分类**（可选）：将文献分类并合并 RIS 文件

### 主文件选择策略

**多 PDF 文件夹的关键逻辑**：

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

## 性能优化

### 并发处理

- **云 API**（`openai_sdk`）：默认 10 workers，可处理 10-50+ 并发请求
- **本地 GPU**（`ollama_native`）：默认 1 worker（VRAM 限制）

**性能对比**：
- 单线程：~1-2 条记录/分钟
- 10 workers（云）：~10-20 条记录/分钟（5-10倍加速）
- 20 workers（云）：~15-30 条记录/分钟（10-15倍加速）

### 推荐配置

**RTX 3080 10GB（本地 GPU）**：
```bash
--provider ollama_native \
--model qwen2.5:7b \
--max_workers 1 \
--enable_ocr \
--ocr_method vision \
--ocr_model qwen2-vl:7b
```

**云 API（高吞吐量）**：
```bash
--provider openai_sdk \
--model gpt-4 \
--max_workers 20 \
--enable_ocr
```

## 故障排除

### 常见问题

**1. JSON 解析错误**
- 工具包含强大的 JSON 修复逻辑
- 原始 LLM 响应记录在 `logs/openai_raw_*.txt`
- 检查日志了解详情

**2. OCR 失败**
- Vision 模式：确保 Ollama 正在运行且模型已下载
- Tesseract 模式：确保已安装 tesseract-ocr
- 检查 `out_intermediate/ocr_pdfs/` 中的 OCR 输出

**3. 分类率低于 80%**
- 增加 `--num_categories` 使类别更广泛
- 使用 `--predefined_categories` 指定已知类别
- 检查 `classification_report.json` 了解详情

**4. 内存不足（本地 GPU）**
- 使用 `--max_workers 1` 单线程模式
- 使用较小模型（如 `qwen2.5:3b`）
- 减少 `--num_ctx`（默认 16384）

## 依赖项

### Python 包
- `PyMuPDF` (fitz)：PDF 文本提取和页面渲染
- `python-docx`：Word 文件读取
- `python-pptx`：PowerPoint 文件读取
- `openai`：OpenAI SDK（API 调用）
- `httpx`：HTTP 客户端
- `requests`：HTTP 客户端（Ollama）
- `Pillow` (PIL)：图像处理（vision OCR）

### 外部工具（可选）
- `ocrmypdf`：Tesseract OCR 处理
- `LibreOffice` 或 `unoconv`：旧版 Office 格式转换（.doc, .ppt）
- `Ollama`：本地 LLM 和 vision 模型服务器

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

本工具使用大语言模型技术，支持多种 LLM 提供商（OpenAI、Ollama 等）。
