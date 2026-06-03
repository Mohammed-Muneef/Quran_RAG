// 114 Surahs mapping for dropdown filters
const SURAHS = [
    { number: 1, name: "Al-Fatihah" },
    { number: 2, name: "Al-Baqarah" },
    { number: 3, name: "Ali 'Imran" },
    { number: 4, name: "An-Nisa" },
    { number: 5, name: "Al-Ma'idah" },
    { number: 6, name: "Al-An'am" },
    { number: 7, name: "Al-A'raf" },
    { number: 8, name: "Al-Anfal" },
    { number: 9, name: "At-Tawbah" },
    { number: 10, name: "Yunus" },
    { number: 11, name: "Hud" },
    { number: 12, name: "Yusuf" },
    { number: 13, name: "Ar-Ra'd" },
    { number: 14, name: "Ibrahim" },
    { number: 15, name: "Al-Hijr" },
    { number: 16, name: "An-Nahl" },
    { number: 17, name: "Al-Isra" },
    { number: 18, name: "Al-Kahf" },
    { number: 19, name: "Maryam" },
    { number: 20, name: "Ta-Ha" },
    { number: 21, name: "Al-Anbiya" },
    { number: 22, name: "Al-Hajj" },
    { number: 23, name: "Al-Mu'minun" },
    { number: 24, name: "An-Nur" },
    { number: 25, name: "Al-Furqan" },
    { number: 26, name: "Ash-Shu'ara" },
    { number: 27, name: "An-Naml" },
    { number: 28, name: "Al-Qasas" },
    { number: 29, name: "Al-'Ankabut" },
    { number: 30, name: "Ar-Rum" },
    { number: 31, name: "Luqman" },
    { number: 32, name: "As-Sajdah" },
    { number: 33, name: "Al-Ahzab" },
    { number: 34, name: "Saba" },
    { number: 35, name: "Fatir" },
    { number: 36, name: "Ya-Sin" },
    { number: 37, name: "As-Saffat" },
    { number: 38, name: "Sad" },
    { number: 39, name: "Az-Zumar" },
    { number: 40, name: "Ghafir" },
    { number: 41, name: "Fussilat" },
    { number: 42, name: "Ash-Shura" },
    { number: 43, name: "Az-Zukhruf" },
    { number: 44, name: "Ad-Dukhan" },
    { number: 45, name: "Al-Jathiyah" },
    { number: 46, name: "Al-Ahqaf" },
    { number: 47, name: "Muhammad" },
    { number: 48, name: "Al-Fath" },
    { number: 49, name: "Al-Hujurat" },
    { number: 50, name: "Qaf" },
    { number: 51, name: "Adh-Dhariyat" },
    { number: 52, name: "At-Tur" },
    { number: 53, name: "An-Najm" },
    { number: 54, name: "Al-Qamar" },
    { number: 55, name: "Ar-Rahman" },
    { number: 56, name: "Al-Waqi'ah" },
    { number: 57, name: "Al-Hadid" },
    { number: 58, name: "Al-Mujadila" },
    { number: 59, name: "Al-Hashr" },
    { number: 60, name: "Al-Mumtahanah" },
    { number: 61, name: "As-Saf" },
    { number: 62, name: "Al-Jumu'ah" },
    { number: 63, name: "Al-Munafiqun" },
    { number: 64, name: "At-Taghabun" },
    { number: 65, name: "At-Talaq" },
    { number: 66, name: "At-Tahrim" },
    { number: 67, name: "Al-Mulk" },
    { number: 68, name: "Al-Qalam" },
    { number: 69, name: "Al-Haqqah" },
    { number: 70, name: "Al-Ma'arij" },
    { number: 71, name: "Nuh" },
    { number: 72, name: "Al-Jinn" },
    { number: 73, name: "Al-Muzzammil" },
    { number: 74, name: "Al-Muddaththir" },
    { number: 75, name: "Al-Qiyamah" },
    { number: 76, name: "Al-Insan" },
    { number: 77, name: "Al-Mursalat" },
    { number: 78, name: "An-Naba" },
    { number: 79, name: "An-Nazi'at" },
    { number: 80, name: "'Abasa" },
    { number: 81, name: "At-Takwir" },
    { number: 82, name: "Al-Infitar" },
    { number: 83, name: "Al-Mutaffifin" },
    { number: 84, name: "Al-Inshiqaq" },
    { number: 85, name: "Al-Buruj" },
    { number: 86, name: "At-Tariq" },
    { number: 87, name: "Al-A'la" },
    { number: 88, name: "Al-Ghashiyah" },
    { number: 89, name: "Al-Fajr" },
    { number: 90, name: "Al-Balad" },
    { number: 91, name: "Ash-Shams" },
    { number: 92, name: "Al-Layl" },
    { number: 93, name: "Ad-Duha" },
    { number: 94, name: "Ash-Sharh" },
    { number: 95, name: "At-Tin" },
    { number: 96, name: "Al-'Alaq" },
    { number: 97, name: "Al-Qadr" },
    { number: 98, name: "Al-Bayyinah" },
    { number: 99, name: "Az-Zalzalah" },
    { number: 100, name: "Al-'Adiyat" },
    { number: 101, name: "Al-Qari'ah" },
    { number: 102, name: "At-Takathur" },
    { number: 103, name: "Al-'Asr" },
    { number: 104, name: "Al-Humazah" },
    { number: 105, name: "Al-Fil" },
    { number: 106, name: "Quraysh" },
    { number: 107, name: "Al-Ma'un" },
    { number: 108, name: "Al-Kawthar" },
    { number: 109, name: "Al-Kafirun" },
    { number: 110, name: "An-Nasr" },
    { number: 111, name: "Al-Masad" },
    { number: 112, name: "Al-Ikhlas" },
    { number: 113, name: "Al-Falaq" },
    { number: 114, name: "An-Nas" }
];

