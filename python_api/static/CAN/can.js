document.getElementById('initialize-btn').addEventListener('click', () => {
    const interfaceValue = document.getElementById('interface').value;

    fetch('INITIALIZE', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ interface: interfaceValue })
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('response-container');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('response-container');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

document.getElementById('check-status-btn').addEventListener('click', () => {
    fetch('STATUS', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('status-container');
        if (data.status === 'success') {
            const { interfaces } = data;
            container.innerHTML = `
                <p style="color: green;">${data.message}</p>
                <ul>
                    <li>CAN0: ${interfaces.can0}</li>
                    <li>CAN1: ${interfaces.can1}</li>
                </ul>
            `;
        } else {
            container.innerHTML = `<p style="color: red;">Error: ${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('status-container');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

document.getElementById('can-send-form').addEventListener('submit', (event) => {
    event.preventDefault();  // Zapobiega domyślnemu wysyłaniu formularza

    const interfaceValue = document.getElementById('interface').value;
    const idValue = parseInt(document.getElementById('id').value);
    const dataValue = JSON.parse(document.getElementById('data').value);

    // Walidacja danych wejściowych
    if (isNaN(idValue) || idValue < 0 || idValue > 0x7FF) {
        alert('Invalid message ID. It must be an integer between 0 and 2047.');
        return;
    }
    if (!Array.isArray(dataValue) || !dataValue.every(byte => Number.isInteger(byte) && byte >= 0 && byte <= 255)) {
        alert('Invalid data. It must be an array of integers between 0 and 255.');
        return;
    }

    fetch('SEND', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interface: interfaceValue,
            id: idValue,
            data: dataValue
        })
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('send-response-container');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('send-response-container');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

document.getElementById('can-log-form').addEventListener('submit', (event) => {
    event.preventDefault();  // Zapobiega domyślnemu wysyłaniu formularza

    const interfaceValue = document.getElementById('log-interface').value;
    const actionValue = document.getElementById('action').value;

    // Wysyłanie żądania POST do /CAN/LOG
    fetch('LOG', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interface: interfaceValue,
            action: actionValue
        })
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('log-response-container');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('log-response-container');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});

document.getElementById('can-shutdown-form').addEventListener('submit', (event) => {
    event.preventDefault();  // Zapobiega domyślnemu wysyłaniu formularza

    const interfaces = [];
    if (document.getElementById('can0').checked) {
        interfaces.push("can0");
    }
    if (document.getElementById('can1').checked) {
        interfaces.push("can1");
    }

    // Walidacja, czy wybrano co najmniej jeden interfejs
    if (interfaces.length === 0) {
        alert('Please select at least one interface.');
        return;
    }

    // Wysyłanie żądania POST do /SHUTDOWN
    fetch('SHUTDOWN', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interfaces: interfaces
        })
    })
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('shutdown-response-container');
        if (data.status === 'success') {
            container.innerHTML = `<p style="color: green;">${data.message}</p>`;
            container.innerHTML += `<pre>${JSON.stringify(data.details, null, 2)}</pre>`;
        } else {
            container.innerHTML = `<p style="color: red;">${data.message}</p>`;
        }
    })
    .catch(error => {
        const container = document.getElementById('shutdown-response-container');
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    });
});
