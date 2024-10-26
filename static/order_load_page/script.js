const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("xml-file");
const loadBtn = document.getElementById("loadBtn");
const filterInput = document.getElementById("filters");
const filtersDiv = document.getElementById("filters-box");
const filtersUl = document.getElementById("filters-ul");

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

function handleFileSelect(files) {
    if (files.length > 0) {
        const fileName = files[0].name;
        dropZone.textContent = `Выбран файл: ${fileName}`;
    } else {
        dropZone.textContent = "Кликните или перетащите XLSX файл";
    }
}

fileInput.addEventListener('change', function() {
    handleFileSelect(fileInput.files);
})

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
    handleFileSelect(event.dataTransfer.files);
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

async function uploadFile() {
    const file = fileInput.files[0]

    if (!file) {
        alert('Файл не выбран.');
        return;
    }

    const formData = new FormData();
    file.type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            alert('Файл загружен.');
        } else {
            alert('Ошибка при загрузке файла.');
        }
    } catch (error) {
        alert('Неизвестная ошибка.');
    }
}

filterInput.addEventListener('input', function() {
    if (filterInput.value.trim() === '') {
        filterInput.placeholder = 'Добавить фильтры';
    } else {
        filterInput.placeholder = '';
    }
});

filterInput.addEventListener('blur', function() {
    if (filterInput.value.trim() !== '') {
        filterInput.style.color = 'black';
    }
    else {
        filterInput.style.color = 'gray';
    }
});

filterInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter'){
        if (filtersDiv.style.display === '') {
            filtersDiv.style.display = 'block';
        }
        const li = document.createElement('li');
        const button = document.createElement('button');
        button.textContent = filterInput.value;
        button.className = 'order_filter';
        li.appendChild(button);
        filtersUl.appendChild(li);
    }
})

document.addEventListener('click', function(e) {
    if (e.target && e.target.className === 'order_filter'){
        e.target.parentElement.remove();
    }
})