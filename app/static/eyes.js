// ------------------------------------------
// SELECT EYES
// ------------------------------------------
const leftEye = document.querySelector(".eye-left");
const rightEye = document.querySelector(".eye-right");
const eyes = [leftEye, rightEye];

// ------------------------------------------
// EYES FOLLOWING MOUSE
// ------------------------------------------
document.addEventListener("mousemove", (e) => {
    eyes.forEach(eye => {
        if (eye.classList.contains("closed")) return; // stop moving if closed

        const rect = eye.getBoundingClientRect();
        const eyeX = rect.left + rect.width / 2;
        const eyeY = rect.top + rect.height / 2;

        const angle = Math.atan2(e.clientY - eyeY, e.clientX - eyeX);
        const distance = 4; // max movement in px

        const moveX = Math.cos(angle) * distance + "px";
        const moveY = Math.sin(angle) * distance + "px";

        eye.style.setProperty('--eye-move-x', moveX);
        eye.style.setProperty('--eye-move-y', moveY);
    });
});

// ------------------------------------------
// EYELID CLOSING WHEN TYPING PASSWORD
// ------------------------------------------
function closeEyes() {
    eyes.forEach(eye => eye.classList.add("closed"));
}

function openEyes() {
    eyes.forEach(eye => {
        eye.classList.remove("closed");
        eye.style.setProperty('--eye-move-x', '0px');
        eye.style.setProperty('--eye-move-y', '0px');
    });
}

// ------------------------------------------
// PASSWORD FIELDS (login & register support)
// ------------------------------------------
const passwordFields = [
    document.getElementById("passwordLogin"),
    document.getElementById("passwordRegister")
];

passwordFields.forEach(field => {
    if (!field) return;

    field.addEventListener("focus", closeEyes);
    field.addEventListener("input", closeEyes);
    field.addEventListener("blur", openEyes);
});
