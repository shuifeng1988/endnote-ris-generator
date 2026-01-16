#!/usr/bin/env python3
"""
JSON 格式自动修复工具 - 使用 AI 自动修复 JSON 格式错误
不需要手动查找规则，直接让大模型修复
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import argparse
import re


class JSONAutoFixer:
    """JSON 自动修复器（使用 AI）"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        初始化修复器

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        # 从环境变量或参数获取配置
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        self.base_url = base_url or os.getenv('BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model = model or os.getenv('MODEL', 'qwen-plus')

        if not self.api_key:
            raise ValueError("需要提供 API 密钥（通过参数或 LLM_API_KEY 环境变量）")

        # 初始化 OpenAI 客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            raise ImportError("需要安装 openai 库: pip install openai")

    def fix_json_file(self, input_file: str, output_file: str = None,
                      backup: bool = True) -> str:
        """
        修复 JSON 文件

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径（默认覆盖原文件）
            backup: 是否备份原文件

        Returns:
            修复后的文件路径
        """
        input_path = Path(input_file)

        if not input_path.exists():
            raise FileNotFoundError(f"文件不存在: {input_file}")

        # 读取文件内容
        print(f"读取文件: {input_file}")
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 尝试直接解析
        try:
            json.loads(content)
            print("✓ JSON 格式正确，无需修复")
            return input_file
        except json.JSONDecodeError as e:
            print(f"✗ JSON 格式错误: {e}")
            print(f"  位置: 行 {e.lineno}, 列 {e.colno}")

        # 使用 AI 修复
        print("\n使用 AI 修复 JSON 格式...")
        fixed_content = self._fix_with_ai(content, str(e))

        if fixed_content is None:
            print("✗ AI 修复失败")
            return None

        # 验证修复后的内容
        try:
            json.loads(fixed_content)
            print("✓ 修复后的 JSON 格式正确")
        except json.JSONDecodeError as e:
            print(f"✗ 修复后仍有错误: {e}")
            print("尝试再次修复...")
            fixed_content = self._fix_with_ai(fixed_content, str(e))

            if fixed_content is None:
                print("✗ 二次修复失败")
                return None

            try:
                json.loads(fixed_content)
                print("✓ 二次修复成功")
            except json.JSONDecodeError:
                print("✗ 无法修复此 JSON 文件")
                return None

        # 确定输出路径
        if output_file is None:
            output_path = input_path
            # 备份原文件
            if backup:
                backup_path = input_path.with_suffix(input_path.suffix + '.bak')
                print(f"备份原文件: {backup_path}")
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        else:
            output_path = Path(output_file)

        # 写入修复后的内容
        print(f"保存修复后的文件: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)

        return str(output_path)

    def _fix_with_ai(self, content: str, error_msg: str) -> Optional[str]:
        """
        使用 AI 修复 JSON

        Args:
            content: JSON 内容
            error_msg: 错误信息

        Returns:
            修复后的 JSON 内容，失败返回 None
        """
        # 如果内容太长，只发送前后部分
        max_length = 50000
        if len(content) > max_length:
            # 找到错误位置
            error_line = None
            match = re.search(r'line (\d+)', error_msg)
            if match:
                error_line = int(match.group(1))

            if error_line:
                # 发送错误位置附近的内容
                lines = content.split('\n')
                start = max(0, error_line - 100)
                end = min(len(lines), error_line + 100)
                content_to_send = '\n'.join(lines[start:end])
                context_info = f"\n\n注意：这是文件的第 {start+1} 到 {end+1} 行（共 {len(lines)} 行），错误在第 {error_line} 行附近。"
            else:
                # 发送开头和结尾
                content_to_send = content[:max_length//2] + "\n\n... [中间内容省略] ...\n\n" + content[-max_length//2:]
                context_info = "\n\n注意：文件内容过长，已省略中间部分。"
        else:
            content_to_send = content
            context_info = ""

        prompt = f"""请修复以下 JSON 格式错误。

错误信息：
{error_msg}

JSON 内容：
```json
{content_to_send}
```
{context_info}

要求：
1. 只返回修复后的完整 JSON 内容，不要有任何解释
2. 不要添加 markdown 代码块标记
3. 确保 JSON 格式完全正确
4. 保持原有数据结构和内容不变，只修复格式错误
5. 常见错误包括：
   - 缺少逗号或多余逗号
   - 引号不匹配
   - 括号不匹配
   - 非法字符
   - 转义字符错误

直接输出修复后的 JSON："""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个 JSON 格式修复专家。你只返回修复后的 JSON 内容，不添加任何解释或标记。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=60000
            )

            fixed_content = response.choices[0].message.content.strip()

            # 移除可能的 markdown 代码块标记
            fixed_content = re.sub(r'^```json\s*', '', fixed_content)
            fixed_content = re.sub(r'^```\s*', '', fixed_content)
            fixed_content = re.sub(r'\s*```$', '', fixed_content)

            return fixed_content

        except Exception as e:
            print(f"AI 调用失败: {e}")
            return None

    def fix_json_string(self, json_str: str) -> Optional[str]:
        """
        修复 JSON 字符串

        Args:
            json_str: JSON 字符串

        Returns:
            修复后的 JSON 字符串，失败返回 None
        """
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            return self._fix_with_ai(json_str, str(e))

    def validate_json_file(self, file_path: str) -> bool:
        """
        验证 JSON 文件格式

        Args:
            file_path: 文件路径

        Returns:
            是否有效
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError):
            return False


def load_env_file(env_file: str = '.env'):
    """
    加载 .env 文件

    Args:
        env_file: .env 文件路径
    """
    env_path = Path(env_file)
    if not env_path.exists():
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='使用 AI 自动修复 JSON 格式错误'
    )
    parser.add_argument(
        'input',
        help='输入的 JSON 文件路径'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径（默认覆盖原文件）'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不备份原文件'
    )
    parser.add_argument(
        '--api-key',
        help='API 密钥（也可通过 LLM_API_KEY 环境变量设置）'
    )
    parser.add_argument(
        '--base-url',
        help='API 基础 URL（也可通过 BASE_URL 环境变量设置）'
    )
    parser.add_argument(
        '--model',
        help='模型名称（也可通过 MODEL 环境变量设置）'
    )
    parser.add_argument(
        '--env-file',
        default='.env',
        help='.env 文件路径（默认: .env）'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("JSON 格式自动修复工具")
    print("=" * 60)
    print()

    # 加载 .env 文件
    load_env_file(args.env_file)

    try:
        fixer = JSONAutoFixer(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model
        )

        result = fixer.fix_json_file(
            args.input,
            args.output,
            backup=not args.no_backup
        )

        if result:
            print("\n" + "=" * 60)
            print("修复完成！")
            print("=" * 60)
            print(f"修复后的文件: {result}")

            # 验证
            if fixer.validate_json_file(result):
                print("✓ JSON 格式验证通过")
            else:
                print("✗ JSON 格式验证失败")
                return 1
        else:
            print("\n✗ 修复失败")
            return 1

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
