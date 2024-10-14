const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("xml-file");
const loadBtn = document.getElementById("loadBtn");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");

// Toggle Sidebar
menuBtn.addEventListener('click', function() {
    if (sidebar.style.left === "0px") {
        sidebar.style.left = "-300px";
        menuBtn.classList.remove("active");
    } else {
        sidebar.style.left = "0px";
        menuBtn.classList.add("active");
    }
});

// Drag and drop functionality for the file input
// dropZone.addEventListener('click', function() {
//     fileInput.click();
// });

dropZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    dropZone.style.backgroundColor = '#e0e0e0';
});

dropZone.addEventListener('dragleave', function() {
    dropZone.style.backgroundColor = '#f9f9f9';
});

dropZone.addEventListener('drop', function(e) {
    event.preventDefault();
      dropZone.style.borderColor = '#ccc';

      const file = event.dataTransfer.files[0];
      if (file) {
        console.log(`File dropped: ${file.name}`);
        let formData = new FormData();
            
        formData.append("file", file);
        fetch('/files/', {method: "POST", body: formData});
      } else {
        console.log('No file dropped.');
      }
    });



function call_back() {
    fetch('/print-hello', {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
    })
    .catch(error => {
        console.error('Error', error);
    });
}