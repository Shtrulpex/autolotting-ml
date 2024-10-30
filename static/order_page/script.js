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
const allDfDiv = document.getElementById("all-data-div");
const ulSidebarAllDf = document.getElementById("all-orders-ul");
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
    calendarMenu.classList.add('hidden-calendar');
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

if (allDfDiv.textContent !== '') {
    const allDfData = JSON.parse(allDfDiv.textContent);
    if (allDfData.length > 0) {
        allDfData.forEach(row => {
            const li = document.createElement("li");
            for (let key in row) {
                const p = document.createElement("p");
                p.textContent = key + ": " + row[key];
                li.appendChild(p);
            }
            li.addEventListener('click', () => {
                window.location.href = `/order_page.html?id=${row['№ заказа']}`;
            });
            ulSidebarAllDf.appendChild(li);
        })
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

    const editableColumns = ['Дата заказа', '№ заказа', '№ позиции', 'Срок поставки', 'Материал', 'Грузополучатель', 'Общее количество', 'Цена', 'Способ закупки', 'Клиент']

    if (submitOrderBtn.textContent === "Редактировать") {
        submitOrderBtn.textContent = "Сохранить";
        const rows = tableBody.querySelectorAll('tr');
        const columnNames = tableBody.querySelectorAll('th');
        Array.from(rows).forEach((row, row_index) => {
            if (row_index != 0) {
                Array.from(row.cells).forEach((cell, index) => {
                    // Check if the column is in the editable columns list
                    const columnName = document.querySelectorAll('th')[index].innerText;
                    if (editableColumns.includes(columnName)) {
                        // Toggle contenteditable attribute
                        cell.contentEditable = cell.isContentEditable ? "false" : "true";
                        cell.style.backgroundColor = cell.isContentEditable ? "#666" : ""; // Highlight if editable
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

        fetch('/api/update_df', {
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

document.addEventListener('DOMContentLoaded', () => {
    const calendarBtn = document.getElementById('calendarBtn');
    const calendarMenu = document.getElementById('calendarMenu');
    const yearSelector = document.getElementById('yearSelector');
    const submitDatesBtn = document.getElementById('submitDatesBtn');
    const closeCalendarBtn = document.getElementById('closeCalendar');
    const calendar = document.getElementById('calendar');
    const monthYear = document.getElementById('monthYear');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth();
    let startDate = null;
    let endDate = null;

    for (let year = 2000; year <= currentYear; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelector.appendChild(option);
    }
    yearSelector.value = currentYear;

    yearSelector.addEventListener('change', () => {
        renderCalendar(yearSelector.value, currentMonth);
    });

    calendarBtn.addEventListener('click', () => {
        calendarMenu.classList.toggle('hidden-calendar');
        renderCalendar(yearSelector.value, currentMonth);
    });

    closeCalendarBtn.addEventListener('click', () => {
        calendarMenu.classList.add('hidden-calendar');
    });

    prevMonthBtn.addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            yearSelector.value--;
        }
        renderCalendar(yearSelector.value, currentMonth);
    });

    nextMonthBtn.addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            yearSelector.value++;
        }
        renderCalendar(yearSelector.value, currentMonth);
    });

    function renderCalendar(year, month) {
        calendar.innerHTML = '';
        const date = new Date(year, month, 1);
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        monthYear.textContent = date.toLocaleString('default', { month: 'long', year: 'numeric' });

        for (let i = 1; i <= daysInMonth; i++) {
            const dateElement = document.createElement('div');
            dateElement.classList.add('calendar-date');
            dateElement.textContent = i;
            dateElement.addEventListener('click', () => selectDate(year, month, i));
            dateElement.addEventListener('mouseover', () => highlightRange(year, month, i));
            calendar.appendChild(dateElement);
        }
    }

    function selectDate(year, month, day) {
        const selectedDate = new Date(year, month, day);
        if (!startDate || (startDate && endDate)) {
            startDate = selectedDate;
            endDate = null;
        } else if (selectedDate < startDate) {
            endDate = startDate;
            startDate = selectedDate;
        } else {
            endDate = selectedDate;
        }
        updateCalendarDisplay();
    }

    function highlightRange(year, month, day) {
        if (startDate && !endDate) {
            const dates = document.querySelectorAll('.calendar-date');
            dates.forEach(date => {
                const dateValue = parseInt(date.textContent);
                const dateObj = new Date(year, month, dateValue);
                if (dateObj >= startDate && dateObj <= new Date(year, month, day)) {
                    date.classList.add('range-date');
                } else {
                    date.classList.remove('range-date');
                }
            });
        }
    }

    function updateCalendarDisplay() {
        const dates = document.querySelectorAll('.calendar-date');
        dates.forEach(date => {
            const dateValue = parseInt(date.textContent);
            const dateObj = new Date(yearSelector.value, currentMonth, dateValue);
            date.classList.remove('selected-date', 'range-date');
            if (dateObj.getTime() === startDate?.getTime() || dateObj.getTime() === endDate?.getTime()) {
                date.classList.add('selected-date');
            } else if (startDate && endDate && dateObj > startDate && dateObj < endDate) {
                date.classList.add('range-date');
            }
        });
    }

    submitDatesBtn.addEventListener('click', () => {
        if (startDate && endDate) {
            fetch('/api/submit-dates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate })
            })
            .then(response => response.json())
            .then(data => {
                const allDfData = JSON.parse(data);
                if (allDfData.length > 0) {
                    ulSidebarAllDf.innerHTML = "";
                    allDfData.forEach(row => {
                        const li = document.createElement("li");
                        for (let key in row) {
                            const p = document.createElement("p");
                            p.textContent = key + ": " + row[key];
                            li.appendChild(p);
                        }
                        li.addEventListener('click', () => {
                            window.location.href = `/order_page.html?id=${row['№ заказа']}`;
                        });
                        ulSidebarAllDf.appendChild(li);
                    })
                }
                calendarMenu.classList.add('hidden-calendar');
            })
            .catch(error => console.error("Error:", error));
        } else {
            alert("Please select a date range.");
        }
    });
});