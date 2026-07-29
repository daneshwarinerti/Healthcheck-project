/* SRE Logs Explorer Form Handling, Pagination, & Live Terminal Formatters */

document.addEventListener("DOMContentLoaded", () => {
    // Highlight Sidebar active selection
    const navLogs = document.getElementById("nav-logs");
    if (navLogs) navLogs.classList.add("active", "bg-primary");

    const queryForm = document.getElementById("logs-query-form");
    const logTypeSelect = document.getElementById("log-type");
    const serviceFilterContainer = document.getElementById("filter-service-container");
    const statusFilterContainer = document.getElementById("filter-status-container");
    
    const tableContainer = document.getElementById("ledger-table-container");
    const terminalContainer = document.getElementById("ledger-terminal-container");
    const terminalScreen = document.getElementById("terminal-screen");
    const tableHead = document.getElementById("logs-explorer-thead");
    const tableBody = document.getElementById("logs-explorer-tbody");
    
    const ledgerTitle = document.getElementById("ledger-title");
    const ledgerBadge = document.getElementById("ledger-count-badge");

    // Pagination elements
    const paginationContainer = document.getElementById("ledger-pagination-container");
    const btnPrevPage = document.getElementById("btn-prev-page");
    const btnNextPage = document.getElementById("btn-next-page");
    const pageIndicator = document.getElementById("page-indicator");

    let currentPage = 1;
    const pageLimit = 25; // 25 rows per page

    // Dynamic Filter Visibility toggles depending on selected type
    logTypeSelect.addEventListener("change", () => {
        const type = logTypeSelect.value;
        if (type === "health") {
            serviceFilterContainer.classList.remove("d-none");
            statusFilterContainer.classList.remove("d-none");
        } else {
            serviceFilterContainer.classList.add("d-none");
            statusFilterContainer.classList.add("d-none");
        }
        // Reset page on type change
        currentPage = 1;
    });

    // Reset page when search parameters are edited
    queryForm.addEventListener("change", () => {
        currentPage = 1;
    });

    // Execute query
    async function executeQuery() {
        const type = logTypeSelect.value;
        const serviceId = document.getElementById("log-service-id").value;
        const statusVal = document.getElementById("log-status").value;
        
        let url = `/logs?type=${type}&page=${currentPage}&limit=${pageLimit}`;
        if (type === "health") {
            if (serviceId) url += `&service_id=${serviceId}`;
            if (statusVal && statusVal !== "All") url += `&status=${statusVal}`;
        }

        const token = localStorage.getItem("token");
        const headers = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        try {
            // Loading State
            tableBody.innerHTML = `<tr><td class="text-center py-5 text-light-50"><div class="spinner-border spinner-border-sm text-primary me-2"></div>Querying logs...</td></tr>`;
            terminalScreen.innerHTML = `<div class="text-light-50 text-center py-5">Loading application process logs stream...</div>`;
            
            const response = await fetch(url, { headers });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || "Failed to execute logs search query.");
            }

            // Hide/Show pagination controls based on log type
            if (type === "application") {
                paginationContainer.classList.add("d-none");
            } else {
                paginationContainer.classList.remove("d-none");
                pageIndicator.textContent = `Page ${currentPage}`;
                
                // Update navigation button states
                btnPrevPage.disabled = currentPage === 1;
                // If returned rows are less than page limit, we are on the last page
                btnNextPage.disabled = data.length < pageLimit;
            }

            // 1. Health Probe Logs
            if (type === "health") {
                tableContainer.classList.remove("d-none");
                terminalContainer.classList.add("d-none");
                ledgerTitle.textContent = "Health Checks Probe Logs";
                ledgerBadge.textContent = `${data.length} Records`;
                
                tableHead.innerHTML = `
                    <tr class="table-header-style">
                        <th class="ps-4">Timestamp</th>
                        <th>Service Node</th>
                        <th>Status</th>
                        <th>Latency Response</th>
                        <th>HTTP Status</th>
                        <th class="pe-4">Remarks / Exception</th>
                    </tr>
                `;
                
                tableBody.innerHTML = "";
                if (data.length === 0) {
                    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-light-50 py-4">No health logs found matching these filters.</td></tr>`;
                    return;
                }
                
                data.forEach(log => {
                    const row = document.createElement("tr");
                    const date = new Date(log.timestamp);
                    const timeStr = date.toLocaleString();
                    const statusClass = `badge status-badge-${log.status.toLowerCase()}`;
                    const httpCode = log.http_status ? log.http_status : '-';
                    const remarksText = log.remarks ? log.remarks : '-';
                    
                    row.innerHTML = `
                        <td class="ps-4 fw-medium text-white-50">${timeStr}</td>
                        <td class="fw-bold">${log.service_name}</td>
                        <td><span class="${statusClass}">${log.status}</span></td>
                        <td class="text-info font-monospace">${log.response_time} ms</td>
                        <td class="fw-bold">${httpCode}</td>
                        <td class="pe-4 text-light-50 font-monospace small" style="max-width:350px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${remarksText}">${remarksText}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 2. Audit Logs
            else if (type === "audit") {
                tableContainer.classList.remove("d-none");
                terminalContainer.classList.add("d-none");
                ledgerTitle.textContent = "SRE Administrative Audit Trail";
                ledgerBadge.textContent = `${data.length} Records`;
                
                tableHead.innerHTML = `
                    <tr class="table-header-style">
                        <th class="ps-4">Timestamp</th>
                        <th>Operator Identity</th>
                        <th>Action</th>
                        <th>Audit Details</th>
                        <th class="pe-4">IP Coordinates</th>
                    </tr>
                `;
                
                tableBody.innerHTML = "";
                if (data.length === 0) {
                    tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-light-50 py-4">No audit logs found.</td></tr>`;
                    return;
                }
                
                data.forEach(log => {
                    const row = document.createElement("tr");
                    const date = new Date(log.timestamp);
                    const timeStr = date.toLocaleString();
                    const ip = log.ip_address ? log.ip_address : '-';
                    
                    row.innerHTML = `
                        <td class="ps-4 fw-medium text-white-50">${timeStr}</td>
                        <td class="text-primary fw-semibold"><i class="bi bi-person-fill me-1"></i>${log.user_email}</td>
                        <td class="fw-bold text-white">${log.action}</td>
                        <td class="text-light-50 small">${log.details || '-'}</td>
                        <td class="pe-4 font-monospace small">${ip}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 3. Live Application logging (stdout application.log)
            else {
                tableContainer.classList.add("d-none");
                terminalContainer.classList.remove("d-none");
                ledgerTitle.textContent = "Live Python Process Logs (application.log)";
                
                const lines = data.logs || [];
                ledgerBadge.textContent = `${lines.length} Lines`;
                
                terminalScreen.innerHTML = "";
                if (lines.length === 0) {
                    terminalScreen.innerHTML = `<div class="text-light-50">Empty log output. Trigger checks or perform operations.</div>`;
                    return;
                }
                
                lines.forEach(line => {
                    const div = document.createElement("div");
                    div.className = "terminal-line";
                    
                    if (line.includes("[ERROR]") || line.includes("[CRITICAL]")) {
                        div.className += " terminal-error";
                    } else if (line.includes("[WARNING]")) {
                        div.className += " terminal-warn";
                    } else {
                        div.className += " terminal-info";
                    }
                    
                    div.textContent = line;
                    terminalScreen.appendChild(div);
                });
                
                // Automatically scroll terminal to the bottom
                terminalScreen.scrollTop = terminalScreen.scrollHeight;
            }

        } catch (ex) {
            showNotification(ex.message, "danger");
            tableBody.innerHTML = `<tr><td class="text-center text-danger py-4"><i class="bi bi-exclamation-octagon me-2"></i>Error querying logs: ${ex.message}</td></tr>`;
        }
    }

    queryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        currentPage = 1; // Reset to page 1 on search submit
        executeQuery();
    });
    
    // Pagination button clicks
    btnPrevPage.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            executeQuery();
        }
    });

    btnNextPage.addEventListener("click", () => {
        currentPage++;
        executeQuery();
    });

    // Auto-run initial query
    executeQuery();
});