// Cache references to DOM Elements
const surahSelect = document.getElementById("surah-select");
const envBadge = document.getElementById("env-badge");
const chatLog = document.getElementById("chat-log");
const queryForm = document.getElementById("query-form");
const queryInput = document.getElementById("query-input");
const submitBtn = document.getElementById("submit-btn");
const inspectorPanel = document.getElementById("inspector-panel");
const inspectorBody = document.getElementById("inspector-body");
const liveRagToggle = document.getElementById("live-rag-toggle");

// Initialize Surah Dropdown options
function initSurahDropdown() {
    SURAHS.forEach(surah => {
        const option = document.createElement("option");
        option.value = surah.number;
        option.textContent = `${surah.number}. ${surah.name}`;
        surahSelect.appendChild(option);
    });
}

// Fetch system health and backend mode
async function checkHealth() {
    try {
        const response = await fetch("/health");
        if (response.ok) {
            const data = await response.json();
            if (data.status === "ok") {
                envBadge.textContent = "Mode: Active (DB Ready)";
                envBadge.className = "mode-badge live";
            } else {
                envBadge.textContent = "Mode: Warning";
                envBadge.className = "mode-badge";
            }
        } else {
            envBadge.textContent = "Mode: Disconnected";
            envBadge.className = "mode-badge";
        }
    } catch (error) {
        console.error("Health check failed:", error);
        envBadge.textContent = "Mode: Offline";
        envBadge.className = "mode-badge";
    }
}

// Helper to scroll chat log to the bottom
function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Global function to set query and submit it
window.setQuery = function(text) {
    queryInput.value = text;
    queryInput.focus();
    // Auto submit
    queryForm.dispatchEvent(new Event('submit'));
};

// Global function to toggle inspection panel
window.toggleInspector = function(show) {
    if (show) {
        inspectorPanel.classList.add("open");
    } else {
        inspectorPanel.classList.remove("open");
    }
};

// Handle showing a detailed inspection
window.inspectCitations = function(versesJsonEscaped, timeMs) {
    const verses = JSON.parse(decodeURIComponent(versesJsonEscaped));
    inspectorBody.innerHTML = "";
    
    if (!verses || verses.length === 0) {
        inspectorBody.innerHTML = `<p class="empty-state">No context verses were cited for this response.</p>`;
        window.toggleInspector(true);
        return;
    }

    verses.forEach((v, index) => {
        const card = document.createElement("div");
        card.className = "verse-inspect-card";
        
        card.innerHTML = `
            <div class="card-ref">
                <span>Reference: ${v.ref}</span>
                <span class="confidence">Rank #${index + 1}</span>
            </div>
            <div class="card-arabic">${v.arabic}</div>
            <div class="card-english">${v.english}</div>
        `;
        inspectorBody.appendChild(card);
    });

    // Add search metadata
    const footer = document.createElement("div");
    footer.style.fontSize = "0.8rem";
    footer.style.color = "var(--text-secondary)";
    footer.style.marginTop = "20px";
    footer.style.textAlign = "center";
    footer.textContent = `Retrieved in ${timeMs}ms using Hybrid RRF & Reranking.`;
    inspectorBody.appendChild(footer);

    window.toggleInspector(true);
};

