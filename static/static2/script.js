const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("xlsx-file");
const loadBtn = document.getElementById("loadBtn");
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
            alert('Файл загружен.');// Response: '+result.message);
        } else {
            alert('Ошибка при загрузке файла.');// Response: ' + response.status);
        }
    } catch (error) {
        alert('Неизвестная ошибка.');//: ' + error.message);
    }
}