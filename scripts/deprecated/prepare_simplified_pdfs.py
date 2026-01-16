#!/usr/bin/env python3
"""
为缺失的PDF创建简化命名的副本
格式: 001_文件名.pdf, 002_文件名.pdf...
同时在Zotero的Extra字段添加ref_id标记
"""

import os
import json
import re
import shutil
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


def sanitize_filename(filename):
    """清理文件名，移除特殊字符"""
    # 保留扩展名
    stem = Path(filename).stem
    ext = Path(filename).suffix

    # 移除或替换特殊字符
    # 保留：字母、数字、空格、下划线、连字符
    stem = re.sub(r'[^\w\s\-]', '', stem, flags=re.UNICODE)

    # 统一多个空格/下划线为单个
    stem = re.sub(r'[\s_]+', '_', stem)

    # 截断过长的文件名（保留前60个字符）
    if len(stem) > 60:
        stem = stem[:60]

    return f"{stem}{ext}"


def prepare_simplified_pdfs(zot, mapping_file, output_dir='pdfs_simplified', dry_run=False):
    """创建简化命名的PDF副本"""

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

        # 检查是否有附件
        children = zot.children(item_key)
        has_pdf = any(
            child['data'].get('contentType') == 'application/pdf'
            for child in children
        )

        if not has_pdf:
            missing_pdfs.append({
                'item_key': item_key,
                'title': title,
                'pdf_path': pdf_path,
                'collection': info['collection']
            })

    print(f"找到 {len(missing_pdfs)} 个缺少PDF的条目\n")

    if not missing_pdfs:
        print("所有条目都已有PDF附件！")
        return

    # 创建输出目录
    output_path = Path(output_dir)
    if not dry_run:
        output_path.mkdir(exist_ok=True)

    # 创建README
    readme_lines = [
        "# PDF附件添加指南\n",
        f"\n**总计：{len(missing_pdfs)} 个PDF需要添加**\n",
        "\n## 操作步骤\n",
        "\n1. 打开Zotero\n",
        "2. 在Zotero中搜索或筛选出有 `AttachID:` 标记的条目\n",
        "3. 对于每个条目：\n",
        "   - 查看Extra字段中的 `AttachID: 001` 编号\n",
        "   - 在本文件夹中找到对应的 `001_xxx.pdf` 文件\n",
        "   - 将PDF文件拖放到Zotero条目上\n",
        "4. 完成后删除本文件夹\n",
        "\n---\n\n"
    ]

    mapping_lines = ["## 文件映射表\n\n"]

    # 处理每个PDF
    print("正在处理PDF文件...\n")

    updated_items = 0

    for i, item in enumerate(missing_pdfs, 1):
        ref_id = f"{i:03d}"  # 001, 002, 003...
        item_key = item['item_key']
        pdf_path = item['pdf_path']
        title = item['title']
        collection = item['collection']

        # 清理文件名
        original_name = pdf_path.name
        clean_name = sanitize_filename(original_name)

        # 新文件名: 001_cleaned_name.pdf
        new_filename = f"{ref_id}_{clean_name}"
        new_path = output_path / new_filename

        title_short = title[:60] + '...' if len(title) > 60 else title

        print(f"[{i}/{len(missing_pdfs)}] {ref_id} - {title_short}")
        print(f"  原文件: {original_name}")
        print(f"  新文件: {new_filename}")

        # 添加到映射表
        mapping_lines.append(f"### {ref_id}. {title}\n\n")
        mapping_lines.append(f"- **集合**: {collection}\n")
        mapping_lines.append(f"- **PDF文件**: `{new_filename}`\n")
        mapping_lines.append(f"- **原文件**: `{original_name}`\n")
        mapping_lines.append("\n---\n\n")

        if dry_run:
            print(f"  [测试模式] 跳过复制")
        else:
            # 复制PDF文件
            try:
                shutil.copy2(pdf_path, new_path)
                print(f"  ✓ 已复制")
            except Exception as e:
                print(f"  ✗ 复制失败: {e}")

            # 更新Zotero条目的Extra字段
            try:
                item_data = zot.item(item_key)
                extra = item_data['data'].get('extra', '')

                # 添加AttachID标记
                if 'AttachID:' not in extra:
                    if extra:
                        extra += f"\nAttachID: {ref_id}"
                    else:
                        extra = f"AttachID: {ref_id}"

                    item_data['data']['extra'] = extra
                    zot.update_item(item_data)
                    print(f"  ✓ 已更新Zotero Extra字段")
                    updated_items += 1
                else:
                    print(f"  ⊙ Extra字段已有AttachID")

            except Exception as e:
                print(f"  ✗ 更新Extra字段失败: {e}")

        print()

    # 写入README
    if not dry_run:
        readme_path = output_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.writelines(readme_lines + mapping_lines)
        print(f"✓ README已保存到: {readme_path}")

    print(f"\n完成!")
    print(f"  处理文件数: {len(missing_pdfs)}")
    if not dry_run:
        print(f"  输出目录: {output_path.absolute()}")
        print(f"  更新条目数: {updated_items}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='为缺失PDF创建简化命名的副本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 测试模式（不复制文件，不更新Zotero）
  python3 prepare_simplified_pdfs.py --dry-run

  # 正式执行
  python3 prepare_simplified_pdfs.py

  # 指定输出目录
  python3 prepare_simplified_pdfs.py --output my_pdfs
        """
    )

    parser.add_argument(
        '--mapping-file',
        default='zotero_item_mapping.json',
        help='映射文件路径'
    )
    parser.add_argument(
        '--output',
        default='pdfs_simplified',
        help='输出目录'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='测试模式：不复制文件，不更新Zotero'
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

    prepare_simplified_pdfs(zot, args.mapping_file, args.output, args.dry_run)
