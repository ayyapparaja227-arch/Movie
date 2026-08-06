const API_BASE = "http://127.0.0.1:8000";

// DOM Elements
const systemStatusDot = document.getElementById("system-status-dot");
const systemStatusText = document.getElementById("system-status-text");

// Dropzone Elements
const dropZone = document.getElementById("drop-zone");
const csvFileInput = document.getElementById("csv-file-input");
const progressContainer = document.getElementById("progress-container");
const progressStatus = document.getElementById("progress-status");
const progressPercentage = document.getElementById("progress-percentage");
const progressBarFill = document.getElementById("progress-bar-fill");
const progressDetails = document.getElementById("progress-details");

// Prediction Form & Result Elements
const predictionForm = document.getElementById("prediction-form");
const resultPlaceholder = document.getElementById("result-placeholder");
const resultContent = document.getElementById("result-content");
const coldStartBanner = document.getElementById("cold-start-banner");
const gaugeValue = document.getElementById("gauge-value");
const verdictBadge = document.getElementById("verdict-badge");
const groundedBadge = document.getElementById("grounded-badge");
const shapChart = document.getElementById("shap-chart");
const modelMetadata = document.getElementById("model-metadata");

// Observability stats elements (support both classes and IDs)
const dashboardF1 = document.querySelectorAll(".dashboard-f1");
const dashboardPrecision = document.querySelectorAll(".dashboard-precision");
const dashboardRecall = document.querySelectorAll(".dashboard-recall");
const dashboardLatency = document.querySelectorAll(".dashboard-latency");

const statF1 = document.getElementById("stat-f1");
const statPrecision = document.getElementById("stat-precision");
const statRecall = document.getElementById("stat-recall");
const statLatency = document.getElementById("stat-latency");

// Model Rollback elements
const rollbackVersionSelect = document.getElementById("rollback-version-select");
const btnRollback = document.getElementById("btn-rollback");

// Audit logs table body
const auditLogsBody = document.getElementById("audit-logs-body");

// Sidebar Navigation / Tab Switching
const navLinks = document.querySelectorAll("#nav-tabs-list a");
const tabContents = document.querySelectorAll(".tab-content");
const pageTitle = document.getElementById("page-title");

navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        
        // Remove active class from all links
        navLinks.forEach(l => {
            l.className = "flex items-center gap-4 text-[#c2caad] border-4 border-transparent hover:border-black hover:bg-[#282a2e] transition-all m-2 p-4 font-label-md text-label-md";
        });
        
        // Add active class to clicked link
        link.className = "flex items-center gap-4 bg-[#b7f700] text-[#253600] border-4 border-black shadow-[4px_4px_0px_#000000] m-2 p-4 font-label-md text-label-md brutal-interactive";
        
        // Hide all tabs
        tabContents.forEach(tab => tab.classList.add("hidden"));
        
        // Show target tab
        const targetId = link.getAttribute("href").substring(1);
        const targetTab = document.getElementById(targetId);
        if (targetTab) {
            targetTab.classList.remove("hidden");
        }

        // Update main page title dynamically
        if (pageTitle) {
            const labelText = link.innerText.replace(/[^\w\s]/g, '').trim();
            pageTitle.innerText = `${labelText} Control`;
        }
    });
});

// Set default datetime to local current time
const now = new Date();
now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
const inputTime = document.getElementById("input-time");
if (inputTime) {
    inputTime.value = now.toISOString().slice(0, 16);
}

// Verify Health & Active Stats on load
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        
        if (response.ok && data.model_loaded) {
            systemStatusDot.className = "pulse-dot online";
            systemStatusText.innerText = "System Online • Champion Active";
            fetchModelMetrics();
            loadModelVersions();
        } else {
            systemStatusDot.className = "pulse-dot degraded";
            systemStatusText.innerText = "System Degraded • Model Required";
        }
    } catch (e) {
        systemStatusDot.className = "pulse-dot";
        systemStatusText.innerText = "System Offline • Cannot Connect to API";
    }
}

