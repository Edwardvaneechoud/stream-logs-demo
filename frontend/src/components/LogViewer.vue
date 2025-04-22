<script setup lang="ts">
import { ref, onUnmounted, nextTick, onMounted, watch } from "vue";
import axios from "axios";

// Types
interface Props {
  sessionId: string;
  height?: string;
  maxLogsHeight?: string; // Added prop for logs area max height
}

type ConnectionStatus = "connected" | "disconnected" | "error";

// Props from parent
const props = defineProps<Props>();

const emit = defineEmits<{
  'update:status': [status: ConnectionStatus];
  'error': [message: string];
}>();

const logs = ref<string>("");
const logLines = ref<string[]>([]);
const eventSourceRef = ref<EventSource | null>(null);
const autoScroll = ref<boolean>(true);
const connectionRetries = ref<number>(0);
const maxRetries = 5;
const connectionStatus = ref<ConnectionStatus>("disconnected");
const errorMessage = ref<string | null>(null);
const isMonitoring = ref<boolean>(false);
const reconnectionTimer = ref<number | null>(null);

// Scroll to the bottom of the log container
const scrollToBottom = (): void => {
  console.log("scrolling to bottom", autoScroll.value)
  // if (!autoScroll.value) return;
  
  nextTick(() => {
    requestAnimationFrame(() => {
      const logsElement = document.querySelector(".logs");
      if (logsElement) logsElement.scrollTop = logsElement.scrollHeight;
    });
  });
};

// Watch connection status and emit it to parent
watch(connectionStatus, (status) => {
  emit('update:status', status);
});

// Watch logs to update log lines and check for errors
watch(logs, (newLogs) => {
  logLines.value = newLogs
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "");
});

// Clear any existing reconnection timer
const clearReconnectionTimer = (): void => {
  if (reconnectionTimer.value !== null) {
    clearTimeout(reconnectionTimer.value);
    reconnectionTimer.value = null;
  }
};

// Handle connection close
const handleConnectionClosed = (reason: string = "Connection closed"): void => {
  if (connectionStatus.value === "connected") {
    logs.value += `\n${reason}\n`;
    connectionStatus.value = "disconnected";
    scrollToBottom();
  }
};

// Start streaming logs
const startStreamingLogs = async (): Promise<void> => {
  stopStreamingLogs(); // Ensure previous connection is closed

  // Reset state
  logs.value = "";
  errorMessage.value = null;
  connectionStatus.value = "disconnected";
  
  try {
    // Create new EventSource
    const url = `/api/sessions/${props.sessionId}/logs`;
    const eventSource = new EventSource(url);
    eventSourceRef.value = eventSource;

    eventSource.onopen = () => {
      connectionStatus.value = "connected";
      connectionRetries.value = 0; // Reset retry counter on successful connection
      console.log("Log connection established");
    };

    eventSource.onmessage = (event) => {
      try {
        // Check for timeout or server-side disconnection messages
        if (event.data.includes("Connection timed out") || 
            event.data.includes("disconnected") ||
            event.data.includes("session not found")) {
          
          const parsedData = JSON.parse(event.data);
          logs.value += parsedData + "\n";
          handleConnectionClosed(parsedData);
          stopStreamingLogs();
          return;
        }
        
        const parsedData = JSON.parse(event.data);
        logs.value += parsedData + "\n";
        scrollToBottom();
      } catch (error) {
        console.error("Error parsing log data:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("EventSource error:", error);
      eventSource.close();
      eventSourceRef.value = null;

      if (connectionStatus.value === "connected") {
        handleConnectionClosed("Connection error occurred");
      }
      
      connectionStatus.value = "error";

      if (connectionRetries.value < maxRetries) {
        connectionRetries.value++;
        console.log(`Retrying log connection (${connectionRetries.value}/${maxRetries})...`);
        errorMessage.value = `Connection failed. Retrying (${connectionRetries.value}/${maxRetries})...`;
        
        clearReconnectionTimer();
        reconnectionTimer.value = setTimeout(startStreamingLogs, 1000 * connectionRetries.value) as unknown as number;
      } else {
        console.error("Max retries reached for log connection");
        errorMessage.value = "Failed to connect after multiple attempts. Try again later.";
        emit('error', errorMessage.value);
      }
    };
  
    
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : "Unknown error";
    console.error("Failed to start log streaming:", error);
    errorMessage.value = `Error: ${errorMsg}`;
    connectionStatus.value = "error";
    emit('error', errorMessage.value);
  }
};

// Stop streaming logs
const stopStreamingLogs = (): void => {
  clearReconnectionTimer();
  
  if (eventSourceRef.value) {
    eventSourceRef.value.close();
    eventSourceRef.value = null;
  }
  
  if (connectionStatus.value === "connected") {
    connectionStatus.value = "disconnected";
  }
};

// Manual reconnection with reset
const reconnect = (): void => {
  connectionRetries.value = 0; // Reset retry counter for manual reconnection
  startStreamingLogs();
};

// Toggle system monitoring
const toggleMonitoring = async (): Promise<void> => {
  try {
    const endpoint = isMonitoring.value ? 'stop-monitoring' : 'start-monitoring';
    await axios.post(`/api/sessions/${props.sessionId}/${endpoint}`);
    isMonitoring.value = !isMonitoring.value;
    
    logs.value += `\n${isMonitoring.value ? 'Started' : 'Stopped'} system monitoring.\n`;
    scrollToBottom();
  } catch (error) {
    const errorMsg = error instanceof Error 
      ? error.message 
      : (axios.isAxiosError(error) && error.response?.data?.detail) || "Unknown error";
    
    // Check if the error is due to session not found/invalid
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      handleConnectionClosed("Session no longer exists");
      stopStreamingLogs();
    }
    
    console.error("Error toggling monitoring:", error);
    errorMessage.value = `Failed to ${isMonitoring.value ? 'stop' : 'start'} monitoring: ${errorMsg}`;
    emit('error', errorMessage.value);
  }
};

// Add custom log message
const addCustomLog = async (message: string, level: "INFO" | "ERROR" = "INFO"): Promise<void> => {
  try {
    await axios.post(`/api/sessions/${props.sessionId}/logs`, null, {
      params: { message, level }
    });
  } catch (error) {
    const errorMsg = error instanceof Error 
      ? error.message 
      : (axios.isAxiosError(error) && error.response?.data?.detail) || "Unknown error";
    
    // Check if the error is due to session not found/invalid
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      handleConnectionClosed("Session no longer exists");
      stopStreamingLogs();
    }
    
    console.error("Error adding custom log:", error);
    errorMessage.value = `Failed to add log: ${errorMsg}`;
    emit('error', errorMessage.value);
  }
};

