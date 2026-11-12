import re
import math
from collections import Counter

# Standard academic stopwords
ACADEMIC_STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t', 'as',
    'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'cannot',
    'could', 'did', 'do', 'does', 'doing', 'don\'t', 'down', 'during', 'each', 'few', 'for', 'from', 'further',
    'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how',
    'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'let\'s', 'me', 'more', 'most', 'my', 'myself',
    'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves',
    'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their',
    'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who',
    'whom', 'why', 'with', 'won\'t', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves',
    # Common academic paper fillers
    'paper', 'propose', 'proposed', 'presents', 'presented', 'study', 'studies', 'approach', 'approaches',
    'method', 'methods', 'methodology', 'framework', 'algorithm', 'algorithms', 'result', 'results',
    'show', 'shows', 'shown', 'demonstrate', 'demonstrates', 'evaluates', 'evaluated', 'evaluation',
    'performance', 'based', 'using', 'used', 'use', 'novel', 'new', 'section', 'table', 'figure', 'et', 'al',
    'state', 'art', 'also', 'furthermore', 'however', 'respectively', 'conducted', 'significant',
    'experimental', 'experiment', 'experiments', 'analysis', 'system', 'systems', 'work', 'works'
}

# Domain Taxonomy mapping: Keyword pattern -> Standardized Canonical Topic & Category
TAXONOMY_MAP = {
    "Artificial Intelligence": ("Artificial Intelligence", "domain", [r"\bartificial intelligence\b", r"\bai\b", r"\bintelligent systems\b"]),
    "Machine Learning": ("Machine Learning", "domain", [r"\bmachine learning\b", r"\bml\b", r"\bsupervised learning\b", r"\bunsupervised learning\b"]),
    "Deep Learning": ("Deep Learning", "technique", [r"\bdeep learning\b", r"\bneural networks?\b", r"\bdnn\b", r"\bbackpropagation\b"]),
    "Transformers": ("Transformers", "technique", [r"\btransformer\b", r"\btransformers\b", r"\bself-attention\b", r"\battention mechanism\b"]),
    "Large Language Models": ("Large Language Models", "domain", [r"\blarge language models?\b", r"\bllms?\b", r"\bgpt\b", r"\bprompting\b", r"\binstruct tuning\b"]),
    "Natural Language Processing": ("Natural Language Processing", "domain", [r"\bnatural language processing\b", r"\bnlp\b", r"\btext mining\b", r"\bnamed entity recognition\b"]),
    "Computer Vision": ("Computer Vision", "domain", [r"\bcomputer vision\b", r"\bobject detection\b", r"\bimage classification\b", r"\bsegmentation\b", r"\bcnn\b", r"\bconvolutional\b"]),
    "Knowledge Graphs": ("Knowledge Graphs", "domain", [r"\bknowledge graphs?\b", r"\bontolog(y|ies)\b", r"\bsemantic web\b", r"\brdf\b", r"\btriple store\b", r"\bentity linking\b"]),
    "Graph Neural Networks": ("Graph Neural Networks", "technique", [r"\bgraph neural networks?\b", r"\bgnn\b", r"\bnode embeddings?\b", r"\bgraph representation\b"]),
    "Information Retrieval": ("Information Retrieval", "domain", [r"\binformation retrieval\b", r"\branking\b", r"\bsearch engine\b", r"\bvector search\b", r"\bbm25\b"]),
    "Reinforcement Learning": ("Reinforcement Learning", "technique", [r"\breinforcement learning\b", r"\brl\b", r"\bq-learning\b", r"\bmarkov decision\b", r"\bpolicy gradient\b"]),
    "Distributed Systems": ("Distributed Systems", "domain", [r"\bdistributed systems?\b", r"\bconsensus\b", r"\braft\b", r"\bpaxos\b", r"\bcloud computing\b", r"\bmicroservices\b"]),
    "Cybersecurity": ("Cybersecurity", "domain", [r"\bcybersecurity\b", r"\bcryptograph(y|ic)\b", r"\bmalware\b", r"\bsecurity\b", r"\bvulnerability\b", r"\badversarial\b"]),
    "Data Mining": ("Data Mining", "domain", [r"\bdata mining\b", r"\bclustering\b", r"\bassociation rules\b", r"\banomaly detection\b"]),
    "Database Systems": ("Database Systems", "domain", [r"\bdatabases?\b", r"\bsql\b", r"\bnosql\b", r"\bquery processing\b", r"\btransaction processing\b"]),
    "Software Engineering": ("Software Engineering", "domain", [r"\bsoftware engineering\b", r"\bcode review\b", r"\brefactoring\b", r"\btesting\b", r"\bstatic analysis\b"]),
    "Human-Computer Interaction": ("Human-Computer Interaction", "domain", [r"\bhuman-computer interaction\b", r"\bhci\b", r"\buser interface\b", r"\bux\b", r"\busability\b"]),
    "Generative AI": ("Generative AI", "domain", [r"\bgenerative ai\b", r"\bgenerative models?\b", r"\bdiffusion models?\b", r"\bgan\b", r"\bvae\b"])
}

