# EndNote RIS Generator

[English](README_EN.md) | [中文](README_CN.md)

---

A powerful, AI-driven tool for generating EndNote and Zotero-compatible RIS files from various document formats and directory structures. This tool goes far beyond simple metadata extraction - it's a comprehensive solution for literature management, document recovery, and intelligent organization.

## What Can This Tool Do?

### 📂 Universal Document Processing
- **Multi-Format Support**: Process PDF, Word (.doc/.docx), PowerPoint (.ppt/.pptx), Excel (.xls/.xlsx), and text files
- **Flexible Input Structures**:
  - Recover records from corrupted EndNote libraries (folder-based exports)
  - Process flat directories of mixed document types
  - Handle complex nested folder structures
  - Automatically detect and process root-level files alongside folders

### 🔄 EndNote Library Recovery
- **Rescue Corrupted Libraries**: Extract and rebuild records from damaged EndNote exports
- **Preserve Attachments**: Automatically identify and link all associated files (PDFs, supplements, presentations)
- **Maintain Relationships**: Keep main papers and supplementary materials properly connected

### 🤖 AI-Powered Metadata Extraction
- **Intelligent Content Analysis**: LLM reads and understands document content to extract accurate metadata
- **Document Type Recognition**: Automatically identifies journal articles, books, conference papers, reports, theses, web pages, and presentations
- **DOI Detection**: Scans documents to find and validate DOIs
- **Multi-Language Support**: Handles documents in English, Chinese, and other languages

### 🔍 Advanced OCR Capabilities
- **Dual OCR Modes**:
  - **Vision LLM Mode** (Recommended): GPU-accelerated, 1-3 seconds per page using models like qwen-vl-max
  - **Tesseract Mode**: Traditional OCR for offline processing
- **Smart Auto-Trigger**: Automatically enables OCR when text extraction yields insufficient content
- **Scanned Document Support**: Extract metadata from image-based PDFs and scanned papers

### 🗂️ Intelligent Auto-Classification
- **User-Defined Categories**: Specify your own research categories (e.g., "Genomics", "Drug Discovery", "AI in Medicine")
- **Flexible Category Count**: Choose how many categories to generate (5, 10, 20, or more)
- **Two-Stage Classification**: Ensures 80%+ classification accuracy
  - Stage 1: AI analyzes your collection and generates category definitions
  - Stage 2: Batch assigns documents to appropriate categories
- **Merged RIS Output**: One RIS file per category for easy batch import
- **Smart Group Ready**: Includes keywords for automatic EndNote Smart Group creation

### 🔗 Smart Supplement Detection & Merging
- **Automatic Supplement Identification**:
  - Filename pattern recognition (-SE, -SM, -SI, -supplement, -supplementary)
  - Content analysis (titles, abstracts containing supplement keywords)
- **Intelligent Matching**: AI matches supplements to main papers based on:
  - Title similarity and author overlap
  - Publication year and content relationships
  - Confidence scoring (high/medium/low)
- **Automatic Merging**: Supplements become attachments to main papers, eliminating duplicate records
- **Clean Library**: No more standalone supplement entries cluttering your EndNote library

### 📎 Smart Attachment Management
- **Automatic Detection**: Identifies all files associated with each record
- **Absolute Path Linking**: Uses `file:///` URLs for reliable attachment access
- **Multi-File Support**: Links PDFs, Word docs, PowerPoint presentations, and other formats
- **Supplement Handling**: Properly associates supplementary materials with main papers

### ⚡ High-Performance Processing
- **Concurrent Processing**: Multi-threaded support (default 10 workers for cloud APIs)
- **Resume Capability**: State management allows retry on failure and skip already-processed records
- **Batch Processing**: Efficiently handle thousands of documents
- **Progress Tracking**: Real-time status updates and detailed logging

### 🎯 Cross-Platform Compatibility
- **EndNote Integration**: Generate standard RIS format compatible with all EndNote versions
- **Zotero Support**: RIS files work seamlessly with Zotero
- **Universal Format**: Compatible with any reference manager supporting RIS format

## Key Features

### 📚 Intelligent Metadata Extraction
- **Multi-format Support**: PDF, Word (.doc/.docx), PowerPoint (.ppt/.pptx), Excel (.xls/.xlsx), text files
- **Smart Primary File Selection**: Automatically identifies main papers (vs supplements)
- **DOI Detection**: Scans first N pages of PDFs to find DOI, prioritizes files with DOI
- **Document Type Recognition**: LLM automatically identifies document types (journal articles, books, web pages, reports, etc.)
- **LLM-Powered**: Uses large language models to extract title, authors, journal, year, abstract, etc.

