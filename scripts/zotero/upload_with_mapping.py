#!/usr/bin/env python3
"""
使用映射文件精确上传PDF附件
完全避免文件名匹配问题
"""

import os
import json
import time
from pathlib import Path

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


def upload_pdfs_with_mapping(zot, mapping_file, max_size_mb=8, dry_run=False, collection_filter=None):
    """使用映射文件上传PDF"""

    # 加载映射
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    print(f"✓ 加载映射文件: {mapping_file}")
    print(f"  总条目数: {len(mapping)}\n")

    if dry_run:
        print("【测试模式】只检查，不上传\n")
    else:
        print(f"最大上传大小: {max_size_mb}MB\n")

    # 按集合分组
    by_collection = {}
    for ref_id, info in mapping.items():
        collection = info['collection']
        if collection not in by_collection:
            by_collection[collection] = []
        by_collection[collection].append((ref_id, info))

    # 统计
    total_success = 0
    total_skipped_has_attachment = 0
    total_skipped_too_large = 0
    total_skipped_no_pdf = 0
    total_failed = 0

    # 处理每个集合
    for collection_name in sorted(by_collection.keys()):
        if collection_filter and collection_name != collection_filter:
            continue

        items = by_collection[collection_name]

        print(f"{'='*70}")
        print(f"集合: {collection_name}")
        print(f"{'='*70}")
        print(f"条目数: {len(items)}\n")

        for i, (ref_id, info) in enumerate(items, 1):
            item_key = info['item_key']
            pdf_path_str = info.get('pdf_path')
            title = info['title']
            title_short = title[:60] + '...' if len(title) > 60 else title

            # 检查是否已有附件
            children = zot.children(item_key)
            has_pdf = any(
                child['data'].get('contentType') == 'application/pdf'
                for child in children
            )

            if has_pdf:
                print(f"  [{i}/{len(items)}] ⊙ {title_short} [已有PDF]")
                total_skipped_has_attachment += 1
                continue

            # 检查PDF路径
            if not pdf_path_str:
                print(f"  [{i}/{len(items)}] ✗ {title_short} [无PDF路径]")
                total_skipped_no_pdf += 1
                continue

            pdf_path = Path(pdf_path_str)

            if not pdf_path.exists():
                print(f"  [{i}/{len(items)}] ✗ {title_short} [PDF不存在]")
                print(f"      路径: {pdf_path}")
                total_skipped_no_pdf += 1
                continue

            # 检查文件大小
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

            if file_size_mb > max_size_mb:
                print(f"  [{i}/{len(items)}] ⚠ {title_short} [过大: {file_size_mb:.1f}MB]")
                print(f"      PDF: {pdf_path.name}")
                total_skipped_too_large += 1
                continue

            if dry_run:
                print(f"  [{i}/{len(items)}] ✓ {title_short} [OK: {pdf_path.name} ({file_size_mb:.1f}MB)]")
                total_success += 1
                continue

            # 上传PDF
            try:
                print(f"  [{i}/{len(items)}] ⟳ {title_short} [上传: {file_size_mb:.1f}MB]", end='', flush=True)

                result = zot.attachment_simple([str(pdf_path)], item_key)

                print(f"\r  [{i}/{len(items)}] ✓ {title_short} [已上传: {file_size_mb:.1f}MB]")
                total_success += 1

                # 避免API限流
                time.sleep(0.5)

            except Exception as e:
                error_msg = str(e)[:60]
                print(f"\r  [{i}/{len(items)}] ✗ {title_short} [失败: {error_msg}]")
                total_failed += 1

        print()

    # 总统计
    print("="*70)
    print("总结:")
    print("="*70)
    print(f"  成功上传: {total_success}")
    print(f"  已有附件: {total_skipped_has_attachment}")
    print(f"  文件过大: {total_skipped_too_large}")
    print(f"  无PDF/不存在: {total_skipped_no_pdf}")
    print(f"  上传失败: {total_failed}")
    print("="*70)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='使用映射文件精确上传PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 1. 先生成映射文件
  python3 generate_mapping.py

  # 2. 测试模式（检查映射是否正确）
  python3 upload_with_mapping.py --dry-run

  # 3. 测试单个集合
  python3 upload_with_mapping.py --collection virtual_cells --dry-run

  # 4. 正式上传单个集合
  python3 upload_with_mapping.py --collection virtual_cells --max-size 8

  # 5. 上传所有集合
  python3 upload_with_mapping.py --max-size 8
        """
    )

    parser.add_argument(
        '--mapping-file',
        default='zotero_item_mapping.json',
        help='映射文件路径'
    )
    parser.add_argument(
        '--collection',
        help='只处理指定集合'
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
        help='测试模式：只检查，不上传'
    )

    args = parser.parse_args()

    # 检查映射文件是否存在
    if not Path(args.mapping_file).exists():
        print(f"错误: 映射文件不存在: {args.mapping_file}")
        print("\n请先运行: python3 generate_mapping.py")
        exit(1)

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    # 上传PDF
    upload_pdfs_with_mapping(
        zot,
        args.mapping_file,
        args.max_size,
        args.dry_run,
        args.collection
    )

    print("\n完成!")
