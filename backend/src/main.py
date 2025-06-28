import os
import re
import uuid
import json
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# --- Add imports for text extraction ---
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

# --- Configuration ---
app = Flask(__name__)
CORS(app)
# CORS(
#     app,
#     origins=["https://685f8e92966d03140c38af75--eloquent-daffodil-e2c0a3.netlify.app"],
# )
# CORS(app, resources={r"/api/*": {"origins": "*"}})

# CORS(app, resources={r"/api/*": {"origins": r"https://.*\.netlify\.app"}})

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB file size limit
app.config["UPLOAD_FOLDER"] = "uploads"

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# --- In-Memory Data Store ---
sample_documents = []

DOCUMENTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")


def load_documents():
    if os.path.exists(DOCUMENTS_JSON_PATH):
        with open(DOCUMENTS_JSON_PATH, "r") as f:
            return json.load(f)
    return []


def save_documents(docs):
    with open(DOCUMENTS_JSON_PATH, "w") as f:
        json.dump(docs, f, indent=2)


documents = load_documents()
total_search_count = 0


# --- Helper Functions ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "txt",
        "pdf",
        "doc",
        "docx",
    }


def highlight_search_terms(text, search_terms, highlight_tag="<mark>"):
    """
    Enhanced highlighting function that handles multiple search terms
    and preserves case sensitivity while highlighting
    """
    if not text or not search_terms:
        return text
    
    # Sort terms by length (longest first) to avoid partial matches
    sorted_terms = sorted(search_terms, key=len, reverse=True)
    
    highlighted_text = text
    for term in sorted_terms:
        # Use case-insensitive regex to find all occurrences
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        
        def replace_func(match):
            original_text = match.group(0)
            return f"{highlight_tag}{original_text}</mark>"
        
        highlighted_text = pattern.sub(replace_func, highlighted_text)
    
    return highlighted_text


def advanced_search_documents(search_criteria, search_type="keyword"):
    """
    Second search function for advanced document searching
    search_type can be: "keyword", "phrase", "exact", "fuzzy"
    """
    if not search_criteria:
        return []
    
    results = []
    
    # Load all documents from both sources
    all_docs = [(doc, "documents.json") for doc in documents]
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs_from_data = json.load(f)
                all_docs.extend([(doc, "data.json") for doc in docs_from_data])
            except Exception:
                pass
    
    search_terms = search_criteria.lower().split()
    
    for doc, source_file in all_docs:
        content = doc.get("content", doc.get("content_preview", "")).lower()
        keywords = [kw.lower() for kw in doc.get("keywords", [])]
        
        score = 0
        matches_found = []
        
        if search_type == "keyword":
            # Keyword-based search (current implementation)
            for term in search_terms:
                content_matches = content.count(term)
                keyword_matches = keywords.count(term)
                
                score += content_matches * 1
                score += keyword_matches * 2
                
                if content_matches > 0 or keyword_matches > 0:
                    matches_found.append(term)
                    
        elif search_type == "phrase":
            # Phrase search - look for exact phrase in content only
            if search_criteria.lower() in content:
                score += 10
                matches_found.append(search_criteria)
                
        elif search_type == "exact":
            # Exact match search in content only
            if search_criteria.lower() == content:
                score += 20
                matches_found.append(search_criteria)
            elif search_criteria.lower() in content:
                score += 10
                matches_found.append(search_criteria)
                
        elif search_type == "fuzzy":
            # Fuzzy search - partial matches in content only
            for term in search_terms:
                words_in_content = content.split()
                for word in words_in_content:
                    if term in word or word in term:
                        score += 1
                        matches_found.append(term)
                        break
        
        if score > 0:
            # Only highlight in content, not in title
            highlighted_content = highlight_search_terms(
                doc.get("content_preview", doc.get("content", "")[:200]), 
                matches_found
            )
            
            # Extract text snippets from full content if available
            text_snippets = []
            if "content" in doc and doc["content"]:
                text_snippets = extract_text_snippets(doc["content"], matches_found)
            elif doc.get("content_preview"):
                text_snippets = extract_text_snippets(doc["content_preview"], matches_found)
            
            results.append({
                "id": doc.get("id"),
                "title": doc.get("title", ""),  # No highlighting in title
                "classification": doc.get("classification"),
                "confidence_score": doc.get("confidence_score"),
                "relevance_score": score,
                "content_snippet": highlighted_content,
                "source_file": source_file,
                "search_type": search_type,
                "matches_found": list(set(matches_found)),
                "full_content_available": "content" in doc,
                "text_snippets": text_snippets
            })
    
    # Sort by relevance score
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results


