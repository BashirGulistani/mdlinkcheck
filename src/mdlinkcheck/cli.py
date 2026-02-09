import argparse
import os
import sys
from .core import scan_paths, format_report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mdlinkcheck")
    parser.add_argument("root", nargs="?", default=".", help="Root directory to scan")
    parser.add_argument("--include", nargs="*", default=None, help="Only scan these paths (files or dirs) under root")
    parser.add_argument("--exclude", nargs="*", default=None, help="Exclude paths containing any of these substrings")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout seconds")
    parser.add_argument("--workers", type=int, default=20, help="Max concurrent checks")
    parser.add_argument("--user-agent", default="mdlinkcheck/0.1", help="HTTP user agent")
    parser.add_argument("--ignore", action="append", default=[], help="Ignore links containing this substring (repeatable)")
    parser.add_argument("--fail", action="store_true", help="Exit non-zero if broken links exist")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)

    include = None
    if args.include:
        include = [os.path.join(root, p) if not os.path.isabs(p) else p for p in args.include]

    exclude = args.exclude or []

    result = scan_paths(
        root=root,
        include=include,
        exclude_substrings=exclude,
        ignore_substrings=args.ignore,
        timeout=args.timeout,
        workers=args.workers,
        user_agent=args.user_agent,
    )

    out = format_report(result, as_json=args.json)
    sys.stdout.write(out)
    if out and not out.endswith("\n"):
        sys.stdout.write("\n")

    broken = result["summary"]["broken_count"]
    if args.fail and broken > 0:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
