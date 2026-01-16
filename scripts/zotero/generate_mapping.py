#!/usr/bin/env python3
"""
从现有的Zotero数据和RIS文件生成映射文件
不需要重新导入，直接利用现有数据
"""

import os
import json
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


def parse_ris_for_mapping(ris_dir):
    """从RIS文件解析ref_id和PDF路径映射"""
    ris_dir = Path(ris_dir)
    mapping = {}  # title -> {ref_id, pdf_path, collection}

    for ris_file in sorted(ris_dir.glob("*.ris")):
        if ris_file.stem == 'classification_report':
            continue

        collection_name = ris_file.stem

        with open(ris_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for part in content.split('ER  -'):
            part = part.strip()
            if not part or 'TY  -' not in part:
                continue

            title = None
            ref_id = None
            pdf_path = None

            lines = part.split('\n')
            for line in lines:
                if line.startswith('TI  - '):
                    title = line[6:].strip()
                elif line.startswith('N1  - '):
                    # 提取ref_id
                    folder_match = re.search(r'EndNote folder=([^|]+)', line)
                    if folder_match:
                        ref_id = folder_match.group(1).strip()

                    # 提取PDF路径
                    attach_match = re.search(r'attachments=(file://[^\s\|]+)', line)
                    if attach_match:
                        pdf_url = attach_match.group(1)
                        if pdf_url.startswith('file:///'):
                            pdf_path = pdf_url[7:]
                        elif pdf_url.startswith('file://'):
                            pdf_path = pdf_url[7:]
                        else:
                            pdf_path = pdf_url
                        pdf_path = unquote(pdf_path)

            if title:
                mapping[title] = {
                    'ref_id': ref_id or 'unknown',
                    'pdf_path': pdf_path,
                    'collection': collection_name
                }

    return mapping


def generate_mapping_from_zotero(zot, ris_mapping):
    """从Zotero获取item_key，结合RIS映射生成完整映射"""
    print("正在从Zotero获取所有条目...")

    # 获取所有条目
    all_items = zot.everything(zot.items())
    print(f"找到 {len(all_items)} 条记录")

    # 构建完整映射
    complete_mapping = {}
    matched = 0
    unmatched = 0

    for item in all_items:
        if item['data'].get('itemType') == 'attachment':
            continue

        title = item['data'].get('title', '')
        item_key = item['key']

        # 从RIS映射中查找对应的ref_id和PDF路径
        if title in ris_mapping:
            ref_id = ris_mapping[title]['ref_id']
            pdf_path = ris_mapping[title]['pdf_path']
            collection = ris_mapping[title]['collection']

            complete_mapping[ref_id] = {
                'item_key': item_key,
                'pdf_path': pdf_path,
                'title': title,
                'collection': collection
            }
            matched += 1
        else:
            # 没有匹配的，也保存但标记pdf_path为None
            complete_mapping[f"unknown_{item_key}"] = {
                'item_key': item_key,
                'pdf_path': None,
                'title': title,
                'collection': 'unknown'
            }
            unmatched += 1

    print(f"\n匹配结果:")
    print(f"  已匹配: {matched}")
    print(f"  未匹配: {unmatched}")

    return complete_mapping


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


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='从现有数据生成Zotero映射文件'
    )

    parser.add_argument(
        '--ris-dir',
        default='outputs2/out_ris_class',
        help='RIS文件目录'
    )
    parser.add_argument(
        '--output',
        default='zotero_item_mapping.json',
        help='输出映射文件路径'
    )

    args = parser.parse_args()

    print("="*70)
    print("从现有数据生成映射文件")
    print("="*70)

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    # 解析RIS文件
    print(f"正在解析RIS文件: {args.ris_dir}")
    ris_mapping = parse_ris_for_mapping(args.ris_dir)
    print(f"找到 {len(ris_mapping)} 条RIS记录\n")

    # 生成完整映射
    complete_mapping = generate_mapping_from_zotero(zot, ris_mapping)

    # 保存映射
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(complete_mapping, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 映射已保存到: {args.output}")
    print(f"  总条目数: {len(complete_mapping)}")

    # 统计有PDF的数量
    pdf_count = sum(1 for v in complete_mapping.values()
                    if v['pdf_path'] and Path(v['pdf_path']).exists())
    print(f"  有PDF: {pdf_count}/{len(complete_mapping)}")

    print("\n" + "="*70)
    print("完成！现在可以使用映射文件上传PDF了")
    print("="*70)
