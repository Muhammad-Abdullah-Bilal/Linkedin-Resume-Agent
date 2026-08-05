// Application Session State
const AppState = {
    jobs: [],
    selectedJobId: null,
    currentPreviewDoc: "cv", // "cv" or "letter"
    currentTemplate: "modern",
    zoomPercent: 100
};

// Start initialization
document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initTemplateSelector();
    initZoomControls();
    initFileUpload();
    initChatListener();
    loadJobs();
});

// 1. Navigation Menu Router
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(item => {
        if (item.getAttribute("data-tab") === tabId) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    document.querySelectorAll(".tab-panel").forEach(panel => {
        if (panel.id === `tab-${tabId}`) {
            panel.classList.add("active");
        } else {
            panel.classList.remove("active");
        }
    });

    const titleMap = {
        dashboard: { title: "Dashboard", sub: "Tailoring stats and recommended job alignments" },
        jobs: { title: "Job Search", sub: "Explore scraped LinkedIn job openings" },
        upload: { title: "Upload Resume", sub: "Verify candidate profile text details" },
        analysis: { title: "ATS Match Scorecard", sub: "Cross-reference target skills and compatibility" },
        preview: { title: "Live Preview", sub: "Render tailored drafts in real-time" },
        downloads: { title: "Download Center", sub: "Export packages as recruiter-ready PDF/DOCX" }
    };

    if (titleMap[tabId]) {
        document.getElementById("page-title").textContent = titleMap[tabId].title;
        document.getElementById("page-subtitle").textContent = titleMap[tabId].sub;
    }
}

// 2. Load scraped jobs
async function loadJobs() {
    try {
        const res = await fetch("/api/jobs");
        const jobs = await res.json();
        AppState.jobs = jobs;
        
        populateDashboardJobs(jobs);
        populateSearchList(jobs);
    } catch (e) {
        console.error("Failed to load jobs list:", e);
    }
}

function populateDashboardJobs(jobs) {
    const list = document.getElementById("dashboard-job-list");
    list.innerHTML = "";
    
    jobs.slice(0, 3).forEach(job => {
        const div = document.createElement("div");
        div.className = "job-card-compact";
        div.onclick = () => {
            switchTab("jobs");
            selectJob(job.job_id);
        };
        
        div.innerHTML = `
            <div>
                <strong style="color:var(--text-primary); font-size:14px;">${job.title}</strong>
                <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">${job.company} &bull; ${job.location}</div>
            </div>
            <span class="badge badge-info">Evaluation Available</span>
        `;
        list.appendChild(div);
    });
}

function populateSearchList(jobs) {
    const list = document.getElementById("job-search-list");
    list.innerHTML = "";
    
    jobs.forEach(job => {
        const div = document.createElement("div");
        div.className = "job-card-compact";
        div.id = `job-search-card-${job.job_id}`;
        div.onclick = () => selectJob(job.job_id);
        
        div.innerHTML = `
            <div>
                <strong>${job.title}</strong>
                <div style="font-size:11.5px; color:var(--text-secondary); margin-top:2px;">${job.company}</div>
            </div>
            <i class="fa-solid fa-chevron-right" style="font-size:12px; color:var(--text-secondary);"></i>
        `;
        list.appendChild(div);
    });
}

// 3. Select Job Detail view
async function selectJob(jobId) {
    AppState.selectedJobId = jobId;
    
    document.querySelectorAll(".job-card-compact").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`job-search-card-${jobId}`);
    if (activeCard) activeCard.classList.add("active");
    
    const job = AppState.jobs.find(j => j.job_id === jobId);
    if (!job) return;
    
    const badge = document.getElementById("active-job-badge");
    badge.style.display = "flex";
    document.getElementById("active-job-text").textContent = `Active Job: ${job.company}`;

    const pane = document.getElementById("job-details-pane");
    pane.innerHTML = `
        <div class="job-details-pane-content">
            <div>
                <h2 style="font-family:'Outfit',sans-serif; font-size:22px; margin-bottom:5px;">${job.title}</h2>
                <h3 style="font-size:15px; color:var(--accent); font-weight:500; margin-bottom:15px;">${job.company} &bull; ${job.location}</h3>
                
                <div style="border-top: 1px solid var(--border-color); padding-top:15px; overflow-y:auto; max-height:320px; font-size:12.5px; line-height:1.6; text-align:justify; padding-right:5px;">
                    <strong>Description:</strong><br>
                    ${job.description.replace(/\n/g, "<br>")}
                </div>
            </div>
            
            <div style="margin-top:20px; display:flex; gap:12px;">
                <button class="btn btn-primary" onclick="triggerAnalyze(${jobId})">
                    <i class="fa-solid fa-gauge-high"></i> Run ATS Audit
                </button>
                <a href="${job.url}" target="_blank" class="btn btn-outline">
                    <i class="fa-solid fa-external-link"></i> View on LinkedIn
                </a>
            </div>
        </div>
    `;
}

