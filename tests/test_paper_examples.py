import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io

from scripts.fetch_paper_examples import fetch_examples

ROOT = Path(__file__).resolve().parents[1]


class ExampleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.media = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr" and attrs.get("id", "").startswith("sample-"):
            self.rows.append(attrs["id"])
        if tag in ("source", "img") and attrs.get("src", "").startswith("assets/examples/"):
            self.media.append(attrs["src"].removeprefix("assets/"))


class PaperExamplesTest(unittest.TestCase):
    def test_all_five_examples_have_pinned_media(self):
        parser = ExampleParser()
        parser.feed((ROOT / "paper_site/index.html").read_text())
        self.assertEqual(parser.rows, [f"sample-{i}" for i in range(1, 6)])
        manifest = json.loads((ROOT / "paper_site/examples-media.json").read_text())
        self.assertRegex(manifest["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(set(parser.media), {item["path"] for item in manifest["assets"]})
        self.assertEqual(len(parser.media), 11)

    def test_download_rejects_corrupted_media(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "media.json"
            manifest.write_text(json.dumps({"repository": "owner/demo", "revision": "a" * 40,
                "assets": [{"path": "examples/clip.mp4", "sha256": hashlib.sha256(b"expected").hexdigest()}]}))
            with patch("scripts.fetch_paper_examples.urlopen", return_value=io.BytesIO(b"corrupted")):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    fetch_examples(manifest, root / "assets")
            self.assertFalse((root / "assets/examples/clip.mp4").exists())


if __name__ == "__main__":
    unittest.main()
