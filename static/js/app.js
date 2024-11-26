'use strict';

let currentContentId = null;
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const viewButtons = document.querySelectorAll('[data-view]');
    const saveButton = document.getElementById('saveToNotion');
    const propertiesForm = document.getElementById('propertiesForm');

    if (urlForm) {
        urlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = document.getElementById('urlInput').value;
            await handleUrlSubmit(url);
        });
    }

    if (viewButtons) {
        viewButtons.forEach(button => {
            button.addEventListener('click', () => {
                const view = button.dataset.view;
                updateViewMode(view);
            });
        });
    }

    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            if (!currentContentId) return;
            await handleSaveToNotion();
        });
    }

    // Fetch initial Notion properties
    fetchNotionProperties();
});

// Handle URL submission
async function handleUrlSubmit(url) {
    try {
        showLoading('URLからコンテンツを抽出中...');
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok || data.status === 'error') {
            throw new Error(data.message || data.error || 'Failed to scrape URL');
        }
        
        currentContentId = data.data.id;
        updatePreview(data.data);
        
        // Auto-fill Notion properties
        const form = document.getElementById('propertiesForm');
        if (form) {
            const scrapedData = data.data;
            
            // Set URL
            const urlInput = form.querySelector('#notion_URL');
            if (urlInput) urlInput.value = scrapedData.url;
            
            // Set title
            const titleInput = form.querySelector('#notion_titlename');
            if (titleInput) titleInput.value = scrapedData.title;
            
            // Set date to current date
            const dateInput = form.querySelector('#notion_日付');
            if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
            
            // Set author/site name
            const authorInput = form.querySelector('#notion_発言者');
            if (authorInput) authorInput.value = scrapedData.author || scrapedData.site_name || '';
        }
        
        document.getElementById('saveToNotion').disabled = false;
        document.getElementById('contentPreview').classList.remove('d-none');
    } catch (error) {
        console.error('Error:', error);
        showError('URLの抽出に失敗しました: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Handle translation
async function handleTranslate() {
    if (!currentContentId) return;
    
    try {
        showLoading('翻訳中...');
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content_id: currentContentId })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Translation failed');
        }
        
        updateTranslatedContent(data);
    } catch (error) {
        console.error('Error:', error);
        showError('翻訳に失敗しました: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Save to Notion
async function handleSaveToNotion() {
    if (!currentContentId) return;
    
    try {
        showLoading('Notionに保存中...');
        const properties = getNotionProperties();
        const response = await fetch('/api/save-to-notion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content_id: currentContentId,
                properties: properties
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to save to Notion');
        }
        
        showSuccess('Notionに保存しました！');
    } catch (error) {
        console.error('Error:', error);
        showError('Notionへの保存に失敗しました: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Fetch Notion properties
async function fetchNotionProperties() {
    try {
        const response = await fetch('/api/notion/properties');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to fetch properties');
        }
        
        if (data.status === 'success') {
            updatePropertiesForm(data.data);
        }
    } catch (error) {
        console.error('Error fetching Notion properties:', error);
        showError('Notionプロパティの取得に失敗しました');
    }
}

// Update preview content
function updatePreview(data) {
    const originalContent = document.getElementById('originalContent');
    if (originalContent) {
        const titleElem = originalContent.querySelector('.content-title');
        const bodyElem = originalContent.querySelector('.content-body');
        
        if (titleElem) titleElem.textContent = data.title;
        if (bodyElem) bodyElem.innerHTML = data.content;
    }
}

function updateTranslatedContent(data) {
    const translatedContent = document.getElementById('translatedContent');
    if (translatedContent) {
        const titleElem = translatedContent.querySelector('.content-title');
        const bodyElem = translatedContent.querySelector('.content-body');
        
        if (titleElem) titleElem.textContent = data.translated_title;
        if (bodyElem) bodyElem.innerHTML = data.translated_content;
        
        translatedContent.classList.remove('d-none');
    }
}

function updateViewMode(mode) {
    const originalContent = document.getElementById('originalContent');
    const translatedContent = document.getElementById('translatedContent');
    const viewButtons = document.querySelectorAll('[data-view]');
    
    viewButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.view === mode);
    });

    if (originalContent && translatedContent) {
        switch (mode) {
            case 'original':
                originalContent.classList.remove('d-none');
                translatedContent.classList.add('d-none');
                break;
            case 'translated':
                if (!translatedContent.querySelector('.content-title').textContent) {
                    handleTranslate();
                }
                originalContent.classList.add('d-none');
                translatedContent.classList.remove('d-none');
                break;
            case 'both':
                if (!translatedContent.querySelector('.content-title').textContent) {
                    handleTranslate();
                }
                originalContent.classList.remove('d-none');
                translatedContent.classList.remove('d-none');
                break;
        }
    }
}

// Helper functions
function showLoading(message) {
    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.textContent = message;
    }
    loadingModal.show();
}

function hideLoading() {
    loadingModal.hide();
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>エラー:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    setTimeout(() => alertDiv.remove(), 5000);
}

function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <strong>成功:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    setTimeout(() => alertDiv.remove(), 5000);
}

function updatePropertiesForm(properties) {
    const form = document.getElementById('propertiesForm');
    if (!form) return;
    
    form.innerHTML = '';
    
    Object.entries(properties).forEach(([name, prop]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = name;
        
        let input;
        
        switch (prop.type) {
            case 'select':
            case 'multi_select':
                input = document.createElement('select');
                input.className = 'form-select';
                if (prop.type === 'multi_select') {
                    input.multiple = true;
                }
                if (prop.options) {
                    prop.options.forEach(option => {
                        const opt = document.createElement('option');
                        opt.value = option.value;
                        opt.textContent = option.label;
                        input.appendChild(opt);
                    });
                }
                break;
            case 'date':
                input = document.createElement('input');
                input.type = 'date';
                input.className = 'form-control';
                break;
            default:
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
        }
        
        input.name = name;
        input.id = `notion_${name}`;
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        form.appendChild(formGroup);
    });
}

function getNotionProperties() {
    const form = document.getElementById('propertiesForm');
    if (!form) return {};
    
    const formData = new FormData(form);
    const properties = {};
    
    for (const [name, value] of formData.entries()) {
        if (value) {
            properties[name] = value;
        }
    }
    
    return properties;
}
