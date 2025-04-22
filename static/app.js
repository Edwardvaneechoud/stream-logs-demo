const { createApp, ref } = Vue;

createApp({
  setup() {
    const logLines = ref(["Starting countdown:"]);
    const numberLine = ref("");
    const isStreaming = ref(false);
    let eventSource = null;

    const startStreaming = () => {
      logLines.value = ["Starting countdown:"];
      numberLine.value = "";
      isStreaming.value = true;

      eventSource = new EventSource("/api/stream");

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data === "explode!") {
            logLines.value.push(numberLine.value);
            logLines.value.push("Wooow we just made it");
            eventSource.close();
            eventSource = null;
            isStreaming.value = false;
          } else {
            if (numberLine.value === "") {
              numberLine.value = data;
            } else {
              numberLine.value += `, ${data}`;
            }
          }
        } catch (error) {
          console.error("Error parsing log data:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("EventSource error:", error);
        if (eventSource) {
          eventSource.close();
          eventSource = null;
        }
        isStreaming.value = false;
      };
    };

    return {
      logLines,
      numberLine,
      isStreaming,
      startStreaming
    };
  }
}).mount("#app");
