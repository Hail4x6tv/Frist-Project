/* ==========================================================================
   ScholarGraph - Activity Audit Log Interactivity
   ========================================================================== */

let activityDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    fetchActivityLogs();
});

function filterActivityDebounced() {
    clearTimeout(activityDebounceTimer);
    activityDebounceTimer = setTimeout(() => {
        fetchActivityLogs();
    }, 300);
}

async function fetchActivityLogs() {
    const tableBody = document.getElementById("activityTableBody");
    if (!tableBody) return;

    const action = document.getElementById("activityActionFilter")?.value || "";
    const search = document.getElementById("activitySearchInput")?.value.trim() || "";

    const queryParams = new URLSearchParams({ action, search, limit: 150 });

    try {
        const res = await fetch(`/api/activity?${queryParams.toString()}`);
        const data = await res.json();
        const logs = data.activities || [];

        if (logs.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4 text-muted">
                        No activity records found matching criteria.
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = "";
        logs.forEach(log => {
            const tr = document.createElement("tr");

            // Format Action badge
            let actionBadgeClass = "badge-neutral";
            if (log.action.includes("UPLOAD")) actionBadgeClass = "badge-success";
            if (log.action.includes("EDIT")) actionBadgeClass = "badge-year";
            if (log.action.includes("DELETE")) actionBadgeClass = "badge-danger";
            if (log.action.includes("TAG")) actionBadgeClass = "badge-amber";
            if (log.action.includes("REF")) actionBadgeClass = "badge-neutral";
            if (log.action.includes("RE_EXTRACT")) actionBadgeClass = "badge-warning";

            // Paper link
            let paperCol = log.paper_title || "General Event";
            if (log.paper_id && log.action !== "DELETE") {
                paperCol = `<a href="/paper/${log.paper_id}" class="matched-paper-link">${escapeHtml(log.paper_title || 'Paper #' + log.paper_id)}</a>`;
            }

            // Format timestamp
            const dateStr = formatDateTime(log.timestamp);

            tr.innerHTML = `
                <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);">${dateStr}</td>
                <td><span class="badge ${actionBadgeClass}">${log.action}</span></td>
                <td><strong>${escapeHtml(log.user || 'Admin')}</strong></td>
                <td>${paperCol}</td>
                <td style="font-size: 12.5px; line-height: 1.4;">${escapeHtml(log.details || '')}</td>
            `;
            tableBody.appendChild(tr);
        });

    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-danger text-center">Error loading logs: ${e.message}</td></tr>`;
    }
}

function formatDateTime(isoString) {
    if (!isoString) return "";
    try {
        const d = new Date(isoString + "Z");
        if (isNaN(d.getTime())) return isoString;
        return d.toLocaleDateString(undefined, {
            year: "numeric", month: "short", day: "numeric",
            hour: "2-digit", minute: "2-digit"
        });
    } catch {
        return isoString;
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
