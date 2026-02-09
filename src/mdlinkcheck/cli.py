import argparse
import os
import sys
from .core import scan_paths, format_report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mdlinkcheck")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan")
    parser.add_argument("--include", nargs="*", default=None, help="Only scan these paths (files or dirs) under root")
    parser.add_argument("--exclude", nargs="*", default=None, help="Exclude paths containing any of these substrings")
