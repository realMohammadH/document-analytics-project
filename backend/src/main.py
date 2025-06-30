import os
import re
import uuid
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO
from dotenv import load_dotenv
from supabase import create_client, Client
from postgrest.types import ReturnMethod

# Text extraction imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

# Configuration
app = Flask(__name__)
CORS(app)
# CORS(app, resources={r"/api/*": {"origins": r"https://.*\.netlify\.app"}})

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB file size limit

# Supabase Configuration
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

total_search_count = 0


# Helper functions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {
        "txt", "pdf", "doc", "docx"
    }

def highlight_search_terms(text, search_terms, highlight_tag="<mark>"):
    """Highlight search terms in text while preserving case sensitivity"""
    if not text or not search_terms:
        return text
    
    highlighted_text = text
    sorted_terms = sorted(search_terms, key=len, reverse=True)
    
    for term in sorted_terms:
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        highlighted_text = pattern.sub(f"{highlight_tag}\\g<0></mark>", highlighted_text)
    
    return highlighted_text

def extract_text_snippets(text, search_terms, snippet_length=100):
    """Extract text snippets around search terms"""
    if not text or not search_terms:
        return []
    
    snippets = []
    text_lower = text.lower()
    
    for term in search_terms:
        term_lower = term.lower()
        start_pos = 0
        
        while True:
            pos = text_lower.find(term_lower, start_pos)
            if pos == -1:
                break
            
            snippet_start = max(0, pos - snippet_length // 2)
            snippet_end = min(len(text), pos + len(term) + snippet_length // 2)
            
            snippet = text[snippet_start:snippet_end]
            
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(text):
                snippet = snippet + "..."
            
            highlighted_snippet = highlight_search_terms(snippet, [term])
            
            snippets.append({
                "term": term,
                "snippet": highlighted_snippet,
                "position": pos
            })
            
            start_pos = pos + 1
    
    # Remove duplicates and limit results
    unique_snippets = []
    seen_positions = set()
    
    for snippet in sorted(snippets, key=lambda x: x["position"]):
        is_duplicate = any(abs(snippet["position"] - seen_pos) < snippet_length 
                          for seen_pos in seen_positions)
        
        if not is_duplicate:
            unique_snippets.append(snippet)
            seen_positions.add(snippet["position"])
    
    return unique_snippets[:5]


def extract_text_from_file_stream(file_stream, file_type):
    """Extract text from a file stream without saving to disk"""
    text = ""
    file_stream.seek(0)
    
    if file_type == "pdf" and PyPDF2:
        try:
            reader = PyPDF2.PdfReader(file_stream)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception:
            text = ""
    elif file_type == "docx" and docx:
        try:
            doc = docx.Document(file_stream)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception:
            text = ""
    elif file_type == "txt":
        try:
            text = file_stream.read().decode('utf-8', errors='ignore')
        except Exception:
            text = ""
    
    file_stream.seek(0)
    return text.strip()

def extract_title_from_content(content):
    """Extract the first meaningful line as title"""
    if not content:
        return "Untitled Document"
    
    for line in content.splitlines():
        line = line.strip()
        if line and len(line) > 5:
            return line[:120]
    
    return "Untitled Document"

# Classification system
CLASSIFICATION_TREE = {
    "Academic": [
        "research", "study", "analysis", "methodology", "hypothesis", "conclusion", 
        "literature", "review", "citation", "reference", "academic", "university", 
        "college", "education", "learning", "teaching", "student", "professor", 
        "lecture", "assignment", "thesis", "dissertation", "paper", "journal", 
        "publication", "scholarly", "scientific", "experiment", "data", "statistics",
        "survey", "questionnaire", "interview", "observation", "theory", "concept",
        "framework", "model", "approach", "method", "technique", "procedure"
    ],
    "IT": [
        "software", "hardware", "programming", "code", "algorithm", "database", 
        "system", "network", "server", "client", "application", "web", "mobile", 
        "cloud", "security", "cybersecurity", "encryption", "authentication", 
        "authorization", "firewall", "virus", "malware", "backup", "recovery", 
        "maintenance", "update", "patch", "version", "deployment", "testing", 
        "debugging", "optimization", "performance", "scalability", "architecture", 
        "framework", "api", "interface", "user", "experience", "design", "development",
        "agile", "scrum", "devops", "ci", "cd", "git", "repository", "branch", "merge"
    ],
    "Business": [
        "business", "company", "organization", "corporation", "enterprise", "startup", 
        "management", "leadership", "strategy", "planning", "marketing", "sales", 
        "finance", "accounting", "budget", "revenue", "profit", "loss", "investment", 
        "stock", "market", "customer", "client", "product", "service", "brand", 
        "advertising", "promotion", "campaign", "competitive", "analysis", 
        "market", "research", "survey", "feedback", "satisfaction", "loyalty", 
        "retention", "acquisition", "growth", "expansion", "partnership", "alliance", 
        "merger", "acquisition", "contract", "agreement", "negotiation", "deal", 
        "transaction", "payment", "invoice", "billing", "pricing", "cost", "expense",
        "roi", "kpi", "metric", "performance", "target", "goal", "objective", "mission",
        "vision", "values", "culture", "team", "employee", "staff", "workforce", "hr",
        "recruitment", "training", "development", "career", "promotion", "compensation"
    ]
}

def classify_document(content):
    """Classify document based on predefined categories"""
    # If the document has no content, it cannot be classified.
    if not content:
        return "Other"
    
    # Convert content to lowercase to ensure case-insensitive matching.
    content_lower = content.lower()
    # This dictionary will hold the match count (score) for each category.
    scores = {}
    
    # Iterate through each category and its associated keywords in the classification tree.
    for category, keywords in CLASSIFICATION_TREE.items():
        score = 0
        # For each keyword in the category, count how many times it appears in the text.
        for keyword in keywords:
            # Use regex to find whole words only (e.g., 'art' doesn't match 'part').
            matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_lower))
            score += matches
        # Store the total score for the category.
        scores[category] = score
    
    # If no keywords were matched in any category, classify as "Other".
    if not scores or all(s == 0 for s in scores.values()):
        return "Other"

    # Find the category with the highest score.
    best_category = max(scores, key=lambda k: scores[k])
    best_score = scores[best_category]
    
    # Calculate a confidence score to determine if the classification is reliable.
    # It's the ratio of the best category's score to the total score of all matched keywords.
    total_matches = sum(scores.values())
    confidence = best_score / total_matches if total_matches > 0 else 0
    
    # Only return the best category if its confidence is above a certain threshold (30%).
    # Otherwise, the match is too weak, so we classify it as "Other".
    return best_category if confidence >= 0.3 else "Other"


