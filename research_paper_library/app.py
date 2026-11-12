import os
import csv
import io
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, send_from_directory,
    Response, redirect, url_for, flash
)
from werkzeug.utils import secure_filename

import config
from database import (
    init_db, get_db, log_activity, get_paper_by_id,
    check_duplicate_paper, link_citation_references
)
from extractor import process_pdf_file
from nlp_tagger import generate_tags_and_topics
from graph_builder import build_knowledge_graph

app = Flask(__name__)
app.config.from_object(config)

# Initialize database tables on app startup
with app.app_context():
    init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS

# ==========================================
# Web Page Views
# ==========================================

@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")

@app.route("/paper/<int:paper_id>")
def paper_detail_view(paper_id):
    """Paper detail and management view."""
    paper = get_paper_by_id(paper_id)
    if not paper:
        return render_template("404.html", message="Research paper not found"), 404
    return render_template("paper_detail.html", paper=paper)

@app.route("/graph")
def graph_view():
    """Interactive Knowledge Graph explorer view."""
    return render_template("graph.html")

@app.route("/activity")
def activity_view():
    """System activity audit trail view."""
    return render_template("activity.html")

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Serves the uploaded PDF file for viewing or downloading."""
    return send_from_directory(config.UPLOAD_FOLDER, filename)

@app.route("/samples/<path:filename>")
def serve_sample(filename):
    """Serves sample PDF files."""
    sample_dir = os.path.join(config.BASE_DIR, "samples")
    return send_from_directory(sample_dir, filename)

@app.route("/api/samples/seed", methods=["POST"])
def seed_sample_papers():
    """Seeds the library with pre-generated sample research papers."""
    sample_dir = os.path.join(config.BASE_DIR, "samples")
    if not os.path.exists(sample_dir):
        return jsonify({"error": "Sample directory not found"}), 404

    sample_files = [
        "attention_gnn_discovery.pdf",
        "scalable_semantic_search.pdf",
        "benchmarking_ann_search.pdf",
        "automated_scientific_knowledge_extraction.pdf",
        "robustness_verification_llms.pdf"
    ]

    imported_count = 0
    results = []

    for s_file in sample_files:
        s_path = os.path.join(sample_dir, s_file)
        if not os.path.exists(s_path):
            continue

        extracted = process_pdf_file(s_path, s_file)
        existing = check_duplicate_paper(extracted["file_hash"])
        if existing:
            results.append({"filename": s_file, "status": "duplicate", "existing_id": existing["id"]})
            continue

        # Copy to uploads
        temp_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        saved_filename = f"{temp_timestamp}_{s_file}"
        dest_path = os.path.join(config.UPLOAD_FOLDER, saved_filename)
        with open(s_path, "rb") as rf, open(dest_path, "wb") as wf:
            wf.write(rf.read())

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO papers (
                file_hash, filename, original_filename, title, abstract,
                publication_year, doi, file_size, page_count,
                extraction_status, extraction_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extracted["file_hash"], saved_filename, s_file,
            extracted["title"], extracted["abstract"],
            extracted["publication_year"], extracted["doi"],
            extracted["file_size"], extracted["page_count"],
            extracted["status"], extracted.get("notes", "")
        ))
        paper_id = cursor.lastrowid

        # Insert authors
        for idx, author_name in enumerate(extracted["authors"], 1):
            cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
            arow = cursor.fetchone()
            if arow:
                a_id = arow[0]
            else:
                cursor.execute("INSERT INTO authors (name) VALUES (?)", (author_name,))
                a_id = cursor.lastrowid
            cursor.execute("""
                INSERT OR IGNORE INTO paper_authors (paper_id, author_id, author_order)
                VALUES (?, ?, ?)
            """, (paper_id, a_id, idx))

        # Generate topics
        auto_topics = generate_tags_and_topics(
            extracted["title"], extracted["abstract"], extracted.get("full_text", "")
        )
        for t_info in auto_topics:
            t_name = t_info["name"]
            cursor.execute("SELECT id FROM topics WHERE name = ?", (t_name,))
            trow = cursor.fetchone()
            if trow:
                t_id = trow[0]
            else:
                cursor.execute("INSERT INTO topics (name, category) VALUES (?, ?)", (t_name, t_info["category"]))
                t_id = cursor.lastrowid
            cursor.execute("""
                INSERT OR IGNORE INTO paper_topics (paper_id, topic_id, confidence, is_auto)
                VALUES (?, ?, ?, 1)
            """, (paper_id, t_id, t_info["confidence"]))

        # References
        for r in extracted["references"]:
            cursor.execute("""
                INSERT INTO paper_references (paper_id, ref_index, raw_text, extracted_title, extracted_authors, extracted_year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (paper_id, r["ref_index"], r["raw_text"], r["extracted_title"], r["extracted_authors"], r["extracted_year"]))

        conn.commit()
        conn.close()

        log_activity(
            action="UPLOAD",
            paper_id=paper_id,
            paper_title=extracted["title"],
            user="System (Sample Seeder)",
            details=f"Seeded sample paper '{s_file}'."
        )
        imported_count += 1
        results.append({"filename": s_file, "status": "success", "id": paper_id})

    link_citation_references()
    return jsonify({"imported": imported_count, "results": results})

# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Returns library summary metrics."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM papers")
    paper_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM authors")
    author_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM topics")
    topic_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM paper_references WHERE matched_paper_id IS NOT NULL")
    citation_links = cursor.fetchone()[0]

    cursor.execute("""
        SELECT t.name, COUNT(pt.paper_id) as count
        FROM topics t
        JOIN paper_topics pt ON t.id = pt.topic_id
        GROUP BY t.id
        ORDER BY count DESC
        LIMIT 5
    """)
    top_topics = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return jsonify({
        "paper_count": paper_count,
        "author_count": author_count,
        "topic_count": topic_count,
        "citation_links": citation_links,
        "top_topics": top_topics
    })

@app.route("/api/papers", methods=["GET"])
def list_papers():
    """Lists papers with search, filtering, and sorting."""
    search_query = request.args.get("search", "").strip()
    topic_filter = request.args.get("topic", "").strip()
    author_filter = request.args.get("author", "").strip()
    year_filter = request.args.get("year", "").strip()
    status_filter = request.args.get("status", "").strip()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "DESC").upper()

    allowed_sorts = {
        "title": "p.title",
        "created_at": "p.created_at",
        "year": "p.publication_year",
        "file_size": "p.file_size"
    }
    sort_col = allowed_sorts.get(sort_by, "p.created_at")
    if order not in ["ASC", "DESC"]:
        order = "DESC"

    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT p.id, p.title, p.abstract, p.publication_year, p.doi,
                        p.file_size, p.page_count, p.extraction_status, p.filename,
                        p.original_filename, p.created_at,
                        (SELECT COUNT(*) FROM paper_references pr WHERE pr.paper_id = p.id) as ref_count,
                        (SELECT COUNT(*) FROM paper_references pr WHERE pr.matched_paper_id = p.id) as cited_by_count
        FROM papers p
        LEFT JOIN paper_authors pa ON p.id = pa.paper_id
        LEFT JOIN authors a ON pa.author_id = a.id
        LEFT JOIN paper_topics pt ON p.id = pt.paper_id
        LEFT JOIN topics t ON pt.topic_id = t.id
        WHERE 1=1
    """
    params = []

    if search_query:
        query += """ AND (
            p.title LIKE ? OR
            p.abstract LIKE ? OR
            a.name LIKE ? OR
            t.name LIKE ? OR
            p.doi LIKE ?
        )"""
        s_wild = f"%{search_query}%"
        params.extend([s_wild, s_wild, s_wild, s_wild, s_wild])

    if topic_filter:
        query += " AND t.name = ?"
        params.append(topic_filter)

    if author_filter:
        query += " AND a.name = ?"
        params.append(author_filter)

    if year_filter:
        query += " AND p.publication_year = ?"
        params.append(int(year_filter))

    if status_filter:
        query += " AND p.extraction_status = ?"
        params.append(status_filter)

    query += f" ORDER BY {sort_col} {order}"

    cursor.execute(query, params)
    raw_papers = [dict(row) for row in cursor.fetchall()]

    # Attach authors and topics to each paper for table rendering
    papers = []
    for p in raw_papers:
        p_id = p['id']
        cursor.execute("""
            SELECT a.name FROM authors a
            JOIN paper_authors pa ON a.id = pa.author_id
            WHERE pa.paper_id = ? ORDER BY pa.author_order ASC
        """, (p_id,))
        p['authors'] = [r['name'] for r in cursor.fetchall()]

        cursor.execute("""
            SELECT t.name, pt.confidence FROM topics t
            JOIN paper_topics pt ON t.id = pt.topic_id
            WHERE pt.paper_id = ? ORDER BY pt.confidence DESC LIMIT 4
        """, (p_id,))
        p['topics'] = [r['name'] for r in cursor.fetchall()]
        papers.append(p)

    conn.close()
    return jsonify({"papers": papers, "total": len(papers)})

@app.route("/api/papers/<int:paper_id>", methods=["GET"])
def get_paper(paper_id):
    """Returns single paper with complete details."""
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404
    return jsonify(paper)

@app.route("/api/papers/upload", methods=["POST"])
def upload_papers():
    """
    Handles PDF file uploads.
    Validates file, checks for duplicates via SHA-256, extracts content,
    runs automatic tagging, cross-links citations, and logs activity.
    """
    if "files" not in request.files and "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_files = request.files.getlist("files") or [request.files["file"]]
    results = []
    user_name = request.form.get("user", "Admin Researcher")

    for file_obj in uploaded_files:
        if not file_obj or file_obj.filename == "":
            continue

        orig_filename = file_obj.filename
        if not allowed_file(orig_filename):
            results.append({
                "filename": orig_filename,
                "status": "error",
                "message": "Only PDF files are supported (.pdf)"
            })
            log_activity(
                action="UPLOAD_FAILED",
                paper_title=orig_filename,
                user=user_name,
                details=f"Invalid file type attempted: {orig_filename}"
            )
            continue

        # Save to temporary staging path to compute hash
        safe_orig = secure_filename(orig_filename) or "paper.pdf"
        temp_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        saved_filename = f"{temp_timestamp}_{safe_orig}"
        file_path = os.path.join(config.UPLOAD_FOLDER, saved_filename)
        file_obj.save(file_path)

        # Process PDF and extract information
        extracted = process_pdf_file(file_path, orig_filename)

        # Check for duplicate upload
        existing = check_duplicate_paper(extracted["file_hash"])
        if existing:
            # Clean up the duplicate physical file
            try:
                os.remove(file_path)
            except OSError:
                pass

            results.append({
                "filename": orig_filename,
                "status": "duplicate",
                "message": f"Duplicate paper detected. '{existing['title']}' is already in your library.",
                "existing_id": existing["id"]
            })
            log_activity(
                action="UPLOAD_DUPLICATE",
                paper_id=existing["id"],
                paper_title=existing["title"],
                user=user_name,
                details=f"Duplicate upload skipped for file {orig_filename}"
            )
            continue

        # Check if PDF extraction completely failed (corrupt or 0 byte)
        if extracted["status"] == "failed":
            try:
                os.remove(file_path)
            except OSError:
                pass

            results.append({
                "filename": orig_filename,
                "status": "failed",
                "message": extracted.get("error", "Failed to parse PDF document.")
            })
            log_activity(
                action="UPLOAD_CORRUPT",
                paper_title=orig_filename,
                user=user_name,
                details=extracted.get("error", "Corrupt file rejected")
            )
            continue

        # Insert paper record into database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO papers (
                file_hash, filename, original_filename, title, abstract,
                publication_year, doi, file_size, page_count,
                extraction_status, extraction_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            extracted["file_hash"],
            saved_filename,
            orig_filename,
            extracted["title"],
            extracted["abstract"],
            extracted["publication_year"],
            extracted["doi"],
            extracted["file_size"],
            extracted["page_count"],
            extracted["status"],
            extracted.get("notes", "")
        ))
        paper_id = cursor.lastrowid

        # Insert authors and link
        for idx, author_name in enumerate(extracted["authors"], 1):
            cursor.execute("SELECT id FROM authors WHERE name = ?", (author_name,))
            author_row = cursor.fetchone()
            if author_row:
                a_id = author_row[0]
            else:
                cursor.execute("INSERT INTO authors (name) VALUES (?)", (author_name,))
                a_id = cursor.lastrowid

            cursor.execute("""
                INSERT OR IGNORE INTO paper_authors (paper_id, author_id, author_order)
                VALUES (?, ?, ?)
            """, (paper_id, a_id, idx))

        # Generate and insert automatic tags/topics
        auto_topics = generate_tags_and_topics(
            extracted["title"],
            extracted["abstract"],
            extracted.get("full_text", "")
        )
        for t_info in auto_topics:
            t_name = t_info["name"]
            cursor.execute("SELECT id FROM topics WHERE name = ?", (t_name,))
            t_row = cursor.fetchone()
            if t_row:
                t_id = t_row[0]
            else:
                cursor.execute("INSERT INTO topics (name, category) VALUES (?, ?)", (t_name, t_info["category"]))
                t_id = cursor.lastrowid

            cursor.execute("""
                INSERT OR IGNORE INTO paper_topics (paper_id, topic_id, confidence, is_auto)
                VALUES (?, ?, ?, 1)
            """, (paper_id, t_id, t_info["confidence"]))

        # Insert extracted references
        for r in extracted["references"]:
            cursor.execute("""
                INSERT INTO paper_references (paper_id, ref_index, raw_text, extracted_title, extracted_authors, extracted_year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (paper_id, r["ref_index"], r["raw_text"], r["extracted_title"], r["extracted_authors"], r["extracted_year"]))

        conn.commit()
        conn.close()

        # Cross-link citations between library papers
        link_citation_references()

        # Record activity log
        log_activity(
            action="UPLOAD",
            paper_id=paper_id,
            paper_title=extracted["title"],
            user=user_name,
            details=f"Uploaded '{orig_filename}' ({extracted['page_count']} pages). Extracted {len(extracted['authors'])} authors, {len(auto_topics)} topics, {len(extracted['references'])} references."
        )

        results.append({
            "id": paper_id,
            "filename": orig_filename,
            "title": extracted["title"],
            "status": "success",
            "extraction_status": extracted["status"],
            "topics": [t["name"] for t in auto_topics],
            "authors": extracted["authors"]
        })

    return jsonify({"results": results})

