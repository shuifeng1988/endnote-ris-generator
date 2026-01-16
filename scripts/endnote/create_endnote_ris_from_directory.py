#!/usr/bin/env python3
"""
从目录扫描文档并生成 EndNote 可用的 RIS 文件
支持子目录和各种文档格式，使用相对路径指向附件

目录结构：
输入：
  source_dir/
    ├── file1.pdf
    ├── file2.docx
    └── subdir/
        ├── file3.pdf
        └── file4.pptx

输出：
  output/
    ├── out_ris/
    │   ├── file1_xxxxx.ris
    │   ├── file2_xxxxx.ris
    │   └── ...
    └── pdf/  (复制所有源文件到这里)
        ├── file1.pdf
        ├── file2.docx
        ├── subdir_file3.pdf
        └── subdir_file4.pptx

使用方法：
  python create_endnote_ris_from_directory.py /path/to/source --out_dir ./output

在 Windows 导入时：
  1. 将整个 output 文件夹复制到 Windows
  2. 在 EndNote 中批量导入 output/out_ris/*.ris
  3. EndNote 会自动识别 ./pdf/ 下的附件并复制到库中
"""

from __future__ import annotations
import argparse
import pathlib
import shutil
import hashlib
import json
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os


# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.ppt', '.pptx',
    '.xls', '.xlsx', '.txt', '.rtf', '.odt',
    '.epub', '.mobi', '.djvu', '.ps', '.eps'
}


def folder_id(path: pathlib.Path) -> str:
    """生成文件/文件夹的唯一 ID"""
    st = path.stat()
    key = f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def ris_escape(s: str) -> str:
    """转义 RIS 字段中的特殊字符"""
    return " ".join(str(s).replace("\n", " ").split()).strip()


def get_relative_attachment_path(source_file: pathlib.Path, source_root: pathlib.Path) -> str:
    """
    生成附件的相对路径（相对于 RIS 文件）

    RIS 文件在: output/out_ris/xxx.ris
    附件在: output/pdf/xxx.pdf
    所以相对路径是: ../pdf/xxx.pdf

    但为了兼容性，我们使用 ./pdf/xxx.pdf（假设导入时在 output 目录）
    """
    # 保留子目录结构在文件名中
    try:
        rel_path = source_file.relative_to(source_root)
        # 将路径分隔符替换为下划线，保持文件名唯一
        safe_name = str(rel_path).replace(os.sep, '_')
    except ValueError:
        # 如果不在 source_root 下，直接使用文件名
        safe_name = source_file.name

    # 返回相对路径格式：./pdf/filename
    return f"./pdf/{safe_name}"


def copy_attachment_to_output(source_file: pathlib.Path, source_root: pathlib.Path,
                               pdf_dir: pathlib.Path) -> Optional[str]:
    """
    复制附件到输出目录

    Args:
        source_file: 源文件路径
        source_root: 源文件根目录
        pdf_dir: 输出的 pdf 目录

    Returns:
        相对路径（相对于 output 目录），失败返回 None
    """
    try:
        # 生成目标文件名（保留子目录结构）
        try:
            rel_path = source_file.relative_to(source_root)
            safe_name = str(rel_path).replace(os.sep, '_')
        except ValueError:
            safe_name = source_file.name

        dest_file = pdf_dir / safe_name

        # 如果文件已存在且内容相同，跳过
        if dest_file.exists():
            if dest_file.stat().st_size == source_file.stat().st_size:
                return f"./pdf/{safe_name}"

        # 复制文件
        shutil.copy2(source_file, dest_file)
        return f"./pdf/{safe_name}"

    except Exception as e:
        print(f"  ✗ 复制文件失败 {source_file}: {e}")
        return None


