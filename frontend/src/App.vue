<script setup lang="ts">
import { ref, onUnmounted } from 'vue';
import axios from 'axios';
import LogViewer from './components/LogViewer.vue';

// Types
interface LogViewerInstance {
  startStreamingLogs: () => Promise<void>;
  stopStreamingLogs: () => void;
  clearLogs: () => void;
  addCustomLog: (message: string, level?: "INFO" | "ERROR") => Promise<void>;
  toggleMonitoring: () => Promise<void>;
}

type ViewerStatus = "connected" | "disconnected" | "error";

// Refs
const sessionId = ref<string | null>(null);
const isLoading = ref<boolean>(false);
const error = ref<string | null>(null);
const logViewerRef = ref<LogViewerInstance | null>(null);
const showLogViewer = ref<boolean>(false);
const viewerStatus = ref<ViewerStatus>('disconnected');
const customMessage = ref<string>('');
const customLogLevel = ref<"INFO" | "ERROR">('INFO');

// Handle session creation
const createSession = async (): Promise<void> => {
  isLoading.value = true;
  error.value = null;
  
  try {
    const response = await axios.post<{ session_id: string }>('/api/sessions');
    sessionId.value = response.data.session_id;
    showLogViewer.value = true;
    console.log('Created session:', sessionId.value);
  } catch (err) {
    const errorMsg = err instanceof Error 
      ? err.message 
      : (axios.isAxiosError(err) && err.response?.data?.detail) || "Unknown error";
    
    error.value = `Failed to create session: ${errorMsg}`;
    console.error(error.value);
  } finally {
    isLoading.value = false;
  }
};

// Handle session cleanup
const closeSession = async (): Promise<void> => {
  if (!sessionId.value) return;
  
  isLoading.value = true;
  
  try {
    // Stop streaming logs first
    if (logViewerRef.value) {
      logViewerRef.value.stopStreamingLogs();
    }
    
    // Delete the session
    await axios.delete(`/api/sessions/${sessionId.value}`);
    console.log('Closed session:', sessionId.value);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : "Unknown error";
    console.error(`Error closing session: ${errorMsg}`);
  } finally {
    showLogViewer.value = false;
    sessionId.value = null;
    isLoading.value = false;
  }
};

// Handle custom log message
const sendCustomLog = async (): Promise<void> => {
  if (!sessionId.value || !customMessage.value || !logViewerRef.value) return;
  
  try {
    await logViewerRef.value.addCustomLog(customMessage.value, customLogLevel.value);
    customMessage.value = ''; // Reset input after sending
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : "Unknown error";
    error.value = `Failed to send log: ${errorMsg}`;
  }
};

// Handle viewer errors
const handleViewerError = (message: string): void => {
  error.value = message;
};

// Cleanup on component destruction
onUnmounted(() => {
  if (sessionId.value) {
    closeSession();
  }
});
</script>

<template>
  <div class="app-container">
    <header>
      <h1>Stream Logs Demo</h1>
      <p>A simple demo of real-time log streaming with FastAPI and Vue.js</p>
    </header>

    <main>
      <div v-if="error" class="error-message">
        {{ error }}
        <button class="dismiss-btn" @click="error = null">×</button>
      </div>

      <div v-if="!showLogViewer" class="welcome-panel">
        <h2>Welcome to Log Streaming Demo</h2>
        <p>
          This demo shows how to implement real-time log streaming from a FastAPI backend to a Vue.js
          frontend using Server-Sent Events (SSE).
        </p>
        <p>Features:</p>
        <ul>
          <li>Create a log session on the server</li>
          <li>Stream logs in real-time</li>
          <li>Monitor system stats (CPU, memory)</li>
          <li>Send custom log messages</li>
        </ul>
        <button 
          class="primary-btn" 
          @click="createSession" 
          :disabled="isLoading"
        >
          <i class="fas fa-play"></i> 
          {{ isLoading ? 'Creating Session...' : 'Start New Session' }}
        </button>
      </div>

      <div v-else class="log-panel">
        <div class="panel-header">
          <div class="session-info">
            <h3>Session: <span class="session-id">{{ sessionId }}</span></h3>
            <span 
              class="status-badge" 
              :class="{
                'connected': viewerStatus === 'connected',
                'error': viewerStatus === 'error',
                'disconnected': viewerStatus === 'disconnected'
              }"
            >
              {{ viewerStatus }}
            </span>
          </div>
          <button class="close-btn" @click="closeSession" :disabled="isLoading">
            <i class="fas fa-times"></i> Close Session
          </button>
        </div>

        <LogViewer 
          ref="logViewerRef"
          :sessionId="sessionId!"
          @update:status="viewerStatus = $event"
          @error="handleViewerError"
        />

        <div class="custom-log-form">
          <div class="input-group">
            <input 
              v-model="customMessage" 
              placeholder="Enter custom log message..." 
              @keyup.enter="sendCustomLog"
            />
            <select v-model="customLogLevel">
              <option value="INFO">INFO</option>
              <option value="ERROR">ERROR</option>
            </select>
            <button 
              class="send-btn" 
              @click="sendCustomLog" 
              :disabled="!customMessage.trim()"
            >
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </main>

    <footer>
      <p>Created as a demo project for streaming logs with FastAPI and Vue.js</p>
    </footer>
  </div>
</template>

<style>
/* Global Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f5f5;
}

/* App Container */
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Header */
header {
  margin-bottom: 30px;
  text-align: center;
}

header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

header p {
  color: #666;
}

/* Main Content */
main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Welcome Panel */
.welcome-panel {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.welcome-panel h2 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.welcome-panel p {
  margin-bottom: 15px;
}

.welcome-panel ul {
  margin-bottom: 20px;
  margin-left: 20px;
}

.welcome-panel li {
  margin-bottom: 5px;
}

/* Log Panel */
.log-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.session-info {
  display: flex;
  align-items: center;
}

.session-info h3 {
  font-size: 16px;
  margin-right: 10px;
}

.session-id {
  font-family: monospace;
  background-color: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-badge.connected {
  background-color: #d4edda;
  color: #155724;
}

.status-badge.error {
  background-color: #f8d7da;
  color: #721c24;
}

.status-badge.disconnected {
  background-color: #e2e3e5;
  color: #383d41;
}

/* LogViewer Component */
.log-panel .log-container {
  flex: 1;
  min-height: 400px;
  border-radius: 0;
  border: none;
}

/* Custom Log Form */
.custom-log-form {
  padding: 10px;
  background-color: #f8f9fa;
  border-top: 1px solid #dee2e6;
}

.input-group {
  display: flex;
  width: 100%;
}

.input-group input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px 0 0 4px;
  font-size: 14px;
}

.input-group select {
  width: 100px;
  padding: 8px;
  border: 1px solid #ced4da;
  border-left: none;
  font-size: 14px;
  background-color: #fff;
}

.input-group .send-btn {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
}

.input-group .send-btn:hover {
  background-color: #0069d9;
}

.input-group .send-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

/* Buttons */
.primary-btn {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.primary-btn:hover {
  background-color: #0069d9;
}

.primary-btn:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.close-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.close-btn:hover {
  background-color: #5a6268;
}

/* Error Message */
.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 10px 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dismiss-btn {
  background: none;
  border: none;
  color: #721c24;
  font-size: 20px;
  cursor: pointer;
}

/* Footer */
footer {
  margin-top: 30px;
  text-align: center;
  color: #6c757d;
  padding: 20px 0;
}
</style>