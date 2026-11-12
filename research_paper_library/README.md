# ScholarGraph: Research Paper Library & Knowledge Graph

ScholarGraph is an interactive, web-based platform engineered to help researchers, academics, and students organize, extract, search, manage, and visually explore research papers in one unified workspace.

Instead of manually reading and cataloging every academic PDF, users can upload PDF papers to have the system automatically extract metadata (title, authors, abstract, publication year, DOI, and bibliographic references), assign domain topics and statistical tags, construct cross-paper citation links, and visualize connections between research papers, authors, and topics in an interactive force-directed Knowledge Graph.

---

## 🌟 Key Features

1. **Upload Research Papers**
   - Single and batch drag-and-drop PDF upload zone.
   - Upload file size validation up to 32MB per file.
   - Cryptographic SHA-256 hash calculation to prevent accidental duplicate uploads.

2. **Automated Paper Information Extraction**
   - **Title Detection**: Multi-stage heuristics combining embedded PDF metadata, dominant layout headers, and filename fallbacks.
   - **Author Extraction**: Cleans noise, institutional affiliations, and emails to extract individual author names and maintain authorship ordering.
   - **Abstract Extraction**: Regex boundary detection detecting section starts (`Abstract`, `Summary`) and end markers (`1. Introduction`, `Keywords`).
   - **Publication Metadata**: Automatically captures publication year and DOI links.
   - **Reference Extraction**: Parses numbered (`[1]`, `1.`) and author-year citations from the bibliography.

3. **Automatic Tags and Topic Categorization**
   - Hybrid NLP extraction combining explicit author keywords, computer science taxonomy ontology mapping, and statistical bi-gram / TF keyphrase scoring.
   - Confidence scoring for auto-assigned tags.
   - Support for user-defined custom tags.

4. **Instant Search and Multi-Facet Filtering**
   - Real-time debounced full-text search across titles, abstracts, authors, topics, and DOIs.
   - Faceted dropdown filters for Topic, Author, Publication Year, and Extraction Status.
   - Sorting by Date Added, Publication Year, Title (A-Z), and File Size.

5. **Manage Paper Details**
   - Deep inspection page for each paper.
   - In-place editing of title, authors, year, DOI, and abstract.
   - Inline tag creation and deletion.
   - Reference management: add new citations, delete citations, and view auto-linked library citations.
   - Embedded PDF reader directly in the browser.
   - Cascading deletion of paper records and stored files.

6. **Interactive Knowledge Graph**
   - Visual network rendered with **Vis.js Network**.
   - **Nodes**: Papers (Blue), Authors (Green), Topics (Amber).
   - **Edges**: Authorship, Citations (Red directional arrows), Co-authorship (Green dashed), Topic classification.
   - **Interactive Controls**: Dynamic physics force simulation, freeze/unfreeze physics, search-to-focus camera pan, node type filtering, edge type filtering, and PNG export.
   - **Slide-out Node Inspector**: Click any node to inspect all connected papers, authors, and topics.

7. **System Activity Audit Log**
   - Tracks all system actions: `UPLOAD`, `EDIT`, `TAG_ADD`, `TAG_REMOVE`, `REF_ADD`, `REF_DELETE`, `DELETE`, `RE_EXTRACT`.
   - Records timestamp, action type, user, target paper, and modifications.
   - Filterable by action and search keywords.
   - One-click CSV export (`/api/activity/export`).