// 4. Run ATS analysis
async function triggerAnalyze(jobId) {
    switchTab("analysis");
    const container = document.getElementById("analysis-container");
    container.innerHTML = `
        <div style="grid-column: span 2; text-align:center; padding: 50px 0;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:40px; color:var(--accent); margin-bottom:15px;"></i>
            <h3>Analyzing Job Profile compatibility...</h3>
        </div>
    `;
    
    try {
        const res = await fetch(`/api/analyze?job_id=${jobId}`);
        const data = await res.json();
        renderAnalysis(data);
    } catch (e) {
        console.error("ATS audit execution failed:", e);
    }
}

function renderAnalysis(data) {
    const container = document.getElementById("analysis-container");
    container.innerHTML = `
        <div class="score-circle-wrapper">
            <div class="score-circle">
                <span class="number">${data.analysis.ats_score}%</span>
                <span class="label">ATS Match Score</span>
            </div>
            <div style="text-align:center; margin-top:20px;">
                <strong>Skill Match Rate: ${data.analysis.skill_match}%</strong>
                <p style="font-size:11.5px; color:var(--text-secondary); margin-top:4px;">Cross-referenced against target skills.</p>
            </div>
        </div>
        
        <div class="analysis-details-card">
            <h3 style="font-family:'Outfit'; font-size:18px; margin-bottom:15px; border-bottom:1px solid var(--border-color); padding-bottom:8px;">ATS Match Audit Insights</h3>
            
            <strong style="color:var(--success); font-size:13.5px;"><i class="fa-solid fa-circle-check"></i> Profile Strengths:</strong>
            <ul style="margin:5px 0 15px 18px; line-height:1.5; font-size:12.5px;">
                ${data.analysis.strengths.map(s => `<li>${s}</li>`).join("")}
            </ul>
            
            <strong style="color:var(--warning); font-size:13.5px;"><i class="fa-solid fa-triangle-exclamation"></i> Suggested Keywords:</strong>
            <ul style="margin:5px 0 15px 18px; line-height:1.5; font-size:12.5px;">
                ${data.analysis.improvements.map(i => `<li>${i}</li>`).join("")}
            </ul>
            
            <strong style="color:var(--info); font-size:13.5px;"><i class="fa-solid fa-lightbulb"></i> Keyword Analysis:</strong>
            <div style="margin-top:8px; display:flex; gap:10px; flex-wrap:wrap;">
                ${data.analysis.matching_skills.map(s => `<span class="badge badge-success">${s}</span>`).join("")}
                ${data.analysis.missing_skills.map(s => `<span class="badge badge-warning">${s} (Missing)</span>`).join("")}
            </div>
            
            <div style="margin-top:30px;">
                <button class="btn btn-primary" onclick="switchTab('preview')">
                    <i class="fa-solid fa-arrow-right"></i> Open AI Tailor Studio
                </button>
            </div>
        </div>
    `;
}

