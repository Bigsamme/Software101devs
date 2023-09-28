function toggleMobileMenu(menu) {
    menu.classList.toggle('open');
}

const menu = document.getElementById("ham");

document.addEventListener("click", (evt) => {
    if (menu.classList.contains("open")) {
        if (!menu.contains(evt.target)) {
            menu.classList.remove("open");
        }
    }
});
