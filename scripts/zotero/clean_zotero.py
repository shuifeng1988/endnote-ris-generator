#!/usr/bin/env python3
"""
清理Zotero集合 - 删除测试导入的数据
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
        print("请先运行 auto_import_zotero.py 设置API凭证")
        exit(1)


def list_collections(zot):
    """列出所有集合"""
    collections = zot.collections()

    print(f"\n{'='*70}")
    print(f"当前的集合列表")
    print(f"{'='*70}\n")

    if not collections:
        print("没有找到任何集合")
        return []

    collection_map = {}
    for i, col in enumerate(collections, 1):
        name = col['data']['name']
        key = col['key']
        num_items = col['meta'].get('numItems', 0)
        collection_map[str(i)] = {'name': name, 'key': key, 'num_items': num_items}
        print(f"{i}. {name} ({num_items} 条文献)")

    return collection_map


def delete_collection(zot, collection_key, collection_name):
    """删除集合及其所有条目"""
    try:
        # 获取集合中的所有条目
        items = zot.collection_items(collection_key)

        if items:
            print(f"  找到 {len(items)} 条文献")

            # 删除所有条目
            item_keys = []
            for item in items:
                try:
                    if isinstance(item, dict) and 'key' in item:
                        item_keys.append(item['key'])
                    elif isinstance(item, str):
                        # 有时API可能直接返回key字符串
                        item_keys.append(item)
                except Exception as e:
                    print(f"    警告: 跳过无效条目: {e}")
                    continue

            if item_keys:
                # 分批删除（API限制每次50个）
                batch_size = 50
                for i in range(0, len(item_keys), batch_size):
                    batch = item_keys[i:i+batch_size]
                    try:
                        zot.delete_item(batch)
                        print(f"  已删除 {min(i+batch_size, len(item_keys))}/{len(item_keys)} 条文献")
                    except Exception as e:
                        print(f"    警告: 批次删除失败: {e}")

        # 删除集合
        zot.delete_collection(collection_key)
        print(f"  ✓ 已删除集合: {collection_name}")
        return True

    except Exception as e:
        print(f"  ✗ 删除失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def clean_zotero_interactive(zot):
    """交互式清理"""
    collection_map = list_collections(zot)

    if not collection_map:
        return

    print(f"\n{'='*70}")
    print("选择操作")
    print(f"{'='*70}\n")
    print("1. 删除特定集合")
    print("2. 删除所有测试集合（Multi-Omics, Drug-Screening等）")
    print("3. 删除所有集合（危险！）")
    print("0. 取消")

    choice = input("\n请选择 [0-3]: ").strip()

    if choice == '0':
        print("已取消")
        return

    elif choice == '1':
        # 删除特定集合
        print("\n输入要删除的集合编号（多个用逗号分隔，如: 1,3,5）")
        numbers = input("编号: ").strip()

        if not numbers:
            print("已取消")
            return

        # 解析编号
        try:
            indices = [n.strip() for n in numbers.split(',')]
            to_delete = [collection_map[n] for n in indices if n in collection_map]
        except:
            print("输入格式错误")
            return

        if not to_delete:
            print("没有有效的集合编号")
            return

        # 确认
        print(f"\n将删除以下集合:")
        for col in to_delete:
            print(f"  - {col['name']} ({col['num_items']} 条文献)")

        confirm = input("\n确认删除? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("已取消")
            return

        # 执行删除
        print(f"\n{'='*70}")
        print("开始删除...")
        print(f"{'='*70}\n")

        for col in to_delete:
            print(f"正在删除: {col['name']}")
            delete_collection(zot, col['key'], col['name'])

    elif choice == '2':
        # 删除测试集合
        test_collections = [
            'Multi-Omics', 'Drug-Screening', 'Single-Cell-Analysis',
            'AI-Biomedical-Agents', 'Foundation-Models-Genomics',
            'Genetic-Evolution', 'Genome-Regulatory-Models',
            'Perturbation-Response', 'Spatial-Omics',
            'Virtual-Cell-Review', '遗传进化', '药物筛选',
            '虚拟细胞，综述，生物大模型'
        ]

        to_delete = [col for col in collection_map.values()
                     if col['name'] in test_collections]

        if not to_delete:
            print("没有找到测试集合")
            return

        print(f"\n将删除以下测试集合:")
        total_items = 0
        for col in to_delete:
            print(f"  - {col['name']} ({col['num_items']} 条文献)")
            total_items += col['num_items']
        print(f"\n总计: {len(to_delete)} 个集合, {total_items} 条文献")

        confirm = input("\n确认删除? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("已取消")
            return

        # 执行删除
        print(f"\n{'='*70}")
        print("开始删除...")
        print(f"{'='*70}\n")

        success_count = 0
        for col in to_delete:
            print(f"正在删除: {col['name']}")
            if delete_collection(zot, col['key'], col['name']):
                success_count += 1

        print(f"\n完成! 成功删除 {success_count}/{len(to_delete)} 个集合")

    elif choice == '3':
        # 删除所有集合
        print(f"\n⚠️  警告: 这将删除所有集合和文献！")

        total_items = sum(col['num_items'] for col in collection_map.values())
        print(f"总计: {len(collection_map)} 个集合, {total_items} 条文献")

        confirm = input("\n确认删除所有? 输入 'DELETE ALL' 确认: ").strip()
        if confirm != 'DELETE ALL':
            print("已取消")
            return

        # 执行删除
        print(f"\n{'='*70}")
        print("开始删除所有集合...")
        print(f"{'='*70}\n")

        for col in collection_map.values():
            print(f"正在删除: {col['name']}")
            delete_collection(zot, col['key'], col['name'])

        print(f"\n完成! 已删除所有集合")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='清理Zotero测试数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式清理
  python3 clean_zotero.py

  # 直接删除所有测试集合（非交互）
  python3 clean_zotero.py --auto-clean
        """
    )

    parser.add_argument(
        '--auto-clean',
        action='store_true',
        help='自动删除所有测试集合（无需确认）'
    )

    args = parser.parse_args()

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 连接Zotero
    try:
        zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})")
    except Exception as e:
        print(f"\n错误: 无法连接到Zotero API")
        print(f"详情: {e}")
        exit(1)

    if args.auto_clean:
        # 自动删除测试集合
        collections = zot.collections()
        test_collections = [
            'Multi-Omics', 'Drug-Screening', 'Single-Cell-Analysis',
            'AI-Biomedical-Agents', 'Foundation-Models-Genomics',
            'Genetic-Evolution', 'Genome-Regulatory-Models',
            'Perturbation-Response', 'Spatial-Omics',
            'Virtual-Cell-Review', '遗传进化', '药物筛选',
            '虚拟细胞，综述，生物大模型',
            # 新的分类
            'Uncategorized', 'ai_agents_biomedical', 'drug_screening',
            'gene_regulation_networks', 'genomic_adaptation', 'models',
            'multi_omics', 'mutli_omics', 'single_cell_analysis', 'virtual_cells'
        ]

        to_delete = []
        for col in collections:
            try:
                if isinstance(col, dict) and 'data' in col:
                    name = col['data']['name']
                    if name in test_collections:
                        to_delete.append(col)
            except Exception as e:
                print(f"警告: 跳过无效集合: {e}")
                continue

        if not to_delete:
            print("没有找到测试集合")
            exit(0)

        print(f"\n自动删除 {len(to_delete)} 个测试集合...")

        success_count = 0
        for col in to_delete:
            try:
                name = col['data']['name']
                key = col['key']
                print(f"正在删除: {name}")
                if delete_collection(zot, key, name):
                    success_count += 1
            except Exception as e:
                print(f"  ✗ 删除失败: {e}")

        print(f"\n完成! 成功删除 {success_count}/{len(to_delete)} 个集合")
    else:
        # 交互式模式
        clean_zotero_interactive(zot)