def extract_metadata_from_filename(file_path: pathlib.Path) -> Dict[str, Any]:
    """
    从文件名提取元数据（简单版本）

    常见格式：
    - Author_Year_Title.pdf
    - Title (Year).pdf
    - [Year] Author - Title.pdf
    """
    filename = file_path.stem

    meta = {
        "title": filename.replace("_", " ").replace("-", " ").strip(),
        "authors": None,
        "year": None,
        "journal": None,
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "url": None,
        "abstract": None,
        "record_type": "GEN",  # Generic
        "confidence": 0.3,  # 低置信度（仅从文件名提取）
    }

    # 尝试提取年份
    import re
    year_match = re.search(r'\b(19|20)\d{2}\b', filename)
    if year_match:
        meta["year"] = year_match.group()

    # 尝试提取作者（假设格式：Author_Year_Title 或 Author (Year) Title）
    parts = re.split(r'[_\-\(\)]', filename)
    if len(parts) >= 2:
        potential_author = parts[0].strip()
        if potential_author and len(potential_author) > 2:
            meta["authors"] = [potential_author]

    return meta


def create_ris_entry(file_path: pathlib.Path, source_root: pathlib.Path,
                     attachment_rel_path: str, meta: Dict[str, Any] = None) -> str:
    """
    创建单个 RIS 条目

    Args:
        file_path: 文件路径
        source_root: 源文件根目录
        attachment_rel_path: 附件相对路径
        meta: 元数据（如果为 None，从文件名提取）

    Returns:
        RIS 格式文本
    """
    if meta is None:
        meta = extract_metadata_from_filename(file_path)

    lines = []

    # 文献类型
    record_type = meta.get("record_type", "GEN")
    lines.append(f"TY  - {record_type}")

    # 标题
    title = meta.get("title") or file_path.stem.replace("_", " ")
    lines.append(f"TI  - {ris_escape(title)}")

    # 作者（EndNote 支持多行 AU，每行一个作者）
    authors = meta.get("authors") or []
    if authors:
        for author in authors:
            if author:
                lines.append(f"AU  - {ris_escape(author)}")

    # 年份
    if meta.get("year"):
        lines.append(f"PY  - {meta['year']}")

    # 期刊
    if meta.get("journal"):
        lines.append(f"JO  - {ris_escape(meta['journal'])}")

    # 卷号
    if meta.get("volume"):
        lines.append(f"VL  - {ris_escape(meta['volume'])}")

    # 期号
    if meta.get("issue"):
        lines.append(f"IS  - {ris_escape(meta['issue'])}")

    # 页码
    if meta.get("pages"):
        lines.append(f"SP  - {ris_escape(meta['pages'])}")

    # DOI
    if meta.get("doi"):
        lines.append(f"DO  - {ris_escape(meta['doi'])}")

    # URL
    if meta.get("url"):
        lines.append(f"UR  - {ris_escape(meta['url'])}")

    # 摘要
    if meta.get("abstract"):
        lines.append(f"N2  - {ris_escape(meta['abstract'])}")

    # 备注（包含原始文件路径）
    try:
        rel_to_root = file_path.relative_to(source_root)
        note = f"Source: {rel_to_root}"
    except ValueError:
        note = f"Source: {file_path.name}"
    lines.append(f"N1  - {ris_escape(note)}")

    # 附件路径（使用相对路径）
    # EndNote 使用 L1 字段识别附件
    lines.append(f"L1  - {attachment_rel_path}")

    # 结束标记
    lines.append("ER  -")

    return "\n".join(lines) + "\n"


def scan_directory(root_dir: pathlib.Path, recursive: bool = True,
                   include_root_files: bool = True) -> List[pathlib.Path]:
    """
    扫描目录，返回所有支持的文件

    Args:
        root_dir: 根目录
        recursive: 是否递归扫描子目录
        include_root_files: 是否包含根目录下的文件

    Returns:
        文件路径列表
    """
    files = []

    if recursive:
        # 递归扫描所有文件
        for file_path in root_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(file_path)
    else:
        # 只扫描根目录和一级子目录
        if include_root_files:
            for file_path in root_dir.glob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(file_path)

        for subdir in root_dir.glob('*'):
            if subdir.is_dir():
                for file_path in subdir.glob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files.append(file_path)

    return sorted(files)


