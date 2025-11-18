<template>
    <div class="app-container">
        <!-- Top Navigation Bar -->
        <nav class="top-nav">
            <div class="nav-content">
                <div class="nav-brand">
                    <span class="brand-icon">♪</span>
                    <span class="brand-text">Sonic Pi Generator</span>
                </div>
                <div class="nav-status">
                    <span class="status-indicator" :class="{ active: isGenerating }"></span>
                    <span class="status-text">{{ statusText }}</span>
                </div>
            </div>
        </nav>

        <!-- Main Content Area -->
        <div class="main-content">
            <!-- Left Panel: Input & Controls -->
            <aside class="left-panel">
                <div class="panel-section">
                    <div class="section-header">
                        <h2>Input Configuration</h2>
                    </div>

                    <div class="input-group">
                        <label class="input-label">Music Description</label>
                        <textarea v-model="prompt" class="input-field"
                            placeholder="Describe your desired music style, tempo, mood, instruments..."
                            rows="6"></textarea>
                    </div>

                    <div class="action-panel">
                        <button @click="generateMusic" :disabled="isGenerating || !prompt.trim()"
                            class="btn btn-primary btn-large">
                            <span class="btn-icon">▶</span>
                            <span style="margin-left: 20px;">Generate</span>
                        </button>
                    </div>

                    <div class="control-grid">
                        <button @click="showFeedbackDialog" :disabled="!generatedCode || isGenerating"
                            class="btn btn-control">
                            <span class="btn-label">Feedback</span>
                        </button>
                        <button @click="showStyleDialog" :disabled="!generatedCode || isGenerating"
                            class="btn btn-control">
                            <span class="btn-label">Style Transfer</span>
                        </button>
                        <button @click="chooseHistory" class="btn btn-control">
                            <span class="btn-label">Choose History</span>
                        </button>
                    </div>

                    <!-- History File Selection -->
                    <div class="history-section" v-if="historyView">
                        <div class="input-label" style="margin-bottom: 12px;">
                            📁 History Files (for Style Transfer)
                        </div>
                        <div class="history-controls">
                            <select v-model="selectedHistoryFile" class="history-select" @change="onHistoryFileSelected"
                                @click="refreshHistory">
                                <option :value="'Select a history file'">Select a history file...</option>
                                <option v-for="file in historyFiles" :key="file.filename" :value="file.filename">
                                    {{ file.display_name }}
                                </option>
                            </select>
                            <div class="icon-btn refresh-btn" title="Refresh history">
                                {{ selectedHistoryFile }}
                            </div>
                        </div>
                        <div class="history-actions">
                            <button @click="loadHistoryFile" :disabled="!selectedHistoryFile || isGenerating"
                                class="btn btn-control btn-small">
                                📂 Load Selected
                            </button>
                            <button @click="deleteHistoryFile" :disabled="!selectedHistoryFile || isGenerating"
                                class="btn btn-danger btn-small">
                                🗑️ Delete
                            </button>
                        </div>
                    </div>

                    <!-- Progress Indicator -->
                    <div v-if="isGenerating" class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-bar-fill"></div>
                        </div>
                        <p class="progress-text">Processing...</p>
                    </div>
                </div>
            </aside>

            <!-- Right Panel: Output -->
            <main class="right-panel">
                <!-- Log Output -->
                <section class="log-section">
                    <div class="section-header">
                        <h2 style="margin-right: 120px;">Generation Log</h2>
                        <div class="header-actions">
                            <button class="icon-btn" title="Clear log" @click="clearLogs">
                                <span>🗑️</span>
                            </button>
                        </div>
                    </div>
                    <div class="log-container" ref="logDisplay">
                        <div v-for="(log, index) in logs" :key="index" class="log-line">
                            <p>{{ log }}</p>
                        </div>
                        <div v-if="logs.length === 0" class="empty-state-small">
                            <p>Log entries will appear here</p>
                        </div>
                    </div>
                </section>
                <!-- Code Output -->
                <section class="output-section">
                    <div class="section-header">
                        <h2 style="margin-right: 120px;">Generated Code</h2>
                        <div class="header-actions">
                            <button class="icon-btn" title="Copy code" @click="copyCode">
                                <span>📋</span>
                            </button>
                        </div>
                    </div>
                    <div class="code-container">
                        <pre v-if="generatedCode" class="code-content"><code>{{ generatedCode }}</code></pre>
                        <div v-else class="empty-state">
                            <div class="empty-icon">{ }</div>
                            <p>No code generated yet</p>
                            <p class="empty-hint">Enter a description and click Generate to start</p>
                        </div>
                    </div>
                </section>
            </main>
        </div>

        <!-- Feedback Modal -->
        <div v-if="showFeedback" class="modal-backdrop" @click.self="showFeedback = false">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h3>Provide Feedback</h3>
                    <button @click="showFeedback = false" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <p class="modal-description">Describe what you'd like to improve in the generated music</p>
                    <textarea v-model="feedbackText" class="modal-input"
                        placeholder="e.g., Slower tempo, add more bass, increase harmony layers..." rows="6"></textarea>
                </div>
                <div class="modal-footer">
                    <button @click="showFeedback = false" class="btn btn-secondary">Cancel</button>
                    <button @click="submitFeedback" class="btn btn-primary">Submit Feedback</button>
                </div>
            </div>
        </div>

        <!-- Style Transfer Modal -->
        <div v-if="showStyle" class="modal-backdrop" @click.self="showStyle = false">
            <div class="modal-dialog">
                <div class="modal-header">
                    <h3>Style Transfer</h3>
                    <button @click="showStyle = false" class="modal-close">×</button>
                </div>
                <div class="modal-body">
                    <p class="modal-description">Specify the musical style you want to apply</p>
                    <div class="style-tags">
                        <span class="tag" @click="styleRequest = 'Convert to rock style'">Rock</span>
                        <span class="tag" @click="styleRequest = 'Convert to jazz style'">Jazz</span>
                        <span class="tag" @click="styleRequest = 'Convert to classical style'">Classical</span>
                        <span class="tag" @click="styleRequest = 'Convert to electronic style'">Electronic</span>
                        <span class="tag" @click="styleRequest = 'Convert to ambient style'">Ambient</span>
                    </div>
                    <textarea v-model="styleRequest" class="modal-input"
                        placeholder="e.g., Convert to rock style, make it more jazzy, add electronic elements..."
                        rows="4"></textarea>
                </div>
                <div class="modal-footer">
                    <button @click="showStyle = false" class="btn btn-secondary">Cancel</button>
                    <button @click="submitStyleTransfer" class="btn btn-primary">Apply Style</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onBeforeUnmount, onMounted } from 'vue';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

