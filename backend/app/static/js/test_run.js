const panel = document.querySelector('.test-panel');
const sessionId = Number(panel.dataset.sessionId);
const questionArea = document.querySelector('#question-area');
const questionCounter = document.querySelector('#question-counter');
const progressFill = document.querySelector('#progress-fill');
const statusText = document.querySelector('#test-status');

let state = null;
let currentIndex = 0;
let selectedOptionId = null;

function setStatus(message, isError = false) {
    statusText.textContent = message || '';
    statusText.className = `status-text ${isError ? 'status-error' : ''}`;
}

async function fetchJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || 'Ошибка запроса');
    }
    return data;
}

function firstUnansweredIndex(questions) {
    const index = questions.findIndex(q => q.is_correct === null);
    return index === -1 ? questions.length : index;
}

function renderQuestion() {
    const questions = state.questions;
    if (currentIndex >= questions.length) {
        finishTest();
        return;
    }

    const question = questions[currentIndex];
    selectedOptionId = question.selected_answer_option_id || null;
    questionCounter.textContent = `Вопрос ${question.question_number} из ${questions.length}`;
    progressFill.style.width = `${(currentIndex / questions.length) * 100}%`;

    const isChoice = state.session.test_type === 'choice';
    const answerHtml = isChoice
        ? `<div class="options">
            ${question.options.map(option => `
                <button type="button" class="option-btn" data-option-id="${option.answer_option_id}">
                    ${option.option_text}
                </button>`).join('')}
           </div>`
        : `<label>Введите услышанную фразу
                <input id="manual-answer" type="text" autocomplete="off" placeholder="Например: Cleared to land runway two seven">
           </label>`;

    questionArea.innerHTML = `
        <div class="question-card">
            <audio controls src="${question.audio_url}?t=${Date.now()}"></audio>
            ${answerHtml}
            <button id="submit-answer" class="btn btn-primary" type="button">Ответить</button>
        </div>
    `;

    document.querySelectorAll('.option-btn').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.option-btn').forEach(item => item.classList.remove('selected'));
            button.classList.add('selected');
            selectedOptionId = Number(button.dataset.optionId);
        });
    });

    document.querySelector('#submit-answer').addEventListener('click', submitCurrentAnswer);
}

async function submitCurrentAnswer() {
    const question = state.questions[currentIndex];
    const isChoice = state.session.test_type === 'choice';
    const payload = isChoice
        ? { answer_option_id: selectedOptionId }
        : { user_answer_text: document.querySelector('#manual-answer').value };

    if (isChoice && !selectedOptionId) {
        setStatus('Выберите вариант ответа.', true);
        return;
    }
    if (!isChoice && !payload.user_answer_text.trim()) {
        setStatus('Введите ответ.', true);
        return;
    }

    try {
        await fetchJson(`/api/tests/${sessionId}/questions/${question.id}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        setStatus('Ответ сохранён.');
        currentIndex += 1;
        progressFill.style.width = `${(currentIndex / state.questions.length) * 100}%`;
        renderQuestion();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function finishTest() {
    try {
        setStatus('Завершение теста и формирование PDF-отчёта...');
        const data = await fetchJson(`/api/tests/${sessionId}/finish`, { method: 'POST' });
        window.location.href = data.result_url;
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function init() {
    state = await fetchJson(`/api/tests/${sessionId}/state`);
    currentIndex = firstUnansweredIndex(state.questions);
    renderQuestion();
}

init().catch(error => setStatus(error.message, true));
