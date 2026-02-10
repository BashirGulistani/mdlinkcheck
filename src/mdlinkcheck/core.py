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

def _looks_like_relative_path(url):
    if "://" in url:
        return False
    if url.startswith("/"):
        return True
    if url.startswith("./") or url.startswith("../"):
        return True
    if re.match(r"^[A-Za-z0-9_.-]+/.*", url):
        return True
    if re.match(r"^[A-Za-z0-9_.-]+\.(md|markdown|mdx|html|png|jpg|jpeg|gif|svg|pdf)$", url, re.I):
        return True
    return False

def extract_links(markdown_text):
    text = _strip_code_blocks(markdown_text)

    ref_defs = {}
    for line in text.splitlines():
        m = REF_DEF_RE.match(line)
        if m:
            key = m.group(1).strip().lower()
            ref_defs[key] = _normalize_link(m.group(2))

    found = []
    for m in INLINE_LINK_RE.finditer(text):
        found.append(_normalize_link(m.group(2)))

    for m in AUTOLINK_RE.finditer(text):
        found.append(_normalize_link(m.group(1)))

    for m in REF_USE_RE.finditer(text):
        key = m.group(2).strip().lower()
        if key in ref_defs:
            found.append(ref_defs[key])

    cleaned = []
    for u in found:
        if not u:
            continue
        if u.startswith("!"):
            continue
        cleaned.append(u)
    return cleaned

def _resolve_local_path(md_file, url_base):
    url_base = url_base.strip()
    if url_base.startswith("/"):
        return None
    rel = urllib.parse.unquote(url_base)
    rel = rel.split("?", 1)[0]
    here = os.path.dirname(md_file)
    return os.path.normpath(os.path.join(here, rel))

def _check_http(url, timeout, user_agent):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = getattr(r, "status", None) or 200
            if 200 <= code < 400:
                return True, code, None
            return False, code, None
    except Exception as e:
        return False, None, str(e)

def _check_local(md_file, url):
    base, _ = _split_anchor(url)
    if not base:
        return True, None, None
    target = _resolve_local_path(md_file, base)
    if target is None:
        return True, None, None
    return os.path.exists(target), None, None