// 响应式数据
const prompt = ref('');
const generatedCode = ref('');
const originalPrompt = ref('');
const midiPath = ref<string | null>(null);
const currentCodeFile = ref<string | null>(null);
const logs = ref<string[]>([]);
const statusText = ref('Ready to generate');
const isGenerating = ref(false);
const showFeedback = ref(false);
const showStyle = ref(false);
const feedbackText = ref('');
const styleRequest = ref('');
const currentTaskId = ref<string | null>(null);
const logDisplay = ref<HTMLElement | null>(null);
const historyView = ref(false)

// 历史文件管理
const historyFiles = ref<HistoryFile[]>([]);
const selectedHistoryFile = ref<string | null>('Select a history file');

let pollingInterval: number | null = null;

// 接口定义
interface TaskResponse {
    task_id: string;
}

interface TaskStatus {
    task_id: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    progress: string;
    logs: string[];
    result_code: string | null;
    midi_path: string | null;
    code_file_path: string | null;
    action: string | null;
    error_message: string | null;
}

interface HistoryFile {
    filename: string;
    display_name: string;
    modified_time: string;
    size: number;
}

interface HistoryResponse {
    files: HistoryFile[];
    count: number;
}

interface HistoryFileContent {
    filename: string;
    code: string;
    modified_time: string;
}

// 组件挂载时加载历史文件
onMounted(() => {
    refreshHistory();
});

// 刷新历史文件列表
const refreshHistory = async () => {
    try {
        const response = await axios.get<HistoryResponse>(`${API_BASE_URL}/history`);
        historyFiles.value = response.data.files;
    } catch (error) {
        console.error('Failed to load history:', error);
    }
};

// 历史文件选择事件
const onHistoryFileSelected = () => {
}

