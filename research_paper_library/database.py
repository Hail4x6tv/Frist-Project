import sqlite3
import json
import os
from datetime import datetime
from config import DATABASE_PATH

def get_db():
    """Returns a SQLite connection with row factory configured and foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Papers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_hash TEXT UNIQUE NOT NULL,
        filename TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        title TEXT NOT NULL,
        abstract TEXT,
        publication_year INTEGER,
        doi TEXT,
        file_size INTEGER,
        page_count INTEGER,
        extraction_status TEXT DEFAULT 'success', -- 'success', 'partial', 'scanned', 'failed'
        extraction_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Authors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL COLLATE NOCASE,
        institution TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Paper-Authors link table (Many-to-Many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_authors (
        paper_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        author_order INTEGER DEFAULT 1,
        PRIMARY KEY (paper_id, author_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
    );
    """)

    # 4. Topics / Tags table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL COLLATE NOCASE,
        category TEXT DEFAULT 'general',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Paper-Topics link table (Many-to-Many)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_topics (
        paper_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        confidence REAL DEFAULT 1.0,
        is_auto INTEGER DEFAULT 1,
        PRIMARY KEY (paper_id, topic_id),
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
    );
    """)

    # 6. References table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        ref_index INTEGER DEFAULT 1,
        raw_text TEXT NOT NULL,
        extracted_title TEXT,
        extracted_authors TEXT,
        extracted_year INTEGER,
        matched_paper_id INTEGER,
        FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
        FOREIGN KEY (matched_paper_id) REFERENCES papers(id) ON DELETE SET NULL
    );
    """)

    # 7. Activity Log table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL, -- UPLOAD, EDIT, TAG_ADD, TAG_REMOVE, DELETE, RE_EXTRACT
        paper_id INTEGER,
        paper_title TEXT,
        user TEXT DEFAULT 'Admin Researcher',
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create indexes for fast lookup and search
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_hash ON papers(file_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_name ON topics(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_refs_paper ON paper_references(paper_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_action ON activity_logs(action);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_time ON activity_logs(timestamp);")

    conn.commit()
    conn.close()

def log_activity(action, paper_id=None, paper_title=None, user='Admin Researcher', details=None):
    """Logs an activity event into the database."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        else:
            details_str = str(details) if details else ""

        cursor.execute("""
            INSERT INTO activity_logs (action, paper_id, paper_title, user, details, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (action, paper_id, paper_title, user, details_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Error logging activity]: {e}")

def get_paper_by_id(paper_id):
    """Fetches a paper by ID with its authors, topics, and references."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()
    if not paper:
        conn.close()
        return None

    paper_dict = dict(paper)

    # Get authors ordered by author_order
    cursor.execute("""
        SELECT a.id, a.name, a.institution, a.email, pa.author_order
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        WHERE pa.paper_id = ?
        ORDER BY pa.author_order ASC
    """, (paper_id,))
    paper_dict['authors'] = [dict(row) for row in cursor.fetchall()]

    # Get topics
    cursor.execute("""
        SELECT t.id, t.name, t.category, pt.confidence, pt.is_auto
        FROM topics t
        JOIN paper_topics pt ON t.id = pt.topic_id
        WHERE pt.paper_id = ?
        ORDER BY pt.confidence DESC, t.name ASC
    """, (paper_id,))
    paper_dict['topics'] = [dict(row) for row in cursor.fetchall()]

    # Get references
    cursor.execute("""
        SELECT r.id, r.ref_index, r.raw_text, r.extracted_title, r.extracted_authors,
               r.extracted_year, r.matched_paper_id, p.title as matched_paper_title
        FROM paper_references r
        LEFT JOIN papers p ON r.matched_paper_id = p.id
        WHERE r.paper_id = ?
        ORDER BY r.ref_index ASC
    """, (paper_id,))
    paper_dict['references'] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return paper_dict

def check_duplicate_paper(file_hash):
    """Checks if a paper with this exact file hash already exists."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, filename FROM papers WHERE file_hash = ?", (file_hash,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def link_citation_references():
    """Scans all paper references and cross-links with existing papers in the library."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM papers")
    papers = cursor.fetchall()

    for p in papers:
        p_id = p['id']
        p_title = p['title'].strip().lower()
        if len(p_title) < 6:
            continue

        # Match references where extracted_title or raw_text contains paper title
        cursor.execute("""
            UPDATE paper_references
            SET matched_paper_id = ?
            WHERE matched_paper_id IS NULL
              AND paper_id != ?
              AND (
                  (extracted_title IS NOT NULL AND LOWER(extracted_title) LIKE '%' || ? || '%')
                  OR LOWER(raw_text) LIKE '%' || ? || '%'
              )
        """, (p_id, p_id, p_title, p_title))

    conn.commit()
    conn.close()
