const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("xml-file");
const loadBtn = document.getElementById("loadBtn");
const filterInput = document.getElementById("filters");
const allDfDiv = document.getElementById("all-data-div");
const ulSidebarAllDf = document.getElementById("all-orders-ul");
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
    handleFileSelect(event.dataTransfer.files);
    const file = event.dataTransfer.files[0];
    uploadFile(file);
});

function checkFile() {
    const file = fileInput.files[0]

    if (!file) {
        alert('Файл не выбран.');
        return;
    }
    uploadFile(file);
}

async function uploadFile(file) {
    const formData = new FormData();
    file.type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
    formData.append('file', file);

    try {
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then((response, reject) => {
            if (response.ok) {
                return response.json();
            } else {
                alert("Ошибка в содержании файла");
                return Promise.reject(reject)
            }
        })
        .then(data => {
            alert(data.message);
            window.location.href = `/order_page.html?id=${data.ids}`;
        })
        .catch(error => console.error("Ошибка:", error));
    } catch (error) {
        alert('Ошибка:', error);
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
});

document.addEventListener('click', function(e) {
    if (e.target && e.target.className === 'order_filter'){
        e.target.parentElement.remove();
    }
});

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
            .catch(error => console.error("Ошибка:", error));
        } else {
            alert("Пожалуйста, выберете 2 даты");
        }
    });    
});