def classify_document(content):
    """Simple keyword-based classification"""
    classification = "General Document"
    confidence = 0.75

    content_lower = content.lower()

    if any(
        word in content_lower
        for word in ["research", "study", "academic", "methodology"]
    ):
        classification = "Academic Research"
        confidence = 0.85
    elif any(
        word in content_lower
        for word in ["technical", "documentation", "guide", "framework"]
    ):
        classification = "Technical Documentation"
        confidence = 0.80
    elif any(
        word in content_lower for word in ["business", "report", "finance", "strategy"]
    ):
        classification = "Business Report"
        confidence = 0.88
    elif any(
        word in content_lower
        for word in ["educational", "learning", "tutorial", "course"]
    ):
        classification = "Educational Material"
        confidence = 0.90
    elif any(
        word in content_lower
        for word in ["legal", "contract", "agreement", "compliance"]
    ):
        classification = "Legal Document"
        confidence = 0.98
    elif any(
        word in content_lower
        for word in ["news", "article", "journalism", "current events"]
    ):
        classification = "News Article"
        confidence = 0.85
    elif any(
        word in content_lower
        for word in ["scientific", "paper", "climate", "environment"]
    ):
        classification = "Scientific Paper"
        confidence = 0.96

    return classification, confidence


def extract_keywords(text, num_keywords=5):
    """Extract keywords using frequency analysis"""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

    common_words = {
        "the",
        "and",
        "for",
        "are",
        "but",
        "is",
        "in",
        "it",
        "of",
        "to",
        "with",
    }
    filtered_words = [
        word for word in words if word not in common_words and len(word) > 3
    ]

    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1

    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in keywords[:num_keywords]]


def extract_text_snippets(text, search_terms, snippet_length=100):
    """
    Extract text snippets around search terms with context
    Returns a list of snippets with highlighted search terms
    """
    if not text or not search_terms:
        return []
    
    snippets = []
    text_lower = text.lower()
    
    for term in search_terms:
        term_lower = term.lower()
        start_pos = 0
        
        while True:
            # Find the next occurrence of the term
            pos = text_lower.find(term_lower, start_pos)
            if pos == -1:
                break
            
            # Calculate snippet boundaries
            snippet_start = max(0, pos - snippet_length // 2)
            snippet_end = min(len(text), pos + len(term) + snippet_length // 2)
            
            # Extract the snippet
            snippet = text[snippet_start:snippet_end]
            
            # Add ellipsis if we're not at the beginning/end
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(text):
                snippet = snippet + "..."
            
            # Highlight the search term in the snippet
            highlighted_snippet = highlight_search_terms(snippet, [term])
            
            snippets.append({
                "term": term,
                "snippet": highlighted_snippet,
                "position": pos
            })
            
            start_pos = pos + 1
    
    # Remove duplicates and sort by position
    unique_snippets = []
    seen_positions = set()
    
    for snippet in sorted(snippets, key=lambda x: x["position"]):
        # Check if this snippet is too close to a previous one
        is_duplicate = False
        for seen_pos in seen_positions:
            if abs(snippet["position"] - seen_pos) < snippet_length:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_snippets.append(snippet)
            seen_positions.add(snippet["position"])
    
    return unique_snippets[:5]  # Limit to 5 snippets per document


def extract_text_from_file(file_path, file_type):
    """
    Extract text from PDF, DOCX, or TXT file.
    """
    text = ""
    if file_type == "pdf" and PyPDF2:
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            text = ""
    elif file_type == "docx" and docx:
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            text = ""
    elif file_type == "txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception as e:
            text = ""
    else:
        text = ""
    return text.strip()


def extract_title_from_content(content):
    """
    Extract the first non-empty line from the document content as the title.
    """
    if not content:
        return "Untitled Document"
    for line in content.splitlines():
        line = line.strip()
        if line:
            return line[:120]  # Limit to 120 chars
    return "Untitled Document"


# --- API Endpoints ---
@app.route("/api/health")
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "message": "Document Analytics System with Enhanced Search is running",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "4.0.0",
            "features": {
                "document_management": True,
                "file_upload": True,
                "keyword_extraction": True,
                "advanced_search": True,
                "enhanced_highlighting": True,
                "multiple_search_types": True,
                "analytics": True,
                "vue_js_compatible": True,
            },
            "search_features": {
                "basic_search": "/api/search",
                "advanced_search": "/api/advanced_search",
                "search_types": ["keyword", "phrase", "exact", "fuzzy"],
                "highlighting": "Enhanced search term highlighting with <mark> tags",
                "document_content": "/api/document_content with highlighting support"
            },
            "upload_config": {
                "max_file_size_mb": 10,
                "allowed_extensions": ["txt", "pdf", "doc", "docx"],
            },
        }
    )


