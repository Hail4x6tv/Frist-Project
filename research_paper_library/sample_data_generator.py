import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)

PAPERS_SPEC = [
    {
        "filename": "attention_gnn_discovery.pdf",
        "title": "Attention-Based Graph Neural Networks for Knowledge Discovery",
        "authors": "Alexander Vance, Elena Rostova, Marcus Thorne",
        "affiliations": "Department of Computer Science, Stanford University; Institute for AI Research, Zurich",
        "year": "2024",
        "doi": "10.1145/3543873.3587321",
        "abstract": "Graph Neural Networks (GNNs) have emerged as a dominant paradigm for modeling relational structures and complex networks. In this paper, we propose Attention-Based Graph Discovery (AGD), an architecture integrating multi-head self-attention mechanisms with relational knowledge graphs. Our framework dynamically weights multi-hop connections, outperforming previous baseline models on standard benchmark datasets. We evaluate our approach on complex bibliographic citations and semantic inference tasks, demonstrating significant improvements in link prediction and knowledge graph completion.",
        "keywords": "Knowledge Graphs, Graph Neural Networks, Attention Mechanism, Machine Learning, Artificial Intelligence",
        "sections": [
            ("1. Introduction", "Knowledge representation and reasoning constitute fundamental challenges in artificial intelligence. While early methods relied on discrete triple stores, contemporary deep learning leverages continuous vector spaces. Graph Neural Networks have revolutionized this field by combining structural graph topology with node feature embeddings. In this paper, we introduce a novel formulation that explicitly attends to heterogeneous edge types."),
            ("2. Proposed AGD Methodology", "The core innovation of our AGD model lies in its adaptive message-passing operator. Given a graph G = (V, E, R), where V denotes entities and R denotes relations, our attention layer computes normalized coefficients across relational neighborhoods. We incorporate self-attention layers inspired by modern transformer architectures."),
            ("3. Experimental Evaluation", "We performed extensive empirical validation on benchmark datasets including FB15k-237 and WN18RR. Our experimental setup evaluated Mean Reciprocal Rank (MRR) and Hits@10 metrics. AGD achieved a 4.2% relative improvement in Hits@10 compared to standard Relational GCN baselines while maintaining sub-linear memory scaling.")
        ],
        "references": [
            "[1] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., and Polosukhin, I. \"Attention Is All You Need.\" Advances in Neural Information Processing Systems (NeurIPS), pp. 5998-6008, 2017.",
            "[2] Kipf, T. N., and Welling, M. \"Semi-Supervised Classification with Graph Convolutional Networks.\" International Conference on Learning Representations (ICLR), 2017.",
            "[3] Rostova, E., and Vance, A. \"Scalable Semantic Search Using Vector Embeddings.\" Journal of Machine Learning Research, 24(12), pp. 1-28, 2023."
        ]
    },
    {
        "filename": "scalable_semantic_search.pdf",
        "title": "Scalable Semantic Search Using Vector Embeddings",
        "authors": "Elena Rostova, Alexander Vance",
        "affiliations": "Swiss Federal Institute of Technology (ETH Zurich); AI Research Labs",
        "year": "2023",
        "doi": "10.1016/j.jocs.2023.102145",
        "abstract": "Modern information retrieval systems increasingly rely on dense semantic representations rather than traditional keyword matching. We investigate the efficiency and recall tradeoffs in high-dimensional vector spaces using approximate nearest neighbor algorithms. Experimental evaluations across ten million documents demonstrate a 4x throughput improvement while preserving over 96% top-k recall accuracy. Furthermore, we analyze index compression techniques that reduce memory footprints by 60%.",
        "keywords": "Information Retrieval, Vector Search, Machine Learning, Deep Learning, Database Systems",
        "sections": [
            ("1. Introduction", "Traditional lexical search methods such as BM25 remain pervasive due to their inverted index efficiency. However, vocabulary mismatch and synonymy severely constrain retrieval performance in specialized academic literature. Dense retrieval using learned embeddings bridges this semantic gap by projecting queries and documents into a shared metric space."),
            ("2. Vector Compression & Indexing", "We analyze product quantization (PQ) alongside hierarchical navigable small world (HNSW) graphs. By quantizing sub-vectors into codebooks, we retain high recall while dramatically diminishing memory bandwidth pressure on modern multi-core servers."),
            ("3. Empirical Findings", "Throughput measurements on standardized multi-million passage corpora demonstrate query latencies under 12 milliseconds at 99th percentile, facilitating real-time interactive search across expansive research libraries.")
        ],
        "references": [
            "[1] Johnson, J., Douze, M., and Jégou, H. \"Billion-scale similarity search with GPUs.\" IEEE Transactions on Big Data, 7(3), pp. 535-547, 2019.",
            "[2] Thorne, M., and Lin, D. K. \"Benchmarking Approximate Nearest Neighbor Search in Real-time Applications.\" Proceedings of the VLDB Endowment, 15(8), pp. 1620-1632, 2022.",
            "[3] Malkov, Y. A., and Yashunin, D. A. \"Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs.\" IEEE TPAMI, 42(4), pp. 824-836, 2020."
        ]
    },
    {
        "filename": "benchmarking_ann_search.pdf",
        "title": "Benchmarking Approximate Nearest Neighbor Search in Real-time Applications",
        "authors": "Marcus Thorne, David K. Lin",
        "affiliations": "Department of Computer Science, University of California, Berkeley",
        "year": "2022",
        "doi": "10.14778/3538598.3538602",
        "abstract": "Real-time query processing over high-dimensional vector databases poses significant computational challenges for latency-sensitive applications. This study presents a rigorous empirical benchmark comparing HNSW, IVF-PQ, and graph-based indexing strategies across varied hardware configurations. Our findings reveal critical memory bandwidth bottlenecks and suggest optimal indexing parameterizations for microsecond-scale retrieval in large-scale search infrastructure.",
        "keywords": "Information Retrieval, Database Systems, Benchmarking, Distributed Systems",
        "sections": [
            ("1. Introduction", "With the proliferation of deep embedding representations across web search, recommender systems, and scientific indexing, Approximate Nearest Neighbor (ANN) search algorithms serve as a critical infrastructure layer. Despite numerous publications claiming superior Pareto frontiers, systematic cross-architecture evaluations remain sparse."),
            ("2. Evaluation Methodology", "We standardise the evaluation framework using identical CPU instruction sets, memory pinning, and thread allocation across cosine distance, Euclidean metric, and inner-product spaces. Datasets range from 128 to 1536 dimensions."),
            ("3. Memory Hierarchy Analysis", "Cache locality analysis highlights that graph-based approaches incur significant random memory accesses during beam traversal. We propose hardware-aware prefetching routines to alleviate cache thrashing.")
        ],
        "references": [
            "[1] Malkov, Y. A., and Yashunin, D. A. \"Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs.\" IEEE TPAMI, 2020.",
            "[2] Rostova, E., and Vance, A. \"Scalable Semantic Search Using Vector Embeddings.\" Journal of Machine Learning Research, 2023."
        ]
    },
    {
        "filename": "automated_scientific_knowledge_extraction.pdf",
        "title": "Automated Knowledge Extraction from Scientific Literature",
        "authors": "Sophia Chen, David K. Lin, Elena Rostova",
        "affiliations": "MIT Computer Science and Artificial Intelligence Laboratory; ETH Zurich",
        "year": "2024",
        "doi": "10.1109/TKDE.2024.3391024",
        "abstract": "Extracting structured knowledge graphs from unstructured scientific publications accelerates meta-analysis and scholarly discovery. We present SciExtract, a pipeline leveraging transformer-based language models fine-tuned on computer science and biomedical corpora. SciExtract achieves high precision in entity linking, relation classification, and citation resolution, facilitating automatic construction of cross-disciplinary literature graphs.",
        "keywords": "Knowledge Graphs, Natural Language Processing, Transformers, Information Extraction, Machine Learning",
        "sections": [
            ("1. Introduction", "The rate of global academic publication exceeds three million papers annually, presenting severe information overload for researchers. Traditional bibliometric indexes only capture co-authorship and raw citations without extracting granular semantic relations between claims, methods, and outcomes."),
            ("2. The SciExtract Architecture", "SciExtract employs a two-tier extraction pipeline. First, specialized layout-aware parsers extract sections and bibliographies. Second, fine-tuned transformer encoders identify scientific entities (tasks, datasets, metrics) and classify relational links."),
            ("3. Cross-Paper Knowledge Synthesis", "By linking extracted entities into an interconnected knowledge graph, SciExtract enables multi-hop reasoning across independent publications, surfacing hidden thematic bridges between disparate research sub-fields.")
        ],
        "references": [
            "[1] Vance, A., Rostova, E., and Thorne, M. \"Attention-Based Graph Neural Networks for Knowledge Discovery.\" ACM Transactions, 2024.",
            "[2] Beltagy, I., Lo, K., and Cohan, A. \"SciBERT: A Pretrained Language Model for Scientific Text.\" EMNLP, 2019.",
            "[3] Rostova, E., and Vance, A. \"Scalable Semantic Search Using Vector Embeddings.\" Journal of Machine Learning Research, 2023."
        ]
    },
    {
        "filename": "robustness_verification_llms.pdf",
        "title": "Robustness and Verification in Large Language Models",
        "authors": "Marcus Thorne, Sophia Chen",
        "affiliations": "UC Berkeley; MIT CSAIL",
        "year": "2024",
        "doi": "10.1145/3639478.3640019",
        "abstract": "As Large Language Models (LLMs) are deployed in safety-critical domains, guaranteeing factual reliability and robustness against adversarial prompts becomes paramount. We introduce a verification framework that combines formal logic constraints with reinforcement learning from human feedback. Our experiments demonstrate a 42% reduction in hallucinatory outputs across standard question-answering benchmarks.",
        "keywords": "Large Language Models, Artificial Intelligence, Cybersecurity, Reinforcement Learning, Transformers",
        "sections": [
            ("1. Introduction", "Autoregressive language models generate remarkably fluent natural language text. However, their tendency to produce ungrounded hallucinations and vulnerability to prompt injection attacks present severe challenges for real-world adoption in legal, medical, and scientific settings."),
            ("2. Constrained Decoding & Logic Verification", "We construct an external knowledge verification layer that intercepts intermediate token generation. Candidate tokens that contradict verified knowledge graph triples are pruned via constrained beam search."),
            ("3. Experimental Results", "Testing across TruthfulQA and adversarial jailbreak benchmarks shows our method substantially outpaces standard temperature scaling and retrieval-augmented baselines without degrading general conversational fluency.")
        ],
        "references": [
            "[1] Chen, S., Lin, D. K., and Rostova, E. \"Automated Knowledge Extraction from Scientific Literature.\" IEEE TKDE, 2024.",
            "[2] Vance, A., Rostova, E., and Thorne, M. \"Attention-Based Graph Neural Networks for Knowledge Discovery.\" ACM Transactions, 2024."
        ]
    }
]