// Submit Query Handler
queryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = queryInput.value.trim();
    if (!question) return;

    const surahVal = surahSelect.value;
    const surahFilter = surahVal ? parseInt(surahVal) : null;

    // Render User Message
    const userMsg = document.createElement("div");
    userMsg.className = "message user-message";
    userMsg.innerHTML = `<div class="bubble"><p>${escapeHtml(question)}</p></div>`;
    chatLog.appendChild(userMsg);
    
    // Clear Input
    queryInput.value = "";
    scrollToBottom();

    // Disable Submit Button & Input
    submitBtn.disabled = true;
    queryInput.disabled = true;
    
    // Add Loading Indicator Bubble
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "message bot-message";
    loadingMsg.id = "rag-loading";
    loadingMsg.innerHTML = `
        <div class="bubble loading-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    `;
    chatLog.appendChild(loadingMsg);
    scrollToBottom();

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                surah_filter: surahFilter
            })
        });

        // Remove loading
        const loader = document.getElementById("rag-loading");
        if (loader) loader.remove();

        if (response.ok) {
            const data = await response.json();
            
            // Build bot response bubble
            const botMsg = document.createElement("div");
            botMsg.className = "message bot-message";
            
            // Escape/prepare citations array for inline handler
            const versesJsonStr = encodeURIComponent(JSON.stringify(data.verses));
            
            // Format citation links or badge
            let citationHtml = "";
            if (data.verses && data.verses.length > 0) {
                const badgeLabel = `Cited Verses (${data.verses.length})`;
                citationHtml = `
                    <div class="rag-citation" onclick="inspectCitations('${versesJsonStr}', ${data.retrieval_time_ms})">
                        📖 ${badgeLabel} <small style="opacity:0.8; margin-left:4px;">(Click to Inspect)</small>
                    </div>
                `;
            }

            // Assemble RAG bubble contents
            let bubbleContent = `
                <div class="bubble">
                    <div class="rag-answer">
                        ${citationHtml}
                        <div class="rag-text">${escapeHtml(data.answer).replace(/\n/g, "<br>")}</div>
            `;

            // If there are verses, display the primary one directly in the message bubble for visual grounding
            if (data.verses && data.verses.length > 0) {
                const primaryVerse = data.verses[0];
                bubbleContent += `
                    <div class="rag-arabic">${primaryVerse.arabic}</div>
                    <div class="rag-english">"${primaryVerse.english}"</div>
                `;
            }

            bubbleContent += `
                        <div class="rag-meta-footer">
                            <span>⏱️ ${data.retrieval_time_ms}ms</span>
                            <span>⚖️ ${escapeHtml(data.disclaimer)}</span>
                        </div>
                    </div>
                </div>
            `;
            
            botMsg.innerHTML = bubbleContent;
            chatLog.appendChild(botMsg);
            
            // Automatically update inspection panel with the new citations
            if (data.verses && data.verses.length > 0) {
                inspectCitations(versesJsonStr, data.retrieval_time_ms);
            }
        } else {
            const errData = await response.json();
            showErrorMsg(errData.detail || "Server error while processing your request.");
        }
    } catch (err) {
        const loader = document.getElementById("rag-loading");
        if (loader) loader.remove();
        console.error("Query request failed:", err);
        showErrorMsg("Failed to connect to the server. Make sure the backend API is running.");
    } finally {
        submitBtn.disabled = false;
        queryInput.disabled = false;
        queryInput.focus();
        scrollToBottom();
    }
});

// Helper to escape HTML tags to prevent XSS
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Render error message bubble in chat
function showErrorMsg(message) {
    const errorMsg = document.createElement("div");
    errorMsg.className = "message bot-message";
    errorMsg.innerHTML = `
        <div class="bubble" style="border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.1);">
            <p style="color: #ef4444; font-weight: 500;">⚠️ Error</p>
            <p style="font-size: 0.95rem; line-height: 1.5;">${escapeHtml(message)}</p>
        </div>
    `;
    chatLog.appendChild(errorMsg);
    scrollToBottom();
}

// App Initialization
document.addEventListener("DOMContentLoaded", () => {
    initSurahDropdown();
    checkHealth();
    
    // Periodically check health (every 30 seconds)
    setInterval(checkHealth, 30000);
});
