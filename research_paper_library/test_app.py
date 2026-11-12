import os
import unittest
import json
import io
import tempfile
import sqlite3

# Import app modules
import config
from app import app
from database import init_db, get_db, check_duplicate_paper, get_paper_by_id
from extractor import process_pdf_file, compute_file_hash
from nlp_tagger import generate_tags_and_topics
from graph_builder import build_knowledge_graph

class TestResearchPaperLibrary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.sample_dir = os.path.join(config.BASE_DIR, "samples")

    def test_01_database_initialization(self):
        """Verifies database tables and schema creation."""
        init_db()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        required_tables = ["papers", "authors", "paper_authors", "topics", "paper_topics", "paper_references", "activity_logs"]
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Expected table '{tbl}' was not created.")

    def test_02_pdf_extraction_real_paper(self):
        """Verifies PDF extraction pipeline on valid sample paper."""
        pdf_path = os.path.join(self.sample_dir, "attention_gnn_discovery.pdf")
        self.assertTrue(os.path.exists(pdf_path), "Sample PDF should exist.")

        extracted = process_pdf_file(pdf_path, "attention_gnn_discovery.pdf")
        self.assertEqual(extracted["status"], "success")
        self.assertIn("Attention-Based Graph Neural Networks", extracted["title"])
        self.assertIn("Alexander Vance", extracted["authors"])
        self.assertIn("Elena Rostova", extracted["authors"])
        self.assertEqual(extracted["publication_year"], 2024)
        self.assertIsNotNone(extracted["doi"])
        self.assertTrue(len(extracted["references"]) >= 2)

    def test_03_empty_pdf_error_handling(self):
        """Verifies graceful handling of empty (0-byte) files."""
        pdf_path = os.path.join(self.sample_dir, "corrupt_empty_sample.pdf")
        extracted = process_pdf_file(pdf_path, "corrupt_empty_sample.pdf")
        self.assertEqual(extracted["status"], "failed")
        self.assertIn("empty", extracted["error"].lower())

    def test_04_corrupt_pdf_error_handling(self):
        """Verifies graceful handling of corrupt binary bytes."""
        pdf_path = os.path.join(self.sample_dir, "corrupt_invalid_bytes.pdf")
        extracted = process_pdf_file(pdf_path, "corrupt_invalid_bytes.pdf")
        self.assertEqual(extracted["status"], "failed")
        self.assertIn("invalid or corrupt", extracted["error"].lower())

    def test_05_scanned_pdf_detection(self):
        """Verifies detection of scanned documents without extractable text."""
        pdf_path = os.path.join(self.sample_dir, "scanned_image_sample.pdf")
        extracted = process_pdf_file(pdf_path, "scanned_image_sample.pdf")
        self.assertEqual(extracted["status"], "scanned")
        self.assertIn("scanned", extracted["notes"].lower())

    def test_06_nlp_tagger_generation(self):
        """Verifies automatic keyword and topic extraction."""
        title = "Attention-Based Graph Neural Networks for Knowledge Discovery"
        abstract = "Graph Neural Networks (GNNs) have emerged as a dominant paradigm for modeling relational structures and complex networks with multi-head self-attention."
        topics = generate_tags_and_topics(title, abstract, title + " " + abstract)

        topic_names = [t["name"] for t in topics]
        self.assertTrue(any("Graph" in t or "Attention" in t or "Machine Learning" in t for t in topic_names))

    def test_07_api_upload_and_duplicate_prevention(self):
        """Verifies upload API and SHA-256 duplicate rejection."""
        # Create a unique test PDF buffer to guarantee clean state regardless of prior seeding
        import time
        from reportlab.pdfgen import canvas
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        unique_mark = f"Unique Test Document {time.time()}"
        p.drawString(100, 750, unique_mark)
        p.drawString(100, 730, "Author: Test Author")
        p.drawString(100, 710, "Abstract: This is a unique test abstract for duplicate testing.")
        p.save()
        pdf_bytes = buffer.getvalue()

        # First upload -> should succeed
        res1 = self.client.post(
            "/api/papers/upload",
            data={"files": (io.BytesIO(pdf_bytes), "test_unique_doc.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.data)
        self.assertEqual(data1["results"][0]["status"], "success")
        paper_id = data1["results"][0]["id"]

        # Second upload of the EXACT same file -> must detect duplicate
        res2 = self.client.post(
            "/api/papers/upload",
            data={"files": (io.BytesIO(pdf_bytes), "test_unique_doc.pdf")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res2.status_code, 200)
        data2 = json.loads(res2.data)
        self.assertEqual(data2["results"][0]["status"], "duplicate")
        self.assertEqual(data2["results"][0]["existing_id"], paper_id)

    def test_08_api_search_and_filter(self):
        """Verifies full-text search across titles and authors."""
        res = self.client.get("/api/papers?search=semantic")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(len(data["papers"]) >= 1)

    def test_09_api_edit_paper(self):
        """Verifies updating paper details and activity audit logging."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM papers LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row, "At least one paper should exist.")
        p_id = row[0]

        res = self.client.put(
            f"/api/papers/{p_id}",
            json={
                "title": "Scalable Semantic Search Using Vector Embeddings (Edited Edition)",
                "authors": "Elena Rostova, Alexander Vance, Marcus Thorne",
                "publication_year": 2025,
                "doi": "10.1016/j.jocs.2023.102145",
                "abstract": "Updated empirical findings."
            }
        )
        self.assertEqual(res.status_code, 200)

        paper = get_paper_by_id(p_id)
        self.assertEqual(paper["title"], "Scalable Semantic Search Using Vector Embeddings (Edited Edition)")
        self.assertEqual(paper["publication_year"], 2025)

    def test_10_api_knowledge_graph_data(self):
        """Verifies knowledge graph structure generation."""
        res = self.client.get("/api/graph/data")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertIn("metrics", data)
        self.assertTrue(len(data["nodes"]) > 0)

    def test_11_api_activity_log_and_export(self):
        """Verifies activity log tracking and CSV export."""
        res_log = self.client.get("/api/activity")
        self.assertEqual(res_log.status_code, 200)
        logs = json.loads(res_log.data)["activities"]
        self.assertTrue(len(logs) > 0)

        res_csv = self.client.get("/api/activity/export")
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn("text/csv", res_csv.content_type)
        self.assertIn("Timestamp", res_csv.data.decode("utf-8"))

if __name__ == "__main__":
    unittest.main()
