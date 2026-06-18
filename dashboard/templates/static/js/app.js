/**
 * NetMon Operations Dashboard Control Core
 * Integrates REST API routes with live Socket.IO update intervals.
 */

let telemetryChartInstance = null;
let activeTargetHostIP = null;

document.addEventListener("DOMContentLoaded", () => {
  initializeDashboardEngines();
  establishLiveSocketStream();

  // Route event tracking to tracking drop downs
  document
    .getElementById("host-telemetry-selector")
    .addEventListener("change", (e) => {
      activeTargetHostIP = e.target.value;
      refreshTelemetryGraph(activeTargetHostIP);
    });
});

/**
 * Initializes metrics components on page load.
 */
async function initializeDashboardEngines() {
  await reloadSystemMetrics();
  await updateHistoricFeeds();
}

/**
 * Main function to poll standard REST api targets sequentially.
 */
async function reloadSystemMetrics() {
  try {
    const [statsResponse, statusResponse] = await Promise.all([
      fetch("/api/stats"),
      fetch("/api/current"),
    ]);

    const networkStats = await statsResponse.json();
    const absoluteStatuses = await statusResponse.json();

    renderIndustrialHostMatrix(networkStats, absoluteStatuses);
    syncDropdownSelector(networkStats);
  } catch (err) {
    console.error("Critical error mapping operational metric feeds:", err);
  }
}

/**
 * Updates logs for system alerts and security breaches.
 */
async function updateHistoricFeeds() {
  try {
    const [alertsResponse, attacksResponse] = await Promise.all([
      fetch("/api/alerts"),
      fetch("/api/attacks"),
    ]);

    const alertsPayload = await alertsResponse.json();
    const attacksPayload = await attacksResponse.json();

    // Map your alerts as needed...
    populateRawDataTable("table-alerts", alertsPayload, [
      "timestamp",
      "host",
      "message",
    ]);

    populateRawDataTable("table-attacks", attacksPayload, [
      "timestamp",
      "host", // Maps to the target column
      "attack_type", // Maps to the vector column
      "description", // Maps to the src_ip column (or add this field if you want to show it)
    ]);
  } catch (err) {
    console.error("Critical error parsing historic logging pipelines:", err);
  }
}

/**
 * Renders the primary system matrix view.
 */
function renderIndustrialHostMatrix(stats, currentStates) {
  const matrixBox = document.getElementById("host-matrix-container");
  matrixBox.innerHTML = "";

  stats.forEach((target) => {
    // Find the matching host inside the data array returned by your API
    let evaluatesUp = false;

    if (Array.isArray(currentStates)) {
      const match = currentStates.find((item) => item.host === target.host);
      // It is up if the backend object exists and its 'is_up' flag equals 1
      if (match && match.is_up === 1) {
        evaluatesUp = true;
      }
    }

    const targetBlock = document.createElement("div");
    targetBlock.className = `host-block ${evaluatesUp ? "up-state" : "down-state"}`;
    targetBlock.innerHTML = `
            <div class="host-meta-row">
                <span class="host-label">${target.label}</span>
                <span class="host-status-badge" style="color: ${evaluatesUp ? "var(--industrial-green)" : "var(--industrial-red)"}">
                    ${evaluatesUp ? "SYS_OK" : "SYS_FAIL"}
                </span>
            </div>
            <div class="host-meta-row">
                <span class="host-ip">${target.host}</span>
            </div>
            <div class="host-stats-line">
                <div class="stat-cell">
                    <span class="stat-lbl">24H_UPTIME</span>
                    <span class="stat-val" style="color: ${target.uptime < 95 ? "var(--industrial-orange)" : "var(--text-stark)"}">
                        ${target.uptime}%
                    </span>
                </div>
                <div class="stat-cell">
                    <span class="stat-lbl">AVG_LATENCY</span>
                    <span class="stat-val">${target.avg_rtt ? target.avg_rtt + "ms" : "N/A"}</span>
                </div>
            </div>
        `;
    matrixBox.appendChild(targetBlock);
  });
}

/**
 * Rebuilds choices for the time-series dropdown array cleanly without resetting interface focus.
 */
function syncDropdownSelector(stats) {
  const dynamicSelect = document.getElementById("host-telemetry-selector");
  if (dynamicSelect.options.length === 0) {
    stats.forEach((node) => {
      const opt = document.createElement("option");
      opt.value = node.host;
      opt.textContent = `TARGET // ${node.label || node.host}`;
      dynamicSelect.appendChild(opt);
    });

    if (stats.length > 0) {
      activeTargetHostIP = stats[0].host;
      refreshTelemetryGraph(activeTargetHostIP);
    }
  }
}

/**
 * Fetches time-series telemetry metrics for a selected host target.
 */
async function refreshTelemetryGraph(hostIp) {
  if (!hostIp) return;
  try {
    const historicResponse = await fetch(`/api/history/${hostIp}`);
    const historicalPayload = await historicResponse.json();
    renderTelemetryTimeline(historicalPayload, hostIp);
  } catch (err) {
    console.error(
      `Unable to rebuild metric context for endpoint context: ${hostIp}`,
      err,
    );
  }
}

