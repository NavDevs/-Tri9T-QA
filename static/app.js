let selectedNodeId = null;
let activeSelectionId = null;

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
    uploadStatus.textContent = 'Uploading and parsing...';
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/ingest', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            uploadStatus.textContent = `Success! Document Version ${data.version} active.`;
            uploadStatus.style.color = 'var(--success)';
        } else {
            uploadStatus.textContent = `Error: ${data.detail}`;
            uploadStatus.style.color = 'var(--danger)';
        }
    } catch (err) {
        uploadStatus.textContent = 'Network error.';
    }
}

// --- 2. Search Logic ---
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const searchResults = document.getElementById('search-results');

searchBtn.addEventListener('click', async () => {
    const q = searchInput.value.trim();
    if (!q) return;

    searchResults.innerHTML = '<li>Searching...</li>';
    try {
        const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
        const nodes = await res.json();
        
        searchResults.innerHTML = '';
        if (nodes.length === 0) {
            searchResults.innerHTML = '<li>No results found.</li>';
            return;
        }

        nodes.forEach(node => {
            const li = document.createElement('li');
            li.className = 'result-item';
            li.textContent = node.heading;
            li.addEventListener('click', () => {
                document.querySelectorAll('.result-item').forEach(el => el.classList.remove('selected'));
                li.classList.add('selected');
                selectedNodeId = node.id;
                document.getElementById('create-selection-btn').disabled = false;
            });
            searchResults.appendChild(li);
        });
    } catch (err) {
        searchResults.innerHTML = '<li>Error fetching results.</li>';
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

    selStatus.textContent = 'Creating...';
    try {
        const res = await fetch('/selections', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, node_ids: [selectedNodeId]})
        });
        const data = await res.json();
        if (res.ok) {
            activeSelectionId = data.id;
            selStatus.textContent = `Selection #${data.id} created successfully!`;
            selStatus.style.color = 'var(--success)';
            genBtn.disabled = false;
            staleBtn.disabled = false;
        }
    } catch (err) {
        selStatus.textContent = 'Error creating selection.';
    }
});

// --- 4. Generation & Staleness Logic ---
const testCasesContainer = document.getElementById('test-cases-container');
const genStatus = document.getElementById('generation-status');

genBtn.addEventListener('click', async () => {
    if (!activeSelectionId) return;
    genBtn.disabled = true;
    genStatus.textContent = 'Connecting to Groq API... this takes a few seconds.';
    genStatus.style.color = 'var(--text-secondary)';
    
    try {
        const res = await fetch(`/generate?selection_id=${activeSelectionId}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            genStatus.textContent = `Generated successfully (Status: ${data.generation_status})`;
            genStatus.style.color = 'var(--success)';
            renderTestCases([data]); // wrap in array as check_staleness returns array
        } else {
            genStatus.textContent = 'Generation failed.';
            genStatus.style.color = 'var(--danger)';
        }
    } catch (err) {
        genStatus.textContent = 'API Error.';
    } finally {
        genBtn.disabled = false;
    }
});

staleBtn.addEventListener('click', async () => {
    if (!activeSelectionId) return;
    genStatus.textContent = 'Checking staleness against latest document...';
    try {
        const res = await fetch(`/test-cases?selection_id=${activeSelectionId}`);
        const data = await res.json();
        if (res.ok && data.length > 0) {
            genStatus.textContent = 'Staleness fetched.';
            renderTestCases(data);
        } else {
            genStatus.textContent = 'No generations found for this selection.';
        }
    } catch (err) {
        genStatus.textContent = 'Error fetching test cases.';
    }
});

function renderTestCases(generations) {
    testCasesContainer.innerHTML = '';
    
    // Display the most recent generation
    const gen = generations[generations.length - 1];
    const isStale = gen.staleness ? gen.staleness.is_stale : false;
    
    if (isStale) {
        const staleAlert = document.createElement('div');
        staleAlert.className = 'status-msg';
        staleAlert.style.color = 'var(--danger)';
        staleAlert.style.fontWeight = 'bold';
        staleAlert.style.marginBottom = '1rem';
        staleAlert.textContent = '⚠️ WARNING: Underlying requirement has changed! Test cases may be invalid.';
        testCasesContainer.appendChild(staleAlert);
        
        // Show diff
        const diffText = gen.staleness.details.map(d => d.diff).join('\n');
        if (diffText) {
            const diffBox = document.createElement('div');
            diffBox.className = 'diff-box';
            diffBox.textContent = diffText;
            testCasesContainer.appendChild(diffBox);
        }
    }

    gen.parsed_test_cases.forEach(tc => {
        const card = document.createElement('div');
        card.className = `card ${isStale ? 'stale' : ''}`;
        
        let html = `<h3>${tc.title} ${isStale ? '<span class="stale-badge">STALE</span>' : ''}</h3>`;
        html += `<ul>${tc.steps.map(s => `<li>${s}</li>`).join('')}</ul>`;
        html += `<div class="expected">Expected: ${tc.expected_result}</div>`;
        
        card.innerHTML = html;
        testCasesContainer.appendChild(card);
    });
}
