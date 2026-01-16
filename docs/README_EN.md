# Zotero Literature Recovery Tool

An intelligent tool to recover Zotero libraries from EndNote PDF directory structures. Uses Large Language Models (LLM) to automatically extract literature metadata, supports OCR for scanned PDFs, and provides intelligent classification features.

## Key Features

### 📚 Intelligent Metadata Extraction
- **Multi-format Support**: PDF, Word (.doc/.docx), PowerPoint (.ppt/.pptx), text files
- **Smart Primary File Selection**: Automatically identifies main papers (vs supplements)
- **DOI Detection**: Scans first N pages of PDFs to find DOI, prioritizes files with DOI
- **LLM-Powered**: Uses large language models to extract title, authors, journal, year, abstract, etc.

### 🔍 OCR Support
- **Dual OCR Modes**:
  - **Vision Mode** (Recommended): Uses vision LLMs (e.g., qwen2-vl:7b), GPU-accelerated, 1-3s/page
  - **Tesseract Mode**: Traditional OCR, CPU-based, 10-30s/page
- **Flexible Configuration**: OCR can use same or different provider/model from main LLM
- **Auto-trigger**: Automatically enables OCR when PDF text extraction yields too little

### 🗂️ Intelligent Auto-Classification
- **Two-Stage Classification**: Ensures at least 80% of documents are correctly classified
  - Stage 1: LLM generates category definitions
  - Stage 2: Batch assigns documents to categories
- **User-Specified Categories**: Pre-define known categories (e.g., "Non-coding RNA", "High Altitude Adaptation", "Echolocation")
- **Merged RIS Files**: One RIS file per category containing all documents in that category
- **Easy Import**: Drag-and-drop RIS files into Zotero, no need to import individually

### ⚡ High-Performance Processing
- **Concurrent Processing**: Multi-threaded support (cloud API default 10 workers)
- **Resume Capability**: State management supports retry on failure and skip processed records
- **Batch Processing**: Suitable for processing thousands of documents

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Optional Dependencies**:
- OCR (Tesseract): `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
- Legacy Office Conversion: `sudo apt install libreoffice` or `brew install libreoffice`
- Ollama (Local LLM): Download from [ollama.com](https://ollama.com)

### Basic Usage

```bash
# Use default configuration (requires .env file)
python zotero_restore_from_endnote_pdf_directories.py --enable_ocr

# Specify PDF directory and output directory
python zotero_restore_from_endnote_pdf_directories.py \
  --root_dir "C:/Users/YourUsername/Desktop/PDF" \
  --out_dir "./outputs" \
  --enable_ocr
```

### Using Ollama (Local GPU)

```bash
# Recommended config: RTX 3080 10GB
python zotero_restore_from_endnote_pdf_directories.py \
  --provider ollama_native \
  --base_url http://localhost:11434 \
  --model "qwen2.5:7b" \
  --enable_ocr \
  --ocr_method vision \
  --ocr_provider ollama_native \
  --ocr_model qwen2-vl:7b
```

### Using Cloud API (OpenAI-Compatible)

```bash
python zotero_restore_from_endnote_pdf_directories.py \
  --provider openai_sdk \
  --base_url https://api.openai.com/v1 \
  --model gpt-4 \
  --api_key_env OPENAI_API_KEY \
  --max_workers 20 \
  --enable_ocr
```

### Auto-Classification

```bash
# Basic classification: auto-generate 15 categories
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify \
  --num_categories 15

# Advanced classification: specify known categories
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify \
  --num_categories 15 \
  --predefined_categories "Non-coding RNA,High Altitude Adaptation,Echolocation,Cancer Genomics"
```

**Classification Output Example**:
```
outputs/out_ris_class/
├── Non-coding_RNA.ris              # User-specified (50 papers)
├── High_Altitude_Adaptation.ris    # User-specified (30 papers)
├── Echolocation.ris                # User-specified (25 papers)
├── Cancer_Genomics.ris             # User-specified (80 papers)
├── Genomics.ris                    # LLM-generated (200 papers)
├── Evolution.ris                   # LLM-generated (150 papers)
├── Neuroscience.ris                # LLM-generated (120 papers)
├── Uncategorized.ris               # Uncategorized (<20%)
└── classification_report.json
```

## Configuration File

Create a `.env` file to configure default parameters:

```ini
# LLM Configuration
PROVIDER=openai_sdk
MODEL=gpt-4
BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here

# Directory Configuration
PDF_DIR=C:/Users/YourUsername/Desktop/PDF
OUT_DIR=./outputs

