const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const filterInput = document.getElementById("filters");
const filtersDiv = document.getElementById("filters-box");
const filtersUl = document.getElementById("filters-ul");
const tableSection = document.getElementById("tableSection");
const tableBody = document.getElementById("tableBody");

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
        filterInput.placeholder = 'Добавить фильтры';
    } else {
        filterInput.placeholder = '';
    }
});

// Alert the input text after typing
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

async function getOrder() {
    await fetch('/order_number')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return JSON.parse(decodeURIComponent(response));
    })
    .then(data => {
        tableSection.style.display = 'block';
        tableBody.innerHTML = '';
        if(data.length > 0) {
            const headerRow = document.createElement("tr");
            Object.keys(data[0]).forEach(header => {
                const th = document.createElement("th");
                th.textContent = header;
                headerRow.appendChild(th);
            });

            tableBody.appendChild(headerRow);
            data.forEach(row => {
                const tr = document.createElement("tr");
                Object.values(row).forEach(cellData => {
                    const td = document.createElement("td");
                    td.textContent = cellData;
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });
        }
    })
    .catch(error => {
        console.error('There was a problem with the server:', error);
    });
}

getOrder()

// loadBtn.addEventListener('click', function() {
//     tableSection.style.display = 'block';
//     tableBody.innerHTML = '';
//     for (let i = 0; i < 20; i++) {
//         const row = document.createElement('tr');
//         for (let j = 0; j < 3; j++) {
//             const cell = document.createElement('td');
//             cell.textContent = `Row ${i + 1}, Col ${j + 1}`;
//             cell.contentEditable = true;
//             row.appendChild(cell);
//         }
//         tableBody.appendChild(row);
//     }
// });