### 🔍 OCR Support
- **Dual OCR Modes**:
  - **Vision Mode** (Recommended): Uses vision LLMs (e.g., qwen-vl-max), GPU-accelerated, 1-3s/page
  - **Tesseract Mode**: Traditional OCR, CPU-based, 10-30s/page
- **Flexible Configuration**: OCR can use same or different provider/model from main LLM
- **Auto-trigger**: Automatically enables OCR when PDF text extraction yields too little

### 🗂️ Intelligent Auto-Classification
- **Two-Stage Classification**: Ensures at least 80% of documents are correctly classified
  - Stage 1: LLM generates category definitions
  - Stage 2: Batch assigns documents to categories
- **User-Specified Categories**: Pre-define known categories (e.g., "Genomics", "Drug Discovery", "AI Biomedicine")
- **Merged RIS Files**: One RIS file per category containing all documents in that category
- **Easy Import**:
  - Import all RIS files into EndNote at once
  - Use Smart Groups for automatic grouping (based on keywords)
  - Attachments use absolute paths for correct linking

### 🔗 Smart Supplement Merging
- **Dual Detection Mechanism**:
  - **Filename Pattern Recognition**: Automatically identifies suffixes like -SE, -SM, -SI, -supplement, -supplementary
  - **Content Analysis**: LLM analyzes titles, abstracts to identify supplement keywords and relationships
- **Intelligent Matching**: LLM matches supplements to main papers based on title similarity, author overlap, year, and content relationships
- **Automatic Merging**:
  - Adds supplements as attachments to main papers
  - Updates main paper RIS files
  - Removes standalone supplement RIS records
- **Reduces Duplication**: Prevents supplements from appearing as independent records in EndNote

### ⚡ High-Performance Processing
- **Concurrent Processing**: Multi-threaded support (cloud API default 10 workers)
- **Resume Capability**: State management supports retry on failure and skip processed records
- **Batch Processing**: Suitable for processing thousands of documents

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Dependencies**:
- PyMuPDF (PDF processing)
- python-docx (Word documents)
- python-pptx (PowerPoint)
- openai + httpx (LLM API)
- requests (HTTP client)
- Pillow (image processing)

**Optional Dependencies**:
- OCR (Tesseract): `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- Legacy Office Conversion: `sudo apt install libreoffice` or `brew install libreoffice`
- Ollama (Local LLM): Download from [ollama.com](https://ollama.com)
- pywin32 (EndNote COM auto-import): `pip install pywin32`

### Basic Usage

```bash
# Use default configuration (requires .env file)
python endnote_cli.py create --enable_ocr --ocr_lang eng+chi_sim

# Specify PDF directory and output directory
python endnote_cli.py create \
  --root_dir "./pdf" \
  --out_dir "./output" \
  --enable_ocr \
  --ocr_lang eng+chi_sim
```

### Using Alibaba Cloud API (Recommended)

#### use .env
python endnote_cli.py create --enable_ocr --ocr_lang eng+chi_sim --max_workers 10 --merge_supplements --auto_classify --num_categories 20 --predefined_categories "multiple-omics,High-Altitude-Adaptation,Echolocation,Genetic-Evolution,Genomics, Convergent-Evolution,large-models,WORD,PPT,others"

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

### Using Ollama (Local GPU)

```bash
# Recommended config: RTX 3080 10GB
python endnote_cli.py create \
  --provider ollama_native \
  --base_url http://localhost:11434 \
  --model "qwen2.5:7b" \
  --enable_ocr \
  --ocr_method vision \
  --ocr_provider ollama_native \
  --ocr_model qwen2-vl:7b
```

### Auto-Classification

```bash
# Basic classification: auto-generate 5 categories
python endnote_cli.py create \
  --enable_ocr \
  --auto_classify \
  --num_categories 5

# Advanced classification: specify known categories
python endnote_cli.py create \
  --enable_ocr \
  --auto_classify \
  --num_categories 10 \
  --predefined_categories "Genomics,AI Biomedicine,Drug Discovery,Multiomics,Presentations"
```

### Smart Supplement Merging

```bash
# Enable supplement detection and merging
python endnote_cli.py create \
  --enable_ocr \
  --merge_supplements

