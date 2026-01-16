#!/usr/bin/env python3
"""
批量上传PDF附件到Zotero
使用Zotero API上传存储副本
"""

import os
import json
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


def find_pdf_for_item(pdf_dir, title):
    """根据标题查找匹配的PDF文件"""
    pdf_dir = Path(pdf_dir)

    # 简化标题用于匹配
    title_normalized = title.lower().replace(' ', '').replace('-', '')[:50]

    for pdf in pdf_dir.glob("*.pdf"):
        pdf_name_normalized = pdf.stem.lower().replace(' ', '').replace('-', '')

        # 检查是否匹配
        if title_normalized in pdf_name_normalized or pdf_name_normalized in title_normalized:
            return pdf

    return None


def attach_pdfs_to_collection(zot, collection_name, pdf_dir, max_size_mb=10):
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
    print(f"找到 {len(items)} 条文献\n")

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for item in items:
        # 跳过附件类型
        if item['data'].get('itemType') == 'attachment':
            continue

        title = item['data'].get('title', 'Untitled')[:60]
        item_key = item['key']

        # 检查是否已有附件
        children = zot.children(item_key)
        has_pdf = any(child['data'].get('contentType') == 'application/pdf' for child in children)

        if has_pdf:
            print(f"  ⊙ {title}... [已有PDF附件]")
            skipped_count += 1
            continue

        # 查找匹配的PDF
        pdf_path = find_pdf_for_item(pdf_dir, item['data'].get('title', ''))

        if not pdf_path:
            print(f"  ✗ {title}... [找不到PDF]")
            failed_count += 1
            continue

        # 检查文件大小
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

        if file_size_mb > max_size_mb:
            print(f"  ⚠ {title}... [PDF过大: {file_size_mb:.1f}MB，跳过上传]")
            skipped_count += 1
            continue

        # 上传PDF
        try:
            print(f"  ⟳ {title}... [上传中: {file_size_mb:.1f}MB]", end='', flush=True)

            # 使用attachment_simple上传
            zot.attachment_simple([str(pdf_path)], item_key)

            print(f"\r  ✓ {title}... [已上传: {file_size_mb:.1f}MB]")
            success_count += 1

        except Exception as e:
            print(f"\r  ✗ {title}... [上传失败: {str(e)[:50]}]")
            failed_count += 1

    print(f"\n总结:")
    print(f"  成功上传: {success_count}")
    print(f"  已有附件: {skipped_count}")
    print(f"  失败/未找到: {failed_count}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='批量上传PDF附件到Zotero集合'
    )
    parser.add_argument(
        '--collection',
        required=True,
        help='集合名称（如 big_models）'
    )
    parser.add_argument(
        '--pdf-dir',
        default='/media/shuifeng/BEA6-BBCE/pdfs',
        help='PDF文件目录'
    )
    parser.add_argument(
        '--max-size',
        type=float,
        default=10.0,
        help='最大上传文件大小(MB)，默认10MB'
    )

    args = parser.parse_args()

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    # 上传PDF
    attach_pdfs_to_collection(
        zot,
        args.collection,
        args.pdf_dir,
        args.max_size
    )

    print("\n完成!")
