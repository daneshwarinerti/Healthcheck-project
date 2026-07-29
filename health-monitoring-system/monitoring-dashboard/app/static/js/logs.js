/* SRE Logs Explorer Form Handling, Pagination, & Live Terminal Formatters */

document.addEventListener("DOMContentLoaded", () => {
    // Highlight Sidebar active selection
    const navLogs = document.getElementById("nav-logs");
    if (navLogs) navLogs.classList.add("active");

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
        currentPage = 1;
    });

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
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-5 text-muted">
                        <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                        Querying SRE log datasets...
                    </td>
                </tr>
            `;
            terminalScreen.innerHTML = `<div class="text-muted text-center py-5">Loading process stdout trace stream...</div>`;
            
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
                btnPrevPage.disabled = currentPage === 1;
                btnNextPage.disabled = data.length < pageLimit;
            }

            // 1. Health Probe Logs
            if (type === "health") {
                tableContainer.classList.remove("d-none");
                terminalContainer.classList.add("d-none");
                ledgerTitle.textContent = "Health Probes Log ledger";
                ledgerBadge.textContent = `${data.length} Records`;
                
                tableHead.innerHTML = `
                    <tr>
                        <th class="ps-4">Timestamp</th>
                        <th>Service Target</th>
                        <th>Severity</th>
                        <th>Latency</th>
                        <th>HTTP Status</th>
                        <th class="pe-4">Remarks / Exceptions</th>
                    </tr>
                `;
                
                tableBody.innerHTML = "";
                if (data.length === 0) {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="6" class="text-center py-5">
                                <div class="empty-state border-0 bg-transparent">
                                    <i data-lucide="terminal" class="empty-state-icon"></i>
                                    <h6 class="empty-state-title">No health logs found</h6>
                                    <p class="empty-state-desc">Try adjustment filters or refresh target nodes.</p>
                                </div>
                            </td>
                        </tr>
                    `;
                    lucide.createIcons();
                    return;
                }
                
                data.forEach(log => {
                    const row = document.createElement("tr");
                    const date = new Date(log.timestamp);
                    const timeStr = date.toLocaleString();
                    
                    let sevClass = "info";
                    if (log.status.toLowerCase() === "healthy") sevClass = "success";
                    if (log.status.toLowerCase() === "warning") sevClass = "warning";
                    if (log.status.toLowerCase() === "critical") sevClass = "error";
                    if (log.status.toLowerCase() === "offline") sevClass = "error";

                    const badgeHtml = `<span class="badge-severity ${sevClass}">${log.status}</span>`;
                    const httpCode = log.http_status ? log.http_status : '-';
                    const remarksText = log.remarks ? log.remarks : '-';
                    
                    row.innerHTML = `
                        <td class="ps-4 font-monospace text-muted">${timeStr}</td>
                        <td class="fw-semibold text-white">${log.service_name}</td>
                        <td>${badgeHtml}</td>
                        <td class="text-info font-monospace">${log.response_time}ms</td>
                        <td class="font-monospace text-secondary fw-bold">${httpCode}</td>
                        <td class="pe-4 text-secondary font-monospace" style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${remarksText}">${remarksText}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 2. Audit Logs
            else if (type === "audit") {
                tableContainer.classList.remove("d-none");
                terminalContainer.classList.add("d-none");
                ledgerTitle.textContent = "Administrative Audit Trail Log";
                ledgerBadge.textContent = `${data.length} Records`;
                
                tableHead.innerHTML = `
                    <tr>
                        <th class="ps-4">Timestamp</th>
                        <th>Operator Identity</th>
                        <th>Action</th>
                        <th>Audit Details</th>
                        <th class="pe-4">IP Coordinates</th>
                    </tr>
                `;
                
                tableBody.innerHTML = "";
                if (data.length === 0) {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center py-5">
                                <div class="empty-state border-0 bg-transparent">
                                    <i data-lucide="user-x" class="empty-state-icon"></i>
                                    <h6 class="empty-state-title">No audit records</h6>
                                    <p class="empty-state-desc">Operator activities will populate here.</p>
                                </div>
                            </td>
                        </tr>
                    `;
                    lucide.createIcons();
                    return;
                }
                
                data.forEach(log => {
                    const row = document.createElement("tr");
                    const date = new Date(log.timestamp);
                    const timeStr = date.toLocaleString();
                    const ip = log.ip_address ? log.ip_address : '-';
                    
                    row.innerHTML = `
                        <td class="ps-4 font-monospace text-muted">${timeStr}</td>
                        <td class="text-primary fw-semibold d-flex align-items-center gap-1.5">
                            <i data-lucide="user" style="width: 14px; height: 14px;"></i>
                            ${log.user_email}
                        </td>
                        <td class="fw-semibold text-white">${log.action}</td>
                        <td class="text-secondary" style="font-size:0.82rem;">${log.details || '-'}</td>
                        <td class="pe-4 font-monospace text-muted">${ip}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
            
            // 3. Live stdout log output file
            else {
                tableContainer.classList.add("d-none");
                terminalContainer.classList.remove("d-none");
                ledgerTitle.textContent = "Process Stdout Stream (application.log)";
                
                const lines = data.logs || [];
                ledgerBadge.textContent = `${lines.length} Lines`;
                
                terminalScreen.innerHTML = "";
                if (lines.length === 0) {
                    terminalScreen.innerHTML = `<div class="text-muted text-center py-5">Empty log output feed.</div>`;
                    return;
                }
                
                lines.forEach(line => {
                    const div = document.createElement("div");
                    div.className = "terminal-line";
                    
                    if (line.includes("[ERROR]") || line.includes("[CRITICAL]")) {
                        div.className += " text-danger fw-bold";
                    } else if (line.includes("[WARNING]")) {
                        div.className += " text-warning";
                    } else {
                        div.className += " text-secondary";
                    }
                    
                    div.textContent = line;
                    terminalScreen.appendChild(div);
                });
                
                terminalScreen.scrollTop = terminalScreen.scrollHeight;
            }

            lucide.createIcons();

        } catch (ex) {
            showNotification(ex.message, "danger");
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger py-4">Error loading logs: ${ex.message}</td></tr>`;
        }
    }

    queryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        currentPage = 1;
        executeQuery();
    });
    
    // Pagination clicks
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

    // Boot
    executeQuery();
});