# Use with auto-classification (recommended)
python endnote_cli.py create \
  --enable_ocr \
  --merge_supplements \
  --auto_classify \
  --num_categories 5
```

**Supplement Detection Examples**:
- Filename patterns: `paper-SE.pdf`, `study-SM.pdf`, `data-SI.pdf`, `results-supplement.pdf`
- Content patterns: Titles containing "Supplementary Information", "Supporting Data", etc.
- Auto-matching: Based on authors, title similarity, year to match with main papers
- Merge result: Supplements added as attachments to main papers, no longer standalone records

**Classification Output Example**:
```
output/out_ris_class/
├── Genomics_and_Transcriptomics.ris    # 55 papers
├── AI_in_Biomedicine.ris               # 52 papers
├── Drug_Discovery.ris                  # 21 papers
├── Multiomics_and_Disease.ris          # 22 papers
├── Presentation_Slides.ris             # 4 papers
├── Uncategorized.ris                   # 15 papers
├── classification_report.json          # Classification report
├── IMPORT_INSTRUCTIONS.txt             # Import instructions
└── EndNote_Import_Guide.txt            # Detailed import guide
```

## Configuration File

Create a `.env` file to configure default parameters:

```ini
# LLM Configuration (for metadata extraction)
LLM_API_KEY=sk-your-api-key-here
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-plus
PROVIDER=openai_sdk

# OCR Configuration (using Alibaba Cloud vision model)
OCR_METHOD=vision
OCR_PROVIDER=openai_sdk
OCR_MODEL=qwen-vl-max
OCR_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OCR_API_KEY_ENV=LLM_API_KEY

# Path Configuration
ROOT_DIR=./pdf
OUT_DIR=./output
```

## Directory Structure

### Input Structure

Supports three directory structures:

**1. Folder Records (EndNote Export Structure)**
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
Result: 3 records (one per folder)

**2. Mixed Structure (Folders + Root Files)**
```
pdf/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── paper2.pdf
├── presentation.pptx
└── notes.docx
```
Result: 4 records (1 folder + 3 root files)

**3. Flat Structure (Files Only)**
```
pdf/
├── paper1.pdf
├── paper2.pdf
├── presentation.pptx
├── document.docx
└── data.xlsx
```
Result: 5 records (all root files)

### Output Structure

```
output/
├── out_ris/              # Final RIS files (one per record)
│   ├── paper1_abc123.ris
│   ├── paper2_def456.ris
│   └── ...
├── out_ris_class/        # Classified merged RIS files (one per category)
│   ├── Genomics.ris
│   ├── AI_Biomedicine.ris
│   ├── classification_report.json
│   ├── IMPORT_INSTRUCTIONS.txt
│   └── EndNote_Import_Guide.txt
├── pdf/                  # All attachments (copied here, using absolute paths)
│   ├── paper1.pdf
│   ├── paper2.pdf
│   └── ...
├── out_intermediate/     # Intermediate JSON metadata (for debugging)
│   └── paper1_abc123.json
├── logs/                 # Application logs and raw LLM responses
└── state.jsonl          # Processing state (ok/fail)
```

## Command-Line Arguments

### Basic Parameters
- `--root_dir`: PDF root directory (default: read ROOT_DIR from .env)
- `--out_dir`: Output directory (default: `./output`)
- `--dotenv`: .env file path (default: `./.env`)

### LLM Configuration
- `--provider`: LLM provider (`ollama_native` or `openai_sdk`)
- `--model`: Model name (e.g., `qwen-plus`, `gpt-4`)
- `--base_url`: API base URL
- `--api_key_env`: API key environment variable name (default: `LLM_API_KEY`)
- `--timeout`: HTTP timeout (seconds, default: 600)
- `--num_ctx`: Context window size (default: 16384)

### OCR Configuration
- `--enable_ocr`: Enable OCR
- `--ocr_method`: OCR method (`vision` or `tesseract`)
- `--ocr_provider`: OCR provider (vision mode, defaults to main LLM provider)
- `--ocr_model`: OCR model name (vision mode, e.g., `qwen-vl-max`)
- `--ocr_base_url`: OCR API URL (vision mode)
- `--ocr_api_key_env`: OCR API key environment variable name
- `--ocr_lang`: OCR language (tesseract mode, e.g., `eng+chi_sim`)
- `--ocr_force`: Force OCR on all PDFs

### Processing Control
- `--max_records`: Limit number of records to process (for testing, 0=all)
- `--max_workers`: Number of concurrent workers (0=auto-detect: cloud API 10, local GPU 1)
- `--only_failed`: Retry only failed records
- `--skip_ok`: Skip already successful records (default: True)
- `--max_pages`: Maximum pages to extract from PDF (default: 20)
- `--scan_doi_pages`: Pages to scan for DOI (default: 20)

### Auto-Classification
- `--auto_classify`: Enable auto-classification
- `--num_categories`: Target number of categories (default: 20)
- `--predefined_categories`: User-specified categories (comma-separated)

### Supplement Merging
- `--merge_supplements`: Enable intelligent supplement detection and merging

## How It Works

### Processing Pipeline

1. **Record Scanning**: Discover records in directory structure (folders or files)
2. **Primary File Selection**: Intelligently select main file
   - Scan all PDFs to detect DOI
   - If multiple DOI PDFs, LLM chooses main paper (vs supplements)
   - Fallback: filename heuristics + file size
3. **Text Extraction**: Extract text from primary file
   - PDF: First N pages of text
   - Word: Document properties + first 200 paragraphs
   - PowerPoint: First 20 slides content
   - Excel/TXT: Direct reading
4. **OCR Processing** (optional): Trigger OCR if text is too short
5. **Metadata Extraction**: LLM extracts bibliographic information from text
   - Title, authors, year, journal, DOI, abstract
   - **Document Type Recognition**: JOUR (journal), BOOK (book), WEB (web page), RPRT (report), etc.
6. **RIS Export**: Generate RIS file
   - Primary file + all attachments
   - Attachments use absolute paths (`file:///C:/path/to/file.pdf`)
