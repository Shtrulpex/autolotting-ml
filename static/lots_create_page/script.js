const menuBtn = document.getElementById("menuBtn");
const sidebar = document.getElementById("sidebar");


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
            firstDateH2.textContent = startDate.getFullYear()+'-'+(startDate.getMonth()+1)+'-'+startDate.getDate();
            endDate = null;
        } else if (selectedDate < startDate) {
            endDate = startDate;
            startDate = selectedDate;
            firstDateH2.textContent = startDate.getFullYear()+'-'+(startDate.getMonth()+1)+'-'+startDate.getDate();
            secondDateH2.textContent = endDate.getFullYear()+'-'+(endDate.getMonth()+1)+'-'+endDate.getDate();;
        } else {
            endDate = selectedDate;
            secondDateH2.textContent = endDate.getFullYear()+'-'+(endDate.getMonth()+1)+'-'+endDate.getDate();;
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
});