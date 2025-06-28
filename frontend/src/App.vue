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
                                <span class="confidence-score">({{ (file.confidence * 100).toFixed(1) }}%
                                    confidence)</span>
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
                                <span class="confidence-score">({{ (doc.confidence_score * 100).toFixed(1) }}%
                                    confidence)</span>
                            </p>
                            <p><strong>Keywords:</strong> {{ doc.keywords.join(', ') }}</p>
                            <p><strong>Upload Date:</strong> {{ formatDate(doc.upload_date) }}</p>
                            <p style="margin-top: 10px; color: #6c757d;">{{ doc.content_preview }}</p>
                        </div>
                    </div>
                </div>

                <!-- Search Tab -->
                <div v-if="activeTab === 'search'">
                    <h2>🔍 Search Documents</h2>
                    <p style="margin-bottom: 30px; color: #6c757d;">Find documents using advanced search capabilities
                    </p>

                    <div style="margin-bottom: 20px;">
                        <input v-model="searchQuery" type="text" class="search-box"
                            placeholder="Enter search terms (e.g., 'machine learning', 'business', 'legal')..."
                            @keyup.enter="performSearch">
                    </div>

                    <button class="btn" @click="performSearch" :disabled="!searchQuery.trim()">
                        🔍 Search Documents
                    </button>

                    <div v-if="searchResults.length > 0" style="margin-top: 30px;">
                        <h3>📋 Search Results ({{ searchResults.length }} found)</h3>
                        <p v-if="searchTime !== null" style="color: #6c757d; margin-bottom: 10px;">
                            ⏱️ Search took {{ searchTime }} seconds
                        </p>
                        <div v-for="result in searchResults" :key="result.id" class="search-result-card">
                            <div class="search-result-title" v-html="result.title"></div>
                            <div class="search-result-meta">
                                <span>📁 {{ result.source_file }}</span>
                                <span>🏷️ <span class="classification-badge">{{ result.classification }}</span></span>
                                <span>📊 {{ (result.confidence_score * 100).toFixed(1) }}% confidence</span>
                                <span>⭐ <span class="relevance-score">{{ result.relevance_score }}</span></span>
                            </div>
                            
                            <!-- Text Snippets Section -->
                            <div v-if="result.text_snippets && result.text_snippets.length > 0" class="text-snippets-section">
                                <h4 style="margin: 15px 0 10px 0; color: #495057; font-size: 1rem;">
                                    📍 Found {{ result.text_snippets.length }} text snippet{{ result.text_snippets.length > 1 ? 's' : '' }}:
                                </h4>
                                <div class="snippets-list">
                                    <div v-for="(snippet, index) in result.text_snippets" :key="index" class="snippet-item">
                                        <div class="snippet-header">
                                            <span class="snippet-term">🔍 "{{ snippet.term }}"</span>
                                            <span class="snippet-number">#{{ index + 1 }}</span>
                                        </div>
                                        <div class="snippet-text" v-html="snippet.snippet"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- No snippets found message -->
                            <div v-else-if="result.matches_found && result.matches_found.length > 0" class="text-snippets-section">
                                <div style="text-align: center; color: #6c757d; padding: 10px;">
                                    📄 Full document content available for detailed search
                                </div>
                            </div>
                             
                        </div>
                    </div>

                    <div v-else-if="searchPerformed && searchResults.length === 0" class="loading">
                        <p>🔍 No results found for "{{ lastSearchQuery }}"</p>
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
                            <div class="stat-card">
                                <div class="stat-number">{{ (statistics.documents.average_confidence * 100).toFixed(1)
                                    }}%</div>
                                <div class="stat-label">Avg Confidence</div>
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

                        <h3>🔑 Top Keywords</h3>
                        <div style="margin-top: 20px;">
                            <div v-for="keyword in statistics.keywords.top_keywords" :key="keyword.keyword"
                                style="display: inline-block; margin: 5px; padding: 8px 16px; background: #007bff; color: white; border-radius: 20px; font-size: 0.9rem;">
                                {{ keyword.keyword }} ({{ keyword.frequency }})
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
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

        // API base URL - change this for local development
        const API_BASE = 'http://localhost:5000/api'
        // const API_BASE = 'https://document-analytics-project.onrender.com/api'


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

        const performSearch = async () => {
            if (!searchQuery.value.trim()) return

            try {
                const response = await axios.get(`${API_BASE}/search`, {
                    params: { q: searchQuery.value }
                });
                searchResults.value = response.data.results
                searchTime.value = response.data.search_time_seconds
                searchPerformed.value = true
                lastSearchQuery.value = searchQuery.value

                fetchStatistics();
            } catch (error) {
                console.error('Error performing search:', error)
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
                    fileObj.confidence = newDoc.confidence_score;
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

        // Lifecycle
        onMounted(() => {
            fetchDocuments()
            fetchStatistics()
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
            fetchDocuments,
            fetchStatistics,
            performSearch,
            triggerFileInput,
            handleFileSelect,
            handleFileDrop,
            formatFileSize,
            formatDate
        }
    }
}
</script>