7. **Supplement Merging** (optional): Intelligently detect and merge supplement materials
   - Identify supplements based on filename and content
   - LLM matches supplements to main papers
   - Automatically merge as attachments, remove duplicate records
8. **Auto-Classification** (optional): Classify documents and merge RIS files
   - Add `Category: XXX` keyword to each RIS record
   - Generate import guide

### Document Type Recognition

LLM automatically identifies document types based on content:

| Type | RIS Code | Recognition Features |
|------|----------|---------------------|
| Journal Article | JOUR | Has journal name, volume, issue, DOI, abstract |
| Book | BOOK | Book title, publisher, ISBN, chapters |
| Book Chapter | CHAP | Has book title and chapter title |
| Conference Paper | CONF | Conference proceedings |
| Report | RPRT | Technical report, white paper |
| Thesis | THES | Master's or doctoral thesis |
| Web Page | WEB | Has URL, no journal/publisher |
| Generic | GEN | Presentations, notes, etc. |

### Primary File Selection Strategy

**Key logic for multi-file folders**:

1. **DOI Detection Phase**: Scan first N pages of each PDF (default 20 pages)
2. **LLM Selection** (multiple DOI PDFs):
   - Extract first few pages from each DOI PDF
   - LLM chooses "main paper" vs "supplement" based on content
3. **Fallback Heuristics**:
   - Check filename keywords ("supplement", "supporting", "SI", etc.)
   - Prefer non-supplement and larger files

### Auto-Classification Strategy

**Two-stage approach ensures 80%+ classification rate**:

**Stage 1: Category Generation**
- Sample up to 500 documents from collection
- LLM analyzes sample and generates N category definitions
- Includes user-specified categories (if any)
- Categories designed to be broad and inclusive

**Stage 2: Document Assignment**
- Batch process all documents (50 per batch)
- LLM assigns each document to best matching category
- Explicit instruction: at least 80% must be classified (not "Other")
- Uses generous matching criteria to maximize classification rate

### Supplement Merging Strategy

**Dual Detection Mechanism**:

**1. Filename Pattern Detection**
Identifies the following filename patterns:
- `-SE`, `-SM`, `-SI` (common supplement suffixes)
- `-supplement`, `-supplementary`, `-supporting`
- `-supp`, `-appendix`
- Contains keywords like `supplement`, `supplementary`, `supporting`

**2. Content Analysis Detection**
LLM analyzes document content to identify:
- Supplement keywords in titles ("Supplementary Information", "Supporting Data", etc.)
- Content describing supplementary data, additional materials in abstracts
- Citation relationships with other documents

