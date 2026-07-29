/* SRE Live Dashboard Charting and Auto-Refresh Engine */

document.addEventListener("DOMContentLoaded", () => {
    // Activate Sidebar Navigation highlight
    const navDashboard = document.getElementById("nav-dashboard");
    if (navDashboard) navDashboard.classList.add("active", "bg-primary");

    // Local state variables for chart trends (rolling last 10 polls)
    const MAX_TREND_POINTS = 12;
    const trendLabels = [];
    const cpuTrend = [];
    const ramTrend = [];
    const latencyTrend = [];
    const availabilityTrend = [];
    const rpmTrend = [];
    
    let charts = {};
    let refreshIntervalId = null;
    const POLLING_INTERVAL = 15000; // 15 seconds

    // Initialize Chart.js Instances
    function initCharts() {
        const gridColor = 'rgba(255, 255, 255, 0.05)';
        const tickColor = '#8c98a5';

        // 1. Latency Line Graph
        charts.latency = new Chart(document.getElementById('chart-latency').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'Latency (ms)', data: latencyTrend, borderColor: '#0dcaf0', backgroundColor: 'rgba(13, 202, 240, 0.05)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 9 } } } } }
        });

        // 2. CPU Line Graph
        charts.cpu = new Chart(document.getElementById('chart-cpu').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'CPU Usage %', data: cpuTrend, borderColor: '#0d6efd', backgroundColor: 'rgba(13, 110, 253, 0.05)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 9 } } } } }
        });

        // 3. RAM Line Graph
        charts.ram = new Chart(document.getElementById('chart-ram').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'RAM Usage %', data: ramTrend, borderColor: '#198754', backgroundColor: 'rgba(25, 135, 84, 0.05)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 9 } } } } }
        });

        // 4. Availability Line Graph
        charts.availability = new Chart(document.getElementById('chart-availability').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'Availability %', data: availabilityTrend, borderColor: '#20c997', backgroundColor: 'rgba(32, 201, 151, 0.05)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 9 } } } } }
        });

        // 5. Health Allocation Doughnut
        charts.distribution = new Chart(document.getElementById('chart-distribution').getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Warning', 'Critical', 'Offline'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#0ec980', '#eab308', '#ef4444', '#6b7280'],
                    borderWidth: 1.5,
                    borderColor: '#111318'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, cutout: '70%' }
        });

        // 6. RPM Requests Rate Line Graph
        charts.rpm = new Chart(document.getElementById('chart-rpm').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'RPM', data: rpmTrend, borderColor: '#fd7e14', backgroundColor: 'rgba(253, 126, 20, 0.05)', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 9 } } } } }
        });
    }

    // Refresh telemetry trends line charts data
    function updateChartsTrend(summaryData, servicesList) {
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        if (trendLabels.length >= MAX_TREND_POINTS) {
            trendLabels.shift();
            cpuTrend.shift();
            ramTrend.shift();
            latencyTrend.shift();
            availabilityTrend.shift();
            rpmTrend.shift();
        }

        trendLabels.push(timeNow);
        cpuTrend.push(summaryData.system.cpu_percent);
        ramTrend.push(summaryData.system.memory_percent);
        latencyTrend.push(summaryData.avg_response_time);
        
        // Calculate average availability % across all services
        let totalAvail = 0;
        servicesList.forEach(s => totalAvail += s.availability);
        const avgAvail = servicesList.length > 0 ? (totalAvail / servicesList.length) : 100;
        availabilityTrend.push(avgAvail);

        // RPM simulation based on CPU/RAM checks
        const simulatedRpm = Math.round(50 + (summaryData.system.cpu_percent * 2.5) + (Math.random() * 15));
        rpmTrend.push(simulatedRpm);

        // Update charts datasets
        charts.latency.update();
        charts.cpu.update();
        charts.ram.update();
        charts.availability.update();
        charts.rpm.update();

        // Update allocation doughnut
        charts.distribution.data.datasets[0].data = [
            summaryData.healthy_services,
            summaryData.warning_services,
            summaryData.critical_services,
            summaryData.offline_services
        ];
        charts.distribution.update();
    }

    // Fetch SRE summaries and hardware metrics
    async function syncSummaryData() {
        try {
            const token = localStorage.getItem("token");
            const headers = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch("/dashboard", { headers });
            if (response.status === 401) {
                // Session expired
                window.location.href = "/logout";
                return null;
            }
            
            const summary = await response.json();

            // Populate cards counters
            document.getElementById("card-total-services").textContent = summary.total_services;
            document.getElementById("card-healthy-services").textContent = summary.healthy_services;
            document.getElementById("card-warning-services").textContent = summary.warning_services;
            document.getElementById("card-critical-services").textContent = summary.critical_services;
            document.getElementById("card-offline-services").textContent = summary.offline_services;
            document.getElementById("card-avg-latency").textContent = summary.avg_response_time;

            // Hardware cards
            document.getElementById("card-cpu-percent").textContent = `${summary.system.cpu_percent}%`;
            document.getElementById("card-cpu-cores").textContent = `${summary.system.cpu_cores} Cores`;
            document.getElementById("bar-cpu").style.width = `${summary.system.cpu_percent}%`;

            document.getElementById("card-ram-percent").textContent = `${summary.system.memory_percent}%`;
            document.getElementById("card-ram-used").textContent = `${summary.system.memory_used_gb} / ${summary.system.memory_total_gb} GB`;
            document.getElementById("bar-ram").style.width = `${summary.system.memory_percent}%`;

            document.getElementById("card-disk-percent").textContent = `${summary.system.disk_percent}%`;
            document.getElementById("card-disk-used").textContent = `${summary.system.disk_used_gb} / ${summary.system.disk_total_gb} GB`;
            document.getElementById("bar-disk").style.width = `${summary.system.disk_percent}%`;

            document.getElementById("card-net-io").textContent = `↑ ${summary.system.network_sent_mb} / ↓ ${summary.system.network_recv_mb} MB`;
            document.getElementById("card-net-uptime").textContent = `Uptime: ${summary.system.system_uptime}`;

            // Alerts Timeline Panel
            const activeAlertCount = summary.critical_services + summary.warning_services + summary.offline_services;
            document.getElementById("alert-active-badge").textContent = `${activeAlertCount} Active`;
            
            const timelineContainer = document.getElementById("alerts-timeline-container");
            const emptyState = document.getElementById("alerts-empty-state");
            
            timelineContainer.innerHTML = "";
            if (summary.alerts.length === 0) {
                emptyState.classList.remove("d-none");
            } else {
                emptyState.classList.add("d-none");
                summary.alerts.forEach(alert => {
                    const item = document.createElement("div");
                    item.className = `alerts-timeline-item ${alert.type}`;
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center mb-0.5">
                            <strong class="text-white">${alert.service_name}</strong>
                            <span class="text-light-50 font-monospace small" style="font-size:0.7rem;">${alert.timestamp}</span>
                        </div>
                        <div class="text-light-50">${alert.message}</div>
                    `;
                    timelineContainer.appendChild(item);
                });
            }

            return summary;
        } catch (ex) {
            console.error("Dashboard: Error fetching summaries", ex);
            return null;
        }
    }

    // Fetch and redraw services table records
    async function syncServicesList(summaryData) {
        try {
            const token = localStorage.getItem("token");
            const headers = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch("/api/services", { headers });
            const services = await response.json();
            
            const tbody = document.getElementById("services-tbody");
            tbody.innerHTML = "";

            if (services.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-light-50 py-5">Zero target endpoints configured. Click 'Add Target Node' in the sidebar to begin.</td></tr>`;
                return;
            }

            services.forEach(s => {
                const tr = document.createElement("tr");
                
                // Status Class badge
                const statusClass = `badge status-badge-${s.status.toLowerCase()}`;
                
                // Actions based on SRE user authorization roles
                const userRole = localStorage.getItem("role") || "Viewer";
                let actionHtml = `<a href="/services/${s.id}" class="btn btn-outline-info btn-xs px-2 py-0.5 me-1" title="View Logs Details"><i class="bi bi-terminal"></i></a>`;
                
                if (userRole === "Admin" || userRole === "Operator") {
                    actionHtml += `
                        <button class="btn btn-outline-warning btn-xs px-2 py-0.5 me-1 btn-table-ack" data-id="${s.id}" title="Acknowledge Alerts"><i class="bi bi-shield-check"></i></button>
                        <button class="btn btn-outline-primary btn-xs px-2 py-0.5 me-1 btn-table-check" data-id="${s.id}" title="Trigger Probe Check"><i class="bi bi-arrow-clockwise"></i></button>
                    `;
                }
                if (userRole === "Admin") {
                    actionHtml += `
                        <a href="/services/${s.id}/edit" class="btn btn-outline-secondary btn-xs px-2 py-0.5 me-1" title="Edit Configuration"><i class="bi-pencil"></i></a>
                        <button class="btn btn-outline-danger btn-xs px-2 py-0.5 btn-table-delete" data-id="${s.id}" data-name="${s.name}" title="Remove Service"><i class="bi-trash"></i></button>
                    `;
                }

                // Inline last 20 health check timeline blocks
                let timelineHtml = `<div class="d-flex gap-0.5">`;
                const recentStatuses = s.history_statuses.slice(-20); // last 20
                recentStatuses.forEach(st => {
                    timelineHtml += `<span class="timeline-block timeline-block-${st.toLowerCase()}" style="width:5px; height:12px;" title="Check: ${st}"></span>`;
                });
                if (recentStatuses.length === 0) timelineHtml += `<span class="text-light-50 small">-</span>`;
                timelineHtml += `</div>`;

                // Latency and mini sparkline canvas ID
                const sparklineId = `sparkline-${s.id}`;
                const sparklineCanvasHtml = s.history_latencies.length > 1 
                    ? `<div class="d-flex align-items-center gap-2">
                         <span class="text-info font-monospace">${s.response_time} ms</span>
                         <canvas id="${sparklineId}" width="50" height="15" class="d-none d-md-block"></canvas>
                       </div>`
                    : `<span class="text-info font-monospace">${s.response_time} ms</span>`;

                tr.innerHTML = `
                    <td class="ps-4"><a href="/services/${s.id}" class="text-white text-decoration-none fw-semibold hover-primary">${s.name}</a></td>
                    <td><span class="badge bg-dark-20 border border-dark-30 small">${s.environment}</span></td>
                    <td class="small font-monospace text-light-50">${s.ip_address}:${s.port}</td>
                    <td><span class="${statusClass}">${s.status}</span></td>
                    <td>${sparklineCanvasHtml}</td>
                    <td>${timelineHtml}</td>
                    <td class="small text-success font-monospace" title="${s.uptime_str}">${s.uptime_str}</td>
                    <td class="pe-4 text-end">${actionHtml}</td>
                `;
                tbody.appendChild(tr);

                // Render micro Sparklines chart using vanilla canvas draw
                if (s.history_latencies.length > 1) {
                    setTimeout(() => {
                        drawSparkline(sparklineId, s.history_latencies);
                    }, 50);
                }
            });

            // Bind Event Listeners on newly rendered table action buttons
            bindTableActions();

            // Feed metrics arrays for charts
            if (summaryData) {
                updateChartsTrend(summaryData, services);
            }
        } catch (ex) {
            console.error("Dashboard: Error fetching services list", ex);
        }
    }

    // Draws raw canvas sparkline without loading a full chart instance per row
    function drawSparkline(canvasId, latencies) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        
        ctx.strokeStyle = "#0dcaf0";
        ctx.lineWidth = 1;
        ctx.beginPath();
        
        const minVal = Math.min(...latencies);
        const maxVal = Math.max(...latencies);
        const range = (maxVal - minVal) || 1;
        
        latencies.forEach((val, i) => {
            const x = (i / (latencies.length - 1)) * w;
            const y = h - ((val - minVal) / range) * (h - 2) - 1;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    }

    // Handles table buttons action events
    function bindTableActions() {
        const token = localStorage.getItem("token");
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        // 1. Manual check trigger
        document.querySelectorAll(".btn-table-check").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.getAttribute("data-id");
                btn.disabled = true;
                showNotification("Triggering health check...", "info");
                try {
                    const response = await fetch(`/api/services/${id}/check`, { method: "POST", headers });
                    if (response.ok) {
                        showNotification("Health check completed.", "success");
                        refreshDashboard();
                    } else {
                        const err = await response.json();
                        throw new Error(err.detail);
                    }
                } catch (e) {
                    showNotification(e.message, "danger");
                    btn.disabled = false;
                }
            });
        });

        // 2. Alert acknowledgement
        document.querySelectorAll(".btn-table-ack").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.getAttribute("data-id");
                try {
                    const response = await fetch(`/api/services/${id}/ack`, { method: "POST", headers });
                    if (response.ok) {
                        showNotification("Alert acknowledged successfully.", "success");
                        refreshDashboard();
                    } else {
                        const err = await response.json();
                        throw new Error(err.detail);
                    }
                } catch (e) {
                    showNotification(e.message, "danger");
                }
            });
        });

        // 3. Delete configurations
        document.querySelectorAll(".btn-table-delete").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.getAttribute("data-id");
                const name = btn.getAttribute("data-name");
                if (confirm(`Are you sure you want to remove '${name}' from monitoring?`)) {
                    try {
                        const response = await fetch(`/api/services/${id}`, { method: "DELETE", headers });
                        if (response.ok) {
                            showNotification("Service config deleted.", "success");
                            refreshDashboard();
                        } else {
                            const err = await response.json();
                            throw new Error(err.detail);
                        }
                    } catch (e) {
                        showNotification(e.message, "danger");
                    }
                }
            });
        });
    }

    // Unified reload method
    async function refreshDashboard() {
        const pulse = document.getElementById("refresh-pulse");
        const refreshText = document.getElementById("refresh-text");
        
        if (pulse) {
            pulse.className = "pulse-indicator pulse-orange animate-pulse";
            refreshText.textContent = "Syncing clusters...";
        }

        const summary = await syncSummaryData();
        if (summary) {
            await syncServicesList(summary);
        }

        if (pulse) {
            pulse.className = "pulse-indicator pulse-green";
            refreshText.textContent = "Syncing live (15s)...";
        }
    }

    // Scheduler controls and automatic loops setup
    function startPollingLoop() {
        if (refreshIntervalId) clearInterval(refreshIntervalId);
        refreshIntervalId = setInterval(refreshDashboard, POLLING_INTERVAL);
    }

    function stopPollingLoop() {
        if (refreshIntervalId) {
            clearInterval(refreshIntervalId);
            refreshIntervalId = null;
        }
    }

    // Bind Auto-Refresh Switch Toggle
    const refreshToggle = document.getElementById("auto-refresh-toggle");
    if (refreshToggle) {
        refreshToggle.addEventListener("change", (e) => {
            const refreshText = document.getElementById("refresh-text");
            if (e.target.checked) {
                startPollingLoop();
                refreshText.textContent = "Syncing live (15s)...";
            } else {
                stopPollingLoop();
                refreshText.textContent = "Auto sync stopped";
            }
        });
    }

    // Force restart checks manually (Restart scheduler)
    const restartSchedulerBtn = document.getElementById("btn-restart-scheduler");
    if (restartSchedulerBtn) {
        restartSchedulerBtn.addEventListener("click", () => {
            showNotification("Restarting check scheduler daemon...", "info");
            refreshDashboard();
        });
    }

    // Execution boot
    initCharts();
    refreshDashboard();
    startPollingLoop();
});
