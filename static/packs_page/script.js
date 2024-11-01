const menuBtn = document.getElementById("menuBtn");
const sidebarOrders = document.getElementById("sidebar-orders");
const sidebar = document.getElementById("sidebar");
const ordersBtn = document.getElementById("ordersBtn");
const filterInput = document.getElementById("filters");
const filtersDiv = document.getElementById("filters-box");
const filtersUl = document.getElementById("filters-ul");
const allDfDiv = document.getElementById("all-data-div");
const ulSidebarAllDf = document.getElementById("all-orders-ul");
const btnToStats = document.getElementById("includeContent");
const idDiv = document.getElementById("id-div");
const btnToLots = document.getElementById("btn-to-lots");

if (idDiv.textContent !== '') {
    btnToStats.style.display = '';
    btnToLots.style.display = '';
}

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
        filterInput.placeholder = 'Поиск пака';
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
    const idToReadable = {'pack_id': 'Идентификатор', 'pack_name': 'Имя', 'lotting_algorithm':'Алгоритм лотирования', 'formation_dttm':'Дата формирования', 'from_dt':'Дата начала заказов', 'to_dt':'Дата конца заказов'};
    const allDfData = JSON.parse(allDfDiv.textContent);
    if (allDfData.length > 0) {
        allDfData.forEach(row => {
            const li = document.createElement("li");
            for (let key in row) {
                if (key !== 'human_pack_id') {
                    const p = document.createElement("p");
                    p.textContent = idToReadable[key] + ": " + row[key];
                    li.appendChild(p);
                }
            }
            li.addEventListener('click', () => {
                window.location.href = `/packs_page.html?id=${row['pack_id']}`;
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
            if (allDfDiv.textContent !== '') {
                ulSidebarAllDf.innerHTML = '';
                const idToReadable = {'pack_id': 'Идентификатор', 'pack_name': 'Имя', 'lotting_algorithm':'Алгоритм лотирования', 'formation_dttm':'Дата формирования', 'from_dt':'Дата начала заказов', 'to_dt':'Дата конца заказов'};
                const allDfData = JSON.parse(allDfDiv.textContent);
                if (allDfData.length > 0) {
                    allDfData.forEach(row => {
                        if(Date.parse(row['formation_dttm']) < endDate & Date.parse(row['formation_dttm']) > startDate) {
                            const li = document.createElement("li");
                            for (let key in row) {
                                if (key !== 'human_pack_id') {
                                    const p = document.createElement("p");
                                    p.textContent = idToReadable[key] + ": " + row[key];
                                    li.appendChild(p);
                                }
                            }
                            li.addEventListener('click', () => {
                                window.location.href = `/packs_page.html?id=${row['pack_id']}`;
                            });
                            ulSidebarAllDf.appendChild(li);
                        }
                    })
                }
            } else {
                alert("Нет паков для выбора");
            }
        } else {
            alert("Пожалуйста, выберете 2 даты");
        }
    });
});