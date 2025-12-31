// Developer Panel JavaScript

let originalSettings = {};
let currentSettings = {};

// Settings schema with categories
const settingsSchema = {
    'Application': {
        icon: '📱',
        settings: [
            { key: 'APP_NAME', label: 'App Name', type: 'text', default: 'GoldenIT Microsoft Entra', help: 'Application display name' },
            { key: 'APP_VERSION', label: 'Version', type: 'text', default: 'v-1.2', help: 'Current version number' },
            { key: 'APP_TITLE', label: 'App Title', type: 'text', default: 'GoldenIT Microsoft Entra v-1.2', help: 'Full application title' },
            { key: 'DEBUG_MODE', label: 'Debug Mode', type: 'checkbox', default: false, help: 'Enable debug logging' }
        ]
    },
    'Server': {
        icon: '🖥️',
        settings: [
            { key: 'SERVER_HOST', label: 'Host', type: 'text', default: '0.0.0.0', help: 'Server bind address' },
            { key: 'SERVER_PORT', label: 'Port', type: 'number', default: 5000, help: 'Server port (requires restart)' },
            { key: 'REQUEST_TIMEOUT', label: 'Request Timeout (seconds)', type: 'number', default: 30, help: 'Maximum request duration' },
            { key: 'MAX_CONTENT_LENGTH', label: 'Max Upload Size (MB)', type: 'number', default: 16, help: 'Maximum file upload size' }
        ]
    },
    'Security': {
        icon: '🔒',
        settings: [
            { key: 'SESSION_TIMEOUT', label: 'Session Timeout (minutes)', type: 'number', default: 60, help: 'User session expiration' },
            { key: 'MAX_LOGIN_ATTEMPTS', label: 'Max Login Attempts', type: 'number', default: 5, help: 'Failed login attempts before lockout' },
            { key: 'CSRF_ENABLED', label: 'CSRF Protection', type: 'checkbox', default: true, help: 'Enable CSRF token validation' },
            { key: 'RATE_LIMIT_PER_HOUR', label: 'Rate Limit (per hour)', type: 'number', default: 200, help: 'Maximum API requests per hour' }
        ]
    },
    'Database': {
        icon: '🗄️',
        settings: [
            { key: 'DATABASE_PATH', label: 'Database Path', type: 'text', default: 'data/app.db', help: 'SQLite database file location' },
            { key: 'BACKUP_DIR', label: 'Backup Directory', type: 'text', default: 'backups', help: 'Backup storage location' },
            { key: 'AUTO_BACKUP_HOURS', label: 'Auto Backup Interval (hours)', type: 'number', default: 24, help: 'Automatic backup frequency' },
            { key: 'BACKUP_RETENTION_DAYS', label: 'Backup Retention (days)', type: 'number', default: 30, help: 'How long to keep backups' }
        ]
    },
    'License': {
        icon: '🔑',
        settings: [
            { key: 'LICENSE_KEY_LENGTH', label: 'License Key Length', type: 'number', default: 32, help: 'Characters in license key' },
            { key: 'MAX_PCS_PER_LICENSE', label: 'Max PCs per License', type: 'number', default: 5, help: 'Maximum PC activations' },
            { key: 'LICENSE_EXPIRY_WARNING_DAYS', label: 'Expiry Warning (days)', type: 'number', default: 7, help: 'Days before expiry to warn' },
            { key: 'HARDWARE_ID_INCLUDE_MAC', label: 'Include MAC in Hardware ID', type: 'checkbox', default: true, help: 'Use MAC address' },
            { key: 'HARDWARE_ID_INCLUDE_MB', label: 'Include Motherboard ID', type: 'checkbox', default: true, help: 'Use motherboard serial' }
        ]
    },
    'Screenshots': {
        icon: '📸',
        settings: [
            { key: 'SCREENSHOT_DIR', label: 'Screenshot Directory', type: 'text', default: 'screenshots', help: 'Screenshot storage location' },
            { key: 'SCREENSHOT_INTERVAL', label: 'Capture Interval (minutes)', type: 'number', default: 10, help: 'Time between screenshots' },
            { key: 'THUMBNAIL_WIDTH', label: 'Thumbnail Width (px)', type: 'number', default: 300, help: 'Thumbnail image width' },
            { key: 'THUMBNAIL_HEIGHT', label: 'Thumbnail Height (px)', type: 'number', default: 200, help: 'Thumbnail image height' },
            { key: 'MAX_SCREENSHOT_AGE_DAYS', label: 'Max Age (days)', type: 'number', default: 90, help: 'Auto-delete old screenshots' },
            { key: 'AUTO_CLEANUP_ENABLED', label: 'Auto Cleanup', type: 'checkbox', default: true, help: 'Automatically delete old screenshots' }
        ]
    },
    'Email': {
        icon: '📧',
        settings: [
            { key: 'EMAIL_VALIDATION_PATTERN', label: 'Validation Regex', type: 'textarea', default: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', help: 'Email format validation pattern' },
            { key: 'MAX_EMAILS_PER_UPLOAD', label: 'Max Emails per Upload', type: 'number', default: 10000, help: 'Maximum emails in single upload' },
            { key: 'EMAIL_BATCH_SIZE', label: 'Processing Batch Size', type: 'number', default: 100, help: 'Emails processed in one batch' },
            { key: 'DUPLICATE_CHECK_ENABLED', label: 'Duplicate Check', type: 'checkbox', default: true, help: 'Prevent duplicate emails' }
        ]
    },
    'API': {
        icon: '🔌',
        settings: [
            { key: 'API_RATE_LIMIT_USER', label: 'Rate Limit per User (per hour)', type: 'number', default: 100, help: 'API requests per user' },
            { key: 'API_TIMEOUT', label: 'API Timeout (seconds)', type: 'number', default: 30, help: 'API request timeout' },
            { key: 'PAGINATION_DEFAULT_LIMIT', label: 'Default Pagination Limit', type: 'number', default: 100, help: 'Items per page' },
            { key: 'PAGINATION_MAX_LIMIT', label: 'Max Pagination Limit', type: 'number', default: 1000, help: 'Maximum items per page' },
            { key: 'API_VERSION', label: 'API Version', type: 'text', default: 'v1', help: 'Current API version' }
        ]
    },
    'Performance': {
        icon: '⚡',
        settings: [
            { key: 'WORKER_THREADS', label: 'Worker Threads', type: 'number', default: 4, help: 'Number of worker threads' },
            { key: 'CONNECTION_POOL_SIZE', label: 'Connection Pool Size', type: 'number', default: 10, help: 'Database connection pool' },
            { key: 'CACHE_TTL', label: 'Cache TTL (seconds)', type: 'number', default: 300, help: 'Cache time-to-live' },
            { key: 'MAX_CONCURRENT_REQUESTS', label: 'Max Concurrent Requests', type: 'number', default: 100, help: 'Maximum simultaneous requests' }
        ]
    },
    'UI Theme': {
        icon: '🎨',
        settings: [
            { key: 'PRIMARY_COLOR', label: 'Primary Color', type: 'color', default: '#007bff', help: 'Main theme color' },
            { key: 'SECONDARY_COLOR', label: 'Secondary Color', type: 'color', default: '#6c757d', help: 'Secondary theme color' },
            { key: 'ACCENT_COLOR', label: 'Accent Color', type: 'color', default: '#28a745', help: 'Accent/highlight color' },
            { key: 'BACKGROUND_COLOR', label: 'Background Color', type: 'color', default: '#1a252f', help: 'Page background color' },
            { key: 'FONT_FAMILY', label: 'Font Family', type: 'text', default: 'Arial, sans-serif', help: 'Default font' },
            { key: 'FONT_SIZE', label: 'Font Size (px)', type: 'number', default: 14, help: 'Base font size' },
            { key: 'DARK_MODE_DEFAULT', label: 'Dark Mode by Default', type: 'checkbox', default: true, help: 'Use dark theme' }
        ]
    },
    'Feature Toggles': {
        icon: '🎛️',
        settings: [
            { key: 'API_MODE_ENABLED', label: 'API Mode', type: 'checkbox', default: true, help: 'Enable API-based data fetching' },
            { key: 'MANUAL_MODE_ENABLED', label: 'Manual Mode', type: 'checkbox', default: true, help: 'Enable manual file mode' },
            { key: 'SCREENSHOTS_ENABLED', label: 'Screenshots', type: 'checkbox', default: true, help: 'Enable screenshot capture' },
            { key: 'HEARTBEAT_ENABLED', label: 'Heartbeat Monitoring', type: 'checkbox', default: true, help: 'Enable PC heartbeat' },
            { key: 'NOTIFICATIONS_ENABLED', label: 'Notifications', type: 'checkbox', default: true, help: 'Enable notification system' },
            { key: 'AUDIT_LOG_ENABLED', label: 'Audit Logging', type: 'checkbox', default: true, help: 'Log all user actions' },
            { key: 'SOFT_DELETE_ENABLED', label: 'Soft Delete', type: 'checkbox', default: true, help: 'Use soft delete for records' },
            { key: 'PAGINATION_ENABLED', label: 'Pagination', type: 'checkbox', default: true, help: 'Enable pagination on lists' }
        ]
    }
};

// Load all settings from server
async function loadAllSettings() {
    const accordion = document.getElementById('settingsAccordion');
    accordion.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading settings...</p></div>';
    
    try {
        const response = await fetch('/api/admin/settings');
        if (!response.ok) {
            throw new Error('Failed to load settings');
        }
        
        const data = await response.json();
        originalSettings = data.settings || {};
        currentSettings = JSON.parse(JSON.stringify(originalSettings));
        
        renderSettings();
    } catch (error) {
        console.error('Error loading settings:', error);
        accordion.innerHTML = `<div class="error-message">❌ Error loading settings: ${error.message}</div>`;
    }
}

// Render settings UI
function renderSettings() {
    const accordion = document.getElementById('settingsAccordion');
    accordion.innerHTML = '';
    
    for (const [category, config] of Object.entries(settingsSchema)) {
        const section = document.createElement('div');
        section.className = 'setting-section';
        section.innerHTML = `
            <div class="section-header" onclick="toggleSection(this)">
                <h3>
                    <span class="category-icon">${config.icon}</span>
                    ${category}
                    <span class="setting-count">(${config.settings.length})</span>
                </h3>
                <span class="section-toggle">▼</span>
            </div>
            <div class="section-content">
                ${renderCategorySettings(category, config.settings)}
            </div>
        `;
        accordion.appendChild(section);
    }
}

// Render settings for a category
function renderCategorySettings(category, settings) {
    if (category === 'Feature Toggles') {
        // Special grid layout for toggles
        let html = '<div class="setting-grid">';
        for (const setting of settings) {
            const value = currentSettings[setting.key] !== undefined ? currentSettings[setting.key] : setting.default;
            const checked = value ? 'checked' : '';
            html += `
                <div class="toggle-item">
                    <input type="checkbox" id="${setting.key}" ${checked} onchange="updateSetting('${setting.key}', this.checked)">
                    <label for="${setting.key}" title="${setting.help}">${setting.label}</label>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }
    
    let html = '';
    for (const setting of settings) {
        const value = currentSettings[setting.key] !== undefined ? currentSettings[setting.key] : setting.default;
        const inputHtml = renderInput(setting, value);
        
        html += `
            <div class="setting-item" id="item-${setting.key}">
                <label for="${setting.key}">
                    ${setting.label}
                    <span class="setting-status" id="status-${setting.key}"></span>
                </label>
                <div class="setting-help">${setting.help}</div>
                ${inputHtml}
                <div class="setting-item-actions">
                    <button class="btn-save-setting" onclick="saveSingleSetting('${setting.key}')">💾 Save</button>
                    <button class="btn-reset-setting" onclick="resetSingleSetting('${setting.key}', ${JSON.stringify(setting.default)})">🔄 Reset</button>
                </div>
            </div>
        `;
    }
    return html;
}

// Render input based on type
function renderInput(setting, value) {
    const escapedValue = String(value).replace(/"/g, '&quot;');
    
    switch (setting.type) {
        case 'checkbox':
            const checked = value ? 'checked' : '';
            return `<input type="checkbox" id="${setting.key}" ${checked} onchange="updateSetting('${setting.key}', this.checked)">`;
        
        case 'number':
            return `<input type="number" id="${setting.key}" value="${value}" onchange="updateSetting('${setting.key}', Number(this.value))">`;
        
        case 'color':
            return `<input type="color" id="${setting.key}" value="${value}" onchange="updateSetting('${setting.key}', this.value)">`;
        
        case 'textarea':
            return `<textarea id="${setting.key}" onchange="updateSetting('${setting.key}', this.value)">${value}</textarea>`;
        
        default:  // text
            return `<input type="text" id="${setting.key}" value="${escapedValue}" onchange="updateSetting('${setting.key}', this.value)">`;
    }
}

// Update setting in memory
function updateSetting(key, value) {
    currentSettings[key] = value;
    updateStatus(key, 'modified');
}

// Save single setting
async function saveSingleSetting(key) {
    const value = currentSettings[key];
    
    try {
        const response = await fetch('/api/admin/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                settings: { [key]: value }
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save setting');
        }
        
        originalSettings[key] = value;
        updateStatus(key, 'saved');
        
        setTimeout(() => updateStatus(key, ''), 2000);
        
        alert(`✅ Setting "${key}" saved successfully!`);
    } catch (error) {
        console.error('Error saving setting:', error);
        updateStatus(key, 'error');
        alert(`❌ Error saving setting: ${error.message}`);
    }
}

// Reset single setting
function resetSingleSetting(key, defaultValue) {
    if (confirm(`Reset "${key}" to default value?`)) {
        currentSettings[key] = defaultValue;
        document.getElementById(key).value = defaultValue;
        if (document.getElementById(key).type === 'checkbox') {
            document.getElementById(key).checked = defaultValue;
        }
        updateStatus(key, 'modified');
    }
}

// Save all settings
async function saveAllSettings() {
    if (!confirm('Save all modified settings?')) return;
    
    try {
        const response = await fetch('/api/admin/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                settings: currentSettings
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save settings');
        }
        
        originalSettings = JSON.parse(JSON.stringify(currentSettings));
        alert('✅ All settings saved successfully!');
        loadAllSettings(); // Reload to show updated status
    } catch (error) {
        console.error('Error saving settings:', error);
        alert(`❌ Error saving settings: ${error.message}`);
    }
}

// Reset all to defaults
async function resetToDefaults() {
    if (!confirm('⚠️ Reset ALL settings to factory defaults?\n\nThis cannot be undone!')) return;
    
    try {
        const response = await fetch('/api/admin/settings/reset', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to reset settings');
        }
        
        alert('✅ Settings reset to defaults!');
        loadAllSettings();
    } catch (error) {
        console.error('Error resetting settings:', error);
        alert(`❌ Error resetting settings: ${error.message}`);
    }
}

// Export settings
async function exportSettings() {
    try {
        const response = await fetch('/api/admin/settings/export');
        if (!response.ok) {
            throw new Error('Failed to export settings');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `settings-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        alert('✅ Settings exported successfully!');
    } catch (error) {
        console.error('Error exporting settings:', error);
        alert(`❌ Error exporting settings: ${error.message}`);
    }
}

// Import settings
async function importSettings(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!confirm(`Import settings from "${file.name}"?\n\nThis will overwrite current settings!`)) {
        event.target.value = '';
        return;
    }
    
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            const data = JSON.parse(e.target.result);
            
            const response = await fetch('/api/admin/settings/import', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error('Failed to import settings');
            }
            
            alert('✅ Settings imported successfully!');
            loadAllSettings();
        } catch (error) {
            console.error('Error importing settings:', error);
            alert(`❌ Error importing settings: ${error.message}`);
        }
    };
    reader.readAsText(file);
    event.target.value = '';
}