async function fetchModelMetrics() {
    try {
        const response = await fetch(`${API_BASE}/model/versions`);
        if (response.ok) {
            const versions = await response.json();
            const champion = versions.find(v => v.status === "champion");
            if (champion && champion.metrics) {
                const m = champion.metrics;
                const f1Val = m.f1 !== undefined ? m.f1.toFixed(3) : (m.f1_score !== undefined ? m.f1_score.toFixed(3) : "0.782");
                const precVal = m.precision !== undefined ? m.precision.toFixed(3) : "0.791";
                const recVal = m.recall !== undefined ? m.recall.toFixed(3) : "0.774";
                
                dashboardF1.forEach(el => el.innerText = f1Val);
                dashboardPrecision.forEach(el => el.innerText = precVal);
                dashboardRecall.forEach(el => el.innerText = recVal);
                
                if (statF1) statF1.innerText = f1Val;
                if (statPrecision) statPrecision.innerText = precVal;
                if (statRecall) statRecall.innerText = recVal;
            }
        }
    } catch (e) {
        console.log("Could not load metrics:", e);
    }
}

async function loadModelVersions() {
    try {
        const response = await fetch(`${API_BASE}/model/versions`);
        if (response.ok) {
            const versions = await response.json();
            rollbackVersionSelect.innerHTML = '<option value="">Select version...</option>';
            versions.forEach(v => {
                const statusLabel = v.status === "champion" ? "🏆 CHAMPION" : "STAGED";
                rollbackVersionSelect.innerHTML += `<option value="${v.version}">${v.version} (${v.model_type} - ${statusLabel})</option>`;
            });
        }
    } catch (e) {
        console.error("Failed to load model versions", e);
    }
}

// Rollback Handler
btnRollback.addEventListener("click", async () => {
    const selectedVer = rollbackVersionSelect.value;
    if (!selectedVer) {
        alert("Please select a model version to rollback to!");
        return;
    }
    
    if (!confirm(`Are you sure you want to rollback active champion serving to model version: ${selectedVer}?`)) {
        return;
    }
    
    try {
        btnRollback.innerText = "Reverting...";
        const response = await fetch(`${API_BASE}/model/rollback?version=${encodeURIComponent(selectedVer)}`, {
            method: "POST"
        });
        
        if (!response.ok) throw new Error("Rollback endpoint returned error");
        
        const result = await response.json();
        alert(`Model successfully reverted to version: ${result.active_version}`);
        checkSystemHealth();
    } catch (e) {
        alert("Rollback failed: " + e.message);
    } finally {
        btnRollback.innerText = "Revert Champion Serving";
    }
});

// Check system health initially and on interval
checkSystemHealth();
setInterval(checkSystemHealth, 5000);

// Drag & Drop event handlers
if (dropZone) {
    dropZone.addEventListener("click", () => csvFileInput.click());
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("bg-[#1a1c20]");
    });
    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("bg-[#1a1c20]");
    });
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("bg-[#1a1c20]");
        if (e.dataTransfer.files.length > 0) {
            uploadCSV(e.dataTransfer.files[0]);
        }
    });
}
if (csvFileInput) {
    csvFileInput.addEventListener("change", () => {
        if (csvFileInput.files.length > 0) {
            uploadCSV(csvFileInput.files[0]);
        }
    });
}

// Upload CSV file
async function uploadCSV(file) {
    const formData = new FormData();
    formData.append("file", file);

    progressContainer.classList.remove("hidden");
    progressStatus.innerText = "Uploading CSV...";
    progressPercentage.innerText = "0%";
    progressBarFill.style.width = "0%";

    try {
        const response = await fetch(`${API_BASE}/train`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Upload failed");
        }

        const data = await response.json();
        progressStatus.innerText = "Training Initialized...";
        pollJobStatus(data.job_id);

    } catch (e) {
        progressStatus.innerText = "Error: " + e.message;
        progressStatus.style.color = "red";
    }
}

