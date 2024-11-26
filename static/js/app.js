'use strict';

let currentContentId = null;
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    const urlForm = document.getElementById('urlForm');
    const viewButtons = document.querySelectorAll('[data-view]');
    const saveButton = document.getElementById('saveToNotion');

    urlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = document.getElementById('urlInput').value;
        await handleUrlSubmit(url);
    });

    viewButtons.forEach(button => {
        button.addEventListener('click', () => {
            const view = button.dataset.view;
            updateViewMode(view);
        });
    });

    saveButton.addEventListener('click', async () => {
        if (!currentContentId) return;
        await handleSaveToNotion();
    });
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
        
        if (!response.ok) throw new Error('Failed to scrape URL');
        
        const data = await response.json();
        currentContentId = data.id;
        updatePreview(data);
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
        
        if (!response.ok) throw new Error('Translation failed');
        
        const data = await response.json();
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
        
        if (!response.ok) throw new Error('Failed to save to Notion');
        
        const data = await response.json();
        showSuccess('Notionに保存しました！');
    } catch (error) {
        console.error('Error:', error);
        showError('Notionへの保存に失敗しました: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Update preview content
function updatePreview(data) {
    const originalContent = document.getElementById('originalContent');
    originalContent.querySelector('.content-title').textContent = data.title;
    originalContent.querySelector('.content-body').innerHTML = data.content;
}

function updateTranslatedContent(data) {
    const translatedContent = document.getElementById('translatedContent');
    translatedContent.querySelector('.content-title').textContent = data.translated_title;
    translatedContent.querySelector('.content-body').innerHTML = data.translated_content;
}

function updateViewMode(mode) {
    const originalContent = document.getElementById('originalContent');
    const translatedContent = document.getElementById('translatedContent');
    const viewButtons = document.querySelectorAll('[data-view]');
    
    viewButtons.forEach(button => {
        button.classList.toggle('active', button.dataset.view === mode);
    });

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
            originalContent.classList.add('col-6');
            translatedContent.classList.add('col-6');
            break;
    }
}

// Helper functions
function showLoading(message) {
    document.getElementById('loadingMessage').textContent = message;
    loadingModal.show();
}

function hideLoading() {
    loadingModal.hide();
}

function showError(message, type = 'error') {
    const errorDiv = document.createElement('div');
    errorDiv.className = `alert alert-danger alert-dismissible fade show`;
    errorDiv.role = 'alert';
    
    let errorMessage = message;
    if (typeof message === 'object' && message.message) {
        errorMessage = message.message;
        if (message.details) {
            errorMessage += `\n${message.details}`;
        }
    }
    
    errorDiv.innerHTML = `
        <strong>エラー:</strong> ${errorMessage}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    container.insertBefore(errorDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.role = 'alert';
    successDiv.innerHTML = `
        <strong>成功:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert at the top of the container
    const container = document.querySelector('.container');
    container.insertBefore(successDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        successDiv.remove();
    }, 5000);
}

function getNotionProperties() {
    // Implement this based on your Notion properties form structure
    const form = document.getElementById('propertiesForm');
    const formData = new FormData(form);
    return Object.fromEntries(formData);
}
