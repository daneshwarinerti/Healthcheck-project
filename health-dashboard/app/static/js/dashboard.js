// State Variables
let serversData = [];
let refreshIntervalId = null;

// DOM Elements
const serverTableBody = document.getElementById("server-table-body");
const totalCountEl = document.getElementById("total-servers-count");
const healthyCountEl = document.getElementById("healthy-servers-count");
const unhealthyCountEl = document.getElementById("unhealthy-servers-count");
const avgCpuTextEl = document.getElementById("avg-cpu-text");
const avgMemTextEl = document.getElementById("avg-mem-text");

const searchInput = document.getElementById("server-search");
const filterEnv = document.getElementById("filter-env");
const filterStatus = document.getElementById("filter-status");

const autoRefreshToggle = document.getElementById("auto-refresh-toggle");
const refreshPulse = document.getElementById("refresh-pulse");
const refreshText = document.getElementById("refresh-text");

const loginBtn = document.getElementById("login-btn");
const adminLoggedInDiv = document.getElementById("admin-logged-in");
const adminUsernameSpan = document.getElementById("admin-username");
const logoutBtn = document.getElementById("logout-btn");
const addServerBtnTrigger = document.getElementById("add-server-btn");

const tableLoadingSpinner = document.getElementById("table-loading-spinner");
const tableMetaText = document.getElementById("table-meta-text");
const lastUpdatedTime = document.getElementById("last-updated-time");

// Toast Notification Elements
const statusToastEl = document.getElementById("status-toast");
const toastIcon = document.getElementById("toast-icon");
const toastMessage = document.getElementById("toast-message");

// Init application
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    checkAuthState();
    fetchData();
    setupEventListeners();
    setupAutoRefresh();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-bs-theme", savedTheme);
    updateThemeUI(savedTheme);
    
    document.getElementById("theme-toggle-btn").addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-bs-theme");
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-bs-theme", nextTheme);
        localStorage.setItem("theme", nextTheme);
        updateThemeUI(nextTheme);
    });
}

function updateThemeUI(theme) {
    const sunIcon = document.getElementById("theme-icon-light");
    const moonIcon = document.getElementById("theme-icon-dark");
    if (theme === "dark") {
        sunIcon.classList.remove("d-none");
        moonIcon.classList.add("d-none");
    } else {
        sunIcon.classList.add("d-none");
        moonIcon.classList.remove("d-none");
    }
}

// Authentication Check
function checkAuthState() {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    
    if (token) {
        loginBtn.classList.add("d-none");
        adminLoggedInDiv.classList.remove("d-none");
        adminUsernameSpan.textContent = username || "Admin";
        addServerBtnTrigger.classList.remove("d-none");
        
        // Show Actions column header
        document.querySelectorAll(".action-column").forEach(el => el.classList.remove("d-none"));
    } else {
        loginBtn.classList.remove("d-none");
        adminLoggedInDiv.classList.add("d-none");
        addServerBtnTrigger.classList.add("d-none");
        
        // Hide Actions column header
        document.querySelectorAll(".action-column").forEach(el => el.classList.add("d-none"));
    }
}

// Event Listeners Registration
function setupEventListeners() {
    // Filters & Search
    searchInput.addEventListener("input", renderServersTable);
    filterEnv.addEventListener("change", renderServersTable);
    filterStatus.addEventListener("change", renderServersTable);
    
    // Logout Action
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        checkAuthState();
        renderServersTable();
        showNotification("Admin logged out successfully", "info");
    });
    
    // Auto Refresh Toggle
    autoRefreshToggle.addEventListener("change", setupAutoRefresh);

    // Form Submissions
    document.getElementById("add-server-form").addEventListener("submit", createServer);
    document.getElementById("edit-server-form").addEventListener("submit", updateServer);
}

// Notification System
function showNotification(message, type = "success") {
    // Reset toast classes
    statusToastEl.classList.remove("toast-success", "toast-danger", "toast-info");
    
    if (type === "success") {
        statusToastEl.classList.add("toast-success");
        toastIcon.className = "bi bi-check-circle-fill me-1";
    } else if (type === "error") {
        statusToastEl.classList.add("toast-danger");
        toastIcon.className = "bi bi-exclamation-triangle-fill me-1";
    } else {
        statusToastEl.classList.add("toast-info");
        toastIcon.className = "bi bi-info-circle-fill me-1";
    }
    
    toastMessage.textContent = message;
    
    const toast = bootstrap.Toast.getOrCreateInstance(statusToastEl);
    toast.show();
}

