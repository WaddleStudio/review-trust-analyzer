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

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Loading State
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
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
            alert('An error occurred while analyzing the review.');
        } finally {
            // Reset UI
            submitBtn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    });

    function displayResult(data) {
        resultCard.classList.remove('hidden');

        // Trust Score is 0-1. 
        // 1.0 = Trustworthy, 0.0 = Suspicious? 
        // Wait, the model outputs "trust_score" as probability of class 0 (Not Suspicious).
        // So High Trust Score = Good.

        const percentage = Math.round(data.trust_score * 100);
        const isSuspicious = data.is_suspicious;

        // Animate Circle
        // Stroke-dasharray: value, 100
        scoreCircle.setAttribute('stroke-dasharray', `${percentage}, 100`);
        scoreText.textContent = `${percentage}%`;

        // Color Coding
        if (percentage >= 80) {
            scoreCircle.style.stroke = 'var(--success)';
            verdict.textContent = 'Trustworthy';
            verdict.style.color = 'var(--success)';
        } else if (percentage >= 50) {
            scoreCircle.style.stroke = 'var(--warning)';
            verdict.textContent = 'Moderate Risk';
            verdict.style.color = 'var(--warning)';
        } else {
            scoreCircle.style.stroke = 'var(--danger)';
            verdict.textContent = 'Suspicious';
            verdict.style.color = 'var(--danger)';
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
            // Color code sentiment
            if (data.sentiment_score > 0.5) sentimentElem.style.color = 'var(--success)';
            else if (data.sentiment_score < -0.5) sentimentElem.style.color = 'var(--danger)';
            else sentimentElem.style.color = 'var(--text-muted)';
        }
    }
});

// Tab Switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');

    if (tab === 'single') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('analyzeForm').style.display = 'block';
        document.getElementById('analyzeForm').classList.add('active');
        document.getElementById('resultCard').classList.add('hidden');
        document.getElementById('batchResultCard').classList.add('hidden');
    } else {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('batchForm').style.display = 'block';
        document.getElementById('batchForm').classList.add('active');
        document.getElementById('resultCard').classList.add('hidden');
        document.getElementById('batchResultCard').classList.add('hidden');
    }
}

// Batch Form Submission
document.getElementById('batchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files[0]) {
        alert("Please select a CSV file.");
        return;
    }

    const btn = document.getElementById('batchSubmitBtn');
    const loader = btn.querySelector('.loader');
    const btnText = btn.querySelector('.btn-text');

    btn.disabled = true;
    loader.style.display = 'inline-block';
    btnText.style.opacity = '0.5';

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
            // Pass data to modal. Note: data might not have rating/platform if not returned by backend.
            // But we can assume defaults or update backend to return them.
            // For now, let's use what we have.
            viewBtn.onclick = () => openModal(res, index + 1);
            tdText.appendChild(viewBtn);
            tr.appendChild(tdText);

            // Score
            const tdScore = document.createElement('td');
            const percentage = Math.round(res.trust_score * 100);
            tdScore.textContent = `${percentage}%`;
            if (res.trust_score >= 0.8) tdScore.style.color = 'var(--success)';
            else if (res.trust_score >= 0.5) tdScore.style.color = 'var(--warning)';
            else tdScore.style.color = 'var(--danger)';
            tr.appendChild(tdScore);

            // Verdict
            const tdVerdict = document.createElement('td');
            if (res.is_suspicious) {
                tdVerdict.textContent = "Suspicious";
                tdVerdict.className = "verdict-suspicious";
                tdVerdict.style.color = 'var(--danger)';
            } else if (res.trust_score < 0.6) {
                tdVerdict.textContent = "Moderate Risk";
                tdVerdict.className = "verdict-moderate";
                tdVerdict.style.color = 'var(--warning)';
            } else {
                tdVerdict.textContent = "Trustworthy";
                tdVerdict.className = "verdict-trustworthy";
                tdVerdict.style.color = 'var(--success)';
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
        alert('An error occurred while analyzing batch.');
    } finally {
        btn.disabled = false;
        loader.style.display = 'none';
        btnText.style.opacity = '1';
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

    modal.style.display = "block";
}

if (span) {
    span.onclick = function () {
        modal.style.display = "none";
    }
}

window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}
