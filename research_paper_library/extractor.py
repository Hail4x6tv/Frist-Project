import os
import re
import hashlib
from datetime import datetime
import pypdf

def compute_file_hash(file_path):
    """Calculates the SHA-256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def clean_text(text):
    """Normalizes whitespace and removes irregular control characters."""
    if not text:
        return ""
    # Normalize unicode spaces and line breaks
    text = re.sub(r"\r\n|\r", "\n", text)
    # Fix hyphenated words at line ends (e.g., 'trans- \nformer' -> 'transformer')
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    # Collapse 3+ newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def extract_doi(text):
    """Extracts DOI if present in the text."""
    doi_pattern = r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b"
    match = re.search(doi_pattern, text)
    if match:
        doi = match.group(1).rstrip(".")
        return doi
    return None

def extract_year(text, meta_date=None):
    """Infers publication year from metadata or first page text."""
    current_year = datetime.now().year

    # Check metadata first if present
    if meta_date:
        year_match = re.search(r"\b(19\d\d|20\d\d)\b", str(meta_date))
        if year_match:
            y = int(year_match.group(1))
            if 1950 <= y <= current_year + 1:
                return y

    # Check copyright or publication statements on first page
    patterns = [
        r"(?:©|Copyright|Published|Accepted|Proceedings of|arXiv:\d{4}\.\d{4,5}v\d+\s*\[[a-zA-Z\.\-]+\])\s*.*?(\b20\d\d|19\d\d\b)",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d\d|19\d\d)\b",
        r"\b(20[0-2]\d)\b"
    ]

    first_page_sample = text[:3000]
    for pat in patterns:
        m = re.search(pat, first_page_sample, re.IGNORECASE)
        if m:
            try:
                y = int(m.group(1))
                if 1970 <= y <= current_year + 1:
                    return y
            except (ValueError, IndexError):
                continue

    return None

def extract_title(first_page_text, meta_title, filename):
    """
    Extracts the paper title using multi-stage heuristics:
    1. Filtered PDF metadata title.
    2. Dominant text lines before author/abstract.
    3. Filename fallback.
    """
    # Check if metadata title looks legitimate (not placeholder like 'untitled', 'anonymous', or file path)
    if meta_title and isinstance(meta_title, str):
        clean_meta = meta_title.strip()
        is_bad = any(x in clean_meta.lower() for x in [
            "untitled", "anonymous", "unspecified", "microsoft word", "latex", ".pdf", "springer", "elsevier", "ieee", "arxiv"
        ])
        if not is_bad and 5 < len(clean_meta) < 250:
            return clean_meta

    lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
    if not lines:
        # Fallback to cleaned filename
        base = os.path.splitext(filename)[0]
        return re.sub(r"[_\-]+", " ", base).title()

    candidate_lines = []
    # Ignore initial header banners like arXiv preprint, IEEE transactions, ISSN, etc.
    banner_patterns = [
        r"^arxiv:\d+",
        r"^under review",
        r"^in proceedings of",
        r"^ieee\b",
        r"^acm\b",
        r"^springer\b",
        r"^journal of\b",
        r"^volume\s+\d+",
        r"^issn",
        r"^doi:",
        r"^published as",
        r"^http",
        r"^preprint"
    ]

    start_idx = 0
    for idx, line in enumerate(lines[:10]):
        if any(re.search(bp, line, re.IGNORECASE) for bp in banner_patterns):
            start_idx = idx + 1
        else:
            break

    for line in lines[start_idx:start_idx + 8]:
        # Stop if we hit abstract, keywords, or obvious author email/affiliation
        if re.match(r"^(abstract|keywords|index terms|summary)\b", line, re.IGNORECASE):
            break
        if "@" in line or "http" in line:
            break
        # Stop if line looks like author names with affiliations
        if re.search(r"\b(university|institute|department|laboratory|college|school of)\b", line, re.IGNORECASE):
            break

        candidate_lines.append(line)
        # Titles are rarely longer than 3 lines
        if len(" ".join(candidate_lines)) > 180:
            break

    if candidate_lines:
        title = " ".join(candidate_lines)
        # Clean stray quotes or punctuation
        title = re.sub(r"^[\s\"']+|[\s\"']+$", "", title)
        if len(title) > 5:
            return title

    # Fallback to cleaned filename
    base = os.path.splitext(filename)[0]
    return re.sub(r"[_\-]+", " ", base).title()

def extract_authors(first_page_text, title):
    """
    Extracts author names from the block between Title and Abstract.
    Filters out affiliations, emails, institutions, and departments.
    """
    authors = []
    # Find position of abstract
    abstract_match = re.search(r"\b(abstract|summary)\b", first_page_text, re.IGNORECASE)
    if not abstract_match:
        end_pos = 2000
    else:
        end_pos = abstract_match.start()

    region = first_page_text[:end_pos]

    # Remove title if present in region
    if title and len(title) > 5:
        region = region.replace(title, "")

    lines = [l.strip() for l in region.split("\n") if l.strip()]

    # Affiliation / noise indicators
    affiliation_keywords = [
        "university", "institute", "department", "school", "faculty", "center", "centre",
        "laboratory", "corp", "inc", "ltd", "google", "meta", "microsoft", "amazon", "apple",
        "openai", "deepmind", "berkeley", "stanford", "mit", "harvard", "oxford", "cambridge",
        "email:", "@", "http", "www", "usa", "uk", "china", "canada", "germany", "france"
    ]

    for line in lines:
        line_lower = line.lower()

        # Skip headers / metadata lines
        if any(re.search(bp, line_lower) for bp in [r"^arxiv", r"^volume", r"^doi", r"^pages"]):
            continue

        # Skip affiliation lines
        if any(ak in line_lower for ak in affiliation_keywords):
            continue

        # Strip numbers/superscripts e.g. "Alice Smith 1, Bob Jones 2*"
        cleaned_line = re.sub(r"[\d\*†‡§\^]", "", line).strip()
        cleaned_line = re.sub(r"\s+", " ", cleaned_line)

        # Author split delimiters: 'and', commas, semicolons
        parts = re.split(r",|\sand\s|;|&", cleaned_line)
        for part in parts:
            name = part.strip()
            # Validate name characteristics (2-4 words, capitalized letters, reasonable length)
            words = name.split()
            if 1 < len(words) <= 5 and 3 <= len(name) <= 40:
                # Ensure each word begins with uppercase or is an initial
                if all(w[0].isupper() or w.endswith(".") for w in words if len(w) > 0):
                    # Exclude accidental section names
                    if not any(sw in name.lower() for sw in ["abstract", "introduction", "figure", "table", "review"]):
                        if name not in authors:
                            authors.append(name)

        if len(authors) >= 10:
            break

    if not authors:
        authors = ["Unknown Author"]

    return authors

def extract_abstract(full_text):
    """
    Extracts the abstract section by detecting start boundary (Abstract)
    and end boundary (1. Introduction, Keywords, etc.).
    """
    # Regex pattern to match 'Abstract' heading
    start_pattern = r"(?:^|\n)\s*(?:A\s*B\s*S\s*T\s*R\s*A\s*C\s*T|Abstract|Summary)[:\-—–.\s]"
    start_match = re.search(start_pattern, full_text[:6000], re.IGNORECASE)

    if not start_match:
        # Fallback search anywhere in first 4000 characters
        start_match = re.search(r"\bAbstract\b", full_text[:4000], re.IGNORECASE)
        if not start_match:
            return "Abstract could not be automatically detected. You may manually edit the paper details to add it."

    start_idx = start_match.end()

    # Look for boundary indicating the end of the abstract
    end_pattern = r"(?:(?:1|I)\.?\s*Introduction|Key\s*words|Index\s*Terms|Categories\s*and\s*Subject|1\.\s+Background)"
    end_match = re.search(end_pattern, full_text[start_idx:start_idx + 4000], re.IGNORECASE)

    if end_match:
        abstract = full_text[start_idx : start_idx + end_match.start()]
    else:
        # Take the next 1500 chars or until double newline
        sample = full_text[start_idx : start_idx + 1800]
        paragraphs = sample.split("\n\n")
        abstract = paragraphs[0] if paragraphs else sample

    abstract = clean_text(abstract)
    if len(abstract) < 30:
        return "Abstract could not be automatically detected. You may manually edit the paper details to add it."

    return abstract

def extract_references(full_text):
    """
    Extracts bibliographic citations from the end of the paper.
    Supports IEEE [1], APA (Author, Year), and standard numbered lists.
    """
    references = []
    # Find the References / Bibliography heading near the back
    ref_head_pattern = r"(?:^|\n)\s*(?:REFERENCES|References|BIBLIOGRAPHY|Bibliography|Literature\s+Cited)\s*(?:\n|$)"
    matches = list(re.finditer(ref_head_pattern, full_text))

    if not matches:
        return []

    # Use the last reference header match (to avoid table of contents or introductory mentions)
    ref_start = matches[-1].end()
    ref_text = full_text[ref_start:]

    # Heuristic 1: Bracketed numbers e.g. [1], [2], [10]
    bracket_refs = re.split(r"(?:^|\n)\s*\[(\d+)\]\s*", ref_text)
    if len(bracket_refs) > 3:
        # Split gives alternating: [prefix, num1, text1, num2, text2...]
        idx = 1
        while idx < len(bracket_refs) - 1:
            ref_idx = int(bracket_refs[idx])
            raw = clean_text(bracket_refs[idx + 1])
            if raw:
                parsed = parse_single_reference(raw, ref_idx)
                references.append(parsed)
            idx += 2
        return references[:50]

    # Heuristic 2: Dotted numbers e.g. 1. Author..., 2. Author...
    dot_refs = re.split(r"(?:^|\n)\s*(\d{1,3})\.\s+(?=[A-Z])", ref_text)
    if len(dot_refs) > 3:
        idx = 1
        while idx < len(dot_refs) - 1:
            ref_idx = int(dot_refs[idx])
            raw = clean_text(dot_refs[idx + 1])
            if raw:
                parsed = parse_single_reference(raw, ref_idx)
                references.append(parsed)
            idx += 2
        return references[:50]

    # Heuristic 3: Double-newline separated paragraphs if no numbers
    paragraphs = [p.strip() for p in ref_text.split("\n\n") if len(p.strip()) > 25]
    for i, p in enumerate(paragraphs[:30], 1):
        parsed = parse_single_reference(clean_text(p), i)
        references.append(parsed)

    return references

def parse_single_reference(raw_text, index):
    """
    Extracts author, year, and probable title from an individual reference string.
    """
    year = None
    year_match = re.search(r"\b(19\d\d|20\d\d)\b", raw_text)
    if year_match:
        try:
            year = int(year_match.group(1))
        except ValueError:
            pass

    # Attempt to extract title in quotes e.g. "Attention is all you need"
    title = None
    title_quote_match = re.search(r"[\"“]([^\n\"”]{8,180})[\"”]", raw_text)
    if title_quote_match:
        title = title_quote_match.group(1).strip()
    else:
        # Heuristic: Segment between year and journal/conference or first dot
        parts = [p.strip() for p in raw_text.split(".") if len(p.strip()) > 8]
        if len(parts) >= 2:
            # Often the second segment is the title
            title = parts[1]
        elif parts:
            title = parts[0]

    return {
        "ref_index": index,
        "raw_text": raw_text[:500],
        "extracted_title": title[:200] if title else None,
        "extracted_authors": None,
        "extracted_year": year
    }

def process_pdf_file(file_path, original_filename):
    """
    Main extraction pipeline for a PDF document.
    Returns a dictionary of extracted metadata, status, and raw sections.
    """
    file_size = os.path.getsize(file_path)
    file_hash = compute_file_hash(file_path)

    # 1. Error check: Empty file
    if file_size == 0:
        return {
            "status": "failed",
            "file_hash": file_hash,
            "filename": os.path.basename(file_path),
            "original_filename": original_filename,
            "title": original_filename,
            "abstract": "The uploaded file is empty (0 bytes).",
            "authors": ["Unknown Author"],
            "publication_year": None,
            "doi": None,
            "page_count": 0,
            "file_size": 0,
            "references": [],
            "error": "The uploaded PDF is empty."
        }

    # 2. PDF parsing with PyPDF
    try:
        reader = pypdf.PdfReader(file_path)
    except Exception as e:
        return {
            "status": "failed",
            "file_hash": file_hash,
            "filename": os.path.basename(file_path),
            "original_filename": original_filename,
            "title": original_filename,
            "abstract": f"Unable to parse PDF format: {str(e)}",
            "authors": ["Unknown Author"],
            "publication_year": None,
            "doi": None,
            "page_count": 0,
            "file_size": file_size,
            "references": [],
            "error": f"Invalid or corrupt PDF document: {str(e)}"
        }

    page_count = len(reader.pages)
    if page_count == 0:
        return {
            "status": "failed",
            "file_hash": file_hash,
            "filename": os.path.basename(file_path),
            "original_filename": original_filename,
            "title": original_filename,
            "abstract": "The PDF has zero pages.",
            "authors": ["Unknown Author"],
            "publication_year": None,
            "doi": None,
            "page_count": 0,
            "file_size": file_size,
            "references": [],
            "error": "Document contains 0 pages."
        }

    # Extract text from all pages
    extracted_pages = []
    for p_num, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
            extracted_pages.append(txt)
        except Exception as e:
            extracted_pages.append("")

    full_text = "\n\n".join(extracted_pages).strip()
    first_page_text = extracted_pages[0] if extracted_pages else ""

    # 3. Detect Scanned / Non-text PDFs
    if len(full_text.strip()) < 80:
        return {
            "status": "scanned",
            "file_hash": file_hash,
            "filename": os.path.basename(file_path),
            "original_filename": original_filename,
            "title": extract_title("", None, original_filename),
            "abstract": "This document appears to be a scanned image or lacks a selectable text layer. Text extraction could not retrieve content automatically. You can edit the details manually.",
            "authors": ["Unknown Author"],
            "publication_year": datetime.now().year,
            "doi": None,
            "page_count": page_count,
            "file_size": file_size,
            "references": [],
            "notes": "Scanned document detected - no text layer."
        }

    # 4. Extract metadata fields
    pdf_meta = reader.metadata or {}
    meta_title = pdf_meta.get("/Title")
    meta_date = pdf_meta.get("/CreationDate") or pdf_meta.get("/ModDate")

    title = extract_title(first_page_text, meta_title, original_filename)
    authors = extract_authors(first_page_text, title)
    abstract = extract_abstract(full_text)
    doi = extract_doi(full_text[:4000])
    year = extract_year(full_text, meta_date)
    references = extract_references(full_text)

    # Determine status
    has_abstract = "could not be automatically detected" not in abstract.lower()
    has_authors = len(authors) > 0 and authors[0] != "Unknown Author"

    if has_abstract and has_authors:
        status = "success"
    else:
        status = "partial"

    return {
        "status": status,
        "file_hash": file_hash,
        "filename": os.path.basename(file_path),
        "original_filename": original_filename,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "publication_year": year,
        "doi": doi,
        "page_count": page_count,
        "file_size": file_size,
        "references": references,
        "full_text": full_text
    }
