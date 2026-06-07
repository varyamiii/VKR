const categoryList = document.querySelector('#category-list');
const accentList = document.querySelector('#accent-list');
const noiseList = document.querySelector('#noise-list');
const form = document.querySelector('#test-setup-form');
const statusText = document.querySelector('#setup-status');

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

function renderChecks(container, rows, name) {
    container.innerHTML = '';
    rows.forEach(row => {
        const label = document.createElement('label');
        label.className = 'check-item';
        label.innerHTML = `
            <input type="checkbox" name="${name}" value="${row.id}" checked>
            <span>${row.name_ru}</span>
        `;
        container.appendChild(label);
    });
}

function selectedValues(name) {
    return [...document.querySelectorAll(`input[name="${name}"]:checked`)].map(item => Number(item.value));
}

async function init() {
    const [categories, accents, noises] = await Promise.all([
        fetchJson('/api/categories'),
        fetchJson('/api/accents'),
        fetchJson('/api/noise-profiles'),
    ]);
    renderChecks(categoryList, categories, 'category');
    renderChecks(accentList, accents, 'accent');
    renderChecks(noiseList, noises, 'noise');
}

form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    setStatus('Формирование теста и генерация аудиофайлов...');

    try {
        const payload = {
            test_type: document.querySelector('#test-type').value,
            category_ids: selectedValues('category'),
            accent_ids: selectedValues('accent'),
            noise_profile_ids: selectedValues('noise'),
            questions_count: Number(document.querySelector('#questions-count').value || 10),
        };
        if (!payload.category_ids.length || !payload.accent_ids.length || !payload.noise_profile_ids.length) {
            throw new Error('Нужно выбрать хотя бы одну категорию, один акцент и один вариант шума.');
        }
        const data = await fetchJson('/api/tests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        window.location.href = data.run_url;
    } catch (error) {
        setStatus(error.message, true);
        button.disabled = false;
    }
});

init().catch(error => setStatus(error.message, true));
