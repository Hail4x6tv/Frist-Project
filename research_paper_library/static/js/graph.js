/* ==========================================================================
   ScholarGraph - Vis.js Interactive Knowledge Graph Controller
   ========================================================================== */

let network = null;
let rawNodes = [];
let rawEdges = [];
let nodesDataSet = null;
let edgesDataSet = null;
let nodesDataView = null;
let edgesDataView = null;
let physicsEnabled = true;

document.addEventListener("DOMContentLoaded", () => {
    initKnowledgeGraph();
});

async function initKnowledgeGraph() {
    const container = document.getElementById("visNetworkContainer");
    const loading = document.getElementById("graphLoadingIndicator");

    try {
        const response = await fetch("/api/graph/data");
        const data = await response.json();

        rawNodes = data.nodes || [];
        rawEdges = data.edges || [];

        if (loading) loading.style.display = "none";

        if (rawNodes.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding-top: 100px;">
                    <div class="empty-icon"><i class="fa-solid fa-circle-nodes"></i></div>
                    <h3>Knowledge Graph is Empty</h3>
                    <p class="text-secondary mt-2 mb-4">No papers or connections have been indexed yet.</p>
                    <button class="btn btn-primary" onclick="loadSamplePapersPrompt()">
                        <i class="fa-solid fa-flask"></i> Import Sample Papers to Explore Graph
                    </button>
                </div>
            `;
            return;
        }

        // Initialize Vis DataSets
        nodesDataSet = new vis.DataSet(rawNodes);
        edgesDataSet = new vis.DataSet(rawEdges);

        // DataViews for filtering
        nodesDataView = new vis.DataView(nodesDataSet, {
            filter: filterNodesRule
        });

        edgesDataView = new vis.DataView(edgesDataSet, {
            filter: filterEdgesRule
        });

        // Vis.js Network Configuration
        const options = {
            nodes: {
                shape: "dot",
                size: 20,
                borderWidth: 2,
                shadow: { enabled: true, color: "rgba(0,0,0,0.1)", size: 6, x: 2, y: 2 },
                font: { face: "Inter, sans-serif", size: 12, color: "#0f172a" }
            },
            edges: {
                width: 1.5,
                smooth: {
                    type: "continuous",
                    roundness: 0.2
                },
                shadow: { enabled: false }
            },
            physics: {
                enabled: true,
                solver: "forceAtlas2Based",
                forceAtlas2Based: {
                    gravitationalConstant: -45,
                    centralGravity: 0.015,
                    springLength: 90,
                    springConstant: 0.08,
                    damping: 0.4
                },
                stabilization: {
                    iterations: 120,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
                zoomView: true,
                dragView: true,
                dragNodes: true,
                hideEdgesOnDrag: false
            }
        };

        network = new vis.Network(container, { nodes: nodesDataView, edges: edgesDataView }, options);

        // Handle Click Event
        network.on("click", (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const node = nodesDataSet.get(nodeId);
                openNodeInspector(node);
            } else {
                closeInspector();
            }
        });

        // Physics stabilization settled
        network.once("stabilizationIterationsDone", () => {
            // Settle smoothly
            setTimeout(() => {
                if (physicsEnabled) {
                    network.setOptions({ physics: { enabled: false } });
                    physicsEnabled = false;
                    updatePhysicsBtnUI();
                }
            }, 1000);
        });

    } catch (e) {
        if (loading) loading.style.display = "none";
        container.innerHTML = `<div class="card p-4 text-center text-danger">Error rendering knowledge graph: ${e.message}</div>`;
    }
}

// Node and Edge Filtering Rules
function filterNodesRule(node) {
    const showPapers = document.getElementById("togglePapers")?.querySelector("input")?.checked ?? true;
    const showAuthors = document.getElementById("toggleAuthors")?.querySelector("input")?.checked ?? true;
    const showTopics = document.getElementById("toggleTopics")?.querySelector("input")?.checked ?? true;

    if (node.type === "paper" && !showPapers) return false;
    if (node.type === "author" && !showAuthors) return false;
    if (node.type === "topic" && !showTopics) return false;

    return true;
}

function filterEdgesRule(edge) {
    const showCitations = document.getElementById("toggleCitations")?.querySelector("input")?.checked ?? true;
    const showCoauthors = document.getElementById("toggleCoauthors")?.querySelector("input")?.checked ?? true;

    if (edge.type === "citation" && !showCitations) return false;
    if (edge.type === "coauthorship" && !showCoauthors) return false;

    return true;
}

function updateGraphVisibility() {
    // Update chip toggle styling
    const toggles = document.querySelectorAll(".chip-toggle");
    toggles.forEach(t => {
        const input = t.querySelector("input");
        if (input && input.checked) {
            t.classList.add("active");
        } else {
            t.classList.remove("active");
        }
    });

    if (nodesDataView) nodesDataView.refresh();
    if (edgesDataView) edgesDataView.refresh();
}

function togglePhysics() {
    if (!network) return;
    physicsEnabled = !physicsEnabled;
    network.setOptions({ physics: { enabled: physicsEnabled } });
    updatePhysicsBtnUI();
}

function updatePhysicsBtnUI() {
    const text = document.getElementById("physicsStatusText");
    const btn = document.getElementById("physicsToggleBtn");
    if (!text || !btn) return;

    if (physicsEnabled) {
        text.innerText = "Freeze Physics";
        btn.classList.add("btn-primary");
        btn.classList.remove("btn-secondary");
    } else {
        text.innerText = "Unfreeze Physics";
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-secondary");
    }
}

function fitGraphView() {
    if (network) {
        network.fit({
            animation: { duration: 600, easingFunction: "easeInOutQuad" }
        });
    }
}

// Node Inspector Sidebar
function openNodeInspector(node) {
    const inspector = document.getElementById("nodeInspector");
    const badge = document.getElementById("inspectorTypeBadge");
    const body = document.getElementById("inspectorBody");
    if (!inspector || !node) return;

    inspector.style.display = "flex";
    badge.innerText = node.type.toUpperCase();

    if (node.type === "paper") {
        badge.style.background = "#2563eb";
        renderPaperInspector(node, body);
    } else if (node.type === "author") {
        badge.style.background = "#10b981";
        renderAuthorInspector(node, body);
    } else if (node.type === "topic") {
        badge.style.background = "#f59e0b";
        renderTopicInspector(node, body);
    }
}

function renderPaperInspector(node, body) {
    const connectedEdges = network.getConnectedEdges(node.id);
    const connectedNodeIds = network.getConnectedNodes(node.id);

    // Identify connected authors, topics, and citing papers
    let authors = [];
    let topics = [];
    let citations = [];

    connectedNodeIds.forEach(cId => {
        const cNode = nodesDataSet.get(cId);
        if (!cNode) return;
        if (cNode.type === "author") authors.push(cNode);
        if (cNode.type === "topic") topics.push(cNode);
        if (cNode.type === "paper") citations.push(cNode);
    });

    body.innerHTML = `
        <div class="inspector-node-title">${escapeHtml(node.full_title || node.label)}</div>
        
        <div class="inspector-meta-row">
            <span><i class="fa-solid fa-calendar text-primary"></i> ${node.year}</span>
            <span><i class="fa-solid fa-quote-left text-danger"></i> ${node.citations} Citation(s) in Library</span>
        </div>

        <div style="display: flex; gap: 8px; margin-top: 4px;">
            <a href="/paper/${node.entity_id}" class="btn btn-primary btn-sm" style="flex: 1;">
                <i class="fa-solid fa-eye"></i> View Paper Details
            </a>
        </div>

        <div>
            <div class="inspector-section-label">Authors (${authors.length}):</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${authors.map(a => `
                    <button class="author-chip" onclick="focusOnNode('${a.id}')">
                        <i class="fa-solid fa-user"></i> ${escapeHtml(a.label)}
                    </button>
                `).join("")}
            </div>
        </div>

        <div>
            <div class="inspector-section-label">Related Topics (${topics.length}):</div>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                ${topics.map(t => `
                    <button class="tag-pill" onclick="focusOnNode('${t.id}')">
                        #${escapeHtml(t.label)}
                    </button>
                `).join("")}
            </div>
        </div>

        ${citations.length > 0 ? `
            <div>
                <div class="inspector-section-label">Cross-Citations in Library (${citations.length}):</div>
                <ul class="inspector-connected-list">
                    ${citations.map(c => `
                        <li class="inspector-connected-item" onclick="focusOnNode('${c.id}')" style="cursor: pointer;">
                            <i class="fa-solid fa-link text-danger"></i>
                            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(c.full_title || c.label)}</span>
                        </li>
                    `).join("")}
                </ul>
            </div>
        ` : ''}
    `;
}

function renderAuthorInspector(node, body) {
    const connectedNodeIds = network.getConnectedNodes(node.id);
    let papers = [];
    let coauthors = [];

    connectedNodeIds.forEach(cId => {
        const cNode = nodesDataSet.get(cId);
        if (!cNode) return;
        if (cNode.type === "paper") papers.push(cNode);
        if (cNode.type === "author") coauthors.push(cNode);
    });

    body.innerHTML = `
        <div class="inspector-node-title">${escapeHtml(node.label)}</div>
        <div class="inspector-meta-row">
            <span><i class="fa-solid fa-file-lines text-green"></i> ${papers.length} Papers Indexed</span>
            <span><i class="fa-solid fa-user-group text-primary"></i> ${coauthors.length} Co-authors</span>
        </div>

        <div>
            <div class="inspector-section-label">Authored Papers:</div>
            <ul class="inspector-connected-list">
                ${papers.map(p => `
                    <li class="inspector-connected-item" onclick="focusOnNode('${p.id}')" style="cursor: pointer;">
                        <i class="fa-solid fa-file text-primary"></i>
                        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(p.full_title || p.label)}</span>
                    </li>
                `).join("")}
            </ul>
        </div>

        ${coauthors.length > 0 ? `
            <div>
                <div class="inspector-section-label">Co-Authors:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    ${coauthors.map(ca => `
                        <button class="author-chip" onclick="focusOnNode('${ca.id}')">
                            <i class="fa-solid fa-user-pen"></i> ${escapeHtml(ca.label)}
                        </button>
                    `).join("")}
                </div>
            </div>
        ` : ''}

        <div style="margin-top: 10px;">
            <a href="/?author=${encodeURIComponent(node.label)}" class="btn btn-secondary btn-sm" style="width: 100%;">
                <i class="fa-solid fa-list"></i> Filter Library by this Author
            </a>
        </div>
    `;
}

function renderTopicInspector(node, body) {
    const connectedNodeIds = network.getConnectedNodes(node.id);
    let papers = [];

    connectedNodeIds.forEach(cId => {
        const cNode = nodesDataSet.get(cId);
        if (cNode && cNode.type === "paper") papers.push(cNode);
    });

    body.innerHTML = `
        <div class="inspector-node-title">#${escapeHtml(node.label)}</div>
        <div class="inspector-meta-row">
            <span><i class="fa-solid fa-tag text-amber"></i> ${papers.length} Tagged Research Papers</span>
        </div>

        <div>
            <div class="inspector-section-label">Tagged Papers:</div>
            <ul class="inspector-connected-list">
                ${papers.map(p => `
                    <li class="inspector-connected-item" onclick="focusOnNode('${p.id}')" style="cursor: pointer;">
                        <i class="fa-solid fa-file text-primary"></i>
                        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(p.full_title || p.label)}</span>
                    </li>
                `).join("")}
            </ul>
        </div>

        <div style="margin-top: 10px;">
            <a href="/?topic=${encodeURIComponent(node.label)}" class="btn btn-secondary btn-sm" style="width: 100%;">
                <i class="fa-solid fa-list"></i> Filter Library by this Topic
            </a>
        </div>
    `;
}

function closeInspector() {
    const inspector = document.getElementById("nodeInspector");
    if (inspector) inspector.style.display = "none";
}

function focusOnNode(nodeId) {
    if (!network) return;
    network.selectNodes([nodeId]);
    network.focus(nodeId, {
        scale: 1.35,
        animation: { duration: 600, easingFunction: "easeInOutQuad" }
    });
    const node = nodesDataSet.get(nodeId);
    if (node) openNodeInspector(node);
}

// Search to Focus Dropdown
function filterGraphSearch(e) {
    const input = document.getElementById("graphSearchInput");
    const resultsBox = document.getElementById("graphSearchResults");
    const query = input.value.trim().toLowerCase();

    if (!query || !rawNodes.length) {
        if (resultsBox) resultsBox.style.display = "none";
        return;
    }

    const matches = rawNodes.filter(n => {
        const label = (n.full_title || n.label || "").toLowerCase();
        return label.includes(query);
    }).slice(0, 8);

    if (matches.length === 0) {
        resultsBox.innerHTML = '<div class="graph-search-item text-muted">No nodes found.</div>';
        resultsBox.style.display = "block";
        return;
    }

    resultsBox.innerHTML = "";
    matches.forEach(m => {
        const div = document.createElement("div");
        div.className = "graph-search-item";

        let icon = "fa-file text-primary";
        if (m.type === "author") icon = "fa-user text-success";
        if (m.type === "topic") icon = "fa-tag text-amber";

        div.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${escapeHtml(m.full_title || m.label)}
            </span>
        `;
        div.onclick = () => {
            focusOnNode(m.id);
            resultsBox.style.display = "none";
            input.value = m.full_title || m.label;
        };
        resultsBox.appendChild(div);
    });

    resultsBox.style.display = "block";
}

// Export Graph as PNG Image
function exportGraphImage() {
    const container = document.getElementById("visNetworkContainer");
    const canvas = container.querySelector("canvas");
    if (!canvas) {
        showToast("No active canvas to export.", "error");
        return;
    }

    const image = canvas.toDataURL("image/png");
    const link = document.createElement("a");
    link.href = image;
    link.download = "scholargraph_knowledge_graph.png";
    link.click();
    showToast("Knowledge graph exported as PNG image.", "success");
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