// 加载选中的历史文件
const loadHistoryFile = async () => {
    if (!selectedHistoryFile.value) return;
    if (selectedHistoryFile.value == 'Select a history file') {
        currentCodeFile.value = null
        generatedCode.value = '';
        return;
    }
    try {
        const response = await axios.get<HistoryFileContent>(
            `${API_BASE_URL}/history/${selectedHistoryFile.value}`
        );

        generatedCode.value = response.data.code;
        currentCodeFile.value = response.data.filename;
        statusText.value = `📂 Loaded: ${response.data.filename}`;
        logs.value.push(`\n📂 Loaded history file: ${response.data.filename}`);
        logs.value.push('💡 You can now perform style transfer or modifications on this code!\n');

        scrollLogsToBottom();
    } catch (error) {
        handleError(error);
    }
};

// 删除历史文件
const deleteHistoryFile = async () => {
    if (!selectedHistoryFile.value) return;

    if (!confirm(`Are you sure you want to delete ${selectedHistoryFile.value}?`)) {
        return;
    }

    try {
        await axios.delete(`${API_BASE_URL}/history/${selectedHistoryFile.value}`);
        logs.value.push(`🗑️ Deleted file: ${selectedHistoryFile.value}`);
        selectedHistoryFile.value = null;
        await refreshHistory();
        alert('File deleted successfully');
    } catch (error) {
        handleError(error);
    }
};

// 下载代码文件
const downloadCodeFile = () => {
    if (!currentCodeFile.value) return;
    window.open(`${API_BASE_URL}/code/${currentCodeFile.value}`, '_blank');
};

// 生成音乐
const generateMusic = async () => {
    if (!prompt.value.trim()) return;

    isGenerating.value = true;
    generatedCode.value = '';
    logs.value = [];
    midiPath.value = null;
    currentCodeFile.value = null;
    originalPrompt.value = prompt.value;
    statusText.value = 'Generating music code...';

    try {
        const response = await axios.post<TaskResponse>(`${API_BASE_URL}/generate`, {
            prompt: prompt.value
        });

        currentTaskId.value = response.data.task_id;
        startPolling();

    } catch (error) {
        handleError(error);
    }
};

const copyCode = async () => {
    if (!generatedCode.value) {
        return;
    }

    try {
        await navigator.clipboard.writeText(generatedCode.value);
        alert('Code copied to clipboard');
    } catch (err) {
        console.error('Copy failed:', err);
    }
};

const clearLogs = async () => {
    if (!logs.value) {
        return;
    }

    try {
        logs.value = [];
    } catch (err) {
        // Handle error
    }
};

// 提交反馈
const submitFeedback = async () => {
    if (!feedbackText.value.trim()) {
        showFeedback.value = false;
        return;
    }

    showFeedback.value = false;
    isGenerating.value = true;
    logs.value.push('\n' + '='.repeat(60));
    logs.value.push(`Regenerating with user feedback:\n${feedbackText.value}`);
    logs.value.push('='.repeat(60));
    statusText.value = 'Regenerating with feedback...';

    try {
        const response = await axios.post<TaskResponse>(`${API_BASE_URL}/generate`, {
            prompt: originalPrompt.value,
            feedback: feedbackText.value,
            previous_code: generatedCode.value
        });

        currentTaskId.value = response.data.task_id;
        feedbackText.value = '';
        startPolling();

    } catch (error) {
        handleError(error);
    }
};

// 提交风格转换
const submitStyleTransfer = async () => {
    if (!styleRequest.value.trim()) {
        showStyle.value = false;
        return;
    }

    showStyle.value = false;
    isGenerating.value = true;
    logs.value.push('\n' + '='.repeat(60));
    logs.value.push(`Starting style transfer:\nStyle Request: ${styleRequest.value}`);
    logs.value.push('='.repeat(60));
    statusText.value = 'Transferring style...';

    try {
        const response = await axios.post<TaskResponse>(`${API_BASE_URL}/style-transfer`, {
            original_code: generatedCode.value,
            style_request: styleRequest.value
        });

        currentTaskId.value = response.data.task_id;
        styleRequest.value = '';
        startPolling();

    } catch (error) {
        handleError(error);
    }
};