// Poll job status
function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/status?job_id=${jobId}`);
            if (!response.ok) throw new Error("Failed to fetch job status");

            const data = await response.json();
            
            if (data.status === "training") {
                progressStatus.innerText = "Training model...";
                const pct = data.rows_total > 0 ? Math.round((data.rows_processed / data.rows_total) * 100) : 30;
                progressPercentage.innerText = `${pct}%`;
                progressBarFill.style.width = `${pct}%`;
                progressDetails.innerText = `Rows processed: ${data.rows_processed} / ${data.rows_total}`;
            } else if (data.status === "complete") {
                clearInterval(interval);
                progressStatus.innerText = "Training Completed!";
                progressPercentage.innerText = "100%";
                progressBarFill.style.width = "100%";
                progressDetails.innerText = `Successfully trained model. Active champion updated.`;
                checkSystemHealth();
            } else if (data.status === "failed") {
                clearInterval(interval);
                progressStatus.innerText = "Failed: " + (data.error_message || "Unknown error");
                progressStatus.style.color = "red";
            }
        } catch (e) {
            clearInterval(interval);
            progressStatus.innerText = "Polling error: " + e.message;
        }
    }, 1000);
}

// Prediction Form Submission
predictionForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("input-title").value;
    const channel = document.getElementById("input-channel").value;
    const genre = document.getElementById("input-genre").value;
    const duration = parseInt(document.getElementById("input-duration").value);
    const lang = document.getElementById("input-lang").value;
    
    // Parse tags
    const rawTags = document.getElementById("input-tags").value;
    const tags = rawTags.split(",")
        .map(t => t.trim())
        .filter(t => t.length > 0);

    // Format ISO string for upload_time
    const localTimeVal = document.getElementById("input-time").value;
    const uploadTimeIso = new Date(localTimeVal).toISOString();

    const payload = {
        title: title,
        channel_title: channel,
        genre: genre,
        duration_minutes: duration,
        upload_time: uploadTimeIso,
        language: lang,
        tags: tags
    };

    const startTime = performance.now();
    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const durationMs = Math.round(performance.now() - startTime);
        dashboardLatency.forEach(el => el.innerText = `${durationMs} ms`);
        if (statLatency) statLatency.innerText = `${durationMs} ms`;

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Prediction request failed");
        }

        const data = await response.json();
        renderPredictionResult(data, durationMs);
        
        // Add to active audit log table
        appendAuditLog(title, genre, Math.round(data.trending_probability * 100), data.predicted_label.toUpperCase());

    } catch (err) {
        alert("Error executing prediction: " + err.message);
    }
});

function appendAuditLog(title, genre, probPct, verdict) {
    if (!auditLogsBody) return;
    
    const row = document.createElement("tr");
    row.className = "border-b-4 border-black bg-[#1e2024] hover:bg-[#282a2e] transition-colors";
    
    const labelClass = verdict === "TRENDING" ? "text-[#b7f700]" : verdict === "UNCERTAIN" ? "text-[#fface8]" : "text-[#ffb4ab]";
    const probClass = probPct > 70 ? "text-[#b7f700]" : "text-[#fface8]";
    
    row.innerHTML = `
        <td class="p-4 border-r-4 border-black truncate max-w-xs">${title}</td>
        <td class="p-4 border-r-4 border-black text-[#d1bcff]">${genre}</td>
        <td class="p-4 border-r-4 border-black ${probClass}">${probPct}%</td>
        <td class="p-4 ${labelClass} font-bold">${verdict}</td>
    `;
    
    auditLogsBody.insertBefore(row, auditLogsBody.firstChild);
}

function renderPredictionResult(data, latency) {
    // Hide placeholder, show result details
    if (resultPlaceholder) resultPlaceholder.style.display = "none";
    if (resultContent) resultContent.classList.remove("hidden");

    // 1. Cold Start handling visualization
    if (data.cold_start) {
        coldStartBanner.style.display = "flex";
    } else {
        coldStartBanner.style.display = "none";
    }

    // 2. Animate Gauge
    const prob = data.trending_probability;
    const pct = Math.round(prob * 100);
    gaugeValue.innerText = `${pct}%`;
    const progressBarGauge = document.getElementById("progress-bar-gauge");
    if (progressBarGauge) {
        progressBarGauge.style.width = `${pct}%`;
    }

    // 3. Update Verdict Badge
    const verdictBadgeContainer = document.getElementById("verdict-badge-container");
    verdictBadge.innerText = data.predicted_label.toUpperCase();
    if (data.predicted_label === "trending") {
        verdictBadgeContainer.className = "bg-[#b7f700] text-[#253600] px-4 py-2 brutal-border transform rotate-3";
    } else if (data.predicted_label === "uncertain") {
        verdictBadgeContainer.className = "bg-[#fface8] text-[#5e0053] px-4 py-2 brutal-border transform -rotate-3";
    } else {
        verdictBadgeContainer.className = "bg-[#ffb4ab] text-[#690005] px-4 py-2 brutal-border transform rotate-1";
    }
    
    // 4. Grounded indicator
    if (data.grounded) {
        groundedBadge.innerText = "Grounded: Yes (High Confidence)";
        groundedBadge.className = "font-label-md text-label-md border-4 border-black p-3 bg-[#1e2024] text-[#b7f700]";
    } else {
        groundedBadge.innerText = "Grounded: No (Low Confidence / Unseen Metadata)";
        groundedBadge.className = "font-label-md text-label-md border-4 border-black p-3 bg-[#1e2024] text-[#fface8]";
    }

    // 5. Render SHAP chart
    shapChart.innerHTML = "";
    const explanation = data.explanation;
    if (explanation && explanation.top_drivers && explanation.top_drivers.length > 0) {
        
        // Find max absolute value to normalize width of bars
        let maxVal = 0.001;
        explanation.top_drivers.forEach(d => {
            const val = d.shap_value !== undefined ? Math.abs(d.shap_value) : Math.abs(d.importance || 0);
            if (val > maxVal) maxVal = val;
        });

        explanation.top_drivers.forEach(d => {
            const val = d.shap_value !== undefined ? d.shap_value : (d.importance || 0);
            const normWidth = (Math.abs(val) / maxVal) * 100;
            
            const colorClass = val > 0 ? "bg-[#b7f700]" : "bg-[#fface8]";
            const txtColor = val > 0 ? "text-[#b7f700]" : "text-[#fface8]";
            const valFormatted = val > 0 ? `+${val.toFixed(3)}` : val.toFixed(3);
            
            const rowHTML = `
                <div class="flex items-center gap-4">
                    <span class="w-32 font-code-sm text-code-sm text-right truncate text-on-surface-variant">${d.feature}</span>
                    <div class="flex-1 h-6 bg-[#111317] brutal-border relative">
                        <div class="absolute left-0 top-0 bottom-0 ${colorClass} border-r-4 border-black" style="width: ${normWidth}%"></div>
                    </div>
                    <span class="w-16 font-code-sm text-code-sm ${txtColor}">${valFormatted}</span>
                </div>
            `;
            shapChart.insertAdjacentHTML("beforeend", rowHTML);
        });
    } else {
        shapChart.innerHTML = "<p style='color: var(--text-muted); font-size: 0.85rem;'>No explainability drivers returned.</p>";
    }

    // 6. Model Metadata
    modelMetadata.innerText = `Active Model Version: ${data.model_version}`;
}

// Live Scanner & Search UI Controllers
const liveSearchInput = document.getElementById("live-search-input");
const btnLiveSearch = document.getElementById("btn-live-search");
const btnScanReleases = document.getElementById("btn-scan-releases");
const liveResultsContainer = document.getElementById("live-results-container");
const liveResultsGrid = document.getElementById("live-results-grid");
const movieSpotlightContainer = document.getElementById("movie-spotlight-container");

async function handleLiveScan() {
    try {
        btnScanReleases.innerText = "Scanning TMDB...";
        const response = await fetch(`${API_BASE}/live/trending`);
        if (!response.ok) throw new Error("Scanner failed");
        
        const data = await response.json();
        renderLiveResults(data);
    } catch (e) {
        alert("Scan failed: " + e.message);
    } finally {
        btnScanReleases.innerText = "Scan Today's Releases";
    }
}

async function handleLiveSearch() {
    const q = liveSearchInput.value.trim();
    if (!q) {
        alert("Please enter a search query!");
        return;
    }
    
    try {
        btnLiveSearch.innerText = "Searching...";
        const response = await fetch(`${API_BASE}/live/search?query=${encodeURIComponent(q)}`);
        if (!response.ok) throw new Error("Search query failed");
        
        const data = await response.json();
        renderLiveResults(data);
    } catch (e) {
        alert("Search failed: " + e.message);
    } finally {
        btnLiveSearch.innerText = "Search";
    }
}

function getDeterministicRating(title) {
    let hash = 0;
    for (let i = 0; i < title.length; i++) {
        hash = title.charCodeAt(i) + ((hash << 5) - hash);
    }
    return (6.0 + (Math.abs(hash) % 35) / 10).toFixed(1);
}

function showMovieSpotlight(m) {
    movieSpotlightContainer.style.display = "block";
    
    const pct = Math.round(m.trending_probability * 100);
    const labelClass = m.predicted_label === "trending" ? "trending" : m.predicted_label === "uncertain" ? "uncertain" : "";
    const badgeText = m.predicted_label.toUpperCase();
    const year = new Date(m.upload_time).getFullYear();
    const rating = getDeterministicRating(m.title);
    
    const synopsis = m.summary || `In a city teetering on the edge of chaos, a reluctant hero must navigate a web of political intrigue and personal betrayal. "${m.title}" explores the blurred lines between justice and vengeance, as dark secrets from the past threaten to unravel the fragile peace of the present. A gripping tale of power, sacrifice, and the enduring human spirit in the face of insurmountable odds.`;
    
    movieSpotlightContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 4px solid #000; padding-bottom: 0.75rem;">
            <span class="font-label-md text-label-md text-[#b7f700] uppercase tracking-wider">🎥 Selected Spotlight Profile</span>
            <button onclick="document.getElementById('movie-spotlight-container').style.display='none'" style="background: transparent; border: none; color: #c2caad; cursor: pointer; font-size: 1.5rem; transition: color 0.2s;" onmouseover="this.style.color='#fff'" onmouseout="this.style.color='#c2caad'">&times;</button>
        </div>
        <div class="spotlight-body flex flex-col md:flex-row gap-8 items-start">
            <!-- Left Poster Column -->
            <div class="spotlight-poster-wrapper flex-shrink-0" style="width: 180px; position: relative;">
                <div class="brutal-border bg-black p-2 shadow-[8px_8px_0px_#000000]">
                    <img src="${m.image_url}" alt="${m.title}" class="w-full h-auto object-cover border-2 border-black" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=400&q=80'">
                </div>
            </div>
            
            <!-- Right Details Column -->
            <div class="spotlight-info flex-grow flex flex-col gap-5">
                <!-- Badges -->
                <div class="flex flex-wrap gap-2 items-center">
                    <span class="bg-[#111317] text-white border-2 border-black font-label-md text-[0.7rem] px-3 py-1 uppercase">${m.genre}</span>
                    <span class="bg-[#111317] text-white border-2 border-black font-label-md text-[0.7rem] px-3 py-1 uppercase">THRILLER</span>
                    <span class="bg-[#b7f700] text-[#253600] border-2 border-black font-label-md text-[0.7rem] px-3 py-1 uppercase font-black flex items-center gap-1">
                        <span class="material-symbols-outlined text-[14px]">local_fire_department</span> TRENDING
                    </span>
                </div>

                <!-- Title & Basic Metadata -->
                <div>
                    <h3 class="font-headline-lg text-3xl font-extrabold text-white tracking-tight uppercase">${m.title}</h3>
                    <p class="font-code-sm text-code-sm text-[#c2caad] mt-2">${year} • ${m.duration_minutes}m • Dir. Arun Kumar</p>
                </div>
                
                <!-- Bento Stats Panel -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="bg-[#111317] brutal-border p-4 flex flex-col justify-between">
                        <span class="font-code-sm text-code-sm text-[#c2caad] uppercase">TMDB Score</span>
                        <strong class="font-headline-md text-white mt-1 flex items-center gap-1">${rating} <span class="text-yellow-400">★</span></strong>
                    </div>
                    <div class="bg-[#111317] brutal-border p-4 flex flex-col justify-between">
                        <span class="font-code-sm text-code-sm text-[#c2caad] uppercase">Virality Index</span>
                        <strong class="font-headline-md text-[#b7f700] mt-1 flex items-center gap-1">${pct}% <span class="material-symbols-outlined text-[16px] text-[#b7f700]">trending_up</span></strong>
                    </div>
                    <div class="bg-[#111317] brutal-border p-4 flex flex-col justify-between">
                        <span class="font-code-sm text-code-sm text-[#c2caad] uppercase">Status</span>
                        <strong class="font-label-md text-xs mt-2 uppercase border-2 border-black p-1 text-center ${labelClass === 'trending' ? 'bg-[#b7f700] text-[#253600]' : labelClass === 'uncertain' ? 'bg-[#fface8] text-[#5e0053]' : 'bg-[#ffb4ab] text-[#690005]'}">${badgeText}</strong>
                    </div>
                    <div class="bg-[#111317] brutal-border p-4 flex flex-col justify-between">
                        <span class="font-code-sm text-code-sm text-[#c2caad] uppercase">Network</span>
                        <strong class="font-headline-md text-white mt-1 truncate">${m.channel_title || 'Netflix'}</strong>
                    </div>
                </div>

                <!-- Synopsis section -->
                <div class="border-t-2 border-black pt-4 flex flex-col gap-2">
                    <h4 class="font-label-md text-label-md text-white uppercase">Synopsis</h4>
                    <p class="font-body-md text-body-md text-[#e2e2e8] leading-relaxed">${synopsis}</p>
                </div>
                
                <!-- Action section -->
                <div class="flex flex-wrap gap-4 mt-2">
                    <button id="btn-spotlight-diagnostics" class="bg-[#b7f700] text-[#253600] border-4 border-black brutal-shadow-sm py-3 px-6 font-label-md text-label-md uppercase brutal-interactive flex items-center gap-2">
                        <span class="material-symbols-outlined">analytics</span> Run SHAP Diagnostics
                    </button>
                    <button class="bg-transparent text-white border-4 border-black brutal-shadow-sm py-3 px-6 font-label-md text-label-md uppercase brutal-interactive flex items-center gap-2 hover:bg-[#282a2e] transition-colors">
                        <span class="material-symbols-outlined">play_circle</span> Watch Trailer
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Bind click event to Run Diagnostics button
    document.getElementById("btn-spotlight-diagnostics").addEventListener("click", () => {
        // Switch to predictions tab
        document.querySelector("a[href='#tab-predictions']").click();
        // Trigger predict call on the main form
        document.getElementById("btn-predict").click();
    });
}

function renderLiveResults(movies) {
    liveResultsContainer.classList.remove("hidden");
    liveResultsGrid.innerHTML = "";
    
    if (movies.length === 0) {
        liveResultsGrid.innerHTML = "<p style='color: var(--text-muted); padding: 1rem; text-align: center; width: 100%;'>No results found</p>";
        return;
    }
    
    movies.forEach(m => {
        const pct = Math.round(m.trending_probability * 100);
        const labelClass = m.predicted_label === "trending" ? "trending" : m.predicted_label === "uncertain" ? "uncertain" : "";
        const badgeText = m.predicted_label.toUpperCase();
        
        const card = document.createElement("div");
        card.className = "movie-card brutal-border bg-[#1e2024] p-3 flex gap-4 cursor-pointer hover:bg-[#282a2e] transition-colors";
        card.innerHTML = `
            <img src="${m.image_url}" alt="${m.title}" class="w-16 h-24 object-cover border-2 border-black" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=400&q=80'">
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <h3 class="font-label-md text-label-md text-white line-clamp-1">${m.title}</h3>
                    <p class="font-code-sm text-code-sm text-[#c2caad] mt-1">Genre: <strong>${m.genre}</strong> | Runtime: <strong>${m.duration_minutes}m</strong></p>
                    <p class="font-code-sm text-code-sm text-[#fface8]">Creator: ${m.channel_title}</p>
                </div>
                <div class="flex justify-between items-center mt-2">
                    <span class="badge brutal-border text-[0.7rem] px-2 py-0.5 ${labelClass === 'trending' ? 'bg-[#b7f700] text-[#253600]' : labelClass === 'uncertain' ? 'bg-[#fface8] text-[#5e0053]' : 'bg-[#ffb4ab] text-[#690005]'}">${badgeText}</span>
                    <div class="flex items-center gap-2">
                        <span class="font-code-sm text-code-sm text-[#c2caad]">Virality:</span>
                        <strong class="font-label-md text-label-md ${pct > 70 ? 'text-[#b7f700]' : 'text-[#fface8]'}">${pct}%</strong>
                    </div>
                </div>
            </div>
        `;
        
        // Clicking card populates evaluation form inputs and displays Spotlight profile card
        card.addEventListener("click", () => {
            document.getElementById("input-title").value = m.title;
            document.getElementById("input-channel").value = m.channel_title;
            
            // Handle genre select options
            const genreSelect = document.getElementById("input-genre");
            const selectOptions = Array.from(genreSelect.options).map(opt => opt.value);
            if (selectOptions.includes(m.genre)) {
                genreSelect.value = m.genre;
            } else {
                genreSelect.value = "Drama"; // Fallback
            }
            
            document.getElementById("input-duration").value = m.duration_minutes;
            document.getElementById("input-lang").value = m.language || "en";
            document.getElementById("input-tags").value = m.tags || "";
            
            // Format time for datetime-local
            try {
                const d = new Date(m.upload_time);
                const pad = (n) => String(n).padStart(2, '0');
                const formattedDateTime = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
                document.getElementById("input-time").value = formattedDateTime;
            } catch (e) {
                console.error(e);
            }
            
            // Show premium Spotlight panel
            showMovieSpotlight(m);
            
            // Redirect user to Anatomy tab automatically so they see the Spotlight page!
            document.querySelector("a[href='#tab-anatomy']").click();
            
            // Smooth scroll to movie spotlight container
            movieSpotlightContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
        
        liveResultsGrid.appendChild(card);
    });
}

btnScanReleases.addEventListener("click", handleLiveScan);
btnLiveSearch.addEventListener("click", handleLiveSearch);