// Auto Refresh Configuration
function setupAutoRefresh() {
    if (autoRefreshToggle.checked) {
        refreshPulse.className = "pulse-indicator pulse-green";
        refreshText.textContent = "Syncing live...";
        
        // Avoid duplicate timers
        if (refreshIntervalId) clearInterval(refreshIntervalId);
        
        refreshIntervalId = setInterval(() => {
            fetchData();
        }, 10000);
    } else {
        refreshPulse.className = "pulse-indicator pulse-gray";
        refreshText.textContent = "Sync paused";
        if (refreshIntervalId) {
            clearInterval(refreshIntervalId);
            refreshIntervalId = null;
        }
    }
}

// Fetch dashboard aggregated KPIs and server list
async function fetchData() {
    tableLoadingSpinner.classList.remove("d-none");
    try {
        const [dashboardRes, serversRes] = await Promise.all([
            fetch("/dashboard"),
            fetch("/api/servers")
        ]);
        
        if (!dashboardRes.ok || !serversRes.ok) {
            throw new Error("Failed to fetch monitoring metrics");
        }
        
        const summary = await dashboardRes.json();
        serversData = await serversRes.json();
        
        // Update Aggregation Cards
        totalCountEl.textContent = summary.total_servers;
        healthyCountEl.textContent = summary.healthy_servers;
        unhealthyCountEl.textContent = summary.unhealthy_servers;
        avgCpuTextEl.textContent = `${summary.avg_cpu.toFixed(1)}%`;
        avgMemTextEl.textContent = `${summary.avg_memory.toFixed(1)}%`;
        
        // Update Last Updated Timestamp
        const now = new Date();
        lastUpdatedTime.textContent = now.toLocaleTimeString();
        
        // Render server table
        renderServersTable();
    } catch (err) {
        console.error("Fetch Data Error:", err);
        showNotification("Failed to refresh live metrics from server", "error");
    } finally {
        tableLoadingSpinner.classList.add("d-none");
    }
}

// Render dynamic server grid
function renderServersTable() {
    const query = searchInput.value.toLowerCase().trim();
    const envFilter = filterEnv.value;
    const statusFilter = filterStatus.value;
    const token = localStorage.getItem("token");
    
    // Filter servers
    const filtered = serversData.filter(s => {
        const matchesSearch = s.name.toLowerCase().includes(query) || s.ip_address.includes(query);
        const matchesEnv = envFilter === "All" || s.environment === envFilter;
        const matchesStatus = statusFilter === "All" || s.status === statusFilter;
        return matchesSearch && matchesEnv && matchesStatus;
    });
    
    // Update footer meta counts
    tableMetaText.textContent = `Showing ${filtered.length} of ${serversData.length} servers`;
    
    // Clear Table
    serverTableBody.innerHTML = "";
    
    if (filtered.length === 0) {
        serverTableBody.innerHTML = `
            <tr>
                <td colspan="${token ? 9 : 8}" class="text-center py-4 text-light-50">
                    No servers matching the filter requirements.
                </td>
            </tr>
        `;
        return;
    }
    
    filtered.forEach(s => {
        const tr = document.createElement("tr");
        
        // Status class selection
        let badgeClass = "badge-offline";
        let pulseClass = "pulse-gray";
        if (s.status === "Healthy") {
            badgeClass = "badge-healthy";
            pulseClass = "pulse-green";
        } else if (s.status === "Warning") {
            badgeClass = "badge-warning";
            pulseClass = "pulse-yellow";
        } else if (s.status === "Critical") {
            badgeClass = "badge-critical";
            pulseClass = "pulse-red";
        }
        
        // Environment Badge Color
        let envClass = "bg-secondary";
        if (s.environment === "Prod") envClass = "bg-primary";
        else if (s.environment === "Test") envClass = "bg-info text-dark";
        
        // CPU progress bar coloring
        let cpuColor = "bg-success";
        if (s.cpu_usage > 85) cpuColor = "bg-danger";
        else if (s.cpu_usage >= 70) cpuColor = "bg-warning";
        else if (s.status === "Offline") cpuColor = "bg-secondary";
        
        // Memory progress bar coloring
        let memColor = "bg-success";
        if (s.memory_usage > 90) memColor = "bg-danger";
        else if (s.memory_usage >= 75) memColor = "bg-warning";
        else if (s.status === "Offline") memColor = "bg-secondary";

        // Uptime representation
        const uptimeDisplay = s.status === "Offline" ? "--" : `${s.uptime}d`;
        
        // Format last checked timestamp
        const timeStr = new Date(s.last_checked).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        // Actions buttons HTML if logged in
        let actionButtonsHtml = "";
        if (token) {
            actionButtonsHtml = `
                <td class="pe-4 text-end action-column">
                    <button class="btn btn-sm btn-outline-warning me-1 px-2.5 py-1" onclick="openEditModal(${s.id}, '${s.name}', '${s.environment}', '${s.ip_address}')" title="Edit Server Config">
                        <i class="bi bi-pencil-fill"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger px-2.5 py-1" onclick="deleteServer(${s.id}, '${s.name}')" title="Delete Server">
                        <i class="bi bi-trash3-fill"></i>
                    </button>
                </td>
            `;
        }

        tr.innerHTML = `
            <td class="ps-4 fw-semibold">${s.name}</td>
            <td><span class="badge ${envClass} small fw-bold">${s.environment}</span></td>
            <td class="font-monospace text-light-50">${s.ip_address}</td>
            <td>
                <span class="status-badge ${badgeClass}">
                    <span class="pulse-indicator ${pulseClass}"></span>
                    ${s.status}
                </span>
            </td>
            <td>
                <div class="progress-metrics-wrapper">
                    <div class="d-flex justify-content-between progress-metric-title">
                        <span>CPU</span>
                        <span>${s.status === 'Offline' ? 0 : s.cpu_usage.toFixed(0)}%</span>
                    </div>
                    <div class="progress-custom">
                        <div class="progress-bar-custom ${cpuColor}" style="width: ${s.status === 'Offline' ? 0 : s.cpu_usage}%"></div>
                    </div>
                </div>
            </td>
            <td>
                <div class="progress-metrics-wrapper">
                    <div class="d-flex justify-content-between progress-metric-title">
                        <span>Mem</span>
                        <span>${s.status === 'Offline' ? 0 : s.memory_usage.toFixed(0)}%</span>
                    </div>
                    <div class="progress-custom">
                        <div class="progress-bar-custom ${memColor}" style="width: ${s.status === 'Offline' ? 0 : s.memory_usage}%"></div>
                    </div>
                </div>
            </td>
            <td>${uptimeDisplay}</td>
            <td class="text-light-50 small">${timeStr}</td>
            ${actionButtonsHtml}
        `;
        
        serverTableBody.appendChild(tr);
    });
}

