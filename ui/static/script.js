// script.js — eBay Ali Hunter UI Logic

let eventSource = null;

// -----------------------------------------------
// INIT — load keywords when page opens
// -----------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    loadKeywords();
    pollStatus();
});


// -----------------------------------------------
// KEYWORDS
// -----------------------------------------------

async function loadKeywords() {
    const res  = await fetch("/api/keywords");
    const data = await res.json();
    renderKeywords(data.keywords);
}

function renderKeywords(keywords) {
    const list = document.getElementById("keywordsList");
    list.innerHTML = "";

    if (keywords.length === 0) {
        list.innerHTML = `<div class="log-placeholder">No keywords yet. Click + Add.</div>`;
        return;
    }

    keywords.forEach((kw, i) => {
        const item = document.createElement("div");
        item.className = "keyword-item";
        item.innerHTML = `
            <input type="text" value="${kw}" onchange="saveKeywords()"
                   onblur="saveKeywords()" />
            <button class="del-btn" onclick="this.closest('.keyword-item').remove(); saveKeywords()">×</button>
        `;
        list.appendChild(item);
    });
}

function addKeyword() {
    const list = document.getElementById("keywordsList");
    const item = document.createElement("div");
    item.className = "keyword-item";
    item.innerHTML = `
        <input type="text" placeholder="Enter keyword..."
               onblur="saveKeywords()" onchange="saveKeywords()" />
        <button class="del-btn" onclick="this.parentElement.remove(); saveKeywords()">×</button>
    `;
    list.appendChild(item);
    item.querySelector("input").focus();
}

function deleteKeyword(index) {
    const inputs = document.querySelectorAll(".keyword-item input");
    inputs[index].closest(".keyword-item").remove();
    saveKeywords();
}

async function saveKeywords() {
    const inputs   = document.querySelectorAll(".keyword-item input");
    const keywords = Array.from(inputs)
        .map(i => i.value.trim())
        .filter(v => v.length > 0);

    await fetch("/api/keywords", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ keywords }),
    });
}


// -----------------------------------------------
// SCRAPER CONTROLS
// -----------------------------------------------

async function startScraper() {
    await saveKeywords();

    const res  = await fetch("/api/start", { method: "POST" });
    const data = await res.json();

    if (data.status === "already_running") {
        appendLog("⚠️ Scraper is already running!", "warning");
        return;
    }

    // Clear previous logs and results
    document.getElementById("logBox").innerHTML   = "";
    document.getElementById("resultsBody").innerHTML = `
        <tr><td colspan="9" class="empty-msg">Waiting for results...</td></tr>
    `;
    document.getElementById("downloadBtn").style.display = "none";
    document.getElementById("statsBox").style.display    = "none";

    setStatus("running");
    startLogStream();
}

async function stopScraper() {
    await fetch("/api/stop", { method: "POST" });
    appendLog("⚠️ Stop requested...", "warning");
}

function startLogStream() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource("/api/logs");

    eventSource.onmessage = (e) => {
        const msg = JSON.parse(e.data);

        if (msg === "__DONE__") {
            eventSource.close();
            setStatus("done");
            loadResults();
            return;
        }

        appendLog(msg);
    };

    eventSource.onerror = () => {
        eventSource.close();
        setStatus("idle");
    };
}


// -----------------------------------------------
// LOGS
// -----------------------------------------------

function appendLog(message, forceType = null) {
    const box = document.getElementById("logBox");

    // Remove placeholder if present
    const placeholder = box.querySelector(".log-placeholder");
    if (placeholder) placeholder.remove();

    const line = document.createElement("div");
    line.className = "log-line";

    // Auto detect log type for color
    const type = forceType || detectLogType(message);
    if (type) line.classList.add(type);

    line.textContent = message;
    box.appendChild(line);

    // Auto scroll to bottom
    box.scrollTop = box.scrollHeight;
}

function detectLogType(msg) {
    const m = msg.toLowerCase();
    if (m.includes("error") || m.includes("failed") || m.includes("❌")) return "error";
    if (m.includes("warning") || m.includes("⚠️"))                        return "warning";
    if (m.includes("✅") || m.includes("done") || m.includes("saved"))    return "success";
    if (m.includes("keyword") || m.includes("🚀") || m.includes("🏁"))    return "info";
    return null;
}

function clearLogs() {
    document.getElementById("logBox").innerHTML =
        `<div class="log-placeholder">Logs cleared.</div>`;
}


// -----------------------------------------------
// RESULTS
// -----------------------------------------------

async function loadResults() {
    const res  = await fetch("/api/results");
    const data = await res.json();

    if (data.count === 0) {
        document.getElementById("resultsBody").innerHTML = `
            <tr><td colspan="9" class="empty-msg">No profitable products found.</td></tr>
        `;
        return;
    }

    // Show stats
    document.getElementById("statCount").textContent    = data.count;
    document.getElementById("statsBox").style.display   = "block";

    // Show download button
    if (data.excel) {
        document.getElementById("downloadBtn").style.display = "inline-block";
        document.getElementById("downloadBtn").dataset.path  = data.excel;
    }

    // Render table rows
    const tbody = document.getElementById("resultsBody");
    tbody.innerHTML = "";

    data.results.forEach(product => {
        const tr = document.createElement("tr");

        // Row highlight class
        if (product.welcome_deal)       tr.classList.add("welcome-deal");
        else if (product.margin_pct >= 40) tr.classList.add("high-margin");

        const ebayLink = product.ebay_url
            ? `<a href="${product.ebay_url}" target="_blank">View</a>` : "-";
        const aliLink  = product.ali_url
            ? `<a href="${product.ali_url}"  target="_blank">View</a>` : "-";
        const welcome  = product.welcome_deal
            ? `<span class="badge-yes">YES</span>`
            : `<span class="badge-no">No</span>`;

        tr.innerHTML = `
            <td>${product.keyword      || "-"}</td>
            <td title="${product.title || ""}">${truncate(product.title, 35)}</td>
            <td>$${product.ebay_price  || "-"}</td>
            <td>$${product.ali_price   || "-"}</td>
            <td>$${product.profit      || "-"}</td>
            <td>${product.margin_pct   || "-"}%</td>
            <td>${welcome}</td>
            <td>${ebayLink}</td>
            <td>${aliLink}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function downloadExcel() {
    appendLog("📥 Opening Excel file location...", "info");
    const path = document.getElementById("downloadBtn").dataset.path;
    await fetch("/api/open_excel?path=" + encodeURIComponent(path));
}


// -----------------------------------------------
// STATUS
// -----------------------------------------------

function setStatus(state) {
    const badge    = document.getElementById("statusBadge");
    const dot      = badge.querySelector(".dot");
    const text     = document.getElementById("statusText");
    const startBtn = document.getElementById("startBtn");
    const stopBtn  = document.getElementById("stopBtn");

    dot.className = `dot ${state}`;

    const labels = { idle: "Idle", running: "Running...", done: "Done", error: "Error" };
    text.textContent = labels[state] || state;

    if (state === "running") {
        startBtn.disabled = true;
        stopBtn.disabled  = false;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled  = true;
    }
}

async function pollStatus() {
    const res  = await fetch("/api/status");
    const data = await res.json();
    if (data.running) setStatus("running");
    setTimeout(pollStatus, 3000);
}


// -----------------------------------------------
// UTILS
// -----------------------------------------------

function truncate(str, max) {
    if (!str) return "-";
    return str.length > max ? str.substring(0, max) + "..." : str;
}