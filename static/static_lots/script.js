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
    tableSection.style.display = 'block';
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