8. **Robust Error Handling & Edge Cases**
   - **Corrupted / Invalid PDFs**: Detected and flagged with informative errors without crashing.
   - **Empty (0-byte) Files**: Gracefully rejected.
   - **Scanned Documents**: Identifies PDFs lacking text layers and flags them as `Scanned / Needs OCR`, providing fallback options.
   - **Duplicate Detection**: Flags identical uploads and provides a direct link to the existing paper.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ / 3.15, [Flask](https://flask.palletsprojects.com/)
- **PDF Extraction**: [pypdf](https://pypdf.readthedocs.io/), custom layout heuristics
- **Sample Generation**: [ReportLab](https://www.reportlab.com/)
- **Database**: [SQLite 3](https://sqlite.org/) with foreign keys (`PRAGMA foreign_keys = ON;`)
- **Frontend**: Semantic HTML5, CSS3 (Light/Dark themes), Modern Vanilla JavaScript (ES6)
- **Graph Visualization**: [Vis.js Network](https://visjs.github.io/vis-network/docs/network/) (offline standalone bundle included)

---

## 📂 Project Structure

```
research_paper_library/
├── app.py                     # Main Flask Application & REST API
├── config.py                  # App configuration & paths
├── database.py                # SQLite schema, queries, activity logging
├── extractor.py               # Robust PDF text & metadata extraction engine
├── nlp_tagger.py              # Automatic keyword, topic, and taxonomy engine
├── graph_builder.py          # Vis.js node and edge network constructor
├── sample_data_generator.py   # Script to generate realistic sample academic papers
├── test_app.py                # 11-step automated unit test suite
├── requirements.txt           # Python package dependencies
├── README.md                  # Documentation and quickstart
├── DELIVERABLE_1_CONTEXT.md   # Deliverable 1: Context Document
├── DELIVERABLE_2_PLAN_AND_PROMPTS.md # Deliverable 2: Architecture & Plan
├── DELIVERABLE_3_USER_PROMPTS.md     # Deliverable 3: User Prompts & Reflection
├── uploads/                   # Stored uploaded PDF papers
├── samples/                   # Pre-generated sample research papers
├── templates/
│   ├── base.html              # Layout header, navigation, upload modal, toasts
│   ├── index.html             # Dashboard, stats, paper cards, filters, search
│   ├── graph.html             # Fullscreen Knowledge Graph explorer
│   ├── paper_detail.html      # Deep paper inspector & PDF viewer
│   ├── activity.html          # Audit log table and CSV export
│   ├── 404.html               # 404 error page
│   └── 500.html               # 500 error page
└── static/
    ├── css/
    │   ├── style.css          # Main styling, cards, modals, themes
    │   └── graph.css          # Knowledge graph specific visual styling
    ├── js/
    │   ├── app.js             # Global utilities, theme toggle, toasts
    │   ├── papers.js          # Library search, filter, edit modal
    │   ├── upload.js          # Drag & drop upload, validation, progress
    │   ├── graph.js           # Vis.js network, physics, node inspector
    │   ├── paper_detail.js    # Detail page, tag and reference managers
    │   └── activity.js        # Activity log table and filter
    └── vendor/
        └── vis-network.min.js # Bundled offline Vis.js network library
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. In your terminal, run:

```bash
python -m pip install -r requirements.txt
```

### 2. Generate Sample Research Papers
Generate realistic sample research papers (covering Graph Neural Networks, Semantic Search, Approximate Nearest Neighbor Benchmarks, Automated Knowledge Extraction, and LLM Robustness) along with edge-case test files:

```bash
python sample_data_generator.py
```

### 3. Run the Automated Tests
Verify that all 11 unit tests pass:

```bash
python test_app.py
```

### 4. Launch the Web Application
Start the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📖 Walkthrough of Main Features

### 1. Seeding Sample Papers
- On the dashboard, click **"Import Sample Papers"**.
- 5 realistic papers with interconnected citations and authors will be automatically indexed into your library!

### 2. Uploading Your Own Research Papers
- Click **"Upload Papers"** in the top navigation bar.
- Drag and drop one or multiple PDF papers into the upload box.
- The system checks file size (max 32MB), calculates the SHA-256 hash to reject duplicate uploads, parses the title, authors, abstract, and references, and assigns auto-topics with confidence scores.

### 3. Searching and Filtering
- Type any keyword in the search bar (e.g. `neural`, `transformer`, `semantic`) to filter results in real-time.
- Filter by topic (e.g. `Machine Learning`, `Knowledge Graphs`), by author, by publication year, or by extraction status.
- Sort by newest publication year, date added, or title.

### 4. Managing Paper Details
- Click **"Details"** on any paper card.
- View the paper metadata, abstract, and embedded live PDF document.
- Add or remove custom tags.
- Add or delete citation references.
- Click **"Edit Metadata"** to update titles, authors, years, or abstracts manually.
- Click **"Re-Extract Text"** if you wish to re-run the extraction heuristics.

### 5. Exploring the Interactive Knowledge Graph
- Click **"Knowledge Graph"** in the navigation bar.
- See research papers (blue), authors (green), and topics (amber) arranged dynamically.
- Click on any node to open the **Node Inspector** sidebar, revealing all connected papers, co-authors, and citations.
- Use the search bar to locate and zoom directly to any node.
- Toggle node and edge visibility using the toolbar filters.
- Click **"Export PNG"** to save a snapshot of the graph canvas.

### 6. Activity Log and Audit Trail
- Click **"Activity Log"** in the navigation bar.
- Review all operations with timestamps, action categories, user identities, and modification logs.
- Click **"Export Log (CSV)"** to download the audit trail as a spreadsheet.

---

## 🧪 Testing Edge Cases

The application includes dedicated error handling tests:
1. **Empty File (`corrupt_empty_sample.pdf`)**: Uploading a 0-byte file reports an empty document error and rejects the upload safely.
2. **Corrupted File (`corrupt_invalid_bytes.pdf`)**: Uploading invalid non-PDF data reports an invalid byte stream error without crashing the server.
3. **Scanned PDF (`scanned_image_sample.pdf`)**: Uploading an image-only PDF flags the document as `Scanned / Needs OCR`, allowing manual editing.
4. **Duplicate File**: Uploading a PDF that was already uploaded is immediately detected by SHA-256 hash comparison and flagged with a link to the existing document.

---

## 📄 License
Academic and educational use.
