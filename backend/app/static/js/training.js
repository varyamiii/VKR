const categorySelect = document.querySelector('#category-select');
const phraseSelect = document.querySelector('#phrase-select');
const accentSelect = document.querySelector('#accent-select');
const noiseSelect = document.querySelector('#noise-select');
const form = document.querySelector('#training-form');
const statusText = document.querySelector('#training-status');
const result = document.querySelector('#training-result');

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

function fillSelect(select, rows, labelFn) {
    select.innerHTML = '';
    rows.forEach(row => {
        const option = document.createElement('option');
        option.value = row.id;
        option.textContent = labelFn(row);
        select.appendChild(option);
    });
}

async function loadPhrases() {
    const categoryId = categorySelect.value;
    const phrases = await fetchJson(`/api/phrases?category_id=${categoryId}`);
    fillSelect(phraseSelect, phrases, row => row.phrase_text);
}

async function init() {
    const [categories, accents, noises] = await Promise.all([
        fetchJson('/api/categories'),
        fetchJson('/api/accents'),
        fetchJson('/api/noise-profiles'),
    ]);
    fillSelect(categorySelect, categories, row => row.name_ru);
    fillSelect(accentSelect, accents, row => row.name_ru);
    fillSelect(noiseSelect, noises, row => row.name_ru);
    await loadPhrases();
}

categorySelect.addEventListener('change', () => {
    loadPhrases().catch(error => setStatus(error.message, true));
});

form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    setStatus('Генерация аудио... Это может занять некоторое время.');

    try {
        const payload = {
            phrase_id: Number(phraseSelect.value),
            accent_id: Number(accentSelect.value),
            noise_profile_id: Number(noiseSelect.value),
            speed: Number(document.querySelector('#speed-input').value || 1.0),
        };
        const data = await fetchJson('/api/training/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        result.className = 'audio-box';
        result.innerHTML = `
            <p class="phrase-text">${data.phrase_text}</p>
            <p>Акцент: ${data.accent_name}</p>
            <p>Шум: ${data.noise_name}</p>
            <audio controls src="${data.audio_url}?t=${Date.now()}"></audio>
        `;
        setStatus('Аудиофрагмент успешно сформирован.');
    } catch (error) {
        setStatus(error.message, true);
    } finally {
        button.disabled = false;
    }
});

init().catch(error => setStatus(error.message, true));
