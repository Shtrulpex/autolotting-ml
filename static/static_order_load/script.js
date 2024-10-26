const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("xml-file");
const loadBtn = document.getElementById("loadBtn");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");
const filterInput = document.getElementById("filters");

menuBtn.addEventListener('click', function() {
    if (sidebar.style.left === "0px") {
        sidebar.style.left = "-300px";
        menuBtn.classList.remove("active");
    } else {
        if (sidebarOrders.style.left === "0px") {
            sidebarOrders.style.left = "-300px";
            ordersBtn.classList.remove("active");
        }
        sidebar.style.left = "0px";
        menuBtn.classList.add("active");
    }
});

ordersBtn.addEventListener('click', function() {
    if (sidebarOrders.style.left === "0px") {
        sidebarOrders.style.left = "-300px";
        ordersBtn.classList.remove("active");
    } else {
        if (sidebar.style.left === "0px") {
            sidebar.style.left = "-300px";
            menuBtn.classList.remove("active");
        }
        sidebarOrders.style.left = "0px";
        ordersBtn.classList.add("active");
    }
})

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

loadBtn.addEventListener('click', function() {
    tableSection.style.display = 'block';
    tableBody.innerHTML = '';
    for (let i = 0; i < 20; i++) {
        const row = document.createElement('tr');
        for (let j = 0; j < 3; j++) {
            const cell = document.createElement('td');
            cell.textContent = `Row ${i + 1}, Col ${j + 1}`;
            cell.contentEditable = true;
            row.appendChild(cell);
        }
        tableBody.appendChild(row);
    }
});

