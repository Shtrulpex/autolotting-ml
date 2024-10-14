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

        // const reader = new FileReader();
        // reader.onload = function(event) {
        //   const fileContent = event.target.result;

        //   // Trigger file download
        //   const downloadLink = document.createElement('a');
        //   downloadLink.href = URL.createObjectURL(new Blob([fileContent], { type: file.type }));
        //   downloadLink.download = file.name;
        //   document.body.appendChild(downloadLink);
        //   downloadLink.click();
        //   document.body.removeChild(downloadLink);

        //   console.log('File download triggered successfully.');
        // };
        // reader.readAsArrayBuffer(file); // Read the file
      } else {
        console.log('No file dropped.');
      }
    });

// Show table after file upload
loadBtn.addEventListener('click', function() {
    tableSection.style.display = 'block';
    // Create a 3x20 table
    tableBody.innerHTML = '';
    for (let i = 0; i < 20; i++) {
        const row = document.createElement('tr');
        for (let j = 0; j < 3; j++) {
            const cell = document.createElement('td');
            cell.textContent = `Row ${i + 1}, Col ${j + 1}`;
            cell.contentEditable = true; // Make cell content editable
            row.appendChild(cell);
        }
        tableBody.appendChild(row);
    }
    sidebar.style.height = "1194px"; //Need to fix afterwords
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