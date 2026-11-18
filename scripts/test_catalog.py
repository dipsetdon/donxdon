import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import catalog


class CatalogTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        shutil.copytree(catalog.ROOT / "public", self.root / "public")
        (self.root / "catalog").mkdir()
        (self.root / "media").mkdir()
        catalog.catalog_path(self.root).write_text("[]\n", encoding="utf-8")
        self.record = dict(operation="add_or_update", product_id="sample", name="QA sample",
                           price="22.1", category="Tees", description="<test text>")

    def test_check_is_read_only(self):
        self.assertEqual(catalog.update_catalog(self.root, {"operation": "check"}), [])
        self.assertEqual(catalog.catalog_path(self.root).read_text(), "[]\n")

    def test_create_update_build_remove(self):
        data = catalog.update_catalog(self.root, self.record)
        self.assertEqual(data[0]["price_cents"], 2210)
        self.assertEqual(data[0]["description"], "<test text>")
        self.assertEqual(catalog.update_catalog(self.root, {**self.record, "price": "99"})[0]["price_cents"], 9900)
        self.assertEqual(len(catalog.build(self.root, self.root / "_site")), 1)
        self.assertTrue((self.root / "_site" / "catalog.json").is_file())
        self.assertEqual(catalog.update_catalog(self.root, {"operation": "remove", "product_id": "sample"}), [])
        self.assertEqual(catalog.build(self.root, self.root / "_site"), [])

    def test_rejects_bad_price_unsafe_photo_and_invalid_type(self):
        for invalid in ({"price": "10.222"}, {"photo": "../file.png"}, {"category": "invalid"}, {"name": ""}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                catalog.update_catalog(self.root, {**self.record, **invalid})
        (self.root / "media" / "fake.png").write_text("<html>")
        with self.assertRaises(ValueError):
            catalog.update_catalog(self.root, {**self.record, "photo": "fake.png"})
        self.assertEqual(catalog.read_catalog(self.root), [])

    def test_rejects_duplicate_ids_and_wrong_build_path(self):
        catalog.update_catalog(self.root, self.record)
        file = catalog.catalog_path(self.root)
        import json
        records = json.loads(file.read_text())
        file.write_text(json.dumps(records * 2))
        with self.assertRaisesRegex(ValueError, "unique"):
            catalog.read_catalog(self.root)
        file.write_text("[]")
        with self.assertRaisesRegex(ValueError, "Build output"):
            catalog.build(self.root, self.root / "public")
