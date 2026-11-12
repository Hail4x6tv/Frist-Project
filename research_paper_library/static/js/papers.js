/* ==========================================================================
   ScholarGraph - Paper Library Explorer & Management
   ========================================================================== */

let debounceTimer = null;
let currentPaperEditingId = null;

document.addEventListener("DOMContentLoaded", () => {
    initSearchAndFilters();
    fetchFilterOptions();
    fetchPapers();
});

function initSearchAndFilters() {
    const searchInput = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearchBtn");

    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            if (clearBtn) clearBtn.style.display = e.target.value ? "block" : "none";
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                fetchPapers();
            }, 300);
        });
    }

    // Check URL parameters (e.g. ?topic=Machine+Learning or ?author=Alice)
    const urlParams = new URLSearchParams(window.location.search);
    const topicParam = urlParams.get("topic");
    const authorParam = urlParams.get("author");

    if (topicParam) {
        const topicSelect = document.getElementById("topicFilter");
        if (topicSelect) {
            setTimeout(() => {
                topicSelect.value = topicParam;
                fetchPapers();
            }, 250);
        }
    }

    if (authorParam) {
        const authorSelect = document.getElementById("authorFilter");
        if (authorSelect) {
            setTimeout(() => {
                authorSelect.value = authorParam;
                fetchPapers();
            }, 250);
        }
    }
}

function clearSearch() {
    const input = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearchBtn");
    if (input) input.value = "";
    if (clearBtn) clearBtn.style.display = "none";
    fetchPapers();
}

async function fetchFilterOptions() {
    try {
        const [topicsRes, authorsRes] = await Promise.all([
            fetch("/api/topics"),
            fetch("/api/authors")
        ]);

        if (topicsRes.ok) {
            const data = await topicsRes.json();
            const topicSelect = document.getElementById("topicFilter");
            if (topicSelect) {
                topicSelect.innerHTML = '<option value="">All Topics</option>';
                data.topics.forEach(t => {
                    const opt = document.createElement("option");
                    opt.value = t.name;
                    opt.innerText = `${t.name} (${t.paper_count})`;
                    topicSelect.appendChild(opt);
                });
            }
        }

        if (authorsRes.ok) {
            const data = await authorsRes.json();
            const authorSelect = document.getElementById("authorFilter");
            if (authorSelect) {
                authorSelect.innerHTML = '<option value="">All Authors</option>';
                data.authors.forEach(a => {
                    const opt = document.createElement("option");
                    opt.value = a.name;
                    opt.innerText = `${a.name} (${a.paper_count})`;
                    authorSelect.appendChild(opt);
                });
            }
        }
    } catch (e) {
        console.error("Error loading filter options:", e);
    }
}

function applyFilters() {
    fetchPapers();
}

function resetFilters() {
    const sInput = document.getElementById("searchInput");
    const tSelect = document.getElementById("topicFilter");
    const aSelect = document.getElementById("authorFilter");
    const ySelect = document.getElementById("yearFilter");
    const stSelect = document.getElementById("statusFilter");
    const soSelect = document.getElementById("sortFilter");
    const clearBtn = document.getElementById("clearSearchBtn");

    if (sInput) sInput.value = "";
    if (clearBtn) clearBtn.style.display = "none";
    if (tSelect) tSelect.value = "";
    if (aSelect) aSelect.value = "";
    if (ySelect) ySelect.value = "";
    if (stSelect) stSelect.value = "";
    if (soSelect) soSelect.value = "created_at-DESC";

    window.history.replaceState({}, document.title, window.location.pathname);
    fetchPapers();
}