@app.route("/api/documents")
def get_documents():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 10)), 50)

    start = (page - 1) * per_page
    end = start + per_page

    return jsonify(
        {
            "documents": documents[start:end],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": len(documents),
                "pages": (len(documents) + per_page - 1) // per_page,
            },
        }
    )


@app.route("/api/search")
def search_documents():
    import time
    start_time = time.time()
    global total_search_count
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    total_search_count += 1
    query_terms = query.lower().split()
    results = []
    # Only search in data.json
    all_docs = []
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs_from_data = json.load(f)
                all_docs.extend([(doc, "data.json") for doc in docs_from_data])
            except Exception:
                pass
    for doc, source_file in all_docs:
        content = doc.get("content", "").lower()  # Use full content for searching
        keywords = [kw.lower() for kw in doc.get("keywords", [])]
        score = 0
        matches_found = []
        
        for term in query_terms:
            content_matches = content.count(term)
            keyword_matches = keywords.count(term)
            
            score += content_matches * 1
            score += keyword_matches * 2
            
            if content_matches > 0 or keyword_matches > 0:
                matches_found.append(term)
                
        if score > 0:
            # Only highlight in content, not in title
            highlighted_content = highlight_search_terms(
                doc.get("content_preview", ""), 
                matches_found
            )
            
            # Extract text snippets from full content
            text_snippets = []
            if "content" in doc and doc["content"]:
                text_snippets = extract_text_snippets(doc["content"], matches_found)
            
            results.append({
                "id": doc.get("id"),
                "title": doc.get("title", ""),  # No highlighting in title
                "extracted_title": doc.get("extracted_title", ""),
                "classification": doc.get("classification"),
                "confidence_score": doc.get("confidence_score"),
                "relevance_score": score,
                "content_snippet": highlighted_content,
                "source_file": "data.json",
                "search_type": "keyword",
                "matches_found": list(set(matches_found)),
                "full_content_available": "content" in doc,
                "text_snippets": text_snippets
            })
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    elapsed = time.time() - start_time
    # --- Log the search query and results to the console ---
    print("[SEARCH] Query:", query)
    print("[SEARCH] Results:", json.dumps(results, indent=2, ensure_ascii=False))
    return jsonify({"query": query, "results": results, "total_results": len(results), "search_time_seconds": round(elapsed, 4)})