// Toggle section expand/collapse
function toggleSection(header) {
    header.classList.toggle('active');
    const content = header.nextElementSibling;
    content.classList.toggle('show');
}

// Update status indicator
function updateStatus(key, status) {
    const statusEl = document.getElementById(`status-${key}`);
    if (!statusEl) return;
    
    statusEl.className = 'setting-status';
    
    switch (status) {
        case 'saved':
            statusEl.className += ' saved';
            statusEl.textContent = '✓ Saved';
            break;
        case 'modified':
            statusEl.className += ' modified';
            statusEl.textContent = '● Modified';
            break;
        case 'error':
            statusEl.className += ' error';
            statusEl.textContent = '✗ Error';
            break;
        default:
            statusEl.textContent = '';
    }
}

// Filter settings
function filterSettings() {
    const query = document.getElementById('settingsSearch').value.toLowerCase();
    const sections = document.querySelectorAll('.setting-section');
    
    sections.forEach(section => {
        const content = section.querySelector('.section-content');
        const items = content.querySelectorAll('.setting-item, .toggle-item');
        let visibleCount = 0;
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(query)) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        // Show/hide entire section based on matches
        section.style.display = visibleCount > 0 ? '' : 'none';
    });
}

// Update sidebar active state
function updateSidebarActive() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar .menu li').forEach(item => {
        item.classList.remove('active');
        const link = item.querySelector('a');
        if (link && link.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
}
