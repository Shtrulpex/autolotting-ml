const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const filterInput = document.getElementById("filters");
const filtersDiv = document.getElementById("filters-box");
const filtersUl = document.getElementById("filters-ul");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");
const dfDataDiv = document.getElementById("dataDiv");
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
        filterInput.placeholder = 'Поиск заказа';
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

if (dfDataDiv.textContent !== '') {
    const dfData = JSON.parse(dfDataDiv.textContent);
    if (dfData.length > 0) {
        tableSection.style.display = 'block';
        tableBody.innerHTML = '';
        const headerRow = document.createElement("tr");
        Object.keys(dfData[0]).forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        })
        tableBody.appendChild(headerRow);
        dfData.forEach(row => {
            const tr = document.createElement("tr");
            Object.values(row).forEach(cellData => {
                const td = document.createElement("td");
                td.textContent = cellData;
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }
}

submitOrderBtn.addEventListener('click', function() {
    if (submitOrderBtn.textContent === "Редактировать") {
        submitOrderBtn.textContent = "Сохранить";
        const cells = tableBody.querySelectorAll('td');
        cells.forEach(cell => {
            cell.contentEditable = true;
        })
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

        fetch('/api/update_df', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                alert("Error with database");
            }
            else {
                alert("Edited successfully");
            }
        })
        .catch(error => console.error("Error updating CSV data:", error));
        submitOrderBtn.textContent = "Редактировать";
        const cells = tableBody.querySelectorAll('td');
        cells.forEach(cell => {
            cell.contentEditable = false;
        })
    }
});