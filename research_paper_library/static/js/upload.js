/* ==========================================================================
   ScholarGraph - File Upload & Drag-and-Drop Handler
   ========================================================================== */

let selectedFiles = [];

document.addEventListener("DOMContentLoaded", () => {
    initDropzone();
});

function openUploadModal() {
    const modal = document.getElementById("uploadModal");
    if (modal) {
        modal.style.display = "flex";
        clearSelectedFiles();
        document.getElementById("uploadResults").style.display = "none";
        document.getElementById("uploadProgress").style.display = "none";
    }
}

function closeUploadModal() {
    const modal = document.getElementById("uploadModal");
    if (modal) modal.style.display = "none";
}

function initDropzone() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");

    if (!dropzone || !fileInput) return;

    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        }, false);
    });

    dropzone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener("change", (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showToast(`Skipped '${file.name}': Only PDF files are supported.`, "error");
            continue;
        }
        if (file.size > 32 * 1024 * 1024) {
            showToast(`Skipped '${file.name}': Exceeds 32MB limit.`, "error");
            continue;
        }

        // Avoid adding duplicate in queue
        if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    }

    renderSelectedFiles();
}

function renderSelectedFiles() {
    const container = document.getElementById("selectedFilesContainer");
    const list = document.getElementById("fileList");
    const countSpan = document.getElementById("selectedCount");
    const uploadBtn = document.getElementById("startUploadBtn");

    if (!container || !list) return;

    if (selectedFiles.length === 0) {
        container.style.display = "none";
        if (uploadBtn) uploadBtn.disabled = true;
        return;
    }

    container.style.display = "block";
    if (countSpan) countSpan.innerText = selectedFiles.length;
    if (uploadBtn) uploadBtn.disabled = false;

    list.innerHTML = "";
    selectedFiles.forEach((file, index) => {
        const li = document.createElement("li");
        li.className = "file-item";
        li.innerHTML = `
            <div class="file-item-info">
                <i class="fa-solid fa-file-pdf text-danger"></i>
                <span class="file-item-name">${file.name}</span>
                <span class="file-item-size">(${(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <button type="button" class="file-remove-btn" onclick="removeSelectedFile(${index})">&times;</button>
        `;
        list.appendChild(li);
    });
}

function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
}

function clearSelectedFiles() {
    selectedFiles = [];
    renderSelectedFiles();
    const input = document.getElementById("fileInput");
    if (input) input.value = "";
}

async function submitFiles() {
    if (selectedFiles.length === 0) return;

    const progressBox = document.getElementById("uploadProgress");
    const progressBar = document.getElementById("progressBarFill");
    const progressText = document.getElementById("uploadStatusText");
    const resultsBox = document.getElementById("uploadResults");
    const resultsList = document.getElementById("resultsList");
    const uploadBtn = document.getElementById("startUploadBtn");

    if (uploadBtn) uploadBtn.disabled = true;
    if (progressBox) progressBox.style.display = "block";
    if (progressBar) progressBar.style.width = "30%";
    if (progressText) progressText.innerText = "Parsing PDFs and extracting paper metadata...";

    const formData = new FormData();
    selectedFiles.forEach(f => formData.append("files", f));
    formData.append("user", "Admin Researcher");

    try {
        const response = await fetch("/api/papers/upload", {
            method: "POST",
            body: formData
        });

        if (progressBar) progressBar.style.width = "100%";

        const data = await response.json();
        if (progressBox) progressBox.style.display = "none";
        if (resultsBox) resultsBox.style.display = "block";

        resultsList.innerHTML = "";
        let successCount = 0;

        (data.results || []).forEach(res => {
            const div = document.createElement("div");
            div.className = "upload-result-item";

            if (res.status === "success") {
                successCount++;
                div.innerHTML = `
                    <div class="res-badge res-success"><i class="fa-solid fa-check"></i> Indexed</div>
                    <div class="res-details">
                        <strong>${res.title}</strong>
                        <div class="res-sub">Authors: ${res.authors.join(", ")}</div>
                        <div class="res-tags">${res.topics.map(t => `<span class="badge badge-neutral">#${t}</span>`).join(" ")}</div>
                    </div>
                `;
            } else if (res.status === "duplicate") {
                div.innerHTML = `
                    <div class="res-badge res-warning"><i class="fa-solid fa-triangle-exclamation"></i> Duplicate</div>
                    <div class="res-details">
                        <strong>${res.filename}</strong>
                        <div class="res-sub">${res.message}</div>
                        <a href="/paper/${res.existing_id}" class="btn-link">View Existing Paper &rarr;</a>
                    </div>
                `;
            } else {
                div.innerHTML = `
                    <div class="res-badge res-danger"><i class="fa-solid fa-xmark"></i> Failed</div>
                    <div class="res-details">
                        <strong>${res.filename}</strong>
                        <div class="res-sub text-danger">${res.message}</div>
                    </div>
                `;
            }
            resultsList.appendChild(div);
        });

        if (successCount > 0) {
            showToast(`Successfully indexed ${successCount} paper(s)!`, "success");
            loadDashboardStats();
            if (typeof fetchPapers === "function") fetchPapers();
        }

        clearSelectedFiles();

    } catch (e) {
        if (progressBox) progressBox.style.display = "none";
        showToast("Error processing upload: " + e.message, "error");
        if (uploadBtn) uploadBtn.disabled = false;
    }
}
