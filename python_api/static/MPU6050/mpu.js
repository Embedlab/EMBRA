document.addEventListener("DOMContentLoaded", function () {
    const initializeButton = document.getElementById('initialize-btn');
    const responseContainer = document.getElementById('initialize-response-container');

    // Obsługa inicjalizacji MPU6050
    initializeButton.addEventListener('click', function () {
        fetch('INITIALIZE', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                responseContainer.innerHTML = `<p style="color: green;">${data.messege}</p>`;
            } else {
                responseContainer.innerHTML = `<p style="color: red;">${data.messege}</p>`;
            }
        })
        .catch(error => {
            responseContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const checkStatusButton = document.getElementById('check-status-btn');
    const statusContainer = document.getElementById('status-container');

    // Obsługuje kliknięcie przycisku, aby sprawdzić status MPU6050
    checkStatusButton.addEventListener('click', function () {
        fetch('STATUS', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                statusContainer.innerHTML = `<p style="color: green;">${data.state}</p>`;
            } else {
                statusContainer.innerHTML = `<p style="color: red;">${data.error || data.state}</p>`;
            }
        })
        .catch(error => {
            statusContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const readDataButton = document.getElementById('read-data-btn');
    const dataContainer = document.getElementById('data-container');

    // Obsługuje kliknięcie przycisku, aby odczytać dane z MPU6050
    readDataButton.addEventListener('click', function () {
        fetch('READ', {
            method: 'GET'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                if (data.state === "not initialized") {
                    dataContainer.innerHTML = `<p style="color: red;">MPU6050 is not initialized.</p>`;
                } else {
                    const accel = data.data.accel;
                    const gyro = data.data.gyro;
                    const temp = data.data.temp;

                    dataContainer.innerHTML = `
                        <p><strong>Acceleration:</strong> X: ${accel.x}, Y: ${accel.y}, Z: ${accel.z}</p>
                        <p><strong>Gyroscope:</strong> X: ${gyro.x}, Y: ${gyro.y}, Z: ${gyro.z}</p>
                        <p><strong>Temperature:</strong> ${temp} °C</p>
                    `;
                }
            } else {
                dataContainer.innerHTML = `<p style="color: red;">Error: ${data.state}</p>`;
            }
        })
        .catch(error => {
            dataContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const startLogButton = document.getElementById('start-log-btn');
    const stopLogButton = document.getElementById('stop-log-btn');
    const logStatusContainer = document.getElementById('log-status-container');

    // Start logging for MPU6050
    startLogButton.addEventListener('click', function () {
        fetch('/LOG', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: "start" })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                logStatusContainer.innerHTML = `<p style="color: green;">${data.message}</p>`;
            } else {
                logStatusContainer.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            logStatusContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const mpuLogForm = document.getElementById('mpu-log-form');
    const logResponseContainer = document.getElementById('log-response-container');
    const logActionSelect = document.getElementById('log-action');

    mpuLogForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const action = logActionSelect.value;

        fetch('LOG', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: action })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                logResponseContainer.innerHTML = `<p style="color: green;">${data.message}</p>`;
            } else {
                logResponseContainer.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            logResponseContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const mpuShutdownForm = document.getElementById('mpu-shutdown-form');
    const shutdownResponseContainer = document.getElementById('shutdown-response-container');

    mpuShutdownForm.addEventListener('submit', function (e) {
        e.preventDefault();

        fetch('SHUTDOWN', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                shutdownResponseContainer.innerHTML = `<p style="color: green;">${data.message}</p>`;
            } else {
                shutdownResponseContainer.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            shutdownResponseContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});
