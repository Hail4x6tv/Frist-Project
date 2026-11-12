/* ==========================================================================
   ScholarGraph - Paper Detail Page Interactivity
   ========================================================================== */

function openEditModalFromDetail() {
    const modal = document.getElementById("editModal");
    if (modal) modal.style.display = "flex";
}

function closeEditModal() {
    const modal = document.getElementById("editModal");
    if (modal) modal.style.display = "none";
}

async function submitPaperEditsFromDetail() {
    const paperId = document.getElementById("editPaperId").value;
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
        const res = await fetch(`/api/papers/${paperId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title, authors, publication_year: year, doi, abstract,
                user: "Admin Researcher"
            })
        });

        if (res.ok) {
            showToast("Paper details updated successfully! Reloading...", "success");
            closeEditModal();
            setTimeout(() => window.location.reload(), 600);
        } else {
            showToast("Failed to update paper details.", "error");
        }
    } catch (e) {
        showToast("Error updating paper: " + e.message, "error");
    }
}

async function addTagInline(paperId) {
    const input = document.getElementById("inlineNewTagInput");
    const tagName = input.value.trim();
    if (!tagName) return;

    try {
        const res = await fetch(`/api/papers/${paperId}/tags`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: tagName, user: "Admin Researcher" })
        });

        if (res.ok) {
            showToast(`Tag '#${tagName}' added.`, "success");
            input.value = "";
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast("Failed to add tag.", "error");
        }
    } catch (e) {
        showToast("Error adding tag: " + e.message, "error");
    }
}

async function removeTag(paperId, tagId, tagName) {
    if (!confirm(`Remove tag '#${tagName}' from this paper?`)) return;

    try {
        const res = await fetch(`/api/papers/${paperId}/tags/${tagId}?user=Admin+Researcher`, {
            method: "DELETE"
        });

        if (res.ok) {
            showToast(`Tag '#${tagName}' removed.`, "info");
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast("Failed to remove tag.", "error");
        }
    } catch (e) {
        showToast("Error removing tag: " + e.message, "error");
    }
}

function toggleAddRefForm() {
    const form = document.getElementById("addRefForm");
    if (!form) return;
    form.style.display = form.style.display === "none" ? "block" : "none";
}

async function submitNewReference(paperId) {
    const rawText = document.getElementById("newRefRawText").value.trim();
    const title = document.getElementById("newRefTitle").value.trim();
    const year = document.getElementById("newRefYear").value.trim();

    if (!rawText) {
        showToast("Citation text is required.", "error");
        return;
    }

    try {
        const res = await fetch(`/api/papers/${paperId}/references`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                raw_text: rawText,
                title: title || null,
                year: year ? parseInt(year) : null,
                user: "Admin Researcher"
            })
        });

        if (res.ok) {
            showToast("Citation reference added successfully.", "success");
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast("Failed to add reference.", "error");
        }
    } catch (e) {
        showToast("Error adding reference: " + e.message, "error");
    }
}

async function deleteReference(paperId, refId) {
    if (!confirm("Are you sure you want to delete this citation reference?")) return;

    try {
        const res = await fetch(`/api/papers/${paperId}/references/${refId}?user=Admin+Researcher`, {
            method: "DELETE"
        });

        if (res.ok) {
            showToast("Reference removed.", "info");
            setTimeout(() => window.location.reload(), 500);
        } else {
            showToast("Failed to remove reference.", "error");
        }
    } catch (e) {
        showToast("Error deleting reference: " + e.message, "error");
    }
}

async function reextractCurrentPaper(paperId) {
    if (!confirm("Re-run the extraction engine on this paper? This will re-parse the PDF text, metadata, topics, and references.")) return;

    showToast("Re-extracting document content...", "info", 5000);

    try {
        const res = await fetch(`/api/papers/${paperId}/reextract`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: "Admin Researcher" })
        });

        if (res.ok) {
            showToast("Paper re-extracted and refreshed successfully!", "success");
            setTimeout(() => window.location.reload(), 600);
        } else {
            showToast("Failed to re-extract paper.", "error");
        }
    } catch (e) {
        showToast("Error during re-extraction: " + e.message, "error");
    }
}

async function deleteCurrentPaper(paperId, paperTitle) {
    if (!confirm(`Are you sure you want to delete "${paperTitle}"?\nThis cannot be undone.`)) return;

    try {
        const res = await fetch(`/api/papers/${paperId}?user=Admin+Researcher`, {
            method: "DELETE"
        });

        if (res.ok) {
            alert(`Paper "${paperTitle}" has been deleted.`);
            window.location.href = "/";
        } else {
            showToast("Failed to delete paper.", "error");
        }
    } catch (e) {
        showToast("Error deleting paper: " + e.message, "error");
    }
}
