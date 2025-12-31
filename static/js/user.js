// User Dashboard JavaScript

let activityChart;

document.addEventListener('DOMContentLoaded', () => {
    loadUserActivities();
    loadStats();
    loadSettings();
});

// ===== Panel Navigation =====

function showAccountsPanel() {
    hideAllPanels();
    document.getElementById('accountsPanel').style.display = 'block';
    loadAccounts();
}

function showEmailsPanel() {
    hideAllPanels();
    document.getElementById('emailsPanel').style.display = 'block';
    loadEmails();
}

function showSettingsPanel() {
    hideAllPanels();
    document.getElementById('settingsPanel').style.display = 'block';
    loadSettings();
}

function showPCsPanel() {
    hideAllPanels();
    document.getElementById('pcsPanel').style.display = 'block';
    loadPCs();
}

function hideAllPanels() {
    document.getElementById('accountsPanel').style.display = 'none';
    document.getElementById('emailsPanel').style.display = 'none';
    document.getElementById('settingsPanel').style.display = 'none';
    document.getElementById('pcsPanel').style.display = 'none';
}

// ===== Feature 2: Account Management =====

async function loadAccounts() {
    try {
        const response = await fetch('/api/user/accounts');
        if (!response.ok) throw new Error('Failed to load accounts');
        const data = await response.json();
        renderAccountsTable(data.accounts);
    } catch (error) {
        console.error('Error loading accounts:', error);
        alert('Error loading accounts');
    }
}

function renderAccountsTable(accounts) {
    const tbody = document.getElementById('accountsTableBody');
    if (!accounts || accounts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No accounts uploaded yet</td></tr>';
        return;
    }
    tbody.innerHTML = accounts.map(acc => `
        <tr>
            <td>${acc.email}</td>
            <td>${acc.twofa_secret ? '✅' : '❌'}</td>
            <td>${acc.proxy || 'None'}</td>
            <td><span class="badge badge-success">Active</span></td>
            <td><button class="btn btn-danger btn-sm" onclick="deleteAccount(${acc.id})">Delete</button></td>
        </tr>
    `).join('');
}

async function uploadAccounts() {
    const input = document.getElementById('accountsInput').value.trim();
    if (!input) {
        alert('Please enter accounts');
        return;
    }
    
    const lines = input.split('\n');
    const accounts = [];
    
    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        const parts = line.split(',');
        if (parts.length >= 2) {
            accounts.push({
                email: parts[0].trim(),
                password: parts[1].trim(),
                '2fa_secret': parts[2] ? parts[2].trim() : '',
                proxy: parts[3] ? parts[3].trim() : ''
            });
        }
    }
    
    if (accounts.length === 0) {
        alert('No valid accounts found');
        return;
    }
    
    try {
        const response = await fetch('/api/user/accounts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(accounts)
        });
        if (!response.ok) throw new Error('Upload failed');
        const data = await response.json();
        alert(`${data.count} accounts uploaded successfully!`);
        document.getElementById('accountsInput').value = '';
        loadAccounts();
    } catch (error) {
        console.error('Error uploading accounts:', error);
        alert('Error uploading accounts');
    }
}

async function deleteAccount(accountId) {
    if (!confirm('Delete this account?')) return;
    try {
        const response = await fetch(`/api/user/accounts?account_id=${accountId}`, {method: 'DELETE'});
        if (!response.ok) throw new Error('Delete failed');
        alert('Account deleted');
        loadAccounts();
    } catch (error) {
        console.error('Error deleting account:', error);
        alert('Error deleting account');
    }
}

// ===== Feature 2: Email Management =====

async function loadEmails() {
    try {
        const response = await fetch('/api/user/emails');
        if (!response.ok) throw new Error('Failed to load emails');
        const data = await response.json();
        renderEmailsTable(data.emails);
        updateEmailCounts(data.emails);
    } catch (error) {
        console.error('Error loading emails:', error);
        alert('Error loading emails');
    }
}

function renderEmailsTable(emails) {
    const tbody = document.getElementById('emailsTableBody');
    if (!emails || emails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No emails uploaded yet</td></tr>';
        return;
    }
    tbody.innerHTML = emails.slice(0, 100).map(email => `
        <tr>
            <td>${email.email}</td>
            <td>${email.is_processed ? '<span class="badge badge-success">Processed</span>' : '<span class="badge badge-info">Pending</span>'}</td>
            <td>${email.processed_at || 'N/A'}</td>
            <td><button class="btn btn-danger btn-sm" onclick="deleteEmail(${email.id})">Delete</button></td>
        </tr>
    `).join('');
}

function updateEmailCounts(emails) {
    document.getElementById('emailCount').textContent = emails.length;
    document.getElementById('emailPending').textContent = emails.filter(e => !e.is_processed).length;
    document.getElementById('emailProcessed').textContent = emails.filter(e => e.is_processed).length;
}

