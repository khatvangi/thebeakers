// subscribe.js - handle subscription form

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('subscribe-form');
    const submitBtn = document.getElementById('submit-btn');
    const statusDiv = document.getElementById('status');

    // radio option styling
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach(option => {
        option.addEventListener('click', function() {
            radioOptions.forEach(o => o.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // checkbox option styling
    const checkboxOptions = document.querySelectorAll('.checkbox-option');
    checkboxOptions.forEach(option => {
        const checkbox = option.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', function() {
            option.classList.toggle('selected', this.checked);
        });
    });

    // form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // disable button
        submitBtn.disabled = true;
        submitBtn.textContent = 'Subscribing...';
        statusDiv.className = 'status';
        statusDiv.style.display = 'none';

        // collect form data
        const formData = new FormData(form);
        const email = formData.get('email');
        const cadence = formData.get('cadence');
        const consent = formData.get('consent');
        const honeypot = formData.get('website');

        // collect subjects
        const subjects = [];
        formData.getAll('subjects').forEach(s => subjects.push(s));

        // basic validation
        if (!email || !email.includes('@')) {
            showError('Please enter a valid email address.');
            return;
        }

        if (!consent) {
            showError('Please agree to receive emails.');
            return;
        }

        // prepare payload
        const payload = {
            email: email,
            cadence: cadence || 'daily',
            subjects: subjects,
            website: honeypot // honeypot
        };

        try {
            const response = await fetch('/api/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.ok) {
                showSuccess(result.message || 'You\'re subscribed! Check your email to confirm.');
                form.reset();
                // reset styling
                radioOptions.forEach(o => o.classList.remove('selected'));
                radioOptions[0].classList.add('selected');
                checkboxOptions.forEach(o => o.classList.remove('selected'));
            } else {
                showError(result.error || 'Something went wrong. Please try again.');
            }
        } catch (err) {
            console.error('Subscribe error:', err);
            showError('Could not connect to server. Please try again later.');
        }
    });

    function showSuccess(message) {
        statusDiv.textContent = message;
        statusDiv.className = 'status success';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
    }

    function showError(message) {
        statusDiv.textContent = message;
        statusDiv.className = 'status error';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Subscribe';
    }
});
