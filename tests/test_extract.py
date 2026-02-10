import unittest
from mdlinkcheck.core import extract_links

class TestExtractLinks(unittest.TestCase):
    def test_inline(self):
        md = "See [a](https://example.com) and [b](docs/guide.md)."
        links = extract_links(md)
        self.assertIn("https://example.com", links)
        self.assertIn("docs/guide.md", links)


