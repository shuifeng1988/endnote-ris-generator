#!/usr/bin/env python3
"""
生成缺失PDF的详细清单（Markdown格式）
方便手动添加附件
"""

import os
import json
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


def generate_checklist(zot, mapping_file, output_file='missing_pdfs_checklist.md'):
    """生成缺失PDF的清单"""

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

        # 检查PDF是否存在
        pdf_exists = pdf_path.exists()

        # 检查是否有附件
        children = zot.children(item_key)
        has_pdf = any(
            child['data'].get('contentType') == 'application/pdf'
            for child in children
        )

        if not has_pdf:
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024) if pdf_exists else 0
            missing_pdfs.append({
                'title': title,
                'pdf_path': str(pdf_path),
                'pdf_name': pdf_path.name if pdf_exists else 'FILE NOT FOUND',
                'size_mb': file_size_mb,
                'collection': info['collection'],
                'exists': pdf_exists
            })

    print(f"找到 {len(missing_pdfs)} 个缺少PDF的条目\n")

    # 按集合分组
    by_collection = {}
    for item in missing_pdfs:
        col = item['collection']
        if col not in by_collection:
            by_collection[col] = []
        by_collection[col].append(item)

    # 生成Markdown清单
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 缺失PDF附件清单\n\n")
        f.write(f"**总计：{len(missing_pdfs)} 个PDF需要手动添加**\n\n")
        f.write("---\n\n")

        f.write("## 操作步骤\n\n")
        f.write("1. 打开Zotero\n")
        f.write("2. 打开文件管理器，导航到：`/media/shuifeng/BEA6-BBCE/pdfs`\n")
        f.write("3. 对于下面列出的每个条目：\n")
        f.write("   - 在Zotero中找到对应的条目\n")
        f.write("   - 在文件管理器中找到对应的PDF文件\n")
        f.write("   - 将PDF文件**拖放**到Zotero条目上\n")
        f.write("   - Zotero会自动复制文件到存储目录\n\n")
        f.write("---\n\n")

        total_size_mb = sum(item['size_mb'] for item in missing_pdfs)
        f.write(f"## 统计\n\n")
        f.write(f"- **总文件数**: {len(missing_pdfs)}\n")
        f.write(f"- **总大小**: {total_size_mb:.1f} MB\n")
        f.write(f"- **集合数**: {len(by_collection)}\n\n")
        f.write("---\n\n")

        # 按集合输出
        for collection_name in sorted(by_collection.keys()):
            items = by_collection[collection_name]
            col_size = sum(item['size_mb'] for item in items)

            f.write(f"## {collection_name} ({len(items)} 个PDF, {col_size:.1f}MB)\n\n")

            for i, item in enumerate(items, 1):
                f.write(f"### {i}. {item['title']}\n\n")
                f.write(f"- **PDF文件名**: `{item['pdf_name']}`\n")
                f.write(f"- **文件大小**: {item['size_mb']:.1f} MB\n")
                f.write(f"- **文件路径**: `{item['pdf_path']}`\n")

                if not item['exists']:
                    f.write(f"- **状态**: ❌ 文件不存在！\n")
                elif item['size_mb'] > 20:
                    f.write(f"- **注意**: ⚠️ 文件较大，拖放可能需要一些时间\n")
                else:
                    f.write(f"- **状态**: ✅ 文件存在\n")

                f.write("\n")
                f.write("---\n\n")

    print(f"✓ 清单已保存到: {output_file}")
    print(f"\n可以用以下命令查看:")
    print(f"  cat {output_file}")
    print(f"  或在文本编辑器中打开")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='生成缺失PDF的详细清单'
    )

    parser.add_argument(
        '--mapping-file',
        default='zotero_item_mapping.json',
        help='映射文件路径'
    )
    parser.add_argument(
        '--output',
        default='missing_pdfs_checklist.md',
        help='输出清单文件'
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

    generate_checklist(zot, args.mapping_file, args.output)

    print("\n完成!")