@app.route("/api/advanced_search")
def advanced_search():
    """
    Advanced search endpoint with multiple search types
    """
    query = request.args.get("q", "")
    search_type = request.args.get("type", "keyword")  # keyword, phrase, exact, fuzzy
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    if search_type not in ["keyword", "phrase", "exact", "fuzzy"]:
        return jsonify({"error": "Invalid search type. Use: keyword, phrase, exact, or fuzzy"}), 400
    
    results = advanced_search_documents(query, search_type)
    
    return jsonify({
        "query": query,
        "search_type": search_type,
        "results": results,
        "total_results": len(results)
    })


@app.route("/api/statistics")
def get_statistics():
    import time
    total_docs = len(documents)
    total_size_mb = sum(doc["file_size"] for doc in documents) / (1024 * 1024)
    total_words = sum(doc["word_count"] for doc in documents)
    avg_confidence = (
        sum(doc["confidence_score"] for doc in documents) / total_docs
        if total_docs > 0
        else 0
    )

    classifications = {}
    for doc in documents:
        cat = doc["classification"]
        classifications[cat] = classifications.get(cat, 0) + 1

    classification_dist = [
        {
            "name": cat,
            "count": count,
            "percentage": round((count / total_docs) * 100, 2),
        }
        for cat, count in classifications.items()
    ]

    all_keywords = [kw for doc in documents for kw in doc["keywords"]]
    keyword_freq = {}
    for kw in all_keywords:
        keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # --- Add timing for sort and search ---
    # Sort timing
    sort_start = time.time()
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")
    docs = []
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs = json.load(f)
            except Exception:
                pass
    sorted_docs = sorted(docs, key=lambda d: d.get("extracted_title", "").lower())
    sort_elapsed = time.time() - sort_start

    # Search timing (simulate a search for 'test')
    search_start = time.time()
    test_query = "test"
    test_results = []
    for doc in docs:
        content = doc.get("content", "").lower()
        if test_query in content:
            test_results.append(doc)
    search_elapsed = time.time() - search_start

    return jsonify(
        {
            "documents": {
                "total": total_docs,
                "total_size_mb": round(total_size_mb, 2),
                "total_words": total_words,
                "average_confidence": round(avg_confidence, 2),
            },
            "classifications": classification_dist,
            "keywords": {
                "total_unique": len(keyword_freq),
                "top_keywords": [
                    {"keyword": kw, "frequency": freq} for kw, freq in top_keywords
                ],
            },
            "search": {
                "total_searches": total_search_count,
                "popular_terms": [],
                "average_search_time_seconds": round(search_elapsed, 4),
                "average_sort_time_seconds": round(sort_elapsed, 4),
            },
        }
    )


@app.route("/api/classifications")
def get_classifications():
    categories = sorted(list(set(doc["classification"] for doc in documents)))
    return jsonify({"categories": categories, "total_categories": len(categories)})


@app.route("/api/classify", methods=["POST"])
def classify_content():
    import time
    start_time = time.time()
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    classification, confidence = classify_document(data["content"])
    keywords = extract_keywords(data["content"])
    elapsed = time.time() - start_time

    return jsonify(
        {
            "classification": classification,
            "confidence_score": confidence,
            "keywords": keywords,
            "processing_time_ms": 50,
            "classification_time_seconds": round(elapsed, 4),
        }
    )


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(file_path)
        file_type = filename.rsplit(".", 1)[1].lower()
        # --- Extract real text from the file ---
        content = extract_text_from_file(file_path, file_type)
        if not content:
            content = f"[No extractable text found in {filename}]"
        extracted_title = extract_title_from_content(content)
        classification, confidence = classify_document(content)
        keywords = extract_keywords(content)
        new_doc = {
            "id": len(documents) + 1,
            "title": filename,
            "extracted_title": extracted_title,
            "file_type": file_type,
            "file_size": os.path.getsize(file_path),
            "classification": classification,
            "confidence_score": confidence,
            "keywords": keywords,
            "upload_date": datetime.utcnow().isoformat() + "Z",
            "content_preview": content[:200],
            "word_count": len(content.split()),
            "reading_time": len(content.split()) // 200,
            "content": content,  # Store the full extracted text
        }
        documents.append(new_doc)
        save_documents(documents)
        return jsonify(
            {
                "success": True,
                "message": "File uploaded successfully",
                "document": new_doc,
            }
        )
    return jsonify({"error": "File type not allowed"}), 400


