let selectedNodeId = null;
let activeSelectionId = null;

// Helper to set status message classes
function setStatus(element, msg, type) {
    element.textContent = msg;
    element.className = 'status-msg'; // Reset
    if (type) element.classList.add(`status-${type}`);
}

// --- 1. Upload Logic ---
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('pdf-upload');
const uploadStatus = document.getElementById('upload-status');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleUpload(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleUpload(e.target.files[0]);
    }
});

async function handleUpload(file) {
    setStatus(uploadStatus, 'UPLOADING AND PARSING DOCUMENT...', 'loading');
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/ingest', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            setStatus(uploadStatus, `DOCUMENT VERSION ${data.version} ACTIVE`, 'success');
        } else {
            setStatus(uploadStatus, `SYSTEM FAULT: ${data.detail}`, 'error');
        }
    } catch (err) {
        setStatus(uploadStatus, 'NETWORK EXCEPTION', 'error');
    }
}

// --- 2. Search Logic ---
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const searchResults = document.getElementById('search-results');

searchBtn.addEventListener('click', async () => {
    const q = searchInput.value.trim();
    if (!q) return;

    searchResults.innerHTML = '<li class="result-item mono-label">Querying database...</li>';
    try {
        const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
        const nodes = await res.json();
        
        searchResults.innerHTML = '';
        if (nodes.length === 0) {
            searchResults.innerHTML = '<li class="result-item mono-label">No records found.</li>';
            return;
        }

        nodes.forEach(node => {
            const li = document.createElement('li');
            li.className = 'result-item';
            
            const textSpan = document.createElement('span');
            textSpan.className = 'display-font';
            textSpan.textContent = node.heading;
            
            const idSpan = document.createElement('span');
            idSpan.className = 'mono-label';
            idSpan.textContent = node.logical_node_id;
            
            li.appendChild(textSpan);
            li.appendChild(idSpan);
            
            li.addEventListener('click', () => {
                document.querySelectorAll('.result-item').forEach(el => el.classList.remove('selected'));
                li.classList.add('selected');
                selectedNodeId = node.id;
                document.getElementById('create-selection-btn').disabled = false;
            });
            searchResults.appendChild(li);
        });
    } catch (err) {
        searchResults.innerHTML = '<li class="result-item mono-label status-error">Fetch Error</li>';
    }
});

// --- 3. Selection Logic ---
const createSelBtn = document.getElementById('create-selection-btn');
const selNameInput = document.getElementById('selection-name');
const selStatus = document.getElementById('selection-status');
const genBtn = document.getElementById('generate-btn');
const staleBtn = document.getElementById('check-staleness-btn');

createSelBtn.addEventListener('click', async () => {
    if (!selectedNodeId) return;
    const name = selNameInput.value.trim() || 'Custom Selection';

    setStatus(selStatus, 'INITIALIZING SELECTION...', 'loading');
    try {
        const res = await fetch('/selections', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, node_ids: [selectedNodeId]})
        });
        const data = await res.json();
        if (res.ok) {
            activeSelectionId = data.id;
            setStatus(selStatus, `SELECTION ${data.id} REGISTERED`, 'success');
            genBtn.disabled = false;
            staleBtn.disabled = false;
        }
    } catch (err) {
        setStatus(selStatus, 'INITIALIZATION FAULT', 'error');
    }
});

// --- 4. Generation & Staleness Logic ---
const testCasesContainer = document.getElementById('test-cases-container');
const genStatus = document.getElementById('generation-status');

genBtn.addEventListener('click', async () => {
    if (!activeSelectionId) return;
    genBtn.disabled = true;
    setStatus(genStatus, 'CONTACTING GROQ API (LLAMA-3.3-70B)', 'loading');
    
    try {
        const res = await fetch(`/generate?selection_id=${activeSelectionId}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            setStatus(genStatus, `GENERATION ${data.generation_status.toUpperCase()}`, 'success');
            renderTestCases([data]); 
        } else {
            setStatus(genStatus, 'GENERATION FAILED', 'error');
        }
    } catch (err) {
        setStatus(genStatus, 'API FAULT', 'error');
    } finally {
        genBtn.disabled = false;
    }
});

staleBtn.addEventListener('click', async () => {
    if (!activeSelectionId) return;
    setStatus(genStatus, 'AUDITING STALENESS', 'loading');
    try {
        const res = await fetch(`/test-cases?selection_id=${activeSelectionId}`);
        const data = await res.json();
        if (res.ok && data.length > 0) {
            setStatus(genStatus, 'AUDIT COMPLETE', 'success');
            renderTestCases(data);
        } else {
            setStatus(genStatus, 'NO GENERATIONS FOUND', 'error');
        }
    } catch (err) {
        setStatus(genStatus, 'AUDIT FAULT', 'error');
    }
});

function renderTestCases(generations) {
    testCasesContainer.innerHTML = '';
    
    const gen = generations[generations.length - 1];
    const isStale = gen.staleness ? gen.staleness.is_stale : false;
    
    // Stale Alert using inversion and heavy lines (no colors)
    if (isStale) {
        const staleAlert = document.createElement('div');
        staleAlert.className = 'stale-state';
        
        const warning = document.createElement('h3');
        warning.className = 'display-font';
        warning.style.fontSize = '2.5rem';
        warning.textContent = 'REQUIREMENT ALTERED';
        
        const sub = document.createElement('p');
        sub.className = 'mono-label';
        sub.style.color = 'inherit';
        sub.textContent = 'TEST CASES BELOW MAY BE INVALID DUE TO UPSTREAM DOCUMENT MODIFICATION';
        
        staleAlert.appendChild(warning);
        staleAlert.appendChild(sub);
        
        const diffText = gen.staleness.details.map(d => d.diff).join('\n');
        if (diffText) {
            const diffBox = document.createElement('div');
            diffBox.className = 'diff-box';
            diffBox.textContent = diffText;
            staleAlert.appendChild(diffBox);
        }
        
        testCasesContainer.appendChild(staleAlert);
    }

    gen.parsed_test_cases.forEach(tc => {
        const card = document.createElement('div');
        card.className = `test-card ${isStale ? 'stale-card-context' : ''}`;
        
        let html = `<h3>${tc.title} ${isStale ? '<span class="stale-badge">[ STALE ]</span>' : ''}</h3>`;
        html += `<ul>${tc.steps.map(s => `<li>${s}</li>`).join('')}</ul>`;
        html += `<div class="expected-result">Expected: ${tc.expected_result}</div>`;
        
        card.innerHTML = html;
        testCasesContainer.appendChild(card);
    });
}
