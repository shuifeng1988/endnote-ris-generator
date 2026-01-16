#!/usr/bin/env python3
"""
检查Zotero中的集合和条目
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
    print("运行: pip install pyzotero")
    exit(1)


def load_config():
    """加载Zotero配置"""
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['library_id'], config['api_key'], config.get('library_type', 'user')
    else:
        print("错误: 找不到配置文件 .zotero_config.json")
        exit(1)


if __name__ == '__main__':
    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: 无法连接到Zotero API: {e}")
        exit(1)

    # 获取所有集合
    print("="*70)
    print("当前的集合")
    print("="*70)

    collections = zot.collections()

    if not collections:
        print("没有找到任何集合！")
        print("\n这就是为什么Zotero左侧没有显示分类。")
    else:
        print(f"找到 {len(collections)} 个集合：\n")
        for col in collections:
            name = col['data']['name']
            num_items = col['meta'].get('numItems', 0)
            print(f"  - {name}: {num_items} 条文献")

    # 获取所有条目
    print(f"\n{'='*70}")
    print("文库中的条目")
    print("="*70)

    items = zot.items(limit=100)
    print(f"找到至少 {len(items)} 条文献记录\n")

    # 检查条目是否分配到集合
    items_with_collections = 0
    items_without_collections = 0

    for item in items[:10]:  # 只检查前10个
        if item['data'].get('itemType') == 'attachment':
            continue

        title = item['data'].get('title', 'Untitled')[:60]
        colls = item['data'].get('collections', [])

        if colls:
            items_with_collections += 1
            print(f"✓ {title}... (在 {len(colls)} 个集合中)")
        else:
            items_without_collections += 1
            print(f"✗ {title}... (未分配到任何集合)")

    print(f"\n前10条记录统计:")
    print(f"  有集合: {items_with_collections}")
    print(f"  无集合: {items_without_collections}")

    if items_without_collections > 0:
        print(f"\n⚠️  问题发现: 文献没有被分配到集合中！")
        print(f"这就是为什么Zotero左侧没有显示分类。")
