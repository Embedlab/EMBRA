document.addEventListener("DOMContentLoaded", function () {
    const adcInitializeForm = document.getElementById('adc-initialize-form');
    const initializeResponseContainer = document.getElementById('initialize-response-container');

    adcInitializeForm.addEventListener('submit', function (event) {
        event.preventDefault(); // Zapobiega przeładowaniu strony przy wysyłaniu formularza

        const channelValue = document.getElementById('channel').value;

        fetch('INITIALIZE', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel: channelValue })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                initializeResponseContainer.innerHTML = `<p style="color: green;">${data.message}</p>`;
            } else {
                initializeResponseContainer.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            initializeResponseContainer.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const checkStatusBtn = document.getElementById('check-status-btn');
    const statusContainer = document.getElementById('status-container');

    // Sprawdzanie statusu ADC
    checkStatusBtn.addEventListener('click', function () {
        fetch('STATUS', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let statusMessage = `<p>Status ADC:</p><ul>`;
                    for (let channel in data.channel) {
                        statusMessage += `<li>Channel ${channel}: ${data.channel[channel]}</li>`;
                    }
                    statusMessage += `</ul>`;
                    statusContainer.innerHTML = statusMessage;
                } else {
                    statusContainer.innerHTML = `<p class="error">${data.message}</p>`;
                }
            })
            .catch(error => {
                statusContainer.innerHTML = `<p class="error">Failed to fetch ADC status.</p>`;
            });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const readDataBtn = document.getElementById('read-data-btn');
    const dataContainer = document.getElementById('data-container');

    // Odczyt danych z ADC
    readDataBtn.addEventListener('click', function () {
        fetch('READ', { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    let dataMessage = `<p>ADC Data:</p><ul>`;
                    for (let channel in data.channel) {
                        let channelData = data.channel[channel];
                        if (channelData === "Not initialized") {
                            dataMessage += `<li>Channel ${channel}: Not initialized</li>`;
                        } else {
                            dataMessage += `<li>Channel ${channel}: 
                                <ul>
                                    <li>Bus Voltage: ${channelData.bus_voltage} V</li>
                                    <li>Shunt Voltage: ${channelData.shunt_voltage} V</li>
                                    <li>Current: ${channelData.current} A</li>
                                </ul>
                            </li>`;
                        }
                    }
                    dataMessage += `</ul>`;
                    dataContainer.innerHTML = dataMessage;
                } else {
                    dataContainer.innerHTML = `<p class="error">${data.message}</p>`;
                }
            })
            .catch(error => {
                dataContainer.innerHTML = `<p class="error">Failed to fetch ADC data.</p>`;
            });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const adcLogForm = document.getElementById('adc-log-form');
    const logResponseContainer = document.getElementById('log-response-container');

    // Obsługa formularza logowania
    adcLogForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const channel = document.getElementById('log-channel').value;
        const action = document.getElementById('log-action').value;

        fetch('LOG', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel: channel, action: action })
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
    const adcShutdownForm = document.getElementById('adc-shutdown-form');
    const shutdownResponseContainer = document.getElementById('shutdown-response-container');

    // Obsługa formularza shutdown
    adcShutdownForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const channel = document.getElementById('shutdown-channel').value;

        fetch('SHUTDOWN', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ channel: channel })
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
