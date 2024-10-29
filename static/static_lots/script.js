const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");
const fileInput = document.getElementById("xml-file");
const loadBtn = document.getElementById("loadBtn");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");

menuBtn.addEventListener('click', function() {
    if (sidebar.style.left === "0px") {
        sidebar.style.left = "-300px";
        menuBtn.classList.remove("active");
    } else {
        sidebar.style.left = "0px";
        menuBtn.classList.add("active");
    }
});

loadBtn.addEventListener('click', function() {
    fetch('/api/download')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        const file = new Blob([blob], {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
        const url = URL.createObjectURL(file);
        const link = document.createElement('a');
        link.download = "enter.xlsx";
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    })
    .catch(error => {
        console.error('There was a problem with the download:', error);
    });
});