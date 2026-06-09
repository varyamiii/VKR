const form = document.getElementById("login-form");
const statusEl = document.getElementById("login-status");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    statusEl.textContent = "Проверка данных...";
    statusEl.className = "status-text";

    const payload = {
        role: form.dataset.role,
        login: document.getElementById("login").value.trim(),
        password: document.getElementById("password").value,
    };

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Ошибка входа");
        }
        statusEl.textContent = "Вход выполнен";
        statusEl.classList.add("status-success");
        window.location.href = data.redirect_url;
    } catch (error) {
        statusEl.textContent = error.message;
        statusEl.classList.add("status-error");
    }
});
