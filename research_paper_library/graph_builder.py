from database import get_db

def build_knowledge_graph(filter_topic=None, filter_author=None, min_degree=0):
    """
    Constructs node and edge datasets for Vis.js representation of the research library.
    Includes papers, authors, topics, citations, and co-authorship.
    """
    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch papers
    cursor.execute("""
        SELECT id, title, publication_year, doi, page_count, extraction_status
        FROM papers
        ORDER BY id ASC
    """)
    papers = [dict(row) for row in cursor.fetchall()]

    # 2. Fetch authors and paper_authors
    cursor.execute("""
        SELECT pa.paper_id, pa.author_id, a.name as author_name, a.institution
        FROM paper_authors pa
        JOIN authors a ON pa.author_id = a.id
    """)
    paper_authors = [dict(row) for row in cursor.fetchall()]

    # 3. Fetch topics and paper_topics
    cursor.execute("""
        SELECT pt.paper_id, pt.topic_id, pt.confidence, t.name as topic_name, t.category
        FROM paper_topics pt
        JOIN topics t ON pt.topic_id = t.id
    """)
    paper_topics = [dict(row) for row in cursor.fetchall()]

    # 4. Fetch citation links
    cursor.execute("""
        SELECT paper_id as citing_id, matched_paper_id as cited_id, raw_text
        FROM paper_references
        WHERE matched_paper_id IS NOT NULL AND paper_id != matched_paper_id
    """)
    citations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    nodes = {}
    edges = []
    author_counts = {}
    topic_counts = {}

    # Calculate degrees / counts
    for pa in paper_authors:
        author_counts[pa['author_id']] = author_counts.get(pa['author_id'], 0) + 1

    for pt in paper_topics:
        topic_counts[pt['topic_id']] = topic_counts.get(pt['topic_id'], 0) + 1

    # Citation counts for papers
    citation_counts = {}
    for c in citations:
        citation_counts[c['cited_id']] = citation_counts.get(c['cited_id'], 0) + 1

    # Create Paper Nodes
    for p in papers:
        c_count = citation_counts.get(p['id'], 0)
        p_node_id = f"paper_{p['id']}"

        # Clean title for display
        clean_title = p['title']
        display_label = clean_title if len(clean_title) <= 28 else clean_title[:25] + "..."

        nodes[p_node_id] = {
            "id": p_node_id,
            "entity_id": p['id'],
            "type": "paper",
            "label": display_label,
            "full_title": clean_title,
            "year": p['publication_year'] or "Unknown",
            "doi": p['doi'] or "N/A",
            "citations": c_count,
            "group": "paper",
            "shape": "box",
            "margin": 10,
            "font": {"color": "#ffffff", "face": "Inter, sans-serif", "size": 13, "bold": True},
            "color": {
                "background": "#2563eb",
                "border": "#1d4ed8",
                "highlight": {"background": "#1d4ed8", "border": "#1e40af"}
            },
            "title": f"<b>Paper:</b> {clean_title}<br><b>Year:</b> {p['publication_year'] or 'N/A'}<br><b>Citations in Library:</b> {c_count}"
        }

    # Create Author Nodes & Paper-Author Edges
    paper_to_authors = {}
    for pa in paper_authors:
        p_id = pa['paper_id']
        a_id = pa['author_id']
        a_name = pa['author_name']
        a_node_id = f"author_{a_id}"

        if p_id not in paper_to_authors:
            paper_to_authors[p_id] = []
        paper_to_authors[p_id].append((a_id, a_name))

        if a_node_id not in nodes:
            count = author_counts.get(a_id, 1)
            nodes[a_node_id] = {
                "id": a_node_id,
                "entity_id": a_id,
                "type": "author",
                "label": a_name,
                "paper_count": count,
                "group": "author",
                "shape": "ellipse",
                "font": {"color": "#0f172a", "face": "Inter, sans-serif", "size": 12},
                "color": {
                    "background": "#10b981",
                    "border": "#059669",
                    "highlight": {"background": "#059669", "border": "#047857"}
                },
                "title": f"<b>Author:</b> {a_name}<br><b>Papers in Library:</b> {count}"
            }

        # Edge: Paper -> Author
        edges.append({
            "id": f"edge_{p_id}_{a_node_id}",
            "from": f"paper_{p_id}",
            "to": a_node_id,
            "label": "authored by",
            "type": "authorship",
            "font": {"size": 9, "color": "#64748b", "align": "middle"},
            "color": {"color": "#94a3b8", "highlight": "#475569"},
            "arrows": "to",
            "smooth": {"type": "continuous"}
        })

    # Co-authorship edges (between authors on the same paper)
    seen_coauthors = set()
    for p_id, a_list in paper_to_authors.items():
        if len(a_list) > 1:
            for i in range(len(a_list)):
                for j in range(i + 1, len(a_list)):
                    a1_id, _ = a_list[i]
                    a2_id, _ = a_list[j]
                    pair_key = tuple(sorted([a1_id, a2_id]))
                    if pair_key not in seen_coauthors:
                        seen_coauthors.add(pair_key)
                        edges.append({
                            "id": f"coauthor_{pair_key[0]}_{pair_key[1]}",
                            "from": f"author_{pair_key[0]}",
                            "to": f"author_{pair_key[1]}",
                            "label": "co-author",
                            "type": "coauthorship",
                            "dashes": True,
                            "font": {"size": 8, "color": "#059669"},
                            "color": {"color": "#6ee7b7", "highlight": "#10b981"}
                        })

    # Create Topic Nodes & Paper-Topic Edges
    for pt in paper_topics:
        p_id = pt['paper_id']
        t_id = pt['topic_id']
        t_name = pt['topic_name']
        t_node_id = f"topic_{t_id}"

        if t_node_id not in nodes:
            t_count = topic_counts.get(t_id, 1)
            nodes[t_node_id] = {
                "id": t_node_id,
                "entity_id": t_id,
                "type": "topic",
                "label": t_name,
                "paper_count": t_count,
                "group": "topic",
                "shape": "diamond",
                "font": {"color": "#1e293b", "face": "Inter, sans-serif", "size": 12, "bold": True},
                "color": {
                    "background": "#f59e0b",
                    "border": "#d97706",
                    "highlight": {"background": "#d97706", "border": "#b45309"}
                },
                "title": f"<b>Topic/Tag:</b> {t_name}<br><b>Category:</b> {pt['category']}<br><b>Papers:</b> {t_count}"
            }

        # Edge: Paper -> Topic
        edges.append({
            "id": f"edge_topic_{p_id}_{t_id}",
            "from": f"paper_{p_id}",
            "to": t_node_id,
            "label": "has topic",
            "type": "topic",
            "font": {"size": 8, "color": "#d97706"},
            "color": {"color": "#fcd34d", "highlight": "#f59e0b"}
        })

    # Citation Edges (Paper -> Paper)
    for c in citations:
        edges.append({
            "id": f"cite_{c['citing_id']}_{c['cited_id']}",
            "from": f"paper_{c['citing_id']}",
            "to": f"paper_{c['cited_id']}",
            "label": "cites",
            "type": "citation",
            "width": 2.5,
            "font": {"size": 10, "color": "#dc2626", "bold": True},
            "color": {"color": "#ef4444", "highlight": "#b91c1c"},
            "arrows": "to"
        })

    # Summary Statistics
    paper_node_count = len([n for n in nodes.values() if n['type'] == 'paper'])
    author_node_count = len([n for n in nodes.values() if n['type'] == 'author'])
    topic_node_count = len([n for n in nodes.values() if n['type'] == 'topic'])
    citation_edge_count = len([e for e in edges if e['type'] == 'citation'])

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "metrics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "paper_count": paper_node_count,
            "author_count": author_node_count,
            "topic_count": topic_node_count,
            "citation_links": citation_edge_count
        }
    }
