const panel = document.querySelector('.result-panel');
const sessionId = Number(panel.dataset.sessionId);
const resultArea = document.querySelector('#result-area');

async function fetchJson(url) {
    const response = await fetch(url);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || 'Ошибка запроса');
    }
    return data;
}

async function init() {
    const data = await fetchJson(`/api/tests/${sessionId}/result`);
    const session = data.session;
    const questions = data.questions;
    const reportLink = session.report_file_path
        ? `<a class="btn btn-primary" href="${session.report_file_path}" target="_blank">Скачать PDF-отчёт</a>`
        : '<p class="status-text status-error">PDF-отчёт ещё не сформирован.</p>';

    resultArea.innerHTML = `
        <p class="eyebrow">Test completed</p>
        <h2>Тестовая сессия №${session.id}</h2>
        <div class="result-score">${session.score_percent || 0}%</div>
        <p>Правильных ответов: ${session.correct_answers_count} из ${session.questions_count}</p>
        <div class="hero-actions">${reportLink}<a class="btn btn-outline" href="/test/setup">Новый тест</a></div>
        <div class="audio-box">
            <h3>Детализация</h3>
            ${questions.map(q => `<p><strong>${q.question_number}.</strong> ${q.correct_answer_text} — ${q.is_correct ? 'верно' : 'неверно'}</p>`).join('')}
        </div>
    `;
}

init().catch(error => {
    resultArea.innerHTML = `<p class="status-text status-error">${error.message}</p>`;
});