# API Endpoints
@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Document Analytics System is running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    })


@app.route("/api/documents")
def get_documents():
    try:
        #sort functionality by upload date
        response = supabase.table('documents').select('*').order('upload_date', desc=True).execute()
        documents = response.data
        return jsonify(documents)
    except Exception as e:
        return jsonify({"error": "Could not fetch documents"}), 500

@app.route("/api/search")
def search_documents():
    # Start a timer to measure search performance.
    start_time = time.time()
    # Use a global variable to track how many searches have been performed.
    global total_search_count
    
    # Get the search query from the request's query parameters (e.g., /api/search?q=keyword).
    query = request.args.get("q", "")
    # If the query is empty, return a 400 Bad Request error.
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    # Increment the global search counter.
    total_search_count += 1
    # Split the query into a list of individual keywords, converted to lowercase.
    query_terms = query.lower().split()
    
    # This dictionary will store the results for each individual keyword.
    keyword_results = {}
    # This set will store unique document IDs to avoid double-counting.
    all_doc_ids = set()
    
    try:
        # Loop through each keyword to perform a separate search.
        for term in query_terms:
            # Use Supabase's full-text search on the 'content' column for the current term.
            response = supabase.table('documents').select('*').text_search('content', term).execute()
            docs = response.data
            
            # This list will hold all documents found for the current keyword.
            term_results = []
            for doc in docs:
                doc_id = doc.get("id")
                # Add the document's ID to the set of unique IDs.
                all_doc_ids.add(doc_id)
                
                # Find and extract relevant text snippets where the keyword appears in the document's content.
                text_snippets = extract_text_snippets(doc.get("content", ""), [term])
                
                # Append a structured dictionary of the document's info to the results for this term.
                term_results.append({
                    "id": doc_id,
                    "title": doc.get("title", ""),
                    "extracted_title": doc.get("extracted_title", ""),
                    "classification": doc.get("classification"),
                    "content_preview": doc.get("content_preview", ""),
                    "text_snippets": text_snippets,
                    "file_type": doc.get("file_type", ""),
                    "file_size": doc.get("file_size", 0),
                    "upload_date": doc.get("upload_date", "")
                })
            
            # Store the results for the current keyword.
            keyword_results[term] = {
                "keyword": term,
                "count": len(term_results),
                "documents": term_results
            }
        
        # Stop the timer.
        elapsed = time.time() - start_time
        
        # Construct the final JSON response with all the search information.
        return jsonify({
            "query": query,
            "query_terms": query_terms,
            "keyword_results": keyword_results,
            "total_unique_documents": len(all_doc_ids),
            "search_time_seconds": round(elapsed, 4)
        })
    except Exception as e:
        # If any part of the search fails, return a 500 Internal Server Error.
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@app.route("/api/statistics")
def get_statistics():
    try:
        response = supabase.table('documents').select('classification, file_size, word_count').execute()
        docs = response.data

        total_docs = len(docs)
        if total_docs == 0:
            return jsonify({
                "documents": {"total": 0, "total_size_mb": 0, "total_words": 0},
                "classifications": [],
                "search": {"total_searches": total_search_count}
            })

        total_size_mb = sum(doc.get("file_size", 0) for doc in docs) / (1024 * 1024)
        total_words = sum(doc.get("word_count", 0) for doc in docs)

        classifications = {}
        for doc in docs:
            cat = doc["classification"]
            classifications[cat] = classifications.get(cat, 0) + 1

        classification_dist = [
            {
                "name": cat,
                "count": count,
                "percentage": round((count / total_docs) * 100, 2),
            }
            for cat, count in classifications.items()
            if cat
        ]

        return jsonify({
            "documents": {
                "total": total_docs,
                "total_size_mb": round(total_size_mb, 2),
                "total_words": total_words,
            },
            "classifications": classification_dist,
            "search": {"total_searches": total_search_count},
        })
    except Exception as e:
        return jsonify({"error": "Could not fetch statistics"}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    # 1. --- FILE VALIDATION ---
    # Check if the 'file' key is in the request. This is where the uploaded file is expected.
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    # Check if the file has a name and if its extension is in our allowed list (e.g., pdf, docx, txt).
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # Sanitize the filename to prevent security risks like directory traversal.
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    # 2. --- FILE PROCESSING ---
    # Get the file extension and read the entire file into memory as bytes.
    file_type = filename.rsplit(".", 1)[1].lower()
    file_bytes = file.read()
    # Create an in-memory stream of the file's bytes, so our text extractor can read it.
    file_stream = BytesIO(file_bytes)

    # Extract all the text from the file stream based on its type (PDF, DOCX, etc.).
    content = extract_text_from_file_stream(file_stream, file_type)
    if not content:
        # If no text could be extracted, use a placeholder.
        content = f"[No extractable text found in {filename}]"
    
    # 3. --- UPLOAD TO CLOUD STORAGE ---
    try:
        # Create a unique filename using a UUID to prevent overwriting files with the same name.
        unique_filename = f"uploads/{uuid.uuid4()}_{filename}"
        # Upload the raw file bytes to Supabase's object storage.
        supabase.storage.from_("documents").upload(
            file=file_bytes,
            path=unique_filename,
            file_options={"content-type": file.content_type or 'application/octet-stream'}
        )
        # Get the public URL of the file we just uploaded.
        storage_url = supabase.storage.from_("documents").get_public_url(unique_filename)
    except Exception as e:
        # If the upload fails, log the error and return a server error response.
        print(f"Storage upload error: {str(e)}")
        print(f"Error type: {type(e)}")
        return jsonify({"error": f"Failed to upload file to storage: {str(e)}"}), 500

    # 4. --- CONTENT ANALYSIS & DATABASE PREPARATION ---
    # Analyze the extracted content to generate metadata.
    extracted_title = extract_title_from_content(content)
    classification = classify_document(content)
    
    # Prepare a dictionary with all the data we want to save in our database table.
    new_doc_data = {
        "title": filename,  # Original filename
        "extracted_title": extracted_title,  # Title found inside the document
        "file_type": file_type,
        "file_size": len(file_bytes),
        "classification": classification,
        "upload_date": datetime.utcnow().isoformat() + "Z", # Use UTC time in ISO format
        "content_preview": content[:200], # A short preview of the content
        "word_count": len(content.split()),
        "reading_time": len(content.split()) // 200, # Estimated reading time
        "content": content, # Full extracted text
        "storage_url": storage_url # Public URL to the original file
    }
    
    # 5. --- SAVE METADATA TO DATABASE ---
    try:
        # Insert the new document's metadata into the 'documents' table in our database.
        response = supabase.table('documents').insert(new_doc_data, returning=ReturnMethod.representation).execute()
        
        # If the insert operation fails or returns no data, send an error.
        if not response.data:
            return jsonify({"error": "Failed to save document"}), 500

        # If successful, return a success message along with the newly created document record.
        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "document": response.data[0],
        })
    except Exception as e:
        # If saving to the database fails, return a server error.
        return jsonify({"error": "Failed to save document metadata"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