// POST Create Server
async function createServer(e) {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;

    const submitBtn = document.getElementById("add-submit-btn");
    const spinner = document.getElementById("add-spinner");
    
    // Disable inputs and show loading state
    submitBtn.disabled = true;
    spinner.classList.remove("d-none");

    const name = document.getElementById("add-name").value.trim();
    const environment = document.getElementById("add-env").value;
    const ip_address = document.getElementById("add-ip").value.trim();

    try {
        const response = await fetch("/api/servers", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ name, environment, ip_address })
        });

        const data = await response.json();
        
        if (!response.ok) {
            // Check for custom validation errors (422 format details)
            let errMsg = data.detail || "Failed to create server";
            if (data.errors && data.errors.length > 0) {
                errMsg = data.errors.join(", ");
            }
            throw new Error(errMsg);
        }

        // Hide bootstrap modal
        const modalEl = document.getElementById("addServerModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        document.getElementById("add-server-form").reset();

        showNotification(`Server '${name}' created successfully`, "success");
        fetchData();
    } catch (err) {
        showNotification(err.message, "error");
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add("d-none");
    }
}

// Populate and Open Edit Modal
window.openEditModal = function(id, name, env, ip) {
    document.getElementById("edit-id").value = id;
    document.getElementById("edit-name").value = name;
    document.getElementById("edit-env").value = env;
    document.getElementById("edit-ip").value = ip;
    
    const editModal = new bootstrap.Modal(document.getElementById("editServerModal"));
    editModal.show();
}

// PUT Update Server
async function updateServer(e) {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) return;

    const submitBtn = document.getElementById("edit-submit-btn");
    const spinner = document.getElementById("edit-spinner");
    
    submitBtn.disabled = true;
    spinner.classList.remove("d-none");

    const id = document.getElementById("edit-id").value;
    const name = document.getElementById("edit-name").value.trim();
    const environment = document.getElementById("edit-env").value;
    const ip_address = document.getElementById("edit-ip").value.trim();

    try {
        const response = await fetch(`/api/servers/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ name, environment, ip_address })
        });

        const data = await response.json();
        
        if (!response.ok) {
            let errMsg = data.detail || "Failed to update server";
            if (data.errors && data.errors.length > 0) {
                errMsg = data.errors.join(", ");
            }
            throw new Error(errMsg);
        }

        // Hide modal
        const modalEl = document.getElementById("editServerModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();
        document.getElementById("edit-server-form").reset();

        showNotification(`Server '${name}' configuration updated`, "success");
        fetchData();
    } catch (err) {
        showNotification(err.message, "error");
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add("d-none");
    }
}

// DELETE Server
window.deleteServer = async function(id, name) {
    const token = localStorage.getItem("token");
    if (!token) return;

    if (!confirm(`Are you sure you want to delete server '${name}' from monitoring configurations?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/servers/${id}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || "Failed to delete server");
        }

        showNotification(`Server '${name}' deleted successfully`, "success");
        fetchData();
    } catch (err) {
        showNotification(err.message, "error");
    }
}
