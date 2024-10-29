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