// 开始轮询任务状态
const startPolling = () => {
    if (pollingInterval !== null) {
        clearInterval(pollingInterval);
    }

    pollingInterval = window.setInterval(async () => {
        try {
            const response = await axios.get<TaskStatus>(`${API_BASE_URL}/task/${currentTaskId.value}`);
            const task = response.data;

            if (task.logs && task.logs.length > logs.value.length) {
                logs.value = task.logs;
                scrollLogsToBottom();
            }

            statusText.value = task.progress || statusText.value;

            if (task.status === 'completed') {
                generatedCode.value = task.result_code || '';
                midiPath.value = task.midi_path;
                currentCodeFile.value = task.code_file_path ? task.code_file_path.split('/').pop() || null : null;
                isGenerating.value = false;
                if (pollingInterval !== null) {
                    clearInterval(pollingInterval);
                }

                // 刷新历史文件列表
                await refreshHistory();

                if (midiPath.value) {
                    statusText.value = 'Generation completed successfully';
                } else {
                    statusText.value = 'Generation completed (MIDI compilation failed)';
                }
            } else if (task.status === 'error') {
                statusText.value = `Error: ${task.error_message}`;
                isGenerating.value = false;
                if (pollingInterval !== null) {
                    clearInterval(pollingInterval);
                }
            }

        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000);
};

const showFeedbackDialog = () => {
    if (!generatedCode.value) return;
    showFeedback.value = true;
};

const showStyleDialog = () => {
    if (!generatedCode.value) return;
    showStyle.value = true;
};

const chooseHistory = () => {
    historyView.value = !historyView.value
};

const handleError = (error: any) => {
    isGenerating.value = false;
    statusText.value = 'Generation failed';
    const errorMsg = error.response?.data?.error || error.message || 'Unknown error';
    logs.value.push(`\nError: ${errorMsg}`);
    alert(`Error: ${errorMsg}`);
};

const scrollLogsToBottom = () => {
    nextTick(() => {
        if (logDisplay.value) {
            logDisplay.value.scrollTop = logDisplay.value.scrollHeight;
        }
    });
};

onBeforeUnmount(() => {
    if (pollingInterval !== null) {
        clearInterval(pollingInterval);
    }
});
</script>

<style scoped>
* {
    box-sizing: border-box;
}

.app-container {
    min-height: 100vh;
    width: 99vw;
    padding: 0;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
}

/* Top Navigation */
.top-nav {
    background: #ffffff;
    border-bottom: 1px solid #c6ced4;
    box-shadow: 0 2px 8px rgba(36, 36, 36, 0.05);
    background-color: #d7dce6;
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-content {
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand {
    align-items: center;
    gap: 12px;
    font-weight: 600;
    font-size: 18px;
    color: #1a202c;
}

.brand-icon {
    font-size: 24px;
    margin-right: 30px;
}

.nav-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #4a5568;
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4b5867;
    transition: all 0.3s;
}

.status-indicator.active {
    background: #48bb78;
    box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.2);
    animation: pulse 2s infinite;
}

@keyframes pulse {

    0%,
    100% {
        opacity: 1;
    }

    50% {
        opacity: 0.5;
    }
}

/* Main Content Layout */
.main-content {
    max-width: 1600px;
    margin: 0 auto;
    padding: 32px;
    padding-left: 70px;
    padding-right: 50px;
    display: grid;
    grid-template-columns: 420px 1fr;
    gap: 50px;
    align-items: start;
}

/* Left Panel */
.left-panel {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    position: sticky;
    top: 100px;
}

.panel-section {
    padding: 28px;
}

.section-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 24px;
}

.section-header h2 {
    font-size: 18px;
    font-weight: 600;
    color: #1a202c;
    margin: 0;
}

.header-actions {
    display: flex;
    width: 100px;
}

.icon-btn {
    background: transparent;
    border: none;
    padding: 6px;
    border-radius: 6px;
    transition: background 0.2s;
    font-size: 16px;
    cursor: pointer;
}

/* Input Group */
.input-group {
    margin-bottom: 24px;
}

.input-label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: #4a5568;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.input-field {
    width: 100%;
    padding: 12px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    transition: all 0.2s;
    line-height: 1.5;
}

