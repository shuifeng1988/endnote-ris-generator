#!/usr/bin/env python3
"""
检查哪些条目缺少PDF附件，并尝试重新上传
"""

import os
import json
import time
from pathlib import Path

# 修复代理问题
if 'ALL_PROXY' in os.environ and 'socks' in os.environ['ALL_PROXY'].lower():
    del os.environ['ALL_PROXY']
if 'all_proxy' in os.environ and 'socks' in os.environ['all_proxy'].lower():
    del os.environ['all_proxy']

try:
    from pyzotero import zotero
except ImportError:
    print("错误: 需要安装 pyzotero")
    exit(1)


def load_config():
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['library_id'], config['api_key'], config.get('library_type', 'user')
    else:
        print("错误: 找不到配置文件")
        exit(1)


def retry_failed_uploads(zot, mapping_file, max_size_mb=8, dry_run=False):
    """重试失败的上传"""

    # 加载映射
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    print(f"正在检查缺少附件的条目...\n")

    missing_pdfs = []

    for ref_id, info in mapping.items():
        item_key = info['item_key']
        pdf_path_str = info.get('pdf_path')
        title = info['title']

        if not pdf_path_str:
            continue

        pdf_path = Path(pdf_path_str)
        if not pdf_path.exists():
            continue

        # 检查文件大小
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            continue

        # 检查是否有附件
        children = zot.children(item_key)
        has_pdf = any(
            child['data'].get('contentType') == 'application/pdf'
            for child in children
        )

        if not has_pdf:
            missing_pdfs.append({
                'ref_id': ref_id,
                'item_key': item_key,
                'title': title,
                'pdf_path': pdf_path,
                'size_mb': file_size_mb,
                'collection': info['collection']
            })

    print(f"找到 {len(missing_pdfs)} 个缺少PDF的条目\n")

    if not missing_pdfs:
        print("所有条目都已有PDF附件！")
        return

    # 按集合分组显示
    by_collection = {}
    for item in missing_pdfs:
        col = item['collection']
        if col not in by_collection:
            by_collection[col] = []
        by_collection[col].append(item)

    for collection, items in sorted(by_collection.items()):
        print(f"集合: {collection} - {len(items)} 个缺失")
        for item in items:
            title_short = item['title'][:60] + '...' if len(item['title']) > 60 else item['title']
            print(f"  - {title_short} [{item['size_mb']:.1f}MB]")
        print()

    if dry_run:
        print("【测试模式】仅显示，不上传")
        return

    # 询问是否重试
    confirm = input(f"是否重试上传这 {len(missing_pdfs)} 个PDF? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("已取消")
        return

    print(f"\n开始重试上传...\n")

    success = 0
    failed = 0

    for i, item in enumerate(missing_pdfs, 1):
        title_short = item['title'][:60] + '...' if len(item['title']) > 60 else item['title']

        try:
            print(f"  [{i}/{len(missing_pdfs)}] ⟳ {title_short} [{item['size_mb']:.1f}MB]", end='', flush=True)

            zot.attachment_simple([str(item['pdf_path'])], item['item_key'])

            print(f"\r  [{i}/{len(missing_pdfs)}] ✓ {title_short} [成功]")
            success += 1

            time.sleep(0.5)

        except Exception as e:
            error_msg = str(e)[:60]
            print(f"\r  [{i}/{len(missing_pdfs)}] ✗ {title_short} [失败: {error_msg}]")
            failed += 1

    print(f"\n重试完成:")
    print(f"  成功: {success}")
    print(f"  失败: {failed}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='检查并重试失败的PDF上传'
    )

    parser.add_argument(
        '--mapping-file',
        default='zotero_item_mapping.json',
        help='映射文件路径'
    )
    parser.add_argument(
        '--max-size',
        type=float,
        default=8.0,
        help='最大文件大小(MB)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅检查，不上传'
    )

    args = parser.parse_args()

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    retry_failed_uploads(zot, args.mapping_file, args.max_size, args.dry_run)

    print("\n完成!")