// UI Handlers
const handleScroll = (event: Event): void => {
  const element = event.target as HTMLElement;
  // Calculate if we're near the bottom (within 50px)
  autoScroll.value = element.scrollHeight - element.scrollTop <= element.clientHeight + 50;
};

const clearLogs = (): void => {
  logs.value = "";
};

// Determine if a line is an error
const isErrorLine = (line: string): boolean => {
  return line.toUpperCase().includes("ERROR");
};

// Lifecycle Hooks
onMounted(() => {
  startStreamingLogs();
});

onUnmounted(() => {
  stopStreamingLogs();
  clearReconnectionTimer();
});

// Expose functions to parent component
defineExpose({
  startStreamingLogs,
  stopStreamingLogs,
  clearLogs,
  addCustomLog,
  toggleMonitoring,
  reconnect
});
</script>

<template>
  <div class="log-container">
    <div class="log-header">
      <div class="log-status">
        <span
          :class="[
            'status-indicator',
            {
              active: connectionStatus === 'connected',
              error: connectionStatus === 'error',
              disconnected: connectionStatus === 'disconnected'
            },
          ]"
        ></span>
        {{
          connectionStatus === "connected"
            ? "Connected"
            : connectionStatus === "error"
              ? "Connection Error"
              : "Disconnected"
        }}
      </div>
      <div class="log-controls">
        <button @click="reconnect" class="btn">
          <i class="fas fa-sync"></i> Reconnect
        </button>
        <button @click="toggleMonitoring" class="btn" :class="{ 'btn-active': isMonitoring }" 
                :disabled="connectionStatus !== 'connected'">
          <i class="fas" :class="isMonitoring ? 'fa-stop' : 'fa-play'"></i>
          {{ isMonitoring ? 'Stop Monitoring' : 'Start Monitoring' }}
        </button>
        <button :disabled="!logs || autoScroll" @click="scrollToBottom" class="btn">
          <i class="fas fa-arrow-down"></i>
        </button>
        <button @click="clearLogs" class="btn btn-danger">
          <i class="fas fa-trash"></i> Clear
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="error-banner">
      {{ errorMessage }}
    </div>

    <div v-if="logLines.length === 0 && !errorMessage" class="empty-state">
      No logs available. Start monitoring to see logs appear here.
    </div>

    <div class="logs" :class="{ 'auto-scroll': autoScroll }" @scroll="handleScroll">
      <div
        v-for="(line, index) in logLines"
        :key="index"
        :class="{ 'error-line': isErrorLine(line) }"
      >
        {{ line }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.log-container {
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
  color: #d4d4d4;
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  overflow-y: auto;
  border-radius: 4px;
  border: 1px solid #333;
  max-height: 600px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: #252526;
  border-bottom: 1px solid #333;
  position: sticky;
  top: 0;
  z-index: 10;
}

.log-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #666;
}

.status-indicator.active {
  background-color: #4caf50;
}

.status-indicator.error {
  background-color: #f44336;
}

.status-indicator.disconnected {
  background-color: #ff9800;
}

.log-controls {
  display: flex;
  gap: 8px;
}

.btn {
  background-color: #333;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.btn:hover {
  background-color: #444;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  background-color: #b71c1c;
}

.btn-danger:hover {
  background-color: #d32f2f;
}

.btn-active {
  background-color: #1976d2;
}

.btn-active:hover {
  background-color: #2196f3;
}

.error-banner {
  padding: 8px 12px;
  background-color: rgba(244, 67, 54, 0.2);
  color: #f44336;
  font-size: 0.9em;
  border-bottom: 1px solid #f44336;
}

.empty-state {
  padding: 16px;
  text-align: center;
  color: #777;
  font-style: italic;
}

.logs {
  flex: 1 1 auto;
  margin: 0;
  padding: 8px;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.9em;
  line-height: 1.5;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scrolling */
}

.logs.auto-scroll {
  scroll-behavior: smooth;
}

.error-line {
  background-color: rgba(255, 0, 0, 0.2);
  color: #ffcdd2;
}
</style>