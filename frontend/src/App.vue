<template>
    <div class="container">
        <div class="header">
            <h1>🚀 Document Analytics System</h1>
            <p>Cloud-Based Document Processing & Analytics Platform - Vue.js Edition</p>
        </div>

        <div class="main-content">
            <div class="tabs">
                <button v-for="tab in tabs" :key="tab.id" :class="['tab', { active: activeTab === tab.id }]"
                    @click="activeTab = tab.id">
                    {{ tab.name }}
                </button>
            </div>

            <div class="tab-content">
                <!-- Dashboard Tab -->
                <div v-if="activeTab === 'dashboard'">
                    <h2>📊 System Overview</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Welcome to the Document Analytics System dashboard
                    </p>

                    <div class="stats-grid" v-if="statistics">
                        <div class="stat-card">
                            <div class="stat-number">{{ statistics.documents.total }}</div>
                            <div class="stat-label">Total Documents</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ statistics.documents.total_size_mb }}MB</div>
                            <div class="stat-label">Total Size</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ statistics.search.total_searches }}</div>
                            <div class="stat-label">Total Searches</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ statistics.classifications.length }}</div>
                            <div class="stat-label">Categories</div>
                        </div>
                    </div>

                    <h3>🎯 Quick Actions</h3>
                    <div style="margin-top: 20px;">
                        <button class="btn" @click="activeTab = 'upload'">📤 Upload Documents</button>
                        <button class="btn" @click="activeTab = 'documents'">📄 View All Documents</button>
                        <button class="btn" @click="activeTab = 'search'">🔍 Search Documents</button>
                        <button class="btn" @click="activeTab = 'analytics'">📈 View Analytics</button>
                    </div>
                </div>

                <!-- Upload Tab -->
                <div v-if="activeTab === 'upload'">
                    <h2>📤 Upload Documents</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Upload your documents for analysis and
                        classification</p>

                    <div v-if="uploadMessage" :class="uploadMessage.type">
                        {{ uploadMessage.text }}
                    </div>

                    <div class="upload-area" :class="{ dragover: isDragOver }" @click="triggerFileInput"
                        @dragover.prevent="isDragOver = true" @dragleave.prevent="isDragOver = false"
                        @drop.prevent="handleFileDrop">
                        <div class="upload-icon">📁</div>
                        <h3>Drop files here or click to browse</h3>
                        <p style="margin-top: 10px; color: #6c757d;">
                            Supported formats: PDF, DOC, DOCX, TXT (Max 10MB)
                        </p>
                        <button class="btn btn-success" style="margin-top: 15px;">
                            Choose Files
                        </button>
                    </div>

                    <input ref="fileInput" type="file" multiple accept=".pdf,.doc,.docx,.txt" style="display: none"
                        @change="handleFileSelect">

                    <div v-if="uploadedFiles.length > 0">
                        <h3>📋 Uploaded Files</h3>
                        <div v-for="file in uploadedFiles" :key="file.id" class="document-card">
                            <h4>{{ file.name }}</h4>
                            <p><strong>Size:</strong> {{ formatFileSize(file.size) }}</p>
                            <p><strong>Type:</strong> {{ file.type }}</p>
                            <p v-if="file.classification">
                                <strong>Classification:</strong> {{ file.classification }}
                            </p>
                            <p v-if="file.status === 'processing'" style="color: #007bff;">🔄 Processing...</p>
                            <p v-if="file.status === 'completed'" style="color: #28a745;">✅ Completed</p>
                        </div>
                    </div>
                </div>

                <!-- Documents Tab -->
                <div v-if="activeTab === 'documents'">
                    <h2>📄 Document Library</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Browse and manage your document collection</p>

                    <div v-if="loading" class="loading">
                        <p>🔄 Loading documents...</p>
                    </div>

                    <div v-else-if="documents.length === 0" class="loading">
                        <p>📭 No documents found</p>
                    </div>

                    <div v-else>
                        <div v-for="doc in documents" :key="doc.id" class="document-card">
                            <h4>{{ doc.title }}</h4>
                            <p><strong>Type:</strong> {{ doc.file_type.toUpperCase() }}</p>
                            <p><strong>Size:</strong> {{ formatFileSize(doc.file_size) }}</p>
                            <p><strong>Classification:</strong>
                                <span class="classification-badge">{{ doc.classification }}</span>
                            </p>
                            <p><strong>Keywords:</strong> {{ doc.keywords.join(', ') }}</p>
                            <p><strong>Upload Date:</strong> {{ formatDate(doc.upload_date) }}</p>
                            <div style="margin-top: 15px;">
                                <a 
                                    v-if="doc.storage_url" 
                                    :href="doc.storage_url" 
                                    target="_blank" 
                                    class="btn btn-secondary"
                                >
                                    ⬇️ Download Original
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Search Tab -->
                <div v-if="activeTab === 'search'">
                    <h2>🔍 Multi-Keyword Search</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Find documents using multiple keywords for precise searching</p>

                    <!-- Multi-Keyword Search Interface -->
                    <div class="multi-keyword-search">
                        <!-- Active Keywords Display -->
                        <div v-if="searchKeywords.length > 0" class="active-keywords">
                            <h4>🔑 Active Keywords:</h4>
                            <div class="keyword-tags">
                                <span v-for="(keyword, index) in searchKeywords" :key="index" class="keyword-tag">
                                    {{ keyword }}
                                    <button @click="removeKeyword(index)" class="remove-keyword">×</button>
                                </span>
                            </div>
                        </div>

                        <!-- Keyword Input Section -->
                        <div class="keyword-input-section">
                            <div class="input-group">
                                <input 
                                    v-model="newKeyword" 
                                    type="text" 
                                    class="search-box keyword-input"
                                    placeholder="Enter a keyword..."
                                    @keyup.enter="addKeyword"
                                >
                                <button class="btn btn-primary" @click="addKeyword" :disabled="!newKeyword.trim()">
                                    ➕ Add Keyword
                                </button>
                            </div>
                        </div>

                        <!-- Search Controls -->
                        <div class="search-controls">
                            <button 
                                class="btn btn-success" 
                                @click="performMultiKeywordSearch" 
                                :disabled="searchKeywords.length === 0"
                            >
                                🔍 Search with {{ searchKeywords.length }} keyword{{ searchKeywords.length !== 1 ? 's' : '' }}
                            </button>
                            <button 
                                class="btn btn-secondary" 
                                @click="clearAllKeywords"
                                :disabled="searchKeywords.length === 0"
                            >
                                🗑️ Clear All
                            </button>
                        </div>
                    </div>

                    <!-- Search Results -->
                    <div v-if="searchResults.length > 0 || keywordResults" style="margin-top: 30px;">
                        <h3>📋 Search Results</h3>
                        <p v-if="searchTime !== null" style="color: #6c757d; margin-bottom: 10px;">
                            ⏱️ Search took {{ searchTime }} seconds
                        </p>
                        <p v-if="totalUniqueDocuments !== null" style="color: #495057; margin-bottom: 15px;">
                            📄 Found {{ totalUniqueDocuments }} unique document{{ totalUniqueDocuments !== 1 ? 's' : '' }} total
                        </p>
                        
                        <!-- Results grouped by keyword -->
                        <div v-for="(keywordData, keyword) in keywordResults" :key="keyword" class="keyword-results-section">
                            <div class="keyword-header">
                                <h4>🔍 Results for "{{ keyword }}" ({{ keywordData.count }} found)</h4>
                            </div>
                            
                            <div v-if="keywordData.count === 0" class="no-results-message">
                                <p>No documents found containing "{{ keyword }}"</p>
                            </div>
                            
                            <div v-else>
                                <div v-for="result in keywordData.documents" :key="`${keyword}-${result.id}`" class="search-result-card">
                                    <div class="search-result-title">{{ result.title }}</div>
                                    <div class="search-result-meta">
                                        <span>🏷️ <span class="classification-badge">{{ result.classification }}</span></span>
                                        <span style="margin-left: 15px;">📁 {{ result.file_type.toUpperCase() }}</span>
                                    </div>
                                    
                                    <!-- Text Snippets Section -->
                                    <div v-if="result.text_snippets && result.text_snippets.length > 0" class="text-snippets-section">
                                        <h5 style="margin: 10px 0 8px 0; color: #495057; font-size: 0.9rem;">
                                            📍 Text snippets:
                                        </h5>
                                        <div class="snippets-list">
                                            <div v-for="(snippet, index) in result.text_snippets" :key="index" class="snippet-item">
                                                <div class="snippet-text" v-html="snippet.snippet"></div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <!-- Content preview if no snippets -->
                                    <div v-else-if="result.content_preview" class="content-preview">
                                        <p>{{ result.content_preview }}...</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div v-else-if="searchPerformed && !keywordResults" class="loading">
                        <p>🔍 No results found for keywords: "{{ lastSearchQuery }}"</p>
                    </div>
                </div>

                <!-- Analytics Tab -->
                <div v-if="activeTab === 'analytics'">
                    <h2>📈 Analytics Dashboard</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Comprehensive analytics and insights</p>

                    <div v-if="statistics">
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-number">{{ statistics.documents.total }}</div>
                                <div class="stat-label">Total Documents</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{{ statistics.documents.total_size_mb }}MB</div>
                                <div class="stat-label">Storage Used</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-number">{{ statistics.documents.total_words.toLocaleString() }}</div>
                                <div class="stat-label">Total Words</div>
                            </div>

                        </div>

                        <h3>📊 Document Classifications</h3>
                        <div style="margin-top: 20px;">
                            <div v-for="classification in statistics.classifications" :key="classification.name"
                                style="margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span><strong>{{ classification.name }}</strong></span>
                                    <span>{{ classification.count }} documents ({{ classification.percentage }}%)</span>
                                </div>
                                <div
                                    style="width: 100%; background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 8px;">
                                    <div style="background: #007bff; height: 100%; border-radius: 4px;"
                                        :style="{ width: classification.percentage + '%' }"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'