// 5. AI Tailoring CV / Cover Letter
async function triggerTailoring() {
    if (AppState.selectedJobId === null) {
        alert("Please select a target job opening from Job Search tab first.");
        return;
    }
    
    const btn = document.getElementById("btn-tailor-cv");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Tailoring CV...`;
    
    try {
        const res = await fetch(`/api/tailor?job_id=${AppState.selectedJobId}`);
        const data = await res.json();
        
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> AI Tailored!`;
        
        reloadPreviewFrame();
    } catch (e) {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> AI Tailor CV`;
        console.error("AI tailoring failed:", e);
    }
}

// 6. Template Selector Cards
function initTemplateSelector() {
    const cards = document.querySelectorAll(".template-card");
    cards.forEach(card => {
        card.addEventListener("click", () => {
            cards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            
            AppState.currentTemplate = card.getAttribute("data-template");
            reloadPreviewFrame();
        });
    });
}

function reloadPreviewFrame() {
    const iframe = document.getElementById("preview-frame");
    if (AppState.currentPreviewDoc === "cv") {
        iframe.src = `/api/preview?template=${AppState.currentTemplate}&t=${new Date().getTime()}`;
    } else {
        iframe.src = `/api/cover-letter?t=${new Date().getTime()}`;
    }
}

function switchPreviewDoc(docType) {
    AppState.currentPreviewDoc = docType;
    document.querySelectorAll(".preview-tab").forEach(tab => {
        if (tab.textContent.toLowerCase().includes(docType)) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }
    });
    reloadPreviewFrame();
}

// 7. Interactive File Uploading
function initFileUpload() {
    const input = document.getElementById("cv-file-input");
    const status = document.getElementById("upload-status");
    
    if (!input) return;
    
    input.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        if (file.type !== "application/pdf") {
            status.style.color = "var(--warning)";
            status.textContent = "Error: Only PDF resumes are supported.";
            return;
        }
        
        status.style.color = "var(--text-secondary)";
        status.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading ${file.name}...`;
        
        try {
            const buffer = await file.arrayBuffer();
            const res = await fetch("/api/upload", {
                method: "POST",
                headers: { "Content-Type": "application/pdf" },
                body: buffer
            });
            
            const data = await res.json();
            if (res.ok) {
                status.style.color = "var(--success)";
                status.innerHTML = `<i class="fa-solid fa-circle-check"></i> ${file.name} uploaded successfully!`;
                
                // Update Dashboard resume badge
                const resumeStatus = document.getElementById("stats-resume-status");
                if (resumeStatus) {
                    resumeStatus.textContent = "Custom CV Active";
                }
            } else {
                status.style.color = "var(--warning)";
                status.textContent = `Upload failed: ${data.error}`;
            }
        } catch (err) {
            status.style.color = "var(--warning)";
            status.textContent = `Connection error: ${err}`;
        }
    });
}

// 8. Zoom controls
function initZoomControls() {
    const zoomIn = document.getElementById("zoom-in");
    const zoomOut = document.getElementById("zoom-out");
    const percent = document.getElementById("zoom-percent");
    const iframe = document.getElementById("preview-frame");
    
    zoomIn.addEventListener("click", () => {
        if (AppState.zoomPercent < 150) {
            AppState.zoomPercent += 10;
            percent.textContent = `${AppState.zoomPercent}%`;
            iframe.style.transform = `scale(${AppState.zoomPercent / 100})`;
        }
    });
    
    zoomOut.addEventListener("click", () => {
        if (AppState.zoomPercent > 50) {
            AppState.zoomPercent -= 10;
            percent.textContent = `${AppState.zoomPercent}%`;
            iframe.style.transform = `scale(${AppState.zoomPercent / 100})`;
        }
    });
}

function printPreviewFrame() {
    const iframe = document.getElementById("preview-frame");
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
}

function handleFileDownload(type) {
    if (AppState.selectedJobId === null) {
        alert("Please select and tailor a resume package first.");
        return;
    }
    window.location.href = `/api/download?job_id=${AppState.selectedJobId}&type=${type}`;
}

// 9. AI Career Agent Chat Handlers
function initChatListener() {
    const input = document.getElementById("chat-input-field");
    if (!input) return;
    
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

async function sendChatMessage() {
    const input = document.getElementById("chat-input-field");
    const container = document.getElementById("chat-messages-container");
    const userText = input.value.strip ? input.value.strip() : input.value.trim();
    
    if (!userText) return;
    
    // 1. Render User Message
    renderMessageBubble(userText, "user");
    input.value = "";
    
    // Auto-scroll
    container.scrollTop = container.scrollHeight;
    
    // 2. Render Typing Placeholder
    const typingId = "typing-" + new Date().getTime();
    renderMessageBubble(`<i class="fa-solid fa-ellipsis fa-bounce"></i> Thinking...`, "agent", typingId);
    container.scrollTop = container.scrollHeight;
    
    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userText })
        });
        
        const data = await res.json();
        
        // Remove typing placeholder
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        
        if (res.ok) {
            // Render Agent Response
            renderMessageBubble(data.response || "", "agent");
            
            // Reload Jobs list if updated by scraper
            if (data.jobs_updated) {
                console.log("Scraped job database updated. Reloading dashboard jobs list...");
                await loadJobs();
            }
        } else {
            renderMessageBubble(`Sorry, I couldn't process that: ${data.error}`, "agent");
        }
    } catch (err) {
        const typingEl = document.getElementById(typingId);
        if (typingEl) typingEl.remove();
        renderMessageBubble(`Connection error: ${err}`, "agent");
    }
    
    container.scrollTop = container.scrollHeight;
}

