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






