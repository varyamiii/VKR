const groupSelect = document.getElementById("teacher-group");
const testTypeSelect = document.getElementById("teacher-test-type");
const dateFromInput = document.getElementById("teacher-date-from");
const dateToInput = document.getElementById("teacher-date-to");
const statusEl = document.getElementById("teacher-status");
const reportEl = document.getElementById("teacher-report");

function setStatus(text, isError = false) {
    statusEl.textContent = text;
    statusEl.className = isError ? "status-text status-error" : "status-text";
}

function filtersToQuery() {
    const params = new URLSearchParams();
    if (groupSelect.value) params.set("group_id", groupSelect.value);
    if (testTypeSelect.value) params.set("test_type", testTypeSelect.value);
    if (dateFromInput.value) params.set("date_from", dateFromInput.value);
    if (dateToInput.value) params.set("date_to", dateToInput.value);
    return params.toString();
}

async function loadGroups() {
    const response = await fetch("/api/teacher/groups");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Не удалось загрузить группы");
    data.groups.forEach((group) => {
        const option = document.createElement("option");
        option.value = group.id;
        option.textContent = group.group_name;
        groupSelect.appendChild(option);
    });
}

function formatDate(value) {
    if (!value) return "-";
    return new Date(value).toLocaleString("ru-RU");
}

function testTypeLabel(value) {
    return value === "choice" ? "Варианты" : "Ручной ввод";
}

function renderReport(data) {
    reportEl.classList.remove("hidden");
    document.getElementById("stat-attempts").textContent = data.summary.attempts_count || 0;
    document.getElementById("stat-avg").textContent = `${data.summary.avg_score || 0}%`;
    document.getElementById("stat-best").textContent = `${data.summary.best_score || 0}%`;
    document.getElementById("stat-min").textContent = `${data.summary.min_score || 0}%`;

    const studentsBody = document.getElementById("students-report-body");
    studentsBody.innerHTML = "";
    data.students.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.group_name || "-"}</td>
            <td>${row.full_name || "-"}</td>
            <td>${row.attempts_count || 0}</td>
            <td>${row.avg_score || 0}%</td>
            <td>${row.best_score || 0}%</td>
        `;
        studentsBody.appendChild(tr);
    });

    const attemptsBody = document.getElementById("attempts-report-body");
    attemptsBody.innerHTML = "";
    data.attempts.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${formatDate(row.finished_at)}</td>
            <td>${row.group_name || "-"}</td>
            <td>${row.full_name || "-"}</td>
            <td>${testTypeLabel(row.test_type)}</td>
            <td>${row.correct_answers_count}/${row.questions_count} (${row.score_percent}%)</td>
            <td>${row.categories}<br>${row.accents}<br>${row.noises}</td>
        `;
        attemptsBody.appendChild(tr);
    });
}

async function loadReport() {
    setStatus("Загрузка отчёта...");
    const query = filtersToQuery();
    const response = await fetch(`/api/teacher/report${query ? `?${query}` : ""}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Не удалось сформировать отчёт");
    renderReport(data);
    setStatus("Отчёт сформирован");
}

async function buildPdf() {
    setStatus("Формирование PDF...");
    const query = filtersToQuery();
    const response = await fetch(`/api/teacher/report/pdf${query ? `?${query}` : ""}`, { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Не удалось сформировать PDF");
    setStatus("PDF-отчёт готов");
    window.open(data.report_url, "_blank");
}

document.getElementById("teacher-load-report").addEventListener("click", () => {
    loadReport().catch((error) => setStatus(error.message, true));
});

document.getElementById("teacher-build-pdf").addEventListener("click", () => {
    buildPdf().catch((error) => setStatus(error.message, true));
});

loadGroups().catch((error) => setStatus(error.message, true));
