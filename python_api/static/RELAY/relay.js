document.addEventListener("DOMContentLoaded", () => {
    const statusButton = document.getElementById("status-btn");
    const statusResponse = document.getElementById("status-response");
    const toggleResponse = document.getElementById("toggle-response");

    // Add event listeners to all toggle buttons
    const relayButtons = document.querySelectorAll(".btn");
    relayButtons.forEach(button => {
        button.addEventListener("click", () => {
            const channel = button.getAttribute("data-channel");

            fetch("TOGGLE", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ channel: channel })
            })
            .then(response => response.json())
            .then(data => {
                toggleResponse.innerHTML = `<p>${data.message}</p>`;
            })
            .catch(error => {
                toggleResponse.innerHTML = `<p>Error: ${error.message}</p>`;
            });
        });
    });

    // Function to fetch relay status
    statusButton.addEventListener("click", () => {
        fetch("STATUS", {
            method: "GET"
        })
        .then(response => response.json())
        .then(data => {
            statusResponse.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        })
        .catch(error => {
            statusResponse.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });
});
