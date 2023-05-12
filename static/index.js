
var socket = io();

var logs = document.getElementById("logs");

socket.on('logs', function(log) {
    logs.innerHTML += log + "<br>";
    // Scroll to the bottom of the logs
    logs.scrollTop = logs.scrollHeight;
});

document.querySelector("#process-button").addEventListener("click", function() {
    const youtubeLink = document.querySelector("#youtube-link").value;
    const image = document.querySelector("#image-upload").files[0];

    const formData = new FormData();
    formData.append("youtube-link", youtubeLink);
    formData.append("image-upload", image);

    logs.innerHTML = "UpLOADING Image...";

    fetch("/process", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(responseJson => {
        logs.innerHTML = responseJson["response"];
        if (responseJson["uploaded"]){
            socket.emit('logs', youtubeLink);
        }
    })
    .catch(error => {
        console.error(error);
        document.querySelector("#logs").innerHTML = "An error occurred.";
    });
});

