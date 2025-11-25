document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const stopBtn = document.getElementById('stop-btn');
    const audioPlayback = document.getElementById('audio-playback');
    const recordStatus = document.getElementById('record-status');
    const form = document.getElementById('project-update-form');
    const submitBtn = document.getElementById('submit-update-btn');
    const voiceNoteInput = document.getElementById('id_voice_note'); // Get the hidden input

    let mediaRecorder;
    let audioChunks = [];
    let audioBlob = null; 

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if(recordStatus) recordStatus.textContent = "Recording not supported.";
        if(recordBtn) recordBtn.disabled = true;
    }

    if(recordBtn) {
        recordBtn.addEventListener('click', async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                audioBlob = null; 

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    audioBlob = new Blob(audioChunks, { type: 'audio/webm' }); 
                    const audioUrl = URL.createObjectURL(audioBlob);
                    if(audioPlayback) {
                        audioPlayback.src = audioUrl;
                        audioPlayback.style.display = 'block';
                    }
                    stream.getTracks().forEach(track => track.stop());
                };

                mediaRecorder.start();
                if(recordStatus) recordStatus.textContent = "Recording...";
                recordBtn.disabled = true;
                recordBtn.classList.add('is-recording');
                if(stopBtn) stopBtn.disabled = false;

            } catch (err) {
                console.error("Error accessing microphone:", err);
                if(recordStatus) recordStatus.textContent = "Mic access denied.";
            }
        });
    }

    if(stopBtn) {
        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                if(recordStatus) recordStatus.textContent = "Recording stopped.";
                if(recordBtn) {
                    recordBtn.disabled = false;
                    recordBtn.classList.remove('is-recording');
                }
                stopBtn.disabled = true;
            }
        });
    }

    if(submitBtn) {
        submitBtn.addEventListener('click', (event) => {
            event.preventDefault(); 
            if (!form) return;

            const formData = new FormData(form);

            if (audioBlob && audioBlob.size > 0) {
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const audioFile = new File([audioBlob], `voice_note_${timestamp}.webm`, { type: audioBlob.type });
                formData.set('voice_note', audioFile, audioFile.name); 
            }
            
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
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json()) 
            .then(data => {
                if (data.status === 'success') {
                    // This is the "live" part. The WebSocket will add the update.
                    form.reset(); 
                    if(audioPlayback) audioPlayback.style.display = 'none';
                    if(recordStatus) recordStatus.textContent = "";
                    console.log("Form submitted, waiting for WebSocket update.");
                    
                } else {
                    console.error("Form errors:", data.errors);
                    alert("Submission failed. Please check required fields (e.g., Status, Intent).");
                }
            })
            .catch(error => {
                console.error('Network error:', error);
                alert('Network error, please try again.');
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Submit Update';
            });
        });
    }
});