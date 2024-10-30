const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const filterInput = document.getElementById("filters");
const filtersDiv = document.getElementById("filters-box");
const filtersUl = document.getElementById("filters-ul");
const allDfDiv = document.getElementById("data");
const ulSidebarAllDf = document.getElementById("all-orders-ul");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");
const submitOrderBtn = document.getElementById("submitOrderBtn");

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

filterInput.addEventListener('input', function() {
    if (filterInput.value.trim() === '') {
        filterInput.placeholder = 'Поиск лота';
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
});

document.addEventListener('click', function(e) {
    if (e.target && e.target.className === 'order_filter'){
        e.target.parentElement.remove();
    }
});

if (document.getElementById('lot_id').textContent === '') {
    document.getElementById('submitOrderBtn').style.display = 'none';
}

if (allDfDiv.textContent !== '') {
    const allDfData = JSON.parse(allDfDiv.textContent);
    const id = document.getElementById('id_pack').textContent;
    const lot_id = parseInt(document.getElementById('lot_id').textContent);
    if (allDfData.length > 0) {
        allDfData.forEach(row => {
            const li = document.createElement("li");
            li.textContent = "№ лоттировки: " + row['№ лоттировки'];
            li.addEventListener('click', () => {
                window.location.href = `/lots_page.html?id=${id}&lot_id=${row['№ лоттировки']}`;
            });
            ulSidebarAllDf.appendChild(li);
        });
        tableSection.style.display = 'block';
        tableBody.innerHTML = '';
        const headerRow = document.createElement("tr");
        Object.keys(allDfData[0]).forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        })
        tableBody.appendChild(headerRow);
        
        const tr = document.createElement("tr");
        Object.values(allDfData[lot_id]).forEach(cellData => {
            const td = document.createElement("td");
            td.textContent = cellData;
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    }
}

filterInput.addEventListener('input', () => {
    const filterText = filterInput.value.toLowerCase();
    const listItems = ulSidebarAllDf.getElementsByTagName('li');

    Array.from(listItems).forEach(item => {
        const itemText = item.textContent.toLowerCase();
        if (itemText.includes(filterText)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
});

submitOrderBtn.addEventListener('click', function() {

    const editableColumns = ['Дата заказа', '№ заказа', '№ позиции', 'Срок поставки', 'Материал', 'Грузополучатель', 'Общее количество', 'Цена', 'Способ закупки', 'Клиент'];

    if (submitOrderBtn.textContent === "Редактировать") {
        submitOrderBtn.textContent = "Сохранить";
        const rows = tableBody.querySelectorAll('tr');
        const columnNames = tableBody.querySelectorAll('th');
        Array.from(rows).forEach((row, row_index) => {
            if (row_index != 0) {
                Array.from(row.cells).forEach((cell, index) => {
                    const columnName = document.querySelectorAll('th')[index].innerText;
                    if (editableColumns.includes(columnName)) {
                        cell.contentEditable = cell.isContentEditable ? "false" : "true";
                        cell.style.backgroundColor = cell.isContentEditable ? "#666" : "";
                    }
                });
            }   
        });
    }
    else {
        const rows = Array.from(tableBody.querySelectorAll('tr'));
        const headers = Array.from(rows[0].children).map(header => header.textContent);
        
        const data = rows.slice(1).map(row => {
            const cells = Array.from(row.children);
            const rowData = {};
            cells.forEach((cell, index) => {
                rowData[headers[index]] = cell.textContent;
            });
            return rowData;
        });

        fetch('/api/update_lot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                alert("Ошибка со стороны базы данных");
            }
            else {
                alert("Изменения загружены");
            }
        })
        .catch(error => console.error("Error updating CSV data:", error));
        submitOrderBtn.textContent = "Редактировать";
        const cells = tableBody.querySelectorAll('td');
        cells.forEach(cell => {
            cell.contentEditable = false;
            cell.style.backgroundColor = "";
        })
    }
});