@app.route("/api/papers/<int:paper_id>", methods=["PUT"])
def update_paper(paper_id):
    """
    Updates editable paper details (title, abstract, year, doi, authors).
    Logs change in activity log.
    """
    data = request.json or {}
    user_name = data.get("user", "Admin Researcher")

    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    title = data.get("title", paper["title"]).strip()
    abstract = data.get("abstract", paper["abstract"]).strip()
    year = data.get("publication_year")
    doi = data.get("doi", paper["doi"])
    authors_input = data.get("authors")  # Can be list of strings or comma-separated string

    try:
        year = int(year) if year is not None and str(year).strip() != "" else None
    except ValueError:
        year = paper["publication_year"]

    conn = get_db()
    cursor = conn.cursor()

    changes = []
    if title != paper["title"]:
        changes.append(f"Title changed to '{title}'")
    if str(year) != str(paper["publication_year"]):
        changes.append(f"Year changed to {year}")
    if doi != paper["doi"]:
        changes.append(f"DOI changed to {doi}")
    if abstract != paper["abstract"]:
        changes.append("Abstract updated")

    cursor.execute("""
        UPDATE papers
        SET title = ?, abstract = ?, publication_year = ?, doi = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (title, abstract, year, doi, paper_id))

    # Update authors if provided
    if authors_input is not None:
        if isinstance(authors_input, str):
            authors_list = [a.strip() for a in authors_input.split(",") if a.strip()]
        else:
            authors_list = [str(a).strip() for a in authors_input if str(a).strip()]

        if authors_list:
            cursor.execute("DELETE FROM paper_authors WHERE paper_id = ?", (paper_id,))
            for idx, a_name in enumerate(authors_list, 1):
                cursor.execute("SELECT id FROM authors WHERE name = ?", (a_name,))
                arow = cursor.fetchone()
                if arow:
                    a_id = arow[0]
                else:
                    cursor.execute("INSERT INTO authors (name) VALUES (?)", (a_name,))
                    a_id = cursor.lastrowid
                cursor.execute("""
                    INSERT OR IGNORE INTO paper_authors (paper_id, author_id, author_order)
                    VALUES (?, ?, ?)
                """, (paper_id, a_id, idx))
            changes.append(f"Authors updated to: {', '.join(authors_list)}")

    conn.commit()
    conn.close()

    # Re-link citations in case title changed
    link_citation_references()

    log_activity(
        action="EDIT",
        paper_id=paper_id,
        paper_title=title,
        user=user_name,
        details="; ".join(changes) if changes else "Saved without changes"
    )

    return jsonify({"status": "success", "message": "Paper details updated successfully."})

@app.route("/api/papers/<int:paper_id>", methods=["DELETE"])
def delete_paper(paper_id):
    """
    Deletes paper record, associated relationships, and physical PDF.
    Logs activity.
    """
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    user_name = request.args.get("user", "Admin Researcher")
    paper_title = paper["title"]
    filename = paper["filename"]

    # Delete physical file
    file_path = os.path.join(config.UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

    # Delete DB records (Cascading deletes paper_authors, paper_topics, paper_references)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()

    log_activity(
        action="DELETE",
        paper_id=paper_id,
        paper_title=paper_title,
        user=user_name,
        details=f"Deleted paper '{paper_title}' and removed file {filename}."
    )

    return jsonify({"status": "success", "message": f"Paper '{paper_title}' deleted."})

@app.route("/api/papers/<int:paper_id>/tags", methods=["POST"])
def add_paper_tag(paper_id):
    """Adds a custom or existing tag to a paper."""
    data = request.json or {}
    tag_name = data.get("name", "").strip()
    user_name = data.get("user", "Admin Researcher")

    if not tag_name:
        return jsonify({"error": "Tag name is required"}), 400

    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM topics WHERE name = ?", (tag_name,))
    t_row = cursor.fetchone()
    if t_row:
        t_id = t_row[0]
    else:
        cursor.execute("INSERT INTO topics (name, category) VALUES (?, 'user_tag')", (tag_name,))
        t_id = cursor.lastrowid

    cursor.execute("""
        INSERT OR IGNORE INTO paper_topics (paper_id, topic_id, confidence, is_auto)
        VALUES (?, ?, 1.0, 0)
    """, (paper_id, t_id))
    conn.commit()
    conn.close()

    log_activity(
        action="TAG_ADD",
        paper_id=paper_id,
        paper_title=paper["title"],
        user=user_name,
        details=f"Added tag '{tag_name}' to paper."
    )

    return jsonify({"status": "success", "tag_id": t_id, "tag_name": tag_name})

@app.route("/api/papers/<int:paper_id>/tags/<int:tag_id>", methods=["DELETE"])
def remove_paper_tag(paper_id, tag_id):
    """Removes a tag from a paper."""
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    user_name = request.args.get("user", "Admin Researcher")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM topics WHERE id = ?", (tag_id,))
    t_row = cursor.fetchone()
    tag_name = t_row[0] if t_row else str(tag_id)

    cursor.execute("DELETE FROM paper_topics WHERE paper_id = ? AND topic_id = ?", (paper_id, tag_id))
    conn.commit()
    conn.close()

    log_activity(
        action="TAG_REMOVE",
        paper_id=paper_id,
        paper_title=paper["title"],
        user=user_name,
        details=f"Removed tag '{tag_name}' from paper."
    )

    return jsonify({"status": "success", "message": f"Tag '{tag_name}' removed."})

@app.route("/api/papers/<int:paper_id>/references", methods=["POST"])
def add_paper_reference(paper_id):
    """Manually adds a citation reference to a paper."""
    data = request.json or {}
    raw_text = data.get("raw_text", "").strip()
    extracted_title = data.get("title", "").strip() or None
    extracted_year = data.get("year")
    user_name = data.get("user", "Admin Researcher")

    if not raw_text:
        return jsonify({"error": "Citation text is required"}), 400

    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ref_index) FROM paper_references WHERE paper_id = ?", (paper_id,))
    max_idx = cursor.fetchone()[0] or 0

    cursor.execute("""
        INSERT INTO paper_references (paper_id, ref_index, raw_text, extracted_title, extracted_year)
        VALUES (?, ?, ?, ?, ?)
    """, (paper_id, max_idx + 1, raw_text, extracted_title, extracted_year))
    ref_id = cursor.lastrowid
    conn.commit()
    conn.close()

    link_citation_references()

    log_activity(
        action="REF_ADD",
        paper_id=paper_id,
        paper_title=paper["title"],
        user=user_name,
        details=f"Added manual citation reference: '{raw_text[:80]}...'"
    )

    return jsonify({"status": "success", "ref_id": ref_id})

@app.route("/api/papers/<int:paper_id>/references/<int:ref_id>", methods=["DELETE"])
def delete_paper_reference(paper_id, ref_id):
    """Deletes a reference entry from a paper."""
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM paper_references WHERE id = ? AND paper_id = ?", (ref_id, paper_id))
    conn.commit()
    conn.close()

    log_activity(
        action="REF_DELETE",
        paper_id=paper_id,
        paper_title=paper["title"],
        user=request.args.get("user", "Admin Researcher"),
        details=f"Deleted reference id #{ref_id}."
    )

    return jsonify({"status": "success"})

@app.route("/api/papers/<int:paper_id>/reextract", methods=["POST"])
def reextract_paper(paper_id):
    """Re-runs PDF extraction pipeline on an existing paper."""
    paper = get_paper_by_id(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    file_path = os.path.join(config.UPLOAD_FOLDER, paper["filename"])
    if not os.path.exists(file_path):
        return jsonify({"error": "Original PDF file is missing on server"}), 404

    extracted = process_pdf_file(file_path, paper["original_filename"])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE papers
        SET title = ?, abstract = ?, publication_year = ?, doi = ?,
            extraction_status = ?, extraction_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        extracted["title"], extracted["abstract"], extracted["publication_year"],
        extracted["doi"], extracted["status"], extracted.get("notes", ""), paper_id
    ))

    # Regenerate topics
    auto_topics = generate_tags_and_topics(
        extracted["title"],
        extracted["abstract"],
        extracted.get("full_text", "")
    )
    for t_info in auto_topics:
        cursor.execute("SELECT id FROM topics WHERE name = ?", (t_info["name"],))
        trow = cursor.fetchone()
        t_id = trow[0] if trow else None
        if not t_id:
            cursor.execute("INSERT INTO topics (name, category) VALUES (?, ?)", (t_info["name"], t_info["category"]))
            t_id = cursor.lastrowid
        cursor.execute("""
            INSERT OR IGNORE INTO paper_topics (paper_id, topic_id, confidence, is_auto)
            VALUES (?, ?, ?, 1)
        """, (paper_id, t_id, t_info["confidence"]))

    conn.commit()
    conn.close()

    link_citation_references()

    log_activity(
        action="RE_EXTRACT",
        paper_id=paper_id,
        paper_title=extracted["title"],
        user=request.json.get("user", "Admin Researcher") if request.json else "Admin Researcher",
        details="Re-executed extraction pipeline and refreshed metadata, topics, and references."
    )

    return jsonify({"status": "success", "message": "Paper re-extracted successfully."})

@app.route("/api/graph/data", methods=["GET"])
def get_graph_data():
    """Returns nodes and edges formatted for Vis.js visualization."""
    filter_topic = request.args.get("topic")
    filter_author = request.args.get("author")
    graph_data = build_knowledge_graph(filter_topic=filter_topic, filter_author=filter_author)
    return jsonify(graph_data)

@app.route("/api/activity", methods=["GET"])
def get_activity_log():
    """Returns activity audit records with search and filters."""
    action_filter = request.args.get("action", "").strip()
    search = request.args.get("search", "").strip()
    limit = int(request.args.get("limit", 100))

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM activity_logs WHERE 1=1"
    params = []

    if action_filter:
        query += " AND action = ?"
        params.append(action_filter)

    if search:
        query += " AND (paper_title LIKE ? OR details LIKE ? OR user LIKE ?)"
        s_wild = f"%{search}%"
        params.extend([s_wild, s_wild, s_wild])

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({"activities": logs})

@app.route("/api/activity/export", methods=["GET"])
def export_activity_csv():
    """Exports activity logs as a downloadable CSV file."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, action, user, paper_id, paper_title, details FROM activity_logs ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log ID", "Timestamp (UTC)", "Action", "User", "Paper ID", "Paper Title", "Details"])

    for r in rows:
        writer.writerow([r["id"], r["timestamp"], r["action"], r["user"], r["paper_id"] or "", r["paper_title"] or "", r["details"] or ""])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=research_library_activity_log.csv"}
    )

@app.route("/api/topics", methods=["GET"])
def get_all_topics():
    """Returns list of all topics with usage counts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.id, t.name, t.category, COUNT(pt.paper_id) as paper_count
        FROM topics t
        LEFT JOIN paper_topics pt ON t.id = pt.topic_id
        GROUP BY t.id
        ORDER BY paper_count DESC, t.name ASC
    """)
    topics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"topics": topics})

@app.route("/api/authors", methods=["GET"])
def get_all_authors():
    """Returns list of all authors with paper counts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.name, a.institution, COUNT(pa.paper_id) as paper_count
        FROM authors a
        LEFT JOIN paper_authors pa ON a.id = pa.author_id
        GROUP BY a.id
        ORDER BY paper_count DESC, a.name ASC
    """)
    authors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"authors": authors})

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File size exceeds the 32MB maximum limit."}), 413

@app.errorhandler(404)
def not_found_page(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Resource not found"}), 404
    return render_template("404.html", message="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error occurred."}), 500
    return render_template("500.html", message="An internal server error occurred."), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
