# Document Analytics & Management System

A full-stack, cloud-native application designed to upload, analyze, search, and manage a large collection of documents intelligently.

---

## ✨ Features

- **📄 Document Upload**: Upload documents in PDF, DOCX, and TXT formats.
- **🧠 Automatic Analysis**: Automatically extracts key information upon upload:
  - **Content Extraction**: Full text is extracted from all documents.
  - **Title Extraction**: Intelligently finds the document's true title.
  - **Classification**: Sorts documents into categories (e.g., Academic, Business, IT).
  - **Keyword Generation**: Identifies the most relevant keywords.
- **🚀 Multi-Keyword Search**: A powerful search engine to find documents based on content, with matching text highlighted.
- **📈 Analytics Dashboard**: View statistics about your document library, including total documents, total size, and classification distribution.
- **☁️ Cloud-Native**: Built with a modern architecture and deployed on scalable cloud platforms.

---

## 🏗️ Architecture

The project follows a modern three-tier architecture:

- **Frontend**: A responsive and dynamic single-page application built with **Vue.js** and hosted on **Netlify**.
- **Backend**: A robust REST API built with **Python (Flask)**, responsible for all business logic, document processing, and analysis. Hosted on **Render**.
- **Database & Storage**: A secure and scalable solution using **Supabase**, which provides a **PostgreSQL** database for metadata and **Object Storage** for the original files.

---

## 🚀 Getting Started

Follow these instructions to get a local copy of the project up and running for development and testing purposes.

### Prerequisites

- [Node.js](https://nodejs.org/) (v16 or later)
- [Python](https://www.python.org/) (v3.9 or later)
- A [Supabase](https://supabase.com/) account for the database and storage.

### Local Setup

**1. Clone the Repository**

```bash
git clone https://github.com/your-username/document-analytics-project.git
cd document-analytics-project
```

**2. Backend Setup**

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the required Python packages
pip install -r requirements.txt

# Create a .env file in the `backend/` directory and add your Supabase credentials:
# SUPABASE_URL="YOUR_SUPABASE_URL"
# SUPABASE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"

# Run the Flask server
python src/main.py
```
The backend API will be running at `http://127.0.0.1:5000`.

**3. Frontend Setup**

```bash
# Open a new terminal and navigate to the frontend directory
cd frontend

# Install the required npm packages
npm install

# Run the Vue development server
npm run dev
```
The frontend application will be available at `http://127.0.0.1:5173` (or another port if 5173 is busy).

---

## ⚙️ API Endpoints

The core API endpoints provided by the backend are:

| Method | Endpoint              | Description                                        |
|--------|-----------------------|----------------------------------------------------|
| `GET`  | `/api/health`         | Checks if the API is running.                      |
| `GET`  | `/api/documents`      | Fetches a list of all uploaded documents.          |
| `GET`  | `/api/search?q=`      | Searches documents for one or more keywords.       |
| `GET`  | `/api/statistics`     | Retrieves statistics for the analytics dashboard.  |
| `POST` | `/api/upload`         | Uploads a new document for processing and storage. |

---

## 🔗 Live Links

- **Live Application**: [Link to your deployed Netlify site]
- **GitHub Repository**: [Link to your GitHub repository] 