import unittest
from mdlinkcheck.core import extract_links

class TestExtractLinks(unittest.TestCase):
    def test_inline(self):
        md = "See [a](https://example.com) and [b](docs/guide.md)."
        links = extract_links(md)
        self.assertIn("https://example.com", links)
        self.assertIn("docs/guide.md", links)


    def test_reference(self):
        md = """
Text [x][ref].

[ref]: https://example.com/docs
"""
        links = extract_links(md)
        self.assertIn("https://example.com/docs", links)

    def test_autolink(self):
        md = "Visit <https://example.com> now."
        links = extract_links(md)
        self.assertEqual(links, ["https://example.com"])

    def test_ignores_code_blocks(self):
        md = """
```bash
echo "[x](https://broken.example)"
