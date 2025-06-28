import os
import re
import uuid
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# --- Configuration ---
app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes
# Replace 'your-netlify-app-name' with the real name of your Netlify site
# CORS(
#     app,
#     origins=["https://685f8e92966d03140c38af75--eloquent-daffodil-e2c0a3.netlify.app"],
# )
# CORS(app, resources={r"/api/*": {"origins": "*"}})

CORS(app, resources={r"/api/*": {"origins": r"https://.*\.netlify\.app"}})

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB file size limit
app.config["UPLOAD_FOLDER"] = "uploads"

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# --- In-Memory Data Store ---
sample_documents = []

documents = sample_documents
total_search_count = 0


# --- Helper Functions ---
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "txt",
        "pdf",
        "doc",
        "docx",
    }


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


# --- API Endpoints ---
@app.route("/api/health")
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "message": "Document Analytics System with File Upload is running",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "3.0.0",
            "features": {
                "document_management": True,
                "file_upload": True,
                "keyword_extraction": True,
                "advanced_search": True,
                "analytics": True,
                "vue_js_compatible": True,
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
    global total_search_count
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    total_search_count += 1
    query_terms = query.lower().split()
    results = []

    for doc in documents:
        content = doc["content_preview"].lower()
        title = doc["title"].lower()
        score = 0

        for term in query_terms:
            score += title.count(term) * 3
            score += content.count(term) * 1
            if term in [kw.lower() for kw in doc["keywords"]]:
                score += 2

        if score > 0:
            highlighted_title = doc["title"]
            highlighted_content = doc["content_preview"]
            for term in query_terms:
                highlighted_title = re.sub(
                    f"({re.escape(term)})",
                    r"<mark>\1</mark>",
                    highlighted_title,
                    flags=re.IGNORECASE,
                )
                highlighted_content = re.sub(
                    f"({re.escape(term)})",
                    r"<mark>\1</mark>",
                    highlighted_content,
                    flags=re.IGNORECASE,
                )

            results.append(
                {
                    "id": doc["id"],
                    "title": highlighted_title,
                    "classification": doc["classification"],
                    "confidence_score": doc["confidence_score"],
                    "relevance_score": score,
                    "content_snippet": highlighted_content,
                }
            )

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return jsonify({"query": query, "results": results, "total_results": len(results)})


@app.route("/api/statistics")
def get_statistics():
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
            },
        }
    )


@app.route("/api/classifications")
def get_classifications():
    categories = sorted(list(set(doc["classification"] for doc in documents)))
    return jsonify({"categories": categories, "total_categories": len(categories)})


@app.route("/api/classify", methods=["POST"])
def classify_content():
    data = request.get_json()
    if not data or "content" not in data:
        return jsonify({"error": "Content is required"}), 400

    classification, confidence = classify_document(data["content"])
    keywords = extract_keywords(data["content"])

    return jsonify(
        {
            "classification": classification,
            "confidence_score": confidence,
            "keywords": keywords,
            "processing_time_ms": 50,
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

        # Simulate content extraction
        content = f"Content extracted from {filename}"
        classification, confidence = classify_document(content)
        keywords = extract_keywords(content)

        new_doc = {
            "id": len(documents) + 1,
            "title": filename,
            "file_type": filename.rsplit(".", 1)[1].lower(),
            "file_size": os.path.getsize(file_path),
            "classification": classification,
            "confidence_score": confidence,
            "keywords": keywords,
            "upload_date": datetime.utcnow().isoformat() + "Z",
            "content_preview": content[:200],
            "word_count": len(content.split()),
            "reading_time": len(content.split()) // 200,
        }
        documents.append(new_doc)

        return jsonify(
            {
                "success": True,
                "message": "File uploaded successfully",
                "document": new_doc,
            }
        )

    return jsonify({"error": "File type not allowed"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