def extract_explicit_keywords(text):
    """
    Looks for explicit 'Keywords:' or 'Index Terms:' in the document text.
    """
    keywords = []
    pattern = r"(?:Key\s*words|Index\s*Terms|Categories\s*and\s*Subject\s*Descriptors)[:\-—–]\s*([^\n\r]+(?:\n[^\n\r]+)?)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        raw_kw = match.group(1).strip()
        # Cut off if it hits an introductory header or next section
        cutoff = re.split(r"(?:1\.?\s*Introduction|I\.?\s*Introduction|Introduction\b)", raw_kw, flags=re.IGNORECASE)
        raw_kw = cutoff[0].strip()

        # Split on commas, semicolons, or bullets
        items = re.split(r"[,;•·/]", raw_kw)
        for item in items:
            clean = re.sub(r"[^a-zA-Z0-9\s\-]", "", item).strip()
            clean = re.sub(r"\s+", " ", clean).strip()
            # Clean length check
            if 2 <= len(clean) <= 45 and not clean.lower() in ACADEMIC_STOPWORDS:
                keywords.append(clean.title())
    return keywords

def match_taxonomy_topics(text):
    """
    Matches text against the structured academic taxonomy.
    Returns list of dicts with name, category, and score.
    """
    text_lower = text.lower()
    matched = []
    for topic_name, (canonical, category, patterns) in TAXONOMY_MAP.items():
        score = 0
        for pattern in patterns:
            hits = len(re.findall(pattern, text_lower))
            if hits > 0:
                score += hits

        if score > 0:
            # Normalize confidence between 0.65 and 0.98 based on hit frequency
            conf = min(0.98, 0.65 + (score * 0.05))
            matched.append({
                "name": canonical,
                "category": category,
                "confidence": round(conf, 2),
                "hits": score
            })

    # Sort by hits descending
    matched.sort(key=lambda x: x["hits"], reverse=True)
    return matched

def extract_statistical_keyphrases(title, abstract, full_text, top_k=5):
    """
    Extracts high-frequency statistical keyphrases from title, abstract, and text.
    """
    corpus = f"{title} {title} {abstract} {abstract} {full_text[:4000]}"
    words = re.findall(r"\b[a-zA-Z]{3,20}\b", corpus.lower())

    filtered_words = [w for w in words if w not in ACADEMIC_STOPWORDS]

    # Unigram frequencies
    unigrams = Counter(filtered_words)

    # Bigram frequencies
    bigrams = Counter()
    for i in range(len(filtered_words) - 1):
        w1, w2 = filtered_words[i], filtered_words[i+1]
        bigrams[f"{w1} {w2}"] += 1

    candidate_phrases = []

    # Pick top bigrams with count >= 2
    for phrase, count in bigrams.most_common(10):
        if count >= 2:
            candidate_phrases.append({
                "name": phrase.title(),
                "category": "keyphrase",
                "confidence": round(min(0.85, 0.5 + (count * 0.05)), 2)
            })

    # If few bigrams, supplement with top unigrams
    for word, count in unigrams.most_common(10):
        if count >= 3 and not any(word in c["name"].lower() for c in candidate_phrases):
            candidate_phrases.append({
                "name": word.capitalize(),
                "category": "keyword",
                "confidence": round(min(0.80, 0.45 + (count * 0.04)), 2)
            })

    return candidate_phrases[:top_k]

def generate_tags_and_topics(title, abstract, full_text, max_topics=6):
    """
    Combines explicit keywords, taxonomy mapping, and statistical phrases
    to produce an optimal, deduplicated set of topics for a paper.
    """
    combined_topics = {}

    # 1. Explicit Keywords from PDF (Highest Priority)
    explicit_kw = extract_explicit_keywords(full_text[:3500])
    for kw in explicit_kw:
        key = kw.lower()
        combined_topics[key] = {
            "name": kw,
            "category": "author_keyword",
            "confidence": 0.95
        }

    # 2. Taxonomy Matches
    combined_content = f"{title} {abstract} {full_text[:5000]}"
    tax_matches = match_taxonomy_topics(combined_content)
    for tm in tax_matches:
        key = tm["name"].lower()
        if key not in combined_topics:
            combined_topics[key] = {
                "name": tm["name"],
                "category": tm["category"],
                "confidence": tm["confidence"]
            }

    # 3. Statistical Keyphrases (to ensure niche topics are captured)
    if len(combined_topics) < max_topics:
        stats = extract_statistical_keyphrases(title, abstract, full_text, top_k=max_topics)
        for st in stats:
            key = st["name"].lower()
            if key not in combined_topics and len(combined_topics) < max_topics + 2:
                combined_topics[key] = st

    # Sort by confidence descending
    results = sorted(combined_topics.values(), key=lambda x: x["confidence"], reverse=True)
    return results[:max_topics]