export default {
    name: 'DocumentAnalyticsApp',
    setup() {
        // Reactive data
        const activeTab = ref('dashboard')
        const documents = ref([])
        const statistics = ref(null)
        const loading = ref(false)
        const searchQuery = ref('')
        const searchResults = ref([])
        const searchPerformed = ref(false)
        const lastSearchQuery = ref('')
        const uploadedFiles = ref([])
        const isDragOver = ref(false)
        const uploadMessage = ref(null)
        const fileInput = ref(null)
        const searchTime = ref(null)
        const searchKeywords = ref([])
        const newKeyword = ref('')
        const keywordResults = ref(null)
        const totalUniqueDocuments = ref(null)
        
        // API base URL - change this for local development
        // const API_BASE = 'http://localhost:5000/api'
        const API_BASE = 'https://document-analytics-project.onrender.com/api'


        const tabs = [
            { id: 'dashboard', name: '📊 Dashboard' },
            { id: 'upload', name: '📤 Upload' },
            { id: 'documents', name: '📄 Documents' },
            { id: 'search', name: '🔍 Search' },
            { id: 'analytics', name: '📈 Analytics' }
        ]

        // Methods
        const fetchDocuments = async () => {
            try {
                loading.value = true
                const response = await axios.get(`${API_BASE}/documents`)
                documents.value = response.data.documents
            } catch (error) {
                console.error('Error fetching documents:', error)
            } finally {
                loading.value = false
            }
        }

        const fetchStatistics = async () => {
            try {
                const response = await axios.get(`${API_BASE}/statistics`)
                statistics.value = response.data
            } catch (error) {
                console.error('Error fetching statistics:', error)
            }
        }

        const performMultiKeywordSearch = async () => {
            if (searchKeywords.value.length === 0) return

            try {
                const response = await axios.get(`${API_BASE}/search`, {
                    params: { q: searchKeywords.value.join(' ') }
                });
                // Clear old format results
                searchResults.value = []
                // Set new format results
                keywordResults.value = response.data.keyword_results
                totalUniqueDocuments.value = response.data.total_unique_documents
                searchTime.value = response.data.search_time_seconds
                searchPerformed.value = true
                lastSearchQuery.value = searchKeywords.value.join(' ')

                fetchStatistics();
            } catch (error) {
                console.error('Error performing multi-keyword search:', error)
            }
        }

        const triggerFileInput = () => {
            fileInput.value.click()
        }

        const handleFileSelect = (event) => {
            const files = Array.from(event.target.files)
            processFiles(files)
        }

        const handleFileDrop = (event) => {
            isDragOver.value = false
            const files = Array.from(event.dataTransfer.files)
            processFiles(files)
        }

        const processFiles = async (files) => {
            uploadMessage.value = null;

            for (const file of files) {
                // --- Keep your existing validation logic ---
                if (file.size > 10 * 1024 * 1024) {
                    uploadMessage.value = {
                        type: 'error',
                        text: `File ${file.name} is too large. Maximum size is 10MB.`
                    };
                    continue;
                }
                const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowedTypes.includes(fileExtension)) {
                    uploadMessage.value = {
                        type: 'error',
                        text: `File ${file.name} has an unsupported format. Allowed: PDF, DOC, DOCX, TXT`
                    };
                    continue;
                }

                const fileObj = {
                    id: Date.now() + Math.random(),
                    name: file.name,
                    size: file.size,
                    type: fileExtension,
                    status: 'processing',
                };

                uploadedFiles.value.push(fileObj);

                // --- START: MODIFIED UPLOAD LOGIC ---
                try {
                    // Create a FormData object to send the file
                    const formData = new FormData();
                    formData.append('file', file);

                    // Call the correct /api/upload endpoint
                    const response = await axios.post(`${API_BASE}/upload`, formData, {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    });

                    // Update the frontend object with data from the successful upload
                    const newDoc = response.data.document;
                    fileObj.classification = newDoc.classification;
                    fileObj.keywords = newDoc.keywords;
                    fileObj.status = 'completed';

                    uploadMessage.value = {
                        type: 'success',
                        text: `File ${file.name} uploaded successfully!`
                    };

                    // Refresh the main documents list and statistics from the server
                    await fetchDocuments();
                    await fetchStatistics();

                } catch (error) {
                    console.error('Error uploading file:', error);
                    fileObj.status = 'error';
                    uploadMessage.value = {
                        type: 'error',
                        text: `Error uploading file ${file.name}: ${error.response?.data?.error || error.message}`
                    };
                }
                // --- END: MODIFIED UPLOAD LOGIC ---
            }
        };


        const readFileContent = (file) => {
            return new Promise((resolve, reject) => {
                const reader = new FileReader()
                reader.onload = (e) => {
                    // For demo purposes, we'll use the filename and some sample content
                    // In a real implementation, you'd parse the actual file content
                    const sampleContent = `This is a document titled "${file.name}". The content would be extracted from the actual file in a real implementation. This demo shows the classification capabilities of the system.`
                    resolve(sampleContent)
                }
                reader.onerror = reject
                reader.readAsText(file)
            })
        }

        const formatFileSize = (bytes) => {
            if (bytes === 0) return '0 Bytes'
            const k = 1024
            const sizes = ['Bytes', 'KB', 'MB', 'GB']
            const i = Math.floor(Math.log(bytes) / Math.log(k))
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
        }

        const formatDate = (dateString) => {
            return new Date(dateString).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            })
        }

        const addKeyword = () => {
            if (newKeyword.value.trim() && !searchKeywords.value.includes(newKeyword.value.trim())) {
                searchKeywords.value.push(newKeyword.value.trim())
                newKeyword.value = ''
            }
        }

        const removeKeyword = (index) => {
            searchKeywords.value.splice(index, 1)
            // Clear search results when removing a keyword
            searchResults.value = []
            keywordResults.value = null
            totalUniqueDocuments.value = null
            searchPerformed.value = false
            lastSearchQuery.value = ''
            searchTime.value = null
        }

        const clearAllKeywords = () => {
            searchKeywords.value = []
            searchResults.value = []
            keywordResults.value = null
            totalUniqueDocuments.value = null
            searchPerformed.value = false
            lastSearchQuery.value = ''
            searchTime.value = null
        }

        // Lifecycle
        onMounted(() => {
            fetchDocuments()
            fetchStatistics()
        })

        // Watch for changes in searchKeywords
        watch(searchKeywords, (newKeywords) => {
            if (newKeywords.length === 0) {
                searchResults.value = []
                keywordResults.value = null
                totalUniqueDocuments.value = null
                searchPerformed.value = false
                lastSearchQuery.value = ''
                searchTime.value = null
            }
        })

        return {
            activeTab,
            tabs,
            documents,
            statistics,
            loading,
            searchQuery,
            searchResults,
            searchPerformed,
            lastSearchQuery,
            uploadedFiles,
            isDragOver,
            uploadMessage,
            fileInput,
            searchTime,
            searchKeywords,
            newKeyword,
            keywordResults,
            totalUniqueDocuments,
            fetchDocuments,
            fetchStatistics,
            performMultiKeywordSearch,
            triggerFileInput,
            handleFileSelect,
            handleFileDrop,
            formatFileSize,
            formatDate,
            addKeyword,
            removeKeyword,
            clearAllKeywords
        }
    }
}
</script>