def process_single_file(file_path: pathlib.Path, source_root: pathlib.Path,
                        out_ris_dir: pathlib.Path, pdf_dir: pathlib.Path,
                        use_ai: bool, provider, cfg, log,
                        progress_lock, counters) -> tuple[bool, str]:
    """
    处理单个文件

    Returns:
        (success, error_message)
    """
    try:
        file_id = folder_id(file_path)

        # 复制附件到 pdf 目录
        attachment_rel_path = copy_attachment_to_output(file_path, source_root, pdf_dir)
        if attachment_rel_path is None:
            raise Exception("Failed to copy attachment")

        # 提取元数据
        if use_ai:
            # TODO: 使用 AI 提取元数据（类似 zotero_restore 脚本）
            meta = extract_metadata_from_filename(file_path)
        else:
            meta = extract_metadata_from_filename(file_path)

        # 生成 RIS 条目
        ris_content = create_ris_entry(file_path, source_root, attachment_rel_path, meta)

        # 生成输出文件名
        safe_name = file_path.stem.replace(" ", "_")[:50]
        ris_filename = f"{safe_name}_{file_id[:8]}.ris"
        ris_path = out_ris_dir / ris_filename

        # 写入 RIS 文件
        ris_path.write_text(ris_content, encoding='utf-8')

        # 保存中间 JSON（可选）
        intermediate = {
            "file_id": file_id,
            "source_file": str(file_path),
            "attachment_path": attachment_rel_path,
            "meta": meta,
        }
        json_path = out_ris_dir.parent / "out_intermediate" / f"{safe_name}_{file_id[:8]}.json"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(intermediate, ensure_ascii=False, indent=2), encoding='utf-8')

        with progress_lock:
            counters["success"] += 1
            current = counters["success"] + counters["failed"]
            if log:
                log.info(f"[{current}/{counters['total']}] ✓ {file_path.name}")
            else:
                print(f"[{current}/{counters['total']}] ✓ {file_path.name}")

        return (True, None)

    except Exception as e:
        with progress_lock:
            counters["failed"] += 1
            current = counters["success"] + counters["failed"]
            if log:
                log.error(f"[{current}/{counters['total']}] ✗ {file_path.name}: {e}")
            else:
                print(f"[{current}/{counters['total']}] ✗ {file_path.name}: {e}")

        return (False, str(e))