.input-field:focus {
    outline: none;
    border-color: #4299e1;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

/* History Section */
.history-section {
    margin-bottom: 24px;
    padding: 16px;
    background: #f7fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
}

.history-controls {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 500;
    color: #4a5568;
}

.history-select {
    flex: 1;
    width: 20px;

    border: 2px solid #e2e8f0;
    border-radius: 6px;
    font-size: 13px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;

}

.history-select:focus {
    outline: none;
    border-color: #4299e1;
}

.refresh-btn {
    padding: 8px 12px;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
}

.history-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.btn-small {
    padding: 8px 12px;
    font-size: 12px;
}

.btn-danger {
    background: #fee;
    color: #c53030;
    border: 1px solid #feb2b2;
}

.btn-danger:hover:not(:disabled) {
    background: #fecaca;
    border-color: #fc8181;
}

/* Action Panel */
.action-panel {
    margin-bottom: 20px;
}

.btn {
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    padding: 10px;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-large {
    width: 100%;
    padding: 14px 24px;
    font-size: 15px;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn-primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}

.btn-icon {
    font-size: 16px;
}

/* Control Grid */
.control-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}

.btn-control {
    padding: 12px 8px;
    background: #f7fafc;
    color: #2d3748;
    border: 1px solid #e2e8f0;
}

.btn-control:hover:not(:disabled) {
    background: #edf2f7;
    border-color: #cbd5e0;
}

.btn-label {
    font-size: 13px;
}

/* Progress */
.progress-container {
    margin-top: 20px;
    padding: 16px;
    background: #f7fafc;
    border-radius: 8px;
}

.progress-bar {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    animation: progressAnim 1.5s ease-in-out infinite;
}

@keyframes progressAnim {
    0% {
        width: 0%;
    }

    50% {
        width: 100%;
    }

    100% {
        width: 0%;
    }
}

.progress-text {
    font-size: 12px;
    color: #718096;
    margin: 0;
    text-align: center;
}

/* Right Panel */
.right-panel {
    display: flex;
    gap: 35px;
}

.output-section {
    flex: 1;
}

.output-section,
.log-section {
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
    overflow: hidden;
    width: 450px;
}

.output-section .section-header,
.log-section .section-header {
    padding: 20px 28px;
    background: #f7fafc;
    border-bottom: 1px solid #e2e8f0;
}

/* Code Container */
.code-container {
    margin: 35px;
    height: 420px;
    overflow: auto;
    border-radius: 8px;
    max-width: 380px;
    border: 2px solid #e2e8f0;
}

.code-content {
    color: #7d828b;
    font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.6;
    min-height: 100%;
    overflow-x: auto;
    overflow-y: auto;
    white-space: pre;
    height: 400px;
    scrollbar-width: thin;
    scrollbar-color: #c6c8ce #d4d8e2;
}

.code-content code {
    color: #68467e;
    display: block;
    padding: 10px;
}

/* Log Container */
.log-container {
    height: 420px;
    overflow-y: auto;
    padding: 10px 28px;
    background: #fafafa;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.8;
}

.log-line {
    display: flex;
    margin-bottom: 4px;
    white-space: pre-wrap;
    padding: 0;
    color: #2d3748;
}

/* Empty States */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #a0aec0;
    text-align: center;
    padding: 40px;
}

.empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

.empty-state p {
    margin: 4px 0;
}

.empty-hint {
    font-size: 13px;
    color: #cbd5e0;
}

.empty-state-small {
    text-align: center;
    color: #8d9aa8;
    padding: 40px 20px;
    font-size: 13px;
}

/* Modal */
.modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
}

.modal-dialog {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 560px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
    padding: 24px 28px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1a202c;
}

.modal-close {
    background: transparent;
    border: none;
    font-size: 28px;
    color: #a0aec0;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: all 0.2s;
}

.modal-close:hover {
    background: #f7fafc;
    color: #2d3748;
}

.modal-body {
    padding: 24px 28px;
}

.modal-description {
    font-size: 14px;
    color: #718096;
    margin: 0 0 16px 0;
}

.modal-input {
    width: 100%;
    padding: 12px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    line-height: 1.5;
}

.modal-input:focus {
    outline: none;
    border-color: #4299e1;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.style-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.tag {
    padding: 6px 12px;
    background: #edf2f7;
    color: #4a5568;
    border-radius: 16px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.tag:hover {
    background: #e2e8f0;
    color: #2d3748;
}

.modal-footer {
    padding: 20px 28px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

.btn-secondary {
    padding: 10px 20px;
    background: #edf2f7;
    color: #4a5568;
}

.btn-secondary:hover {
    background: #e2e8f0;
}

.modal-footer .btn-primary {
    padding: 10px 20px;
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: #cbd5e0;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a0aec0;
}

/* Responsive Design */
@media (max-width: 1200px) {
    .main-content {
        grid-template-columns: 1fr;
    }

    .left-panel {
        position: relative;
        top: 0;
    }

    .control-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .nav-content {
        padding: 12px 16px;
    }

    .main-content {
        padding: 16px;
        gap: 16px;
    }

    .control-grid {
        grid-template-columns: 1fr;
    }

    .modal-dialog {
        width: 95%;
        margin: 16px;
    }
}
</style>