# OCR Configuration (Optional)
OCR_METHOD=vision
OCR_PROVIDER=ollama_native
OCR_MODEL=qwen2-vl:7b
OCR_BASE_URL=http://localhost:11434
```

## Directory Structure

### Input Structure

Supports three EndNote export structures:

**1. Folder Records (Original EndNote Structure)**
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
Result: 3 records (one per folder)

**2. Mixed Structure (Folders + Root Files)**
```
PDF/
├── folder1/
│   ├── paper.pdf
│   └── supplement.pdf
├── paper2.pdf
├── presentation.ppt
└── notes.docx
```
Result: 4 records (1 folder + 3 root files)

**3. Flat Structure (Files Only)**
```
PDF/
├── paper1.pdf
├── paper2.pdf
├── presentation.ppt
└── notes.docx
```
Result: 4 records (all root files)

### Output Structure

```
outputs/
├── out_ris/              # Final RIS files (one per record)
├── out_ris_class/        # Classified merged RIS files (one per category)
├── out_intermediate/     # Intermediate JSON metadata (for debugging)
│   └── ocr_pdfs/        # OCR-processed PDFs (if enabled)
├── logs/                 # Application logs and raw LLM responses
└── state.jsonl          # Processing state (ok/fail)
```

## Command-Line Arguments

### Basic Parameters
- `--root_dir`: EndNote PDF root directory
- `--out_dir`: Output directory (default: `./outputs`)
- `--include_root_files`: Include root-level files as individual records (default: True)

### LLM Configuration
- `--provider`: LLM provider (`ollama_native` or `openai_sdk`)
- `--model`: Model name
- `--base_url`: API base URL
- `--api_key_env`: API key environment variable name
- `--timeout`: HTTP timeout (seconds, default: 600)

### OCR Configuration
- `--enable_ocr`: Enable OCR
- `--ocr_method`: OCR method (`vision` or `tesseract`)
- `--ocr_provider`: OCR provider (vision mode)
- `--ocr_model`: OCR model name (vision mode)
- `--ocr_lang`: OCR language (tesseract mode, e.g., `eng+chi_sim`)

### Processing Control
- `--max_records`: Limit number of records to process (for testing, 0=all)
- `--max_workers`: Number of concurrent workers (0=auto-detect)
- `--only_failed`: Retry only failed records
- `--skip_ok`: Skip already successful records (default: True)

### Auto-Classification
- `--auto_classify`: Enable auto-classification
- `--num_categories`: Target number of categories (default: 20)
- `--predefined_categories`: User-specified categories (comma-separated)

## How It Works

### Processing Pipeline

1. **Record Scanning**: Discover records under EndNote `PDF/XXX/*` structure
2. **Primary File Selection**: Intelligently select main file
   - Scan all PDFs to detect DOI
   - If multiple DOI PDFs, LLM chooses main paper (vs supplements)
   - Fallback: filename heuristics + file size
3. **Text Extraction**: Extract text from primary file (first N pages of PDF)
4. **OCR Processing** (optional): Trigger OCR if text is too short
5. **Metadata Extraction**: LLM extracts bibliographic information from text
6. **RIS Export**: Generate RIS file (primary file + all attachments)
7. **Auto-Classification** (optional): Classify documents and merge RIS files

### Primary File Selection Strategy

**Key logic for multi-PDF folders**:

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

## Performance Optimization

### Concurrent Processing

- **Cloud API** (`openai_sdk`): Default 10 workers, can handle 10-50+ concurrent requests
- **Local GPU** (`ollama_native`): Default 1 worker (VRAM limitation)

**Performance Comparison**:
- Single-threaded: ~1-2 records/minute
- 10 workers (cloud): ~10-20 records/minute (5-10x speedup)
- 20 workers (cloud): ~15-30 records/minute (10-15x speedup)

### Recommended Configurations

**RTX 3080 10GB (Local GPU)**:
```bash
--provider ollama_native \
--model qwen2.5:7b \
--max_workers 1 \
--enable_ocr \
--ocr_method vision \
--ocr_model qwen2-vl:7b
```

**Cloud API (High Throughput)**:
```bash
--provider openai_sdk \
--model gpt-4 \
--max_workers 20 \
--enable_ocr
```

## Troubleshooting

### Common Issues

**1. JSON Parsing Errors**
- Tool includes robust JSON repair logic
- Raw LLM responses logged in `logs/openai_raw_*.txt`
- Check logs for details

**2. OCR Failures**
- Vision mode: Ensure Ollama is running and model is downloaded
- Tesseract mode: Ensure tesseract-ocr is installed
- Check OCR output in `out_intermediate/ocr_pdfs/`

**3. Classification Rate Below 80%**
- Increase `--num_categories` to make categories broader
- Use `--predefined_categories` to specify known categories
- Check `classification_report.json` for details

**4. Out of Memory (Local GPU)**
- Use `--max_workers 1` for single-threaded mode
- Use smaller model (e.g., `qwen2.5:3b`)
- Reduce `--num_ctx` (default 16384)

## Dependencies

### Python Packages
- `PyMuPDF` (fitz): PDF text extraction and page rendering
- `python-docx`: Word file reading
- `python-pptx`: PowerPoint file reading
- `openai`: OpenAI SDK (API calls)
- `httpx`: HTTP client
- `requests`: HTTP client (Ollama)
- `Pillow` (PIL): Image processing (vision OCR)

### External Tools (Optional)
- `ocrmypdf`: Tesseract OCR processing
- `LibreOffice` or `unoconv`: Legacy Office format conversion (.doc, .ppt)
- `Ollama`: Local LLM and vision model server

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Acknowledgments

This tool uses Large Language Model technology and supports multiple LLM providers (OpenAI, Ollama, etc.).