async function fetchPapers() {
    const container = document.getElementById("papersContainer");
    const countDisplay = document.getElementById("resultsCount");
    if (!container) return;

    const search = document.getElementById("searchInput")?.value.trim() || "";
    const topic = document.getElementById("topicFilter")?.value || "";
    const author = document.getElementById("authorFilter")?.value || "";
    const year = document.getElementById("yearFilter")?.value || "";
    const status = document.getElementById("statusFilter")?.value || "";
    const sortVal = document.getElementById("sortFilter")?.value || "created_at-DESC";

    const [sort, order] = sortVal.split("-");

    const queryParams = new URLSearchParams({
        search, topic, author, year, status, sort, order
    });

    try {
        const res = await fetch(`/api/papers?${queryParams.toString()}`);
        const data = await res.json();
        const papers = data.papers || [];

        if (countDisplay) {
            countDisplay.innerText = `Showing ${papers.length} research paper${papers.length === 1 ? '' : 's'}`;
        }

        // Dynamically populate year filter dropdown options if not yet populated
        populateYearFilter(papers);

        if (papers.length === 0) {
            container.innerHTML = `
                <div class="empty-state card">
                    <div class="empty-icon"><i class="fa-solid fa-book-open-reader"></i></div>
                    <h3>No Research Papers Found</h3>
                    <p class="text-secondary mt-2 mb-4">No papers matched your search or filter criteria. Upload a PDF paper or import samples to get started.</p>
                    <div style="display: flex; gap: 10px; justify-content: center;">
                        <button class="btn btn-secondary" onclick="loadSamplePapersPrompt()">
                            <i class="fa-solid fa-flask"></i> Import Sample Papers
                        </button>
                        <button class="btn btn-primary" onclick="openUploadModal()">
                            <i class="fa-solid fa-cloud-arrow-up"></i> Upload Paper
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = "";
        papers.forEach(p => {
            const card = createPaperCard(p);
            container.appendChild(card);
        });

    } catch (e) {
        container.innerHTML = `<div class="card p-4 text-center text-danger">Error fetching papers: ${e.message}</div>`;
    }
}

function populateYearFilter(papers) {
    const yearSelect = document.getElementById("yearFilter");
    if (!yearSelect || yearSelect.options.length > 1) return;

    const years = new Set();
    papers.forEach(p => {
        if (p.publication_year) years.add(p.publication_year);
    });

    const sortedYears = Array.from(years).sort((a, b) => b - a);
    sortedYears.forEach(y => {
        const opt = document.createElement("option");
        opt.value = y;
        opt.innerText = y;
        yearSelect.appendChild(opt);
    });
}

function createPaperCard(p) {
    const div = document.createElement("div");
    div.className = "paper-card";
    div.id = `paperCard-${p.id}`;

    // Status badge
    let statusBadge = "";
    if (p.extraction_status === "success") {
        statusBadge = '<span class="badge badge-success"><i class="fa-solid fa-check"></i> Extracted</span>';
    } else if (p.extraction_status === "scanned") {
        statusBadge = '<span class="badge badge-amber"><i class="fa-solid fa-camera"></i> Scanned</span>';
    } else if (p.extraction_status === "partial") {
        statusBadge = '<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> Partial</span>';
    } else {
        statusBadge = '<span class="badge badge-danger">Failed</span>';
    }

    const yearBadge = p.publication_year ? `<span class="badge badge-year">${p.publication_year}</span>` : "";

    // Authors list
    const authorsHtml = (p.authors || []).map(a => `
        <a href="javascript:void(0)" onclick="filterByAuthor('${escapeJs(a)}')" class="author-link">${escapeHtml(a)}</a>
    `).join(", ");

    // Topics list
    const topicsHtml = (p.topics || []).map(t => `
        <a href="javascript:void(0)" onclick="filterByTopic('${escapeJs(t)}')" class="tag-pill">
            <i class="fa-solid fa-hashtag"></i> ${escapeHtml(t)}
        </a>
    `).join("");

    const sizeKb = (p.file_size / 1024).toFixed(1);

    div.innerHTML = `
        <div class="paper-card-header">
            <div>
                <div style="display: flex; gap: 8px; margin-bottom: 6px;">
                    ${yearBadge}
                    ${statusBadge}
                </div>
                <h3 class="paper-title">
                    <a href="/paper/${p.id}">${escapeHtml(p.title)}</a>
                </h3>
            </div>
            <div class="paper-actions-menu">
                <a href="/uploads/${p.filename}" target="_blank" class="btn btn-secondary btn-sm" title="Open PDF in new tab">
                    <i class="fa-solid fa-file-pdf text-danger"></i> PDF
                </a>
                <a href="/paper/${p.id}" class="btn btn-secondary btn-sm" title="View Full Details">
                    <i class="fa-solid fa-eye"></i> Details
                </a>
                <button class="btn btn-secondary btn-sm" onclick="openEditModal(${p.id})" title="Edit Details">
                    <i class="fa-solid fa-pen-to-square"></i>
                </button>
                <button class="btn btn-subtle text-danger" onclick="deletePaperPrompt(${p.id}, '${escapeJs(p.title)}')" title="Delete Paper">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        </div>

        <div class="paper-authors-line">
            <i class="fa-solid fa-users text-muted"></i>
            <span>${authorsHtml || "Unknown Author"}</span>
        </div>

        <div class="paper-abstract-excerpt">
            ${escapeHtml(p.abstract || "No abstract available.")}
        </div>

        <div class="paper-card-footer">
            <div class="paper-topics-list">
                ${topicsHtml}
            </div>
            <div class="paper-meta-stats">
                <span class="paper-meta-stat-item" title="Pages">
                    <i class="fa-solid fa-file-lines"></i> ${p.page_count}p
                </span>
                <span class="paper-meta-stat-item" title="File Size">
                    <i class="fa-solid fa-hard-drive"></i> ${sizeKb} KB
                </span>
                <span class="paper-meta-stat-item" title="Citations in Library">
                    <i class="fa-solid fa-quote-left text-primary"></i> ${p.cited_by_count || 0} cited
                </span>
            </div>
        </div>
    `;

    return div;
}

function filterByTopic(topicName) {
    const select = document.getElementById("topicFilter");
    if (select) {
        select.value = topicName;
        fetchPapers();
    }
}

function filterByAuthor(authorName) {
    const select = document.getElementById("authorFilter");
    if (select) {
        select.value = authorName;
        fetchPapers();
    }
}

// Edit Paper Details Modal
async function openEditModal(paperId) {
    currentPaperEditingId = paperId;
    const modal = document.getElementById("editModal");

    try {
        const res = await fetch(`/api/papers/${paperId}`);
        if (!res.ok) throw new Error("Paper not found");
        const p = await res.json();

        document.getElementById("editPaperId").value = p.id;
        document.getElementById("editTitle").value = p.title || "";
        document.getElementById("editAuthors").value = (p.authors || []).map(a => a.name).join(", ");
        document.getElementById("editYear").value = p.publication_year || "";
        document.getElementById("editDoi").value = p.doi || "";
        document.getElementById("editAbstract").value = p.abstract || "";

        renderEditModalTags(p.topics || []);

        if (modal) modal.style.display = "flex";
    } catch (e) {
        showToast("Error opening edit modal: " + e.message, "error");
    }
}

function renderEditModalTags(topics) {
    const container = document.getElementById("editTagsContainer");
    if (!container) return;

    container.innerHTML = "";
    topics.forEach(t => {
        const pill = document.createElement("span");
        pill.className = "tag-pill";
        pill.innerHTML = `
            #${escapeHtml(t.name)}
            <button type="button" class="tag-del-btn" onclick="removeTagFromModal(${t.id}, '${escapeJs(t.name)}')">&times;</button>
        `;
        container.appendChild(pill);
    });
}

async function addTagFromEditModal() {
    const input = document.getElementById("newTagInput");
    const tagName = input.value.trim();
    if (!tagName || !currentPaperEditingId) return;

    try {
        const res = await fetch(`/api/papers/${currentPaperEditingId}/tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: tagName, user: "Admin Researcher" })
        });
        if (res.ok) {
            input.value = "";
            showToast(`Tag '#${tagName}' added.`, "success");
            // Refresh paper tags in modal
            const pRes = await fetch(`/api/papers/${currentPaperEditingId}`);
            const pData = await pRes.json();
            renderEditModalTags(pData.topics || []);
            loadDashboardStats();
            fetchFilterOptions();
        }
    } catch (e) {
        showToast("Error adding tag: " + e.message, "error");
    }
}

