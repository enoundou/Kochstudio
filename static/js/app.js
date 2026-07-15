/*
--------------------------------------------------
Small UI Helpers
--------------------------------------------------
*/

document.addEventListener("DOMContentLoaded", function () {
    initNavigationToggle();
    initManagerAuthCards();
    initNoteImprovement();
    initNativeFormSubmitLock();
});


function initNavigationToggle() {
    /*
     * Toggle the mobile navigation menu.
     */

    const navToggle = document.getElementById("navToggle");
    const navLinks = document.getElementById("navLinks");

    if (!navToggle || !navLinks) {
        return;
    }

    navToggle.addEventListener("click", function () {
        navLinks.classList.toggle("open");
    });
}


function initManagerAuthCards() {
    /*
     * Switch between manager login and registration cards.
     * Form submission stays native through HTML action attributes.
     */

    const loginCard = document.getElementById("managerLoginCard");
    const registerCard = document.getElementById("managerRegisterCard");
    const showRegisterButton = document.getElementById("showRegisterCard");
    const showLoginButton = document.getElementById("showLoginCard");

    if (!loginCard || !registerCard) {
        return;
    }

    if (showRegisterButton) {
        showRegisterButton.addEventListener("click", function () {
            loginCard.hidden = true;
            registerCard.hidden = false;
        });
    }

    if (showLoginButton) {
        showLoginButton.addEventListener("click", function () {
            registerCard.hidden = true;
            loginCard.hidden = false;
        });
    }
}

function initNoteImprovement() {
    /*
     * Improve the booking note through a Flask endpoint.
     * The OpenAI API key stays on the server.
     */

    const noteInput = document.getElementById("note");
    const improveButton = document.getElementById("improveNoteButton");
    const statusText = document.getElementById("noteImproveStatus");

    if (!noteInput || !improveButton) {
        return;
    }

    improveButton.addEventListener("click", async function () {
        const originalText = noteInput.value.trim();

        if (!originalText) {
            setNoteImproveStatus(
                statusText,
                "Bitte zuerst eine Mitteilung eingeben."
            );
            noteInput.focus();
            return;
        }

        const endpointUrl = improveButton.dataset.url || "/note/improve";
        const originalLabel = improveButton.textContent;

        improveButton.disabled = true;
        improveButton.textContent = "Text wird verbessert...";
        setNoteImproveStatus(statusText, "");

        try {
            const response = await fetch(endpointUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    note: originalText
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Der Text konnte nicht verbessert werden."
                );
            }

            noteInput.value = result.text;
            setNoteImproveStatus(statusText, "Text verbessert.");
        } catch (error) {
            setNoteImproveStatus(statusText, error.message);
        } finally {
            improveButton.disabled = false;
            improveButton.textContent = originalLabel;
        }
    });
}


function setNoteImproveStatus(statusText, message) {
    /*
     * Update the small status text next to the OpenAI button.
     */

    if (!statusText) {
        return;
    }

    statusText.textContent = message;
}

function initNativeFormSubmitLock() {
    /*
     * Prevent double clicks from submitting the same HTML form twice.
     */

    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (form.dataset.submitting === "true") {
                event.preventDefault();
                return;
            }

            form.dataset.submitting = "true";

            const submitButton = (
                event.submitter ||
                form.querySelector('button[type="submit"], input[type="submit"]')
            );

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.dataset.originalText = submitButton.textContent;

                if (submitButton.tagName.toLowerCase() === "button") {
                    submitButton.textContent = "Bitte warten...";
                }
            }
        });
    });
}
