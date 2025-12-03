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
    }
});