async function uploadEmails() {
    const input = document.getElementById('emailsInput').value.trim();
    if (!input) {
        alert('Please enter emails');
        return;
    }
    
    const emails = input.split('\n').map(e => e.trim()).filter(e => e && e.includes('@'));
    
    if (emails.length === 0) {
        alert('No valid emails found');
        return;
    }
    
    try {
        const response = await fetch('/api/user/emails', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(emails)
        });
        if (!response.ok) throw new Error('Upload failed');
        const data = await response.json();
        alert(`${data.count} emails uploaded successfully!`);
        document.getElementById('emailsInput').value = '';
        loadEmails();
    } catch (error) {
        console.error('Error uploading emails:', error);
        alert('Error uploading emails');
    }
}

async function deleteEmail(emailId) {
    if (!confirm('Delete this email?')) return;
    try {
        const response = await fetch(`/api/user/emails?email_id=${emailId}`, {method: 'DELETE'});
        if (!response.ok) throw new Error('Delete failed');
        alert('Email deleted');
        loadEmails();
    } catch (error) {
        console.error('Error deleting email:', error);
        alert('Error deleting email');
    }
}

// ===== Feature 2: Settings Management =====

async function loadSettings() {
    try {
        const response = await fetch('/api/user/settings');
        if (!response.ok) throw new Error('Failed to load settings');
        const data = await response.json();
        const settings = data.settings;
        
        document.getElementById('emailsPerAccount').value = settings.emails_per_account || 10;
        document.getElementById('intervalMinutes').value = settings.interval_minutes || 10;
        document.getElementById('maxBrowsers').value = settings.max_browsers || 3;
        document.getElementById('apiModeEnabled').checked = settings.use_api_mode || false;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function saveSettings() {
    const settings = {
        emails_per_account: parseInt(document.getElementById('emailsPerAccount').value),
        interval_minutes: parseInt(document.getElementById('intervalMinutes').value),
        max_browsers: parseInt(document.getElementById('maxBrowsers').value),
        api_mode_enabled: document.getElementById('apiModeEnabled').checked
    };
    
    try {
        const response = await fetch('/api/user/settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(settings)
        });
        if (!response.ok) throw new Error('Save failed');
        alert('Settings saved successfully!');
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Error saving settings');
    }
}

// ===== Feature 6: PC Monitoring =====

async function loadPCs() {
    try {
        const response = await fetch('/api/pc/status');
        if (!response.ok) throw new Error('Failed to load PCs');
        const data = await response.json();
        renderPCsTable(data.pcs);
    } catch (error) {
        console.error('Error loading PCs:', error);
        alert('Error loading PCs');
    }
}

function renderPCsTable(pcs) {
    const tbody = document.getElementById('pcsTableBody');
    if (!pcs || pcs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No PCs connected yet</td></tr>';
        return;
    }
    tbody.innerHTML = pcs.map(pc => `
        <tr>
            <td>${pc.pc_name}</td>
            <td>${pc.status === 'online' ? '<span class="badge badge-success">Online</span>' : '<span class="badge badge-danger">Offline</span>'}</td>
            <td>${pc.current_account || 'Idle'}</td>
            <td>${formatDate(pc.last_heartbeat)}</td>
        </tr>
    `).join('');
}

// ===== Original Functions =====

async function loadUserActivities() {
    try {
        const response = await fetch('/api/user/activities?limit=50');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const activities = await response.json();
        renderActivitiesTable(activities);
    } catch (error) {
        console.error('Error loading activities:', error);
        // Don't show alert for this, just log it
    }
}

function renderActivitiesTable(activities) {
    const tbody = document.getElementById('activitiesTable');
    if (!activities || activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No activities yet</td></tr>';
        return;
    }

    tbody.innerHTML = activities.map(activity => `
        <tr>
            <td>${formatDate(activity.created_at)}</td>
            <td>${activity.account_email}</td>
            <td>${activity.target_email}</td>
            <td>
                ${activity.status === 'success' 
                    ? '<span class="badge badge-success">Success</span>' 
                    : '<span class="badge badge-danger">Failed</span>'}
            </td>
        </tr>
    `).join('');
}

async function loadStats() {
    try {
        const response = await fetch('/api/user/stats?days=30');
        const stats = await response.json();
        
        // Update today's activity
        const today = new Date().toISOString().split('T')[0];
        const todayStats = stats.daily_stats.find(s => s.date === today);
        document.getElementById('todayEmails').textContent = todayStats ? todayStats.emails_added : 0;
        
        // Render chart
        renderActivityChart(stats.daily_stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function renderActivityChart(dailyStats) {
    if (!dailyStats || dailyStats.length === 0) return;

    const dates = dailyStats.map(s => s.date).reverse();
    const emailsAdded = dailyStats.map(s => s.emails_added || 0).reverse();

    if (activityChart) activityChart.destroy();

    const ctx = document.getElementById('activityChart').getContext('2d');
    activityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: 'Emails Added',
                data: emailsAdded,
                backgroundColor: '#3498db',
                borderColor: '#2980b9',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#ecf0f1' }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#95a5a6' },
                    grid: { color: '#34495e' }
                },
                x: {
                    ticks: { color: '#95a5a6' },
                    grid: { color: '#34495e' }
                }
            }
        }
    });
}

async function exportMyData() {
    window.location.href = '/api/export/csv';
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