function markdownToHtml(text) {
    if (!text) return "";
    
    // 1. Convert any literal HTML break tags to newlines first
    let cleaned = text.replace(/<br\s*\/?>/gi, "\n");
    
    // 2. Escape HTML tags to prevent layout breaks
    let html = cleaned
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // 3. Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // 4. Italic: *text*
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    
    // 5. Parse lines sequentially to extract tables and lists
    let lines = html.split('\n');
    let parsedLines = [];
    let inTable = false;
    let tableRows = [];
    
    function flushTable() {
        if (tableRows.length >= 2) {
            let parsedRows = tableRows.map(r => {
                let s = r.trim();
                if (s.startsWith('|')) s = s.substring(1);
                if (s.endsWith('|')) s = s.substring(0, s.length - 1);
                return s.split('|').map(c => c.trim());
            });
            
            let isDivider = parsedRows[1].every(cell => /^:?-+:?$/.test(cell));
            if (isDivider) {
                let tblHtml = ['<div class="table-container"><table class="chat-table">'];
                tblHtml.push('<thead><tr>');
                for (let cell of parsedRows[0]) {
                    tblHtml.push(`<th>${cell}</th>`);
                }
                tblHtml.push('</tr></thead><tbody>');
                
                for (let i = 2; i < parsedRows.length; i++) {
                    tblHtml.push('<tr>');
                    for (let cell of parsedRows[i]) {
                        tblHtml.push(`<td>${cell}</td>`);
                    }
                    tblHtml.push('</tr>');
                }
                tblHtml.push('</tbody></table></div>');
                parsedLines.push(tblHtml.join(''));
                return;
            }
        }
        parsedLines.push(...tableRows);
    }
    
    let inList = false;
    let listItems = [];
    
    function flushList() {
        if (listItems.length > 0) {
            parsedLines.push("<ul>" + listItems.map(item => `<li>${item}</li>`).join('') + "</ul>");
            listItems = [];
        }
    }
    
    for (let line of lines) {
        let trimmed = line.trim();
        let isTableRow = trimmed.startsWith('|') && trimmed.endsWith('|');
        
        if (isTableRow) {
            flushList();
            if (!inTable) {
                inTable = true;
                tableRows = [];
            }
            tableRows.push(line);
        } else {
            if (inTable) {
                inTable = false;
                flushTable();
            }
            
            let isListItem = trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("• ");
            if (isListItem) {
                if (!inList) {
                    inList = true;
                    listItems = [];
                }
                listItems.push(trimmed.substring(2));
            } else {
                if (inList) {
                    inList = false;
                    flushList();
                }
                parsedLines.push(line);
            }
        }
    }
    
    if (inTable) flushTable();
    if (inList) flushList();
    
    html = parsedLines.join('\n');
    
    // 6. Convert newlines
    html = html.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br>");
    
    if (!html.startsWith("<p>") && !html.startsWith("<ul>") && !html.startsWith("<div")) {
        html = `<p>${html}</p>`;
    }
    
    return html;
}

function renderMessageBubble(text, sender, id = "") {
    const container = document.getElementById("chat-messages-container");
    const div = document.createElement("div");
    div.className = `chat-message ${sender}`;
    if (id) div.id = id;
    
    const avatarLetter = sender === "user" ? "MA" : "AI";
    div.innerHTML = `
        <div class="message-avatar">${avatarLetter}</div>
        <div class="message-bubble">${markdownToHtml(text)}</div>
    `;
    container.appendChild(div);
}
