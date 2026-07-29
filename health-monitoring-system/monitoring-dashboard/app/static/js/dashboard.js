/* SRE Live Dashboard Charting, Filtering, and Drawer Sheet Engine */

document.addEventListener("DOMContentLoaded", () => {
    // Activate Sidebar Navigation highlight
    const navDashboard = document.getElementById("nav-dashboard");
    if (navDashboard) navDashboard.classList.add("active");

    // Local cached state
    let cachedServices = [];
    let charts = {};
    let drawerHistoryChart = null;
    let refreshIntervalId = null;
    const POLLING_INTERVAL = 15000; // 15 seconds

    // Telemetry trend history arrays (last 12 points)
    const MAX_TREND_POINTS = 12;
    const trendLabels = [];
    const cpuTrend = [];
    const ramTrend = [];
    const latencyTrend = [];
    const availabilityTrend = [];
    const rpmTrend = [];

    // Initialize Telemetry Charts
    function initCharts() {
        const gridColor = 'rgba(255, 255, 255, 0.04)';
        const tickColor = '#64748B';
        const labelFont = { family: 'Inter', size: 9, weight: '500' };

        const chartOptions = (color) => ({
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: {
                    grid: { color: gridColor },
                    border: { dash: [4, 4] },
                    ticks: { color: tickColor, font: labelFont }
                }
            }
        });

        // 1. Latency Chart
        charts.latency = new Chart(document.getElementById('chart-latency').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'Latency', data: latencyTrend, borderColor: '#06B6D4', backgroundColor: 'rgba(6, 182, 212, 0.04)', borderWidth: 1.8, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: chartOptions()
        });

        // 2. CPU Chart
        charts.cpu = new Chart(document.getElementById('chart-cpu').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'CPU Usage', data: cpuTrend, borderColor: '#3B82F6', backgroundColor: 'rgba(59, 130, 246, 0.04)', borderWidth: 1.8, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { ...chartOptions(), scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: labelFont } } } }
        });

        // 3. RAM Chart
        charts.ram = new Chart(document.getElementById('chart-ram').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'Memory', data: ramTrend, borderColor: '#22C55E', backgroundColor: 'rgba(34, 197, 94, 0.04)', borderWidth: 1.8, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { ...chartOptions(), scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: labelFont } } } }
        });

        // 4. Availability Chart
        charts.availability = new Chart(document.getElementById('chart-availability').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'Availability', data: availabilityTrend, borderColor: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.04)', borderWidth: 1.8, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: { ...chartOptions(), scales: { x: { display: false }, y: { min: 0, max: 100, grid: { color: gridColor }, ticks: { color: tickColor, font: labelFont } } } }
        });

        // 5. Distribution Doughnut Chart
        charts.distribution = new Chart(document.getElementById('chart-distribution').getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Warning', 'Critical', 'Offline'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: ['#22C55E', '#F59E0B', '#EF4444', '#64748B'],
                    borderWidth: 2,
                    borderColor: '#111827'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                cutout: '76%'
            }
        });

        // 6. RPM Chart
        charts.rpm = new Chart(document.getElementById('chart-rpm').getContext('2d'), {
            type: 'line',
            data: { labels: trendLabels, datasets: [{ label: 'RPM', data: rpmTrend, borderColor: '#EC4899', backgroundColor: 'rgba(236, 72, 153, 0.04)', borderWidth: 1.8, fill: true, tension: 0.3, pointRadius: 1 }] },
            options: chartOptions()
        });
    }

    // Refresh charts dataset with polling trends
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
        
        let totalAvail = 0;
        servicesList.forEach(s => totalAvail += s.availability);
        const avgAvail = servicesList.length > 0 ? (totalAvail / servicesList.length) : 100;
        availabilityTrend.push(avgAvail);

        const simulatedRpm = Math.round(40 + (summaryData.system.cpu_percent * 2.1) + (Math.random() * 12));
        rpmTrend.push(simulatedRpm);

        charts.latency.update();
        charts.cpu.update();
        charts.ram.update();
        charts.availability.update();
        charts.rpm.update();

        charts.distribution.data.datasets[0].data = [
            summaryData.healthy_services,
            summaryData.warning_services,
            summaryData.critical_services,
            summaryData.offline_services
        ];
        charts.distribution.update();
    }

    // Fetch KPI summaries and alerts
    async function syncSummaryData() {
        try {
            const token = localStorage.getItem("token");
            const headers = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch("/dashboard", { headers });
            if (response.status === 401) {
                window.location.href = "/logout";
                return null;
            }
            
            const summary = await response.json();

            // Card values
            document.getElementById("card-total-services").textContent = summary.total_services;
            document.getElementById("card-healthy-services").textContent = summary.healthy_services;
            document.getElementById("card-warning-services").textContent = summary.warning_services;
            document.getElementById("card-critical-offline-services").textContent = summary.critical_services + summary.offline_services;
            document.getElementById("card-avg-latency").textContent = summary.avg_response_time;

            // System Load Indicators
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
            document.getElementById("card-net-uptime").textContent = `Boot: ${summary.system.system_uptime}`;

            // Active Alert timelines
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
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="text-white small d-flex align-items-center gap-1">
                                <span class="status-dot ${alert.type}"></span>
                                ${alert.service_name}
                            </strong>
                            <span class="text-muted font-monospace" style="font-size:0.68rem;">${alert.timestamp}</span>
                        </div>
                        <div class="text-secondary" style="font-size: 0.76rem; line-height:1.3;">${alert.message}</div>
                    `;
                    timelineContainer.appendChild(item);
                });
            }

            return summary;
        } catch (ex) {
            console.error("Dashboard: Error fetching SRE summaries", ex);
            return null;
        }
    }

    // Synchronize services target config data list
    async function syncServicesList(summaryData) {
        try {
            const token = localStorage.getItem("token");
            const headers = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch("/api/services", { headers });
            cachedServices = await response.json();
            
            // Draw filtered list
            renderServicesTable();

            if (summaryData) {
                updateChartsTrend(summaryData, cachedServices);
            }
        } catch (ex) {
            console.error("Dashboard: Error syncing targets configuration list", ex);
        }
    }

    // Render Table based on search, filter, and sort criteria
    function renderServicesTable() {
        const tbody = document.getElementById("services-tbody");
        if (!tbody) return;

        const searchVal = document.getElementById("table-search-input").value.trim().toLowerCase();
        const envVal = document.getElementById("table-filter-env").value;
        const statusVal = document.getElementById("table-filter-status").value;
        const sortBy = document.getElementById("table-sort-by").value;

        // Apply filters
        let filtered = cachedServices.filter(s => {
            const matchesSearch = s.name.toLowerCase().includes(searchVal) || 
                                  s.health_url.toLowerCase().includes(searchVal) ||
                                  s.ip_address.includes(searchVal);
            
            const matchesEnv = (envVal === "All") || (s.environment === envVal);
            const matchesStatus = (statusVal === "All") || (s.status.toLowerCase() === statusVal.toLowerCase());
            
            return matchesSearch && matchesEnv && matchesStatus;
        });

        // Apply sorting
        filtered.sort((a, b) => {
            if (sortBy === "name") {
                return a.name.localeCompare(b.name);
            } else if (sortBy === "latency") {
                return a.response_time - b.response_time;
            } else if (sortBy === "uptime") {
                return b.availability - a.availability;
            } else if (sortBy === "status") {
                return a.status.localeCompare(b.status);
            }
            return 0;
        });

        tbody.innerHTML = "";

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="text-center py-5">
                        <div class="empty-state border-0 bg-transparent">
                            <i data-lucide="search-code" class="empty-state-icon"></i>
                            <h6 class="empty-state-title">No target nodes match criteria</h6>
                            <p class="empty-state-desc">Refine your active dashboard filter settings above.</p>
                        </div>
                    </td>
                </tr>
            `;
            lucide.createIcons();
            return;
        }

        filtered.forEach(s => {
            const tr = document.createElement("tr");
            tr.style.cursor = "pointer";
            
            // Row Click to slide-out details inspector
            tr.addEventListener("click", (e) => {
                if (e.target.closest("button") || e.target.closest("a")) {
                    return; // Ignore row-click details trigger if actions buttons were clicked
                }
                openServiceDrawer(s.id);
            });

            const statusClass = s.status.toLowerCase();
            const badgeClass = `badge-status ${statusClass}`;
            const userRole = localStorage.getItem("role") || "Viewer";

            // Actions HTML
            let actionsHtml = `
                <div class="action-cell">
                    <button class="btn-icon btn-table-check" data-id="${s.id}" title="Trigger Probe Check"><i data-lucide="refresh-cw"></i></button>
            `;
            if (userRole === "Admin" || userRole === "Operator") {
                actionsHtml += `
                    <button class="btn-icon btn-table-ack text-warning" data-id="${s.id}" title="Acknowledge Alerts"><i data-lucide="shield-alert"></i></button>
                `;
            }
            if (userRole === "Admin") {
                actionsHtml += `
                    <a href="/services/${s.id}/edit" class="btn-icon text-secondary" title="Edit Configuration"><i data-lucide="settings"></i></a>
                    <button class="btn-icon text-danger btn-table-delete" data-id="${s.id}" data-name="${s.name}" title="Remove Node"><i data-lucide="trash-2"></i></button>
                `;
            }
            actionsHtml += `</div>`;

            // Last 20 Checks timeline
            let checkBlocks = `<div class="d-flex gap-1">`;
            const recentStatuses = s.history_statuses.slice(-20);
            recentStatuses.forEach(st => {
                const c = st.toLowerCase();
                checkBlocks += `<span class="status-dot ${c}" style="width: 5px; height: 12px; border-radius: 1px;" title="Check: ${st}"></span>`;
            });
            if (recentStatuses.length === 0) checkBlocks += `<span class="text-muted small">-</span>`;
            checkBlocks += `</div>`;

            // Latency canvas mini Sparkline
            const sparklineId = `sparkline-${s.id}`;
            const sparklineHtml = s.history_latencies.length > 1
                ? `<div class="d-flex align-items-center gap-2">
                     <span class="text-primary font-monospace fw-semibold">${s.response_time}ms</span>
                     <div class="sparkline-container"><canvas id="${sparklineId}" class="sparkline-canvas"></canvas></div>
                   </div>`
                : `<span class="text-primary font-monospace fw-semibold">${s.response_time}ms</span>`;

            tr.innerHTML = `
                <td class="ps-4 fw-semibold text-white">${s.name}</td>
                <td><span class="badge" style="background-color: rgba(255,255,255,0.03); border: 1px solid var(--border-color); color: var(--text-secondary); font-size:0.75rem;">${s.environment}</span></td>
                <td class="font-monospace text-secondary">${s.ip_address}:${s.port}</td>
                <td>
                    <span class="${badgeClass}">
                        <span class="status-dot ${statusClass}"></span>
                        ${s.status}
                    </span>
                </td>
                <td>${sparklineHtml}</td>
                <td class="font-monospace text-secondary">${s.availability.toFixed(1)}%</td>
                <td>${checkBlocks}</td>
                <td class="small text-muted font-monospace">${s.version || '1.0.0'}</td>
                <td class="pe-4">${actionsHtml}</td>
            `;

            tbody.appendChild(tr);

            // Draw custom inline canvas sparkline
            if (s.history_latencies.length > 1) {
                setTimeout(() => {
                    drawSparkline(sparklineId, s.history_latencies, s.status);
                }, 50);
            }
        });

        lucide.createIcons();
        bindTableActions();
    }

    // Sparkline Canvas graphics generator with soft fill gradients
    function drawSparkline(canvasId, latencies, status) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        const w = canvas.width;
        const h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        
        let color = '#3B82F6'; // Default primary
        if (status.toLowerCase() === 'healthy') color = '#22C55E';
        if (status.toLowerCase() === 'warning') color = '#F59E0B';
        if (status.toLowerCase() === 'critical') color = '#EF4444';

        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        
        const minVal = Math.min(...latencies);
        const maxVal = Math.max(...latencies);
        const range = (maxVal - minVal) || 1;
        
        latencies.forEach((val, i) => {
            const x = (i / (latencies.length - 1)) * w;
            const y = h - ((val - minVal) / range) * (h - 4) - 2;
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    }

    // Bind event listeners for table buttons
    function bindTableActions() {
        const token = localStorage.getItem("token");
        const headers = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;

        // 1. Manual Check trigger
        document.querySelectorAll(".btn-table-check").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation(); // Stop row click trigger
                const id = btn.getAttribute("data-id");
                btn.disabled = true;
                showNotification("Executing health check probe...", "info");
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

        // 2. Alert Acknowledgement
        document.querySelectorAll(".btn-table-ack").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute("data-id");
                try {
                    const response = await fetch(`/api/services/${id}/ack`, { method: "POST", headers });
                    if (response.ok) {
                        showNotification("Incidents acknowledged.", "success");
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

        // 3. Delete Configurations
        document.querySelectorAll(".btn-table-delete").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute("data-id");
                const name = btn.getAttribute("data-name");
                if (confirm(`Remove SRE node target monitoring configuration for '${name}'?`)) {
                    try {
                        const response = await fetch(`/api/services/${id}`, { method: "DELETE", headers });
                        if (response.ok) {
                            showNotification("Service deleted.", "success");
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

    // Slide-over Drawer Details panel inspector
    async function openServiceDrawer(id) {
        const drawer = document.getElementById("service-detail-drawer");
        const backdrop = document.getElementById("drawer-backdrop");
        const drawerContent = document.getElementById("drawer-content");
        
        // Show panel
        drawer.classList.add("open");
        backdrop.classList.add("show");
        
        drawerContent.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;"></div>
                <p class="mt-2 text-muted">Retrieving metrics history...</p>
            </div>
        `;

        try {
            const token = localStorage.getItem("token");
            const headers = {};
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch(`/api/services/${id}`, { headers });
            const s = await response.json();
            
            document.getElementById("drawer-service-name").textContent = s.name;

            // Details drawer body layout
            const statusClass = s.status.toLowerCase();
            const userRole = localStorage.getItem("role") || "Viewer";
            
            let recentChecks = `<div class="d-flex gap-1.5 flex-wrap">`;
            s.history_statuses.forEach(st => {
                recentChecks += `<span class="status-dot ${st.toLowerCase()}" style="width: 8px; height: 16px; border-radius: 1px;" title="Check: ${st}"></span>`;
            });
            recentChecks += `</div>`;

            // Draw config settings thresholds
            drawerContent.innerHTML = `
                <div class="mb-4">
                    <span class="badge-status ${statusClass} w-100 justify-content-center py-2 fs-6 mb-3">
                        <span class="status-dot ${statusClass}" style="width:10px; height:10px;"></span>
                        STATUS: ${s.status.toUpperCase()}
                    </span>
                    
                    <p class="text-secondary small mb-3">${s.description || 'No descriptive summaries added.'}</p>
                </div>
                
                <h6 class="form-label-enterprise border-bottom pb-1.5" style="border-bottom-color: var(--border-color) !important;">NODE CONFIGURATION</h6>
                <div class="row g-2 mb-4 font-monospace" style="font-size: 0.8rem;">
                    <div class="col-5 text-muted">Environment:</div>
                    <div class="col-7 text-white">${s.environment}</div>
                    
                    <div class="col-5 text-muted">Address:</div>
                    <div class="col-7 text-white">${s.ip_address}:${s.port}</div>
                    
                    <div class="col-5 text-muted">Endpoint URL:</div>
                    <div class="col-7 text-white text-truncate" title="${s.health_url}">${s.health_url}</div>
                    
                    <div class="col-5 text-muted">Version:</div>
                    <div class="col-7 text-white">${s.version || '1.0.0'}</div>

                    <div class="col-5 text-muted">Uptime:</div>
                    <div class="col-7 text-success">${s.uptime_str || 'N/A'}</div>
                </div>

                <h6 class="form-label-enterprise border-bottom pb-1.5" style="border-bottom-color: var(--border-color) !important;">PERFORMANCE METRICS</h6>
                <div class="row g-2 mb-4 font-monospace" style="font-size: 0.8rem;">
                    <div class="col-5 text-muted">Latency Limit:</div>
                    <div class="col-7 text-white">${s.response_time_threshold} ms</div>
                    
                    <div class="col-5 text-muted">Current Latency:</div>
                    <div class="col-7 text-info fw-bold">${s.response_time} ms</div>
                    
                    <div class="col-5 text-muted">Availability:</div>
                    <div class="col-7 text-success fw-bold">${s.availability.toFixed(2)}%</div>
                </div>

                <h6 class="form-label-enterprise border-bottom pb-1.5" style="border-bottom-color: var(--border-color) !important;">HISTORICAL LOG PROBES (20 Checks)</h6>
                <div class="p-3 rounded mb-4" style="background-color: rgba(0,0,0,0.15); border: 1px solid var(--border-color);">
                    ${recentChecks}
                </div>

                <h6 class="form-label-enterprise border-bottom pb-1.5" style="border-bottom-color: var(--border-color) !important;">LATENCY HISTORY PLOT</h6>
                <div class="p-2 rounded mb-4" style="background-color: rgba(0,0,0,0.15); border: 1px solid var(--border-color); height: 160px;">
                    <canvas id="drawer-latency-history-chart" style="width: 100%; height: 100%;"></canvas>
                </div>

                <div class="d-flex gap-2">
                    <button class="btn-primary-enterprise flex-grow-1 py-2 d-flex align-items-center justify-content-center gap-1.5" id="drawer-btn-check" data-id="${s.id}">
                        <i data-lucide="refresh-cw" style="width: 15px; height: 15px;"></i>
                        <span>Run Probe</span>
                    </button>
                    ${(userRole === 'Admin' || userRole === 'Operator') ? `
                    <button class="btn-icon text-warning py-2 w-25 btn-table-ack" data-id="${s.id}" style="height:38px;" title="Acknowledge Alert">
                        <i data-lucide="shield-alert"></i>
                    </button>
                    ` : ''}
                </div>
            `;
            
            lucide.createIcons();

            // Setup latency history chart inside drawer body
            if (s.history_latencies.length > 0) {
                const drawerCtx = document.getElementById("drawer-latency-history-chart").getContext("2d");
                const labels = s.history_latencies.map((_, i) => `Check ${i + 1}`);
                
                if (drawerHistoryChart) drawerHistoryChart.destroy();
                drawerHistoryChart = new Chart(drawerCtx, {
                    type: 'line',
                    data: {
                        labels,
                        datasets: [{
                            label: 'Latency',
                            data: s.history_latencies,
                            borderColor: '#3B82F6',
                            borderWidth: 2,
                            fill: true,
                            backgroundColor: 'rgba(59, 130, 246, 0.05)',
                            pointRadius: 2,
                            tension: 0.15
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            x: { display: false },
                            y: {
                                grid: { color: 'rgba(255, 255, 255, 0.03)' },
                                ticks: { color: '#64748B', font: { size: 9 } }
                            }
                        }
                    }
                });
            }

            // Bind drawer events
            document.getElementById("drawer-btn-check").addEventListener("click", async () => {
                const btn = document.getElementById("drawer-btn-check");
                btn.disabled = true;
                showNotification("Executing health check probe...", "info");
                try {
                    const response = await fetch(`/api/services/${s.id}/check`, { method: "POST", headers });
                    if (response.ok) {
                        showNotification("Health check completed.", "success");
                        openServiceDrawer(s.id); // Reload drawer details
                        refreshDashboard();      // Reload dashboard background
                    } else {
                        const err = await response.json();
                        throw new Error(err.detail);
                    }
                } catch (e) {
                    showNotification(e.message, "danger");
                    btn.disabled = false;
                }
            });

            const ackBtn = drawerContent.querySelector(".btn-table-ack");
            if (ackBtn) {
                ackBtn.addEventListener("click", async () => {
                    try {
                        const response = await fetch(`/api/services/${s.id}/ack`, { method: "POST", headers });
                        if (response.ok) {
                            showNotification("Incidents acknowledged.", "success");
                            openServiceDrawer(s.id);
                            refreshDashboard();
                        } else {
                            const err = await response.json();
                            throw new Error(err.detail);
                        }
                    } catch (e) {
                        showNotification(e.message, "danger");
                    }
                });
            }

        } catch (ex) {
            console.error("Drawer: Error loading service metrics details", ex);
            drawerContent.innerHTML = `<p class="text-danger small py-5 text-center">Failed to query detailed metric history endpoints.</p>`;
        }
    }

    function closeServiceDrawer() {
        document.getElementById("service-detail-drawer").classList.remove("open");
        document.getElementById("drawer-backdrop").classList.remove("show");
        if (drawerHistoryChart) {
            drawerHistoryChart.destroy();
            drawerHistoryChart = null;
        }
    }

    // Bind drawer backdrop and close button clicks
    document.getElementById("drawer-close-btn").addEventListener("click", closeServiceDrawer);
    document.getElementById("drawer-backdrop").addEventListener("click", closeServiceDrawer);

    // Bind filters input actions
    document.getElementById("table-search-input").addEventListener("input", renderServicesTable);
    document.getElementById("table-filter-env").addEventListener("change", renderServicesTable);
    document.getElementById("table-filter-status").addEventListener("change", renderServicesTable);
    document.getElementById("table-sort-by").addEventListener("change", renderServicesTable);

    // Unified reload sync method
    async function refreshDashboard() {
        const pulse = document.getElementById("refresh-pulse");
        const refreshText = document.getElementById("refresh-text");
        
        if (pulse) {
            pulse.className = "status-dot warning animate-pulse";
            refreshText.textContent = "SYNC: LOADING";
        }

        const summary = await syncSummaryData();
        if (summary) {
            await syncServicesList(summary);
        }

        if (pulse) {
            pulse.className = "status-dot healthy";
            refreshText.textContent = "SYNC: ACTIVE";
        }
    }

    // Polling setup
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

    // Auto refresh toggle
    const refreshToggle = document.getElementById("auto-refresh-toggle");
    if (refreshToggle) {
        refreshToggle.addEventListener("change", (e) => {
            const refreshText = document.getElementById("refresh-text");
            if (e.target.checked) {
                startPollingLoop();
                refreshText.textContent = "SYNC: ACTIVE";
            } else {
                stopPollingLoop();
                refreshText.textContent = "SYNC: OFF";
            }
        });
    }

    // Force restart checks manually
    const restartSchedulerBtn = document.getElementById("btn-restart-scheduler");
    if (restartSchedulerBtn) {
        restartSchedulerBtn.addEventListener("click", () => {
            showNotification("Restarting check scheduler daemon...", "info");
            refreshDashboard();
        });
    }

    // Boot
    initCharts();
    refreshDashboard();
    startPollingLoop();
});
