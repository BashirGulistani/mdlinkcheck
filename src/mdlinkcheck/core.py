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

    else:
        for base, _, files in os.walk(root):
            if not allowed(base):
                continue
            for f in files:
                fp = os.path.join(base, f)
                if _is_markdown(fp) and allowed(fp):
                    candidates.append(fp)

    candidates.sort()
    return candidates


def _read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")

def _strip_code_blocks(text):
    lines = text.splitlines(True)
    out = []
    fence = None
    for line in lines:
        m = re.match(r"^\s*(```+|~~~+)", line)
        if m:
            token = m.group(1)
            if fence is None:
                fence = token
            else:
                if token.startswith(fence[:3]):
                    fence = None
            out.append("\n")
            continue
        if fence is not None:
            out.append("\n")
        else:
            out.append(line)
    return "".join(out)

def _normalize_link(raw):
    s = raw.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    s = s.replace("&amp;", "&")
    return s

def _split_anchor(url):
    if "#" in url:
        base, frag = url.split("#", 1)
        return base, frag
    return url, ""

def _is_http(url):
    u = url.lower()
    return u.startswith("http://") or u.startswith("https://")

def _is_mailto(url):
    return url.lower().startswith("mailto:")

def _is_tel(url):
    return url.lower().startswith("tel:")

def _is_fragment_only(url):
    return url.strip().startswith("#")

def _is_data(url):
    return url.lower().startswith("data:")



