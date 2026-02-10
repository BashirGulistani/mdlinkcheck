import concurrent.futures
import json
import os
import re
import time
import urllib.parse
import urllib.request

MD_EXTENSIONS = {".md", ".markdown", ".mdx"}

INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
REF_DEF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)\s*$")
REF_USE_RE = re.compile(r"\[([^\]]+)\]\[([^\]]+)\]")
AUTOLINK_RE = re.compile(r"<(https?://[^ >]+)>")


def _is_markdown(path):
    return os.path.splitext(path)[1].lower() in MD_EXTENSIONS

def _walk_markdown_files(root, include, exclude_substrings):
    candidates = []

    def allowed(p):
        norm = p.replace("\\", "/")
        for s in exclude_substrings:
            if s and s in norm:
                return False
        return True

    if include:
        for item in include:
            if os.path.isfile(item) and _is_markdown(item) and allowed(item):
                candidates.append(item)
            elif os.path.isdir(item) and allowed(item):
                for base, _, files in os.walk(item):
                    if not allowed(base):
                        continue
                    for f in files:
                        fp = os.path.join(base, f)
                        if _is_markdown(fp) and allowed(fp):
                            candidates.append(fp)




