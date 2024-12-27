document.addEventListener("DOMContentLoaded", function () {
    const checkCameraStatusBtn = document.getElementById('check-camera-status-btn');
    const cameraStatusContainer = document.getElementById('camera-status-container');

    // Check Camera Status
    checkCameraStatusBtn.addEventListener('click', function () {
        fetch('STATUS', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    cameraStatusContainer.innerHTML = `<p>${data.message}</p>`;
                } else {
                    cameraStatusContainer.innerHTML = `<p class="error">${data.message}</p>`;
                }
            })
            .catch(error => {
                cameraStatusContainer.innerHTML = `<p class="error">Failed to fetch camera status.</p>`;
            });
    });
});

    // Start Recording Button
document.getElementById('start-recording-btn').addEventListener('click', () => {
    fetch('RECORD', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('start-recording-response');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('start-recording-response');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

// Stop Recording Button
document.getElementById('stop-recording-btn').addEventListener('click', () => {
    fetch('STOP', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('stop-recording-response');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('stop-recording-response');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

// Capture Photo Button
document.getElementById('capture-photo-btn').addEventListener('click', () => {
    fetch('PHOTO', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('capture-photo-response');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>
                                   <p>Photo saved to: ${data.file}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('capture-photo-response');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});
