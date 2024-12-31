document.addEventListener("DOMContentLoaded", () => {
    const startLoggingForm = document.getElementById("start-logging-form");
    const stopLoggingButton = document.getElementById("stop-logging");
    const statusButton = document.getElementById("status-btn");
    const getSessionsButton = document.getElementById("get-sessions");
    const deleteSessionsButton = document.getElementById("delete-sessions");
    const exportLogsForm = document.getElementById("export-logs-form");

    const startLoggingResponse = document.getElementById("start-logging-response");
    const stopLoggingResponse = document.getElementById("stop-logging-response");
    const statusResponse = document.getElementById("status-response");
    const sessionsResponse = document.getElementById("sessions-response");
    const deleteSessionsResponse = document.getElementById("delete-sessions-response");
    const exportLogsResponse = document.getElementById("export-logs-response");

    // Start logging
    startLoggingForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const formData = new FormData(startLoggingForm);
        const data = {};

        for (const [key, value] of formData.entries()) {
            data[key] = value === "on";
        }

        fetch("START", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            startLoggingResponse.innerHTML = `<p>${data.message}</p>`;
        })
        .catch(error => {
            startLoggingResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });

    // Stop logging
    stopLoggingButton.addEventListener("click", () => {
        fetch("STOP", { method: "GET" })
        .then(response => response.json())
        .then(data => {
            stopLoggingResponse.innerHTML = `<p>${data.message}</p>`;
        })
        .catch(error => {
            stopLoggingResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });

    // Get logging status
    statusButton.addEventListener("click", () => {
        fetch("STATUS", { method: "GET" })
        .then(response => response.json())
        .then(data => {
            statusResponse.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => {
            statusResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });

    // Get sessions
    getSessionsButton.addEventListener("click", () => {
        fetch("/SESSIONS/GET", { method: "GET" })
        .then(response => response.json())
        .then(data => {
            const sessionList = data.data.map(session => `<li>${session}</li>`).join("");
            sessionsResponse.innerHTML = `<ul>${sessionList}</ul>`;
        })
        .catch(error => {
            sessionsResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });

    // Delete all sessions
    deleteSessionsButton.addEventListener("click", () => {
        fetch("/SESSIONS/DELETE", { method: "GET" })
        .then(response => response.json())
        .then(data => {
            deleteSessionsResponse.innerHTML = `<p>${data.message}</p>`;
        })
        .catch(error => {
            deleteSessionsResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });

    // Export logs
    exportLogsForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const folderName = document.getElementById("folder-name").value;

        if (!folderName) {
            exportLogsResponse.innerHTML = `<p>Please enter a folder name.</p>`;
            return;
        }

        fetch(`/SESSIONS/EXPORT?folder=${encodeURIComponent(folderName)}`, { method: "GET" })
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then(err => { throw new Error(err.message); });
            }
        })
        .then(blob => {
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = `${folderName}_logs.zip`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            exportLogsResponse.innerHTML = `<p>Logs exported successfully.</p>`;
        })
        .catch(error => {
            exportLogsResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });
});
