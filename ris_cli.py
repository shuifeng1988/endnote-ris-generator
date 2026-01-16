#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RIS Tools - Unified CLI Entry Point

Main commands:
  fix         Fix RIS files for EndNote compatibility
  diagnose    Diagnose RIS file issues
  merge       Merge multiple RIS files
  organize    Organize RIS files by category
  validate    Validate RIS output

Usage:
  python ris_cli.py fix [--ai] [options]
  python ris_cli.py diagnose <file>
  python ris_cli.py merge [options]
  python ris_cli.py organize [options]
  python ris_cli.py validate [options]

For detailed help on each command:
  python ris_cli.py fix --help
  python ris_cli.py diagnose --help
"""

import sys
import argparse
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts" / "ris_tools"))


def main():
    parser = argparse.ArgumentParser(
        description="RIS Tools - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Fix command
    fix_parser = subparsers.add_parser(
        'fix',
        help='Fix RIS files for EndNote compatibility'
    )
    fix_parser.add_argument(
        '--ai',
        action='store_true',
        help='Use AI to fix JSON/RIS issues'
    )

    # Diagnose command
    diagnose_parser = subparsers.add_parser(
        'diagnose',
        help='Diagnose RIS file issues'
    )

    # Merge command
    merge_parser = subparsers.add_parser(
        'merge',
        help='Merge multiple RIS files'
    )

    # Organize command
    organize_parser = subparsers.add_parser(
        'organize',
        help='Organize RIS files by category'
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate RIS output'
    )

    # Parse known args to allow passing through to subscripts
    args, remaining = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate script
    if args.command == 'fix':
        if args.ai:
            from fix_json_with_ai import main as fix_main
        else:
            from fix_ris_for_endnote import main as fix_main

        sys.argv = [sys.argv[0]] + remaining
        return fix_main()

    elif args.command == 'diagnose':
        from diagnose_ris import main as diagnose_main
        sys.argv = [sys.argv[0]] + remaining
        return diagnose_main()

    elif args.command == 'merge':
        from merge_ris_for_import import main as merge_main
        sys.argv = [sys.argv[0]] + remaining
        return merge_main()

    elif args.command == 'organize':
        from organize_ris_by_category import main as organize_main
        sys.argv = [sys.argv[0]] + remaining
        return organize_main()

    elif args.command == 'validate':
        from validate_output import main as validate_main
        sys.argv = [sys.argv[0]] + remaining
        return validate_main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
