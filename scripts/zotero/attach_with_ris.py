#!/usr/bin/env python3
"""
从RIS文件读取PDF路径映射，然后批量上传
这样可以精确匹配，避免文件名不一致的问题
"""

import os
import json
import time
import re
from pathlib import Path
from urllib.parse import unquote

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


def parse_ris_for_pdf_mapping(ris_path):
    """从RIS文件解析标题到PDF路径的映射"""
    with open(ris_path, 'r', encoding='utf-8') as f:
        content = f.read()

    mapping = {}  # title -> pdf_path

    for part in content.split('ER  -'):
        part = part.strip()
        if not part or 'TY  -' not in part:
            continue

        title = None
        pdf_path = None

        lines = part.split('\n')
        for line in lines:
            if line.startswith('TI  - '):
                title = line[6:].strip()
            elif line.startswith('N1  - '):
                # 从N1字段提取PDF路径
                match = re.search(r'attachments=(file://[^\s\|]+)', line)
                if match:
                    pdf_url = match.group(1)
                    if pdf_url.startswith('file:///'):
                        pdf_path = pdf_url[7:]
                    elif pdf_url.startswith('file://'):
                        pdf_path = pdf_url[7:]
                    else:
                        pdf_path = pdf_url
                    pdf_path = unquote(pdf_path)

        if title and pdf_path:
            mapping[title] = pdf_path

    return mapping


def attach_pdfs_with_ris_mapping(zot, collection_name, ris_path, max_size_mb=8, dry_run=False):
    """使用RIS文件的映射信息附加PDF"""

    # 读取RIS映射
    print(f"正在读取RIS文件: {ris_path}")
    pdf_mapping = parse_ris_for_pdf_mapping(ris_path)
    print(f"找到 {len(pdf_mapping)} 个PDF路径映射\n")

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

    print(f"{'='*70}")
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

        # 从RIS映射中查找PDF路径
        pdf_path_str = pdf_mapping.get(title)

        if not pdf_path_str:
            print(f"  [{i}/{len(items)}] ✗ {title_short} [映射中找不到]")
            skipped_not_found += 1
            continue

        pdf_path = Path(pdf_path_str)

        if not pdf_path.exists():
            print(f"  [{i}/{len(items)}] ✗ {title_short} [文件不存在]")
            print(f"      路径: {pdf_path}")
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
        description='使用RIS文件映射批量上传PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 测试模式
  python3 attach_with_ris.py --collection virtual_cells --dry-run

  # 正式上传
  python3 attach_with_ris.py --collection virtual_cells --max-size 8

  # 处理所有集合
  python3 attach_with_ris.py --all
        """
    )

    parser.add_argument(
        '--collection',
        help='集合名称'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='处理所有集合'
    )
    parser.add_argument(
        '--ris-dir',
        default='outputs2/out_ris_class',
        help='RIS文件目录'
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
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    ris_dir = Path(args.ris_dir)

    if args.all:
        # 处理所有集合
        ris_files = sorted(ris_dir.glob("*.ris"))

        for ris_file in ris_files:
            if ris_file.stem == 'classification_report':
                continue

            collection_name = ris_file.stem
            attach_pdfs_with_ris_mapping(
                zot, collection_name, ris_file, args.max_size, args.dry_run
            )
            print()
    else:
        # 处理单个集合
        ris_file = ris_dir / f"{args.collection}.ris"

        if not ris_file.exists():
            print(f"错误: RIS文件不存在: {ris_file}")
            exit(1)

        attach_pdfs_with_ris_mapping(
            zot, args.collection, ris_file, args.max_size, args.dry_run
        )

    print("\n完成!")
