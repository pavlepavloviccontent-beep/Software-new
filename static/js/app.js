let currentJobId = null;
let pollInterval = null;

function startAnalysis() {
    const input = document.getElementById("profileInput").value.trim();
    if (!input) return;

    const btn = document.getElementById("analyzeBtn");
    btn.disabled = true;

    hideAll();
    show("statusSection");

    fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile: input }),
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.error) {
                showError(data.error);
                btn.disabled = false;
                return;
            }
            currentJobId = data.job_id;
            pollStatus();
        })
        .catch((err) => {
            showError("Network error. Please try again.");
            btn.disabled = false;
        });
}

function pollStatus() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(() => {
        fetch(`/api/status/${currentJobId}`)
            .then((r) => r.json())
            .then((data) => {
                document.getElementById("statusMessage").textContent = data.message;

                if (data.progress_total > 0) {
                    const pct = Math.round((data.progress / data.progress_total) * 100);
                    document.getElementById("progressBar").style.width = pct + "%";
                    show("progressContainer");
                }

                if (data.status === "done") {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    document.getElementById("analyzeBtn").disabled = false;

                    if (data.result && data.result.total_videos > 0) {
                        renderResults(data.result);
                    } else {
                        showError(data.message || "No videos found.");
                    }
                } else if (data.status === "error") {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    document.getElementById("analyzeBtn").disabled = false;
                    showError(data.message);
                }
            })
            .catch(() => {});
    }, 2000);
}

function renderResults(result) {
    hideAll();
    show("resultsSection");

    document.getElementById("profileName").textContent =
        `@${result.username}` + (result.full_name ? ` (${result.full_name})` : "");
    document.getElementById("totalVideos").textContent = `${result.total_videos} videos found`;
    document.getElementById("totalPosts").textContent = `${result.total_posts} total posts`;

    renderVideoList("topVideos", result.top_videos, "most");
    renderVideoList("bottomVideos", result.bottom_videos, "least");
}

function renderVideoList(containerId, videos, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!videos || videos.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:20px;">No videos to display</p>';
        return;
    }

    videos.forEach((video, index) => {
        const rank = index + 1;
        const card = document.createElement("div");
        card.className = "video-card";
        card.innerHTML = `
            <div class="video-header" onclick="toggleCard(this)">
                <div class="video-rank">${rank}</div>
                <div class="video-info">
                    <div class="video-caption">${escapeHtml(video.caption || "No caption")}</div>
                    <div class="video-meta">
                        <span>${formatNumber(video.views)} views</span>
                        <span>${formatNumber(video.likes)} likes</span>
                        <span>${formatNumber(video.comments)} comments</span>
                    </div>
                </div>
                <div class="video-expand">&#9660;</div>
            </div>
            <div class="video-transcript">
                <div class="transcript-label">Transcript / Script</div>
                <div class="transcript-text">${escapeHtml(video.transcript || "[Not available]")}</div>
                <button class="copy-btn" onclick="copyTranscript(this, ${JSON.stringify(video.transcript || "").replace(/"/g, "&quot;")})">
                    Copy Transcript
                </button>
                <br>
                <a class="video-link" href="${video.url}" target="_blank" rel="noopener">
                    View on Instagram
                </a>
            </div>
        `;
        container.appendChild(card);
    });
}

function toggleCard(header) {
    header.parentElement.classList.toggle("expanded");
}

function switchTab(tab) {
    const tabs = document.querySelectorAll(".tab");
    tabs.forEach((t, i) => {
        if ((tab === "top" && i === 0) || (tab === "bottom" && i === 1)) {
            t.classList.add("active");
        } else {
            t.classList.remove("active");
        }
    });

    if (tab === "top") {
        show("topVideos");
        hide("bottomVideos");
    } else {
        hide("topVideos");
        show("bottomVideos");
    }
}

function copyTranscript(btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = "Copied!";
        btn.classList.add("copied");
        setTimeout(() => {
            btn.textContent = "Copy Transcript";
            btn.classList.remove("copied");
        }, 2000);
    });
}

function formatNumber(num) {
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
    if (num >= 1_000) return (num / 1_000).toFixed(1) + "K";
    return String(num);
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function showError(msg) {
    hideAll();
    show("errorSection");
    document.getElementById("errorMessage").textContent = msg;
}

function resetUI() {
    hideAll();
    document.getElementById("analyzeBtn").disabled = false;
    document.getElementById("progressBar").style.width = "0%";
}

function hideAll() {
    hide("statusSection");
    hide("errorSection");
    hide("resultsSection");
}

function show(id) {
    document.getElementById(id).classList.remove("hidden");
}

function hide(id) {
    document.getElementById(id).classList.add("hidden");
}

// Allow Enter key to trigger analysis
document.getElementById("profileInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") startAnalysis();
});
