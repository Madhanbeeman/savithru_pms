document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('task-update-form');
    const submitBtn = document.getElementById('submit-task-update-btn');
    if (!form || !submitBtn) return;

    submitBtn.addEventListener('click', (event) => {
        event.preventDefault(); 
        const formData = new FormData(form);
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Submitting...
        `;

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest' // Tells Django it's an AJAX request
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                // Success! The WebSocket will add the update.
                form.reset(); 
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Add Update';
                console.log("Form submitted, waiting for WebSocket update.");
                
            } else {
                // Handle form errors
                response.json().then(data => {
                    alert("Submission failed. Please check your update.");
                });
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Add Update';
            }
        })
        .catch(error => {
            console.error('Network error:', error);
            alert('Network error, please try again.');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Add Update';
        });
    });
});