/**
 * Compiles data logs cleanly inside standard table rows.
 */
function populateRawDataTable(tableId, analyticsArray, keyMap) {
  const executionBody = document.querySelector(`#${tableId} tbody`);
  executionBody.innerHTML = "";

  analyticsArray.forEach((dataPoint) => {
    const interactiveRow = document.createElement("tr");

    keyMap.forEach((headerKey) => {
      const functionalCell = document.createElement("td");
      let resolutionString =
        dataPoint[headerKey] || dataPoint["time"] || "NULL";

      // Format timestamps cleanly if returned as epoch floats
      if (headerKey === "timestamp" && typeof resolutionString === "number") {
        resolutionString = new Date(
          resolutionString * 1000,
        ).toLocaleTimeString();
      }

      functionalCell.textContent = resolutionString;

      // Apply highlighting style parameters directly on severe incidents
      if (
        headerKey === "message" &&
        (dataPoint.severity === "high" ||
          /unreachable|down/i.test(resolutionString))
      ) {
        functionalCell.style.color = "var(--industrial-red)";
        functionalCell.style.fontWeight = "500";
      }
      interactiveRow.appendChild(functionalCell);
    });
    executionBody.appendChild(interactiveRow);
  });
}

/**
 * Uses Chart.js to display system telemetry.
 */
function renderTelemetryTimeline(seriesMetrics, activeIP) {
  const telemetryContext = document
    .getElementById("netmonTelemetryChart")
    .getContext("2d");

  if (!seriesMetrics || seriesMetrics.length === 0) return;

  // 1. Map data using the correct property names ('timestamp' and 'rtt_ms')
  const validMetrics = seriesMetrics.map((item) => ({
    timeStr: item.timestamp,
    rtt: item.rtt_ms || 0,
  }));

  // 2. Parse ISO strings correctly
  const processLabels = validMetrics.map((item) => {
    const date = new Date(item.timeStr); // Directly parse the ISO string
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  });

  const processedMetrics = validMetrics.map((item) => item.rtt);

  if (telemetryChartInstance) {
    telemetryChartInstance.data.labels = processLabels;
    telemetryChartInstance.data.datasets[0].data = processedMetrics;
    telemetryChartInstance.data.datasets[0].label = `MONITOR REFRESH PATHWAY // ${activeIP} (RTT_ms)`;
    telemetryChartInstance.update();
  } else {
    telemetryChartInstance = new Chart(telemetryContext, {
      type: "line",
      data: {
        labels: processLabels,
        datasets: [
          {
            label: `MONITOR REFRESH PATHWAY // ${activeIP} (RTT_ms)`,
            data: processedMetrics,
            borderColor: "#ffffff",
            borderWidth: 2,
            pointBackgroundColor: "#00ff66",
            pointBorderColor: "#00ff66",
            pointRadius: 3,
            pointHoverRadius: 6,
            lineTension: 0.05, // Retains intentional precise stepped edges over artificial curves
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: "#ffffff",
              font: { family: "Apfel Grotezk", size: 11 },
            },
          },
        },
        scales: {
          y: {
            grid: { color: "#2d3748", borderDash: [2, 4] },
            ticks: { color: "#8a9bb4", font: { family: "Apfel Grotezk" } },
          },
          x: {
            grid: { display: false },
            ticks: {
              color: "#8a9bb4",
              font: { family: "Apfel Grotezk" },
              maxTicksLimit: 8,
            },
          },
        },
      },
    });
  }
}

/**
 * Binds a direct Socket.IO event listener to standard client targets.
 */
function establishLiveSocketStream() {
  const operationSocket = io();

  operationSocket.on("connect", () => {
    console.log("Core system link established with backend SocketIO gateway.");
    const pulseElement = document.getElementById("network-pulse");
    if (pulseElement)
      pulseElement.style.backgroundColor = "var(--industrial-green)";
  });

  operationSocket.on("update", async (broadcastPayload) => {
    // Trigger a visual confirmation pulse on the live status indicator
    const visualPulse = document.getElementById("network-pulse");
    if (visualPulse) {
      visualPulse.classList.add("tick");
      setTimeout(() => visualPulse.classList.remove("tick"), 200);
    }

    // Pull updated records from REST routes instantly without page reloads
    await reloadSystemMetrics();
    await updateHistoricFeeds();

    if (activeTargetHostIP) {
      await refreshTelemetryGraph(activeTargetHostIP);
    }

    const currentTime = new Date();
    document.getElementById("timestamp-ticker").textContent =
      `TICK_${currentTime.toLocaleTimeString()}`;
  });

  operationSocket.on("disconnect", () => {
    const pulseElement = document.getElementById("network-pulse");
    if (pulseElement) {
      pulseElement.style.backgroundColor = "var(--industrial-red)";
      pulseElement.style.boxShadow = "0 0 10px var(--industrial-red)";
    }
    document.getElementById("timestamp-ticker").textContent =
      "CONNECTION_OFFLINE";
  });
}
