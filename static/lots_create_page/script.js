const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");
const coeffCheckBox = document.getElementById("coefficientCheckbox")
const inputDiv = document.getElementById("coefficientInputDiv");
const coeffInput = document.getElementById("coefficientInput");
const inputParam1 = document.getElementById("param-1");
const inputParam2 = document.getElementById("param-2");

coeffCheckBox.addEventListener("change", function() {
    inputDiv.classList.toggle("hidden", !this.checked);
});

coeffInput.addEventListener("input", function() {
    const value = this.value;
    if (!Number.isInteger(Number(value)) || value.trim() === "") {
        alert("Please provide an integer");
    }
});

document.querySelectorAll("input[name='countingMethod']").forEach(radio => {
    radio.addEventListener("change", function() {
        inputParam1.value = "";
        inputParam2.value = "";
    });
});

menuBtn.addEventListener('click', function() {
    if (sidebar.style.left === "0px") {
        sidebar.style.left = "-300px";
        menuBtn.classList.remove("active");
    } else {
        sidebar.style.left = "0px";
        menuBtn.classList.add("active");
    }
});


document.body.addEventListener('mouseover', function(event) {
    if (!event.target.closest('.sidebar') && !menuBtn.classList.contains("active")) {
        sidebar.style.left = "-300px";
    }
});

sidebar.addEventListener('click', function(event) {
    event.stopPropagation();
});

document.addEventListener('DOMContentLoaded', () => {
    const calendarBtn = document.getElementById('btn-calendar-1');
    const calendarMenu = document.getElementById('calendarMenu');
    const yearSelector = document.getElementById('yearSelector');
    const submitDatesBtn = document.getElementById('submitDatesBtn');
    const closeCalendarBtn = document.getElementById('closeCalendar');
    const calendar = document.getElementById('calendar');
    const monthYear = document.getElementById('monthYear');
    const prevMonthBtn = document.getElementById('prevMonth');
    const nextMonthBtn = document.getElementById('nextMonth');
    const firstDateH2 = document.getElementById('start-date');
    const secondDateH2 = document.getElementById('end-date')
    const h2NumberOfOrders = document.getElementById('number-of-orders');
    const h2NumberOfPositions = document.getElementById('number-of-positions');
    const formLotsBtn = document.getElementById('form-lots-btn');
    const inputName = document.getElementById('input-name')
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

    async function fetchOrders() {
        if (startDate && endDate) {
            await fetch('/api/fetch-dates', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ start_date: startDate, end_date: endDate })
            })
            .then(response => response.json())
            .then(data => {
                h2NumberOfOrders.textContent = data.numberOrders;
                h2NumberOfPositions.textContent = data.numberPositions;
            })
            .catch(error => console.error("Error:", error));
        } else {
            alert("Please select a date range.");
        }
    }

    function selectDate(year, month, day) {
        const selectedDate = new Date(year, month, day);
        if (!startDate || (startDate && endDate)) {
            startDate = selectedDate;
            firstDateH2.textContent = startDate.getFullYear()+'-'+(startDate.getMonth()+1)+'-'+startDate.getDate();
            endDate = null;
        } else if (selectedDate < startDate) {
            endDate = startDate;
            startDate = selectedDate;
            firstDateH2.textContent = startDate.getFullYear()+'-'+(startDate.getMonth()+1)+'-'+startDate.getDate();
            secondDateH2.textContent = endDate.getFullYear()+'-'+(endDate.getMonth()+1)+'-'+endDate.getDate();
            fetchOrders();
        } else {
            endDate = selectedDate;
            secondDateH2.textContent = endDate.getFullYear()+'-'+(endDate.getMonth()+1)+'-'+endDate.getDate();
            fetchOrders();
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
        calendarMenu.classList.add('hidden-calendar');
    });

    formLotsBtn.addEventListener('click', () => {

        const coefficient = coeffCheckBox.checked ? coeffInput.value : null;
        
        const countingMethod = document.querySelector("input[name='countingMethod']:checked").value;
        const field1 = inputParam1.value;
        if (field1 === '') {
            field1 = null;
        }
        const field2 = inputParam2.value;
        if (field2 === '') {
            field2 = null;
        }
        if (countingMethod === '1' & (field1 === '' | field2 === '')) {
            alert('Введите параметры подсчета')
        } else {
            if (startDate && endDate) {
                if (inputName.value) {
                    fetch('/api/upload_lots', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ start_date: startDate, end_date: endDate, name: inputName.value, dist_coeff: coefficient, count_method: countingMethod, param_1: field1, param_2: field2 })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // window.location.href=`/packs_page.html?id=${data.id}`;
                    })
                    .catch(error => console.error("Error:", error));
                } else {
                    alert('Пожалуйста, впишите название пака.')
                }
            } else {
                alert("Пожалуйста, выберете даты заказов.");
            }
        }
    })
});