async function removeTagFromModal(tagId, tagName) {
    if (!currentPaperEditingId) return;
    try {
        const res = await fetch(`/api/papers/${currentPaperEditingId}/tags/${tagId}`, {
            method: "DELETE"
        });
        if (res.ok) {
            showToast(`Tag '#${tagName}' removed.`, "info");
            const pRes = await fetch(`/api/papers/${currentPaperEditingId}`);
            const pData = await pRes.json();
            renderEditModalTags(pData.topics || []);
            loadDashboardStats();
            fetchFilterOptions();
        }
    } catch (e) {
        showToast("Error removing tag: " + e.message, "error");
    }
}

function closeEditModal() {
    const modal = document.getElementById("editModal");
    if (modal) modal.style.display = "none";
    currentPaperEditingId = null;
}

async function submitPaperEdits() {
    if (!currentPaperEditingId) return;

    const title = document.getElementById("editTitle").value.trim();
    const authors = document.getElementById("editAuthors").value.trim();
    const year = document.getElementById("editYear").value.trim();
    const doi = document.getElementById("editDoi").value.trim();
    const abstract = document.getElementById("editAbstract").value.trim();

    if (!title || !authors) {
        showToast("Title and Authors are required.", "error");
        return;
    }

    try {
        const res = await fetch(`/api/papers/${currentPaperEditingId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title, authors, publication_year: year, doi, abstract,
                user: "Admin Researcher"
            })
        });

        if (res.ok) {
            showToast("Paper details updated successfully!", "success");
            closeEditModal();
            fetchPapers();
            fetchFilterOptions();
        } else {
            showToast("Failed to update paper details.", "error");
        }
    } catch (e) {
        showToast("Error saving edits: " + e.message, "error");
    }
}

async function deletePaperPrompt(paperId, paperTitle) {
    if (!confirm(`Are you sure you want to delete "${paperTitle}"?\nThis will remove the paper, its references, and physical PDF.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/papers/${paperId}?user=Admin+Researcher`, {
            method: "DELETE"
        });

        if (res.ok) {
            showToast("Paper deleted successfully.", "success");
            fetchPapers();
            loadDashboardStats();
            fetchFilterOptions();
        } else {
            showToast("Failed to delete paper.", "error");
        }
    } catch (e) {
        showToast("Error deleting paper: " + e.message, "error");
    }
}

// Helpers
function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function escapeJs(str) {
    if (!str) return "";
    return str.replace(/'/g, "\\'").replace(/"/g, '\\"');
}
