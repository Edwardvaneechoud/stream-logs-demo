const { createApp, ref } = Vue;

createApp({
  setup() {
    const logLines = ref([]);
    const isStreaming = ref(false);
    let eventSource = null;

    const startStreaming = () => {
      logLines.value = [];
      isStreaming.value = true;

      eventSource = new EventSource("/api/stream");

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          logLines.value.push(data);

          // Check if monitoring has completed
          if (data === "RAM monitoring completed") {
            closeEventSource();
          }
        } catch (error) {
          console.error("Error parsing data:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("EventSource error:", error);
        closeEventSource();
      };
    };

    const closeEventSource = () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      isStreaming.value = false;
    };

    return {
      logLines,
      isStreaming,
      startStreaming
    };
  }
}).mount("#app");