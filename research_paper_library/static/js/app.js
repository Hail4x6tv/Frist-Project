/* ==========================================================================
   ScholarGraph - Global App Utilities & Theme Management
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    loadDashboardStats();
});

// Theme Management (Light / Dark Mode)
function initTheme() {
    const savedTheme = localStorage.getItem("scholargraph_theme") || "light";
    setTheme(savedTheme);

    const themeToggleBtn = document.getElementById("themeToggleBtn");
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const currentTheme = document.body.classList.contains("theme-dark") ? "dark" : "light";
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            setTheme(newTheme);
        });
    }
}

function setTheme(theme) {
    if (theme === "dark") {
        document.body.classList.remove("theme-light");
        document.body.classList.add("theme-dark");
        const btn = document.getElementById("themeToggleBtn");
        if (btn) btn.innerHTML = '<i class="fa-solid fa-sun text-warning"></i>';
    } else {
        document.body.classList.remove("theme-dark");
        document.body.classList.add("theme-light");
        const btn = document.getElementById("themeToggleBtn");
        if (btn) btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }
    localStorage.setItem("scholargraph_theme", theme);
}

// Global Toast Notifications
function showToast(message, type = "info", duration = 4000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check text-success";
    if (type === "error") icon = "fa-triangle-exclamation text-danger";

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <div class="toast-body">${message}</div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 250);
    }, duration);
}

// Global Stats Loader
async function loadDashboardStats() {
    try {
        const res = await fetch("/api/stats");
        if (!res.ok) return;
        const data = await res.json();

        const pCount = document.getElementById("statPapersCount");
        const aCount = document.getElementById("statAuthorsCount");
        const tCount = document.getElementById("statTopicsCount");
        const cCount = document.getElementById("statCitationsCount");

        if (pCount) pCount.innerText = data.paper_count || 0;
        if (aCount) aCount.innerText = data.author_count || 0;
        if (tCount) tCount.innerText = data.topic_count || 0;
        if (cCount) cCount.innerText = data.citation_links || 0;
    } catch (e) {
        console.error("Error loading dashboard stats:", e);
    }
}

// Import Sample Papers Prompt
async function loadSamplePapersPrompt() {
    if (!confirm("Import sample research papers into your library? This will seed the library with realistic papers across AI, NLP, and Knowledge Graphs.")) {
        return;
    }

    showToast("Importing sample research papers...", "info", 5000);

    try {
        const res = await fetch("/api/samples/seed", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast(`Imported ${data.imported} sample papers successfully!`, "success");
            loadDashboardStats();
            if (typeof fetchPapers === "function") {
                fetchPapers();
            }
        } else {
            showToast(data.error || "Failed to seed samples", "error");
        }
    } catch (e) {
        showToast("Error importing sample papers: " + e.message, "error");
    }
}
