import unittest

from app.services.ingestion_service import build_collection_name, chunk_text, clean_text


class CompanyRagServiceTests(unittest.TestCase):
    def test_build_collection_name(self):
        self.assertEqual(build_collection_name("Google"), "google_collection")
        self.assertEqual(build_collection_name("TCS"), "tcs_collection")

    def test_clean_text_and_chunking(self):
        raw = "  This is a sample document.   It has repeated spaces.\n\nAnother paragraph.  "
        cleaned = clean_text(raw)
        self.assertIn("This is a sample document.", cleaned)
        self.assertNotIn("  ", cleaned)

        chunks = chunk_text(cleaned, size=6, overlap=2)
        self.assertGreaterEqual(len(chunks), 1)


if __name__ == "__main__":
    unittest.main()
