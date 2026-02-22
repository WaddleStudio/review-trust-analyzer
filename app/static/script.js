// Toast notifications (global — used by both DOMContentLoaded and batch form handlers)
function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('analyzeForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');
    const resultCard = document.getElementById('resultCard');
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreText = document.getElementById('scoreText');
    const verdict = document.getElementById('verdict');
    const reasonsList = document.getElementById('reasonsList');

    // Fetch API Usage
    async function fetchApiUsage() {
        try {
            const resp = await fetch('/api/serpapi/usage');
            const data = await resp.json();
            const creditsElem = document.getElementById('api-credits');
            if (creditsElem) {
                const limit = data.plan_searches_left || data.searches_per_month || 0;
                creditsElem.textContent = limit;
                creditsElem.classList.toggle('text-danger', limit < 10);
            }
        } catch (e) {
            console.error(e);
            const creditsElem = document.getElementById('api-credits');
            if (creditsElem) creditsElem.textContent = 'Error';
        }
    }
    fetchApiUsage();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Loading State
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        resultCard.classList.add('hidden');

        // Gather Data
        const formData = new FormData(form);
        const data = {
            platform: formData.get('platform'),
            rating: parseInt(formData.get('rating')),
            user_id: formData.get('user_id'),
            text: formData.get('text')
        };

        try {
            const response = await fetch('/reviews/score', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error('API Request Failed');
            }

            const result = await response.json();
            displayResult(result);

        } catch (error) {
            console.error(error);
            showToast('An error occurred while analyzing the review.');
        } finally {
            // Reset UI
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

    function displayResult(data) {
        resultCard.classList.remove('hidden');

        const percentage = Math.round(data.trust_score * 100);

        // Animate Circle
        scoreCircle.setAttribute('stroke-dasharray', `${percentage}, 100`);
        scoreText.textContent = `${percentage}%`;

        // Color Coding (scoreCircle stroke stays inline — SVG presentation attribute)
        if (percentage >= 80) {
            scoreCircle.style.stroke = 'var(--success)';
            verdict.textContent = 'Trustworthy';
            verdict.className = 'text-success';
        } else if (percentage >= 50) {
            scoreCircle.style.stroke = 'var(--warning)';
            verdict.textContent = 'Moderate Risk';
            verdict.className = 'text-warning';
        } else {
            scoreCircle.style.stroke = 'var(--danger)';
            verdict.textContent = 'Suspicious';
            verdict.className = 'text-danger';
        }

        // Reasons
        reasonsList.innerHTML = '';
        if (data.reasons && data.reasons.length > 0) {
            data.reasons.forEach(reason => {
                const li = document.createElement('li');
                li.textContent = reason;
                reasonsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = "No specific suspicious patterns detected.";
            li.style.borderLeftColor = 'var(--success)';
            reasonsList.appendChild(li);
        }

        // Debug Info
        const sentimentElem = document.getElementById('sentimentScoreValue');
        if (sentimentElem) {
            sentimentElem.textContent = data.sentiment_score.toFixed(4);
            if (data.sentiment_score > 0.5) sentimentElem.className = 'text-success';
            else if (data.sentiment_score < -0.5) sentimentElem.className = 'text-danger';
            else sentimentElem.className = 'text-muted';
        }
    }
});

// View Switching
function switchTab(tab) {
    document.querySelectorAll('.nav-item[data-tab]').forEach(btn => {
        const isActive = btn.dataset.tab === tab;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-current', isActive ? 'true' : 'false');
    });
    document.getElementById('mainArea').dataset.view = tab;
    document.getElementById('resultCard').classList.add('hidden');
    document.getElementById('batchResultCard').classList.add('hidden');
}

// Batch Form Submission
document.getElementById('batchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files[0]) {
        showToast('Please select a CSV file.', 'info');
        return;
    }

    const btn = document.getElementById('batchSubmitBtn');
    const loader = btn.querySelector('.loader');
    const btnText = btn.querySelector('.btn-text');

    btn.disabled = true;
    loader.classList.remove('hidden');
    btnText.classList.add('hidden');

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch('/reviews/batch', {
            method: 'POST',
            body: formData
        });

        const results = await response.json();

        // Render Results
        const tbody = document.querySelector('#batchTable tbody');
        tbody.innerHTML = '';

        results.forEach((res, index) => {
            const tr = document.createElement('tr');

            // ID
            const tdId = document.createElement('td');
            tdId.textContent = index + 1;
            tr.appendChild(tdId);

            // Text Snippet (View Details Button)
            const tdText = document.createElement('td');
            const viewBtn = document.createElement('button');
            viewBtn.textContent = "View details";
            viewBtn.className = "view-details-btn";
            viewBtn.onclick = () => openModal(res, index + 1);
            tdText.appendChild(viewBtn);
            tr.appendChild(tdText);

            // Score
            const tdScore = document.createElement('td');
            const percentage = Math.round(res.trust_score * 100);
            tdScore.textContent = `${percentage}%`;
            if (res.trust_score >= 0.8) tdScore.className = 'text-success';
            else if (res.trust_score >= 0.5) tdScore.className = 'text-warning';
            else tdScore.className = 'text-danger';
            tr.appendChild(tdScore);

            // Verdict
            const tdVerdict = document.createElement('td');
            if (res.is_suspicious) {
                tdVerdict.textContent = "Suspicious";
                tdVerdict.className = 'verdict-suspicious text-danger';
            } else if (res.trust_score < 0.6) {
                tdVerdict.textContent = "Moderate Risk";
                tdVerdict.className = 'verdict-moderate text-warning';
            } else {
                tdVerdict.textContent = "Trustworthy";
                tdVerdict.className = 'verdict-trustworthy text-success';
            }
            tr.appendChild(tdVerdict);

            // Reasons
            const tdReasons = document.createElement('td');
            tdReasons.textContent = res.reasons.join(", ") || "None";
            tdReasons.style.fontSize = "0.85rem";
            tr.appendChild(tdReasons);

            tbody.appendChild(tr);
        });

        document.getElementById('batchResultCard').classList.remove('hidden');

    } catch (error) {
        console.error('Error:', error);
        showToast('An error occurred while analyzing batch.');
    } finally {
        btn.disabled = false;
        loader.classList.add('hidden');
        btnText.classList.remove('hidden');
    }
});

// Modal Logic
const modal = document.getElementById("reviewModal");
const span = document.getElementsByClassName("close-modal")[0];

function openModal(data, id) {
    document.getElementById("modalRating").textContent = "★".repeat(data.rating || 5);
    document.getElementById("modalPlatform").textContent = data.platform || "Google Maps";
    document.getElementById("modalText").textContent = data.text || "No content available.";
    document.getElementById("modalUserId").textContent = data.user_id || "Anonymous";

    modal.classList.add('open');
}

if (span) {
    span.onclick = () => modal.classList.remove('open');
}

window.addEventListener('click', e => {
    if (e.target === modal) modal.classList.remove('open');
});

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') modal.classList.remove('open');
});
