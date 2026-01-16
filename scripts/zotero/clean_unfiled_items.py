#!/usr/bin/env python3
"""
清理所有未分配集合的条目
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
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['library_id'], config['api_key'], config.get('library_type', 'user')
    else:
        print("错误: 找不到配置文件")
        exit(1)


if __name__ == '__main__':
    library_id, api_key, library_type = load_config()

    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})\n")
    except Exception as e:
        print(f"错误: {e}")
        exit(1)

    print("="*70)
    print("清理未分配集合的条目")
    print("="*70)

    # 获取所有条目
    print("\n正在获取所有条目...")
    all_items = zot.everything(zot.items())
    print(f"找到 {len(all_items)} 条记录")

    # 过滤出主条目（不是附件）
    main_items = []
    for item in all_items:
        if item['data'].get('itemType') != 'attachment':
            # 检查是否没有分配到集合
            collections = item['data'].get('collections', [])
            if not collections:
                main_items.append(item['key'])

    print(f"需要删除 {len(main_items)} 条未分配集合的文献\n")

    if not main_items:
        print("没有需要删除的条目")
        exit(0)

    # 确认
    confirm = input(f"确认删除这 {len(main_items)} 条文献? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("已取消")
        exit(0)

    # 批量删除
    print("\n开始删除...")
    batch_size = 50
    success_count = 0

    for i in range(0, len(main_items), batch_size):
        batch = main_items[i:i+batch_size]
        try:
            zot.delete_item(batch)
            success_count += len(batch)
            print(f"  已删除 {min(i+batch_size, len(main_items))}/{len(main_items)} 条文献")
        except Exception as e:
            print(f"  批次删除失败: {e}")

    print(f"\n完成! 成功删除 {success_count}/{len(main_items)} 条文献")
    print("\n现在可以重新运行导入脚本:")
    print("  python3 auto_import_zotero.py")
