document.addEventListener("DOMContentLoaded", function () {
    const popup = document.getElementById("popup");
    const closeBtn = document.getElementById("close-popup");

    // Show popup when the page loads
    popup.classList.add("active");

    // Close popup when the close button is clicked
    closeBtn.addEventListener("click", function () {
        popup.classList.remove("active");
    });

    // Close popup when clicking outside the popup content
    popup.addEventListener("click", function (e) {
        if (e.target === popup) {
            popup.classList.remove("active");
        }
    });
});