@app.route("/api/document_content")
def get_document_content():
    doc_id = request.args.get("id")
    source_file = request.args.get("source_file")
    query = request.args.get("q", "")
    if not doc_id or not source_file:
        return jsonify({"error": "Document ID and source_file are required"}), 400
    # Determine file path
    if source_file == "documents.json":
        file_path = os.path.join(os.path.dirname(__file__), "../documents.json")
    elif source_file == "data.json":
        file_path = os.path.join(os.path.dirname(__file__), "../data.json")
    else:
        return jsonify({"error": "Invalid source_file"}), 400
    if not os.path.exists(file_path):
        return jsonify({"error": "Source file not found"}), 404
    with open(file_path, "r") as f:
        try:
            docs = json.load(f)
        except Exception:
            return jsonify({"error": "Failed to load documents"}), 500
    doc = next((d for d in docs if str(d.get("id")) == str(doc_id)), None)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    content = doc.get("content", "")
    if not content:
        return jsonify({"error": "No full content available for this document"}), 404
    
    # Use the new highlighting function for better search term highlighting
    if query:
        search_terms = query.lower().split()
        content = highlight_search_terms(content, search_terms)
    
    return jsonify({
        "id": doc_id, 
        "title": doc.get("title", ""), 
        "content": content,
        "search_query": query if query else None
    })


@app.route("/api/search_suggestions")
def get_search_suggestions():
    """
    Get search suggestions based on existing document keywords and content
    """
    query = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 10)), 20)
    
    if not query or len(query) < 2:
        return jsonify({"suggestions": []})
    
    suggestions = set()
    
    # Get suggestions from keywords
    all_keywords = []
    for doc in documents:
        all_keywords.extend(doc.get("keywords", []))
    
    # Also get keywords from data.json
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs_from_data = json.load(f)
                for doc in docs_from_data:
                    all_keywords.extend(doc.get("keywords", []))
            except Exception:
                pass
    
    # Filter keywords that start with or contain the query
    query_lower = query.lower()
    for keyword in all_keywords:
        if keyword.lower().startswith(query_lower) or query_lower in keyword.lower():
            suggestions.add(keyword)
    
    # Get suggestions from document titles
    all_titles = [doc.get("title", "") for doc in documents]
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs_from_data = json.load(f)
                all_titles.extend([doc.get("title", "") for doc in docs_from_data])
            except Exception:
                pass
    
    # Extract words from titles that match the query
    for title in all_titles:
        words = title.split()
        for word in words:
            if word.lower().startswith(query_lower) and len(word) > 2:
                suggestions.add(word)
    
    # Convert to list and sort by relevance
    suggestions_list = list(suggestions)
    suggestions_list.sort(key=lambda x: (
        x.lower().startswith(query_lower),  # Exact prefix matches first
        len(x)  # Shorter matches first
    ), reverse=True)
    
    return jsonify({
        "query": query,
        "suggestions": suggestions_list[:limit],
        "total_suggestions": len(suggestions_list)
    })


@app.route("/api/sorted_documents")
def get_sorted_documents():
    import time
    start_time = time.time()
    DATA_JSON_PATH = os.path.join(os.path.dirname(__file__), "../data.json")
    docs = []
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r") as f:
            try:
                docs = json.load(f)
            except Exception:
                pass
    # Sort by extracted_title (case-insensitive)
    sorted_docs = sorted(docs, key=lambda d: d.get("extracted_title", "").lower())
    elapsed = time.time() - start_time
    return jsonify({
        "documents": sorted_docs,
        "sort_time_seconds": round(elapsed, 4),
        "total": len(sorted_docs)
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