<style scoped>
/* Multi-Keyword Search Styles */
.multi-keyword-search {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
}

.active-keywords {
    margin-bottom: 20px;
}

.active-keywords h4 {
    margin-bottom: 10px;
    color: #495057;
}

.keyword-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.keyword-tag {
    background: #007bff;
    color: white;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

.remove-keyword {
    background: none;
    border: none;
    color: white;
    font-size: 1.2rem;
    cursor: pointer;
    padding: 0;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background-color 0.2s;
}

.remove-keyword:hover {
    background: rgba(255, 255, 255, 0.2);
}

.keyword-input-section {
    margin-bottom: 20px;
}

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
    align-items: center;
}

.keyword-input {
    flex: 1;
    min-width: 200px;
    height: 40px;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: 0;
}

.keyword-suggestions {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    max-height: 200px;
    overflow-y: auto;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.suggestions-header {
    padding: 10px 15px;
    background: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    font-weight: 600;
    color: #495057;
}

.suggestions-list {
    max-height: 150px;
    overflow-y: auto;
}

.suggestion-item {
    padding: 8px 15px;
    cursor: pointer;
    transition: background-color 0.2s;
    border-bottom: 1px solid #f1f3f4;
}

.suggestion-item:hover {
    background: #e9ecef;
}

.suggestion-highlighted {
    background: #007bff !important;
    color: white;
}

.suggestion-item:last-child {
    border-bottom: none;
}

.search-controls {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.search-tips {
    background: white;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #28a745;
}

.search-tips h4 {
    margin-bottom: 10px;
    color: #495057;
}

.search-tips ul {
    margin: 0;
    padding-left: 20px;
}

.search-tips li {
    margin-bottom: 5px;
    color: #6c757d;
}

.matched-keywords {
    margin: 10px 0;
    padding: 8px 12px;
    background: #e8f5e8;
    border-radius: 6px;
    border-left: 3px solid #28a745;
}

.matched-label {
    font-weight: 600;
    color: #155724;
    margin-right: 8px;
}

.matched-keyword {
    background: #28a745;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    margin-right: 5px;
    display: inline-block;
    margin-bottom: 3px;
}

/* Keyword Results Section Styles */
.keyword-results-section {
    margin-bottom: 30px;
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e9ecef;
}

.keyword-header {
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid #dee2e6;
}

.keyword-header h4 {
    margin: 0;
    color: #495057;
    font-size: 1.1rem;
}

.no-results-message {
    text-align: center;
    padding: 20px;
    color: #6c757d;
    font-style: italic;
}

.search-result-card {
    background: white;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 8px;
    border: 1px solid #dee2e6;
    transition: box-shadow 0.2s;
}

.search-result-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-result-title {
    font-weight: 600;
    color: #212529;
    margin-bottom: 8px;
    font-size: 1rem;
}

.search-result-meta {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    font-size: 0.9rem;
    color: #6c757d;
}

.content-preview {
    margin-top: 10px;
    padding: 10px;
    background: #f8f9fa;
    border-radius: 6px;
    font-size: 0.9rem;
    color: #495057;
    line-height: 1.5;
}

.text-snippets-section {
    margin-top: 10px;
}

.snippets-list {
    margin-top: 5px;
}

.snippet-item {
    margin-bottom: 8px;
    padding: 8px;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 3px solid #007bff;
}

.snippet-text {
    font-size: 0.9rem;
    line-height: 1.5;
    color: #495057;
}

/* Responsive Design */
@media (max-width: 768px) {
    .input-group {
        flex-direction: column;
    }
    
    .search-controls {
        flex-direction: column;
    }
    
    .keyword-tags {
        gap: 6px;
    }
    
    .keyword-tag {
        font-size: 0.8rem;
        padding: 4px 10px;
    }
    
    .keyword-results-section {
        padding: 15px;
    }
}
</style>