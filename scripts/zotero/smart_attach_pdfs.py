#!/usr/bin/env python3
"""
智能批量上传PDF附件到Zotero
- 自动跳过过大的文件
- 提供详细的进度报告
- 支持按集合批量处理
"""

import os
import json
import time
from pathlib import Path
from urllib.parse import unquote
import re

# 修复代理问题
if 'ALL_PROXY' in os.environ and 'socks' in os.environ['ALL_PROXY'].lower():
    print("检测到socks代理，临时禁用（pyzotero不支持socks）...")
    del os.environ['ALL_PROXY']
if 'all_proxy' in os.environ and 'socks' in os.environ['all_proxy'].lower():
    del os.environ['all_proxy']

try:
    from pyzotero import zotero
except ImportError:
    print("错误: 需要安装 pyzotero")
    exit(1)


def load_config():
    """加载Zotero配置"""
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['library_id'], config['api_key'], config.get('library_type', 'user')
    else:
        print("错误: 找不到配置文件")
        exit(1)


def normalize_text(text):
    """规范化文本用于匹配"""
    # 统一破折号
    text = text.replace('—', '-').replace('–', '-').replace('‐', '-')
    text = text.replace('\u2010', '-').replace('\u2011', '-').replace('\u2012', '-')
    text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2015', '-')
    # 移除标点和特殊字符
    text = re.sub(r'[^\w\s-]', ' ', text, flags=re.UNICODE)
    # 统一空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def find_pdf_for_title(pdf_dir, title, doi=''):
    """根据标题和DOI查找匹配的PDF"""
    pdf_dir = Path(pdf_dir)

    if not title:
        return None

    normalized_title = normalize_text(title)
    title_prefix = normalized_title[:50] if len(normalized_title) > 50 else normalized_title

    # 策略1: 精确标题匹配
    for pdf in pdf_dir.glob("*.pdf"):
        pdf_name_normalized = normalize_text(pdf.stem)

        # 完全匹配
        if pdf_name_normalized == normalized_title:
            return pdf

        # 前缀匹配
        if title_prefix in pdf_name_normalized or pdf_name_normalized in title_prefix:
            return pdf

    # 策略2: DOI匹配（支持多种DOI格式）
    if doi:
        # 提取DOI的关键部分
        doi_normalized = doi.replace('/', '').replace('.', '').lower()
        doi_parts = [
            doi.split('/')[-1].lower() if '/' in doi else doi.lower(),  # 标准DOI后缀
            doi_normalized,  # 完整DOI去除分隔符
        ]

        for pdf in pdf_dir.glob("*.pdf"):
            pdf_stem_lower = pdf.stem.lower()
            for doi_part in doi_parts:
                if doi_part in pdf_stem_lower or pdf_stem_lower in doi_part:
                    return pdf

    # 策略3: 关键词匹配
    title_words = set(normalized_title.split())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    title_words -= stop_words

    if title_words:
        for pdf in pdf_dir.glob("*.pdf"):
            pdf_words = set(normalize_text(pdf.stem).split())
            pdf_words -= stop_words

            if pdf_words:
                overlap = len(title_words & pdf_words) / len(title_words)
                if overlap > 0.6:  # 60%匹配率
                    return pdf

    return None