def main():
    parser = argparse.ArgumentParser(
        description="从目录扫描文档并生成 EndNote 可用的 RIS 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基本用法
  python create_endnote_ris_from_directory.py /path/to/documents

  # 指定输出目录
  python create_endnote_ris_from_directory.py /path/to/documents --out_dir ./my_output

  # 不递归扫描子目录
  python create_endnote_ris_from_directory.py /path/to/documents --no-recursive

  # 使用 AI 提取元数据（需要配置 .env）
  python create_endnote_ris_from_directory.py /path/to/documents --use-ai

输出结构：
  output/
    ├── out_ris/          # RIS 文件
    │   ├── file1.ris
    │   └── file2.ris
    ├── out_intermediate/ # 中间 JSON 文件（调试用）
    │   ├── file1.json
    │   └── file2.json
    └── pdf/              # 所有源文件（复制）
        ├── file1.pdf
        └── file2.docx

在 Windows 的 EndNote 中导入：
  1. 将整个 output 文件夹复制到 Windows
  2. File → Import → File
  3. 选择 output/out_ris 目录下的所有 .ris 文件（可批量选择）
  4. Import Option: RefMan (RIS)
  5. 确保勾选 "Copy files to library folder"
  6. EndNote 会自动识别 ./pdf/ 路径并复制附件
        """
    )

    parser.add_argument("source_dir", help="源文件目录")
    parser.add_argument("--out_dir", default="./output", help="输出目录（默认: ./output）")
    parser.add_argument("--no-recursive", action="store_true", help="不递归扫描子目录")
    parser.add_argument("--no-root-files", action="store_true", help="不包含根目录下的文件")
    parser.add_argument("--use-ai", action="store_true", help="使用 AI 提取元数据（需要配置 .env）")
    parser.add_argument("--dotenv", default=".env", help=".env 文件路径")
    parser.add_argument("--max-workers", type=int, default=4, help="并发处理数（默认: 4）")

    args = parser.parse_args()

    # 解析路径
    source_dir = pathlib.Path(args.source_dir).expanduser().resolve()
    out_dir = pathlib.Path(args.out_dir).expanduser().resolve()

    if not source_dir.exists():
        print(f"✗ 源目录不存在: {source_dir}")
        return 1

    # 创建输出目录
    out_ris_dir = out_dir / "out_ris"
    pdf_dir = out_dir / "pdf"
    out_ris_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("EndNote RIS 生成工具")
    print("=" * 60)
    print(f"源目录: {source_dir}")
    print(f"输出目录: {out_dir}")
    print(f"递归扫描: {not args.no_recursive}")
    print(f"使用 AI: {args.use_ai}")
    print()

    # 扫描文件
    print("扫描文件...")
    files = scan_directory(
        source_dir,
        recursive=not args.no_recursive,
        include_root_files=not args.no_root_files
    )

    if not files:
        print("✗ 未找到支持的文件")
        return 1

    print(f"找到 {len(files)} 个文件")
    print()

    # 初始化 AI provider（如果需要）
    provider = None
    cfg = None
    log = None

    if args.use_ai:
        print("初始化 AI provider...")
        # TODO: 加载 .env 并初始化 provider
        # 这里暂时跳过，使用简单的文件名提取
        print("警告: AI 提取功能尚未实现，将使用文件名提取")
        args.use_ai = False

    # 处理文件
    print("处理文件...")
    progress_lock = threading.Lock()
    counters = {
        "success": 0,
        "failed": 0,
        "total": len(files),
    }

    if args.max_workers == 1:
        # 单线程模式
        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] 处理: {file_path.name}")
            process_single_file(
                file_path, source_dir, out_ris_dir, pdf_dir,
                args.use_ai, provider, cfg, log,
                progress_lock, counters
            )
    else:
        # 多线程模式
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {}
            for file_path in files:
                future = executor.submit(
                    process_single_file,
                    file_path, source_dir, out_ris_dir, pdf_dir,
                    args.use_ai, provider, cfg, log,
                    progress_lock, counters
                )
                futures[future] = file_path

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    success, error = future.result()
                except Exception as e:
                    print(f"✗ 处理失败 {file_path.name}: {e}")

    # 统计
    print()
    print("=" * 60)
    print("处理完成")
    print("=" * 60)
    print(f"总文件数: {counters['total']}")
    print(f"成功: {counters['success']}")
    print(f"失败: {counters['failed']}")
    print()
    print(f"输出目录: {out_dir}")
    print(f"  - RIS 文件: {out_ris_dir}")
    print(f"  - 附件文件: {pdf_dir}")
    print()
    print("下一步：")
    print(f"1. 将 {out_dir} 文件夹复制到 Windows 系统")
    print(f"2. 在 EndNote 中：")
    print(f"   - File → Import → File")
    print(f"   - 选择 {out_ris_dir} 下的所有 .ris 文件")
    print(f"   - Import Option: RefMan (RIS)")
    print(f"   - 确保勾选 'Copy files to library folder'")
    print(f"3. EndNote 会自动识别 ./pdf/ 路径并复制附件到库中")

    return 0


if __name__ == "__main__":
    exit(main())