def generate_pdf(spec):
    pdf_path = os.path.join(SAMPLE_DIR, spec["filename"])
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
        title=spec["title"],
        author=spec["authors"]
    )

    styles = getSampleStyleSheet()

    # Define custom academic typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=10
    )

    authors_style = ParagraphStyle(
        "DocAuthors",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4
    )

    affil_style = ParagraphStyle(
        "DocAffil",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        alignment=1,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14
    )

    meta_bar_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    abstract_heading = ParagraphStyle(
        "AbsHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    abstract_body = ParagraphStyle(
        "AbsBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        alignment=4, # Justified
        textColor=colors.HexColor("#1e293b"),
        leftIndent=24,
        rightIndent=24,
        spaceAfter=10
    )

    keywords_style = ParagraphStyle(
        "DocKeywords",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        leftIndent=24,
        rightIndent=24,
        spaceAfter=18
    )

    sec_head = ParagraphStyle(
        "SecHead",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6
    )

    sec_body = ParagraphStyle(
        "SecBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=4,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10
    )

    ref_style = ParagraphStyle(
        "RefEntry",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    story = []

    # Title & Authors
    story.append(Paragraph(spec["title"], title_style))
    story.append(Paragraph(spec["authors"], authors_style))
    story.append(Paragraph(spec["affiliations"], affil_style))

    # Meta banner (Year, DOI)
    meta_text = f"Published: {spec['year']} &nbsp;|&nbsp; DOI: {spec['doi']}"
    story.append(Paragraph(meta_text, meta_bar_style))
    story.append(HRFlowable(width="95%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    # Abstract
    story.append(Paragraph("<b>Abstract</b>", abstract_heading))
    story.append(Paragraph(spec["abstract"], abstract_body))

    # Keywords
    story.append(Paragraph(f"<b>Keywords:</b> {spec['keywords']}", keywords_style))
    story.append(HRFlowable(width="95%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=14))

    # Sections
    for h, b in spec["sections"]:
        story.append(Paragraph(h, sec_head))
        story.append(Paragraph(b, sec_body))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # References
    story.append(Paragraph("<b>References</b>", sec_head))
    for r in spec["references"]:
        story.append(Paragraph(r, ref_style))

    doc.build(story)
    print(f"Generated sample paper: {pdf_path}")
    return pdf_path

def generate_test_edge_cases():
    """Generates corrupted, empty, and scanned mock PDFs to test error handling."""
    # 1. Empty 0-byte file
    empty_path = os.path.join(SAMPLE_DIR, "corrupt_empty_sample.pdf")
    with open(empty_path, "wb") as f:
        pass
    print(f"Created empty test file: {empty_path}")

    # 2. Corrupt non-PDF file disguised as PDF
    corrupt_path = os.path.join(SAMPLE_DIR, "corrupt_invalid_bytes.pdf")
    with open(corrupt_path, "wb") as f:
        f.write(b"This is a totally invalid binary file that claims to be a PDF but has no valid headers.\x00\xff\xfe\x01\x02")
    print(f"Created corrupt test file: {corrupt_path}")

    # 3. Scanned PDF mock (valid PDF structure but containing only empty text / image container)
    scanned_path = os.path.join(SAMPLE_DIR, "scanned_image_sample.pdf")
    doc = SimpleDocTemplate(scanned_path, pagesize=letter)
    story = [HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"))]
    doc.build(story)
    print(f"Created scanned-style test file: {scanned_path}")

if __name__ == "__main__":
    for spec in PAPERS_SPEC:
        generate_pdf(spec)
    generate_test_edge_cases()
    print("All sample papers and edge-case test files generated successfully!")