def attach_pdfs_to_collection(zot, collection_name, pdf_dir, max_size_mb=8, dry_run=False):
    """为指定集合的所有条目附加PDF"""

    # 获取集合
    collections = zot.collections()
    collection_key = None

    for col in collections:
        if col['data']['name'] == collection_name:
            collection_key = col['key']
            break

    if not collection_key:
        print(f"错误: 找不到集合 '{collection_name}'")
        return

    print(f"\n{'='*70}")
    print(f"处理集合: {collection_name}")
    print(f"{'='*70}")

    # 获取集合中的所有条目
    items = zot.collection_items(collection_key)
    print(f"找到 {len(items)} 条文献")

    if dry_run:
        print("【测试模式】只检查匹配，不上传\n")
    else:
        print(f"最大上传大小: {max_size_mb}MB\n")

    success_count = 0
    skipped_has_attachment = 0
    skipped_too_large = 0
    skipped_not_found = 0
    failed_upload = 0

    for i, item in enumerate(items, 1):
        # 跳过附件类型
        if item['data'].get('itemType') == 'attachment':
            continue

        title = item['data'].get('title', 'Untitled')
        title_short = title[:60] + '...' if len(title) > 60 else title
        item_key = item['key']
        doi = item['data'].get('DOI', '')

        # 检查是否已有附件
        children = zot.children(item_key)
        has_pdf = any(
            child['data'].get('contentType') == 'application/pdf'
            for child in children
        )

        if has_pdf:
            print(f"  [{i}/{len(items)}] ⊙ {title_short} [已有PDF]")
            skipped_has_attachment += 1
            continue

        # 查找匹配的PDF
        pdf_path = find_pdf_for_title(pdf_dir, title, doi)

        if not pdf_path:
            print(f"  [{i}/{len(items)}] ✗ {title_short} [找不到PDF]")
            skipped_not_found += 1
            continue

        # 检查文件大小
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            print(f"  [{i}/{len(items)}] ⚠ {title_short} [过大: {file_size_mb:.1f}MB]")
            print(f"      PDF: {pdf_path.name}")
            skipped_too_large += 1
            continue

        if dry_run:
            print(f"  [{i}/{len(items)}] ✓ {title_short} [匹配: {pdf_path.name} ({file_size_mb:.1f}MB)]")
            success_count += 1
            continue

        # 上传PDF
        try:
            print(f"  [{i}/{len(items)}] ⟳ {title_short} [上传中: {file_size_mb:.1f}MB]", end='', flush=True)

            # 使用attachment_simple上传
            result = zot.attachment_simple([str(pdf_path)], item_key)

            print(f"\r  [{i}/{len(items)}] ✓ {title_short} [已上传: {file_size_mb:.1f}MB]")
            success_count += 1

            # 避免API限流
            time.sleep(0.5)

        except Exception as e:
            error_msg = str(e)[:80]
            print(f"\r  [{i}/{len(items)}] ✗ {title_short} [失败: {error_msg}]")
            failed_upload += 1

    # 统计
    print(f"\n{'='*70}")
    print(f"总结:")
    print(f"  总文献数: {len(items)}")
    print(f"  成功上传: {success_count}")
    print(f"  已有附件: {skipped_has_attachment}")
    print(f"  文件过大: {skipped_too_large}")
    print(f"  找不到PDF: {skipped_not_found}")
    print(f"  上传失败: {failed_upload}")
    print(f"{'='*70}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='智能批量上传PDF附件到Zotero',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 测试模式（只检查匹配，不上传）
  python3 smart_attach_pdfs.py --collection virtual_cells --dry-run

  # 正式上传（最大8MB）
  python3 smart_attach_pdfs.py --collection virtual_cells --max-size 8

  # 上传所有集合
  python3 smart_attach_pdfs.py --all
        """
    )

    parser.add_argument(
        '--collection',
        help='集合名称（如 virtual_cells）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='处理所有集合'
    )
    parser.add_argument(
        '--pdf-dir',
        default='/media/shuifeng/BEA6-BBCE/pdfs',
        help='PDF文件目录'
    )
    parser.add_argument(
        '--max-size',
        type=float,
        default=8.0,
        help='最大上传文件大小(MB)，默认8MB'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='测试模式：只检查匹配，不实际上传'
    )

    args = parser.parse_args()

    if not args.collection and not args.all:
        parser.error("必须指定 --collection 或 --all")

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    if args.all:
        # 处理所有集合
        all_collections = [
            'Uncategorized', 'ai_drug_discovery', 'big_models',
            'biomedical_agents', 'drug_screenings', 'gene_regulatory_networks',
            'genetic_evolution_adaptations', 'multi_omics', 'single_cell_analysis',
            'spatial_omics', 'virtual_cells'
        ]

        for collection_name in all_collections:
            attach_pdfs_to_collection(
                zot, collection_name, args.pdf_dir, args.max_size, args.dry_run
            )
            print()
    else:
        # 处理单个集合
        attach_pdfs_to_collection(
            zot, args.collection, args.pdf_dir, args.max_size, args.dry_run
        )

    print("\n完成!")