**3. Intelligent Matching**
LLM matches supplements to main papers based on:
- **Title Similarity**: Supplements often reference or include main paper titles
- **Author Overlap**: Same author list
- **Publication Year**: Same year
- **Content Relationship**: Supplements describe additional data from main papers

**4. Confidence Assessment**
- **High**: Title, authors, and year all match
- **Medium**: Partial match (e.g., author overlap + same year)
- **Low**: Only weak association (will not merge)

Only high and medium confidence matches are executed.

## EndNote Import Guide

### Method 1: Import All Files at Once (Recommended)

1. **Open EndNote**
2. **File → Import → File**
3. **Hold Ctrl key**, select all .ris files in `out_ris_class/` directory
4. **Import Option**: Select "RefMan (RIS)"
5. **Click Import**

✅ All documents will be imported with `Category: XXX` keywords

### Method 2: Create Smart Groups for Auto-Grouping

After import, create Smart Groups for each category:

1. **Groups → Create Smart Group**
2. **Name**: Enter category name (e.g., `Genomics_and_Transcriptomics`)
3. **Search Criteria**:
   - Field: **Keywords**
   - Condition: **Contains**
   - Value: `Category: Genomics_and_Transcriptomics`
4. **Click Create**

Repeat for each category.

### Attachment Notes

- ✅ Attachments use absolute paths (`file:///C:/path/to/file.pdf`)
- ✅ EndNote will automatically recognize and link attachments
- ⚠️ Do not move the `output/pdf/` directory, or attachment links will break

## Performance Optimization

### Concurrent Processing

- **Cloud API** (`openai_sdk`): Default 10 workers, can handle 10-50+ concurrent requests
- **Local GPU** (`ollama_native`): Default 1 worker (VRAM limitation)

**Performance Comparison**:
- Single-threaded: ~1-2 records/minute
- 10 workers (cloud): ~10-20 records/minute (5-10x speedup)
- 20 workers (cloud): ~15-30 records/minute (10-15x speedup)

### Recommended Configurations

**Alibaba Cloud API (High Throughput)**:
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

**RTX 3080 10GB (Local GPU)**:
```bash
python endnote_cli.py create \
  --provider ollama_native \
  --model qwen2.5:7b \
  --max_workers 1 \
  --enable_ocr \
  --ocr_method vision \
  --ocr_model qwen2-vl:7b
```

## Troubleshooting

### Common Issues

**1. JSON Parsing Errors**
- Tool includes robust JSON repair logic (3 retries)
- Raw LLM responses logged in `logs/openai_raw_*.txt`
- Check logs for details

**2. OCR Failures**
- Vision mode: Ensure API is available and model is supported
- Tesseract mode: Ensure tesseract-ocr is installed
- Check OCR-related information in logs

**3. Classification Rate Below 80%**
- Increase `--num_categories` to make categories broader
- Use `--predefined_categories` to specify known categories
- Check `classification_report.json` for details

**4. Out of Memory (Local GPU)**
- Use `--max_workers 1` for single-threaded mode
- Use smaller model (e.g., `qwen2.5:3b`)
- Reduce `--num_ctx` (default 16384)

**5. Word/PowerPoint Extraction Failures**
- Ensure installed: `pip install python-docx python-pptx`
- Legacy formats (.doc/.ppt) require LibreOffice conversion

**6. EndNote COM Auto-Import Failures**
- Ensure installed: `pip install pywin32`
- EndNote must support COM interface
- Fall back to manual import method (see import guide)

## Dependencies

### Python Packages (Required)
```bash
PyMuPDF>=1.23.0              # PDF text extraction
python-docx>=1.0.0           # Word documents
python-pptx>=0.6.21          # PowerPoint
openai>=1.0.0                # OpenAI SDK
httpx>=0.24.0                # HTTP client
requests>=2.31.0             # HTTP client
Pillow>=10.0.0               # Image processing
```

### Python Packages (Optional)
```bash
pywin32>=306                 # EndNote COM auto-import
ocrmypdf>=14.0.0            # Tesseract OCR
pytesseract>=0.3.10         # Tesseract wrapper
```

### External Tools (Optional)
- **Tesseract OCR**: `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- **LibreOffice**: `sudo apt install libreoffice` or `brew install libreoffice`
- **Ollama**: Download from [ollama.com](https://ollama.com)

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Acknowledgments

This tool uses Large Language Model technology and supports multiple LLM providers (OpenAI, Alibaba Cloud, Ollama, etc.).
