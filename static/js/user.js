// User Dashboard JavaScript

let activityChart;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();  // Bug Fix #3: Load real stats
    loadUserActivities();
    loadStats();
    loadSettings();
});

// Bug Fix #3: Load real dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/user/dashboard-stats');
        if (!response.ok) throw new Error('Failed to load stats');
        const data = await response.json();
        
        if (data.success) {
            // Update card values with real data
            const stats = data;
            document.querySelector('[data-stat="accounts"]').textContent = stats.accounts || 0;
            document.querySelector('[data-stat="emails"]').textContent = stats.emails || 0;
            document.querySelector('[data-stat="pcs"]').textContent = stats.pcs || 0;
            document.querySelector('[data-stat="done-emails"]').textContent = stats.done_emails || 0;
            document.querySelector('[data-stat="today-added"]').textContent = stats.today_added || 0;
            document.querySelector('[data-stat="today-failed"]').textContent = stats.today_failed || 0;
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

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

function showAddDonePanel() {
    hideAllPanels();
    document.getElementById('addDonePanel').style.display = 'block';
    loadDoneEmails();
    updateSidebarActive();
}

function hideAllPanels() {
    document.getElementById('accountsPanel').style.display = 'none';
    document.getElementById('emailsPanel').style.display = 'none';
    document.getElementById('settingsPanel').style.display = 'none';
    document.getElementById('pcsPanel').style.display = 'none';
    document.getElementById('addDonePanel').style.display = 'none';
}

function updateSidebarActive() {
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
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
    
    // Bug Fix #8 & #10: Email validation on client side
    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    const lines = input.split('\n').map(e => e.trim()).filter(e => e);
    const emails = [];
    const invalids = [];
    const duplicates = new Set();
    
    for (const email of lines) {
        if (!emailPattern.test(email)) {
            invalids.push(email);
        } else if (duplicates.has(email.toLowerCase())) {
            // Skip duplicate within the input
            continue;
        } else {
            emails.push(email);
            duplicates.add(email.toLowerCase());
        }
    }
    
    if (invalids.length > 0) {
        alert(`Found ${invalids.length} invalid emails:\n${invalids.slice(0, 5).join('\n')}${invalids.length > 5 ? '\n...' : ''}\n\nPlease fix them and try again.`);
        return;
    }
    
    if (emails.length === 0) {
        alert('No valid emails found');
        return;
    }
    
    // Bug Fix #10: Confirm before uploading
    if (!confirm(`Upload ${emails.length} emails?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/user/emails', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(emails)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }
        
        const data = await response.json();
        
        // Show detailed result
        if (data.success) {
            let message = `✅ Added: ${data.added || 0}\n`;
            if (data.skipped > 0) {
                message += `⚠️ Skipped (duplicates): ${data.skipped}\n`;
            }
            if (data.errors && data.errors.length > 0) {
                message += `❌ Errors: ${data.errors.length}\n${data.errors.slice(0, 3).join('\n')}`;
            }
            alert(message);
        } else {
            alert(data.count ? `${data.count} emails uploaded!` : 'Upload complete');
        }
        
        document.getElementById('emailsInput').value = '';
        loadEmails();
        loadDashboardStats();  // Refresh stats
    } catch (error) {
        console.error('Error uploading emails:', error);
        alert(`Error: ${error.message}`);
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

// ===== Add Done Emails Management =====

async function loadDoneEmails() {
    try {
        const response = await fetch('/api/user/emails-done');
        if (!response.ok) throw new Error('Failed to load done emails');
        const data = await response.json();
        renderDoneEmailsTable(data.emails);
        document.getElementById('doneEmailCount').textContent = data.emails.length;
    } catch (error) {
        console.error('Error loading done emails:', error);
        alert('Error loading processed emails');
    }
}

function renderDoneEmailsTable(emails) {
    const tbody = document.getElementById('doneEmailsTableBody');
    if (!emails || emails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">No processed emails yet</td></tr>';
        return;
    }
    tbody.innerHTML = emails.map(email => `
        <tr data-id="${email.id}">
            <td>${email.email}</td>
            <td>${formatDate(email.processed_at)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteDoneEmail(${email.id})">🗑️ Delete</button>
            </td>
        </tr>
    `).join('');
}

async function deleteDoneEmail(emailId) {
    if (!confirm('Delete this email from Add Done list?')) return;
    
    try {
        const response = await fetch(`/api/user/emails-done?id=${emailId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Delete failed');
        
        // Remove from UI
        document.querySelector(`#doneEmailsTableBody tr[data-id="${emailId}"]`).remove();
        
        // Update count
        const currentCount = parseInt(document.getElementById('doneEmailCount').textContent);
        document.getElementById('doneEmailCount').textContent = currentCount - 1;
        
        alert('Email deleted successfully!');
    } catch (error) {
        console.error('Error deleting email:', error);
        alert('Error deleting email');
    }
}

async function cleanAllDoneEmails() {
    if (!confirm('Are you sure you want to clean ALL processed emails? This cannot be undone!')) return;
    
    try {
        const response = await fetch('/api/user/emails-done?action=clean', {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Clean failed');
        
        // Clear table
        document.getElementById('doneEmailsTableBody').innerHTML = 
            '<tr><td colspan="3" style="text-align:center;">No processed emails yet</td></tr>';
        document.getElementById('doneEmailCount').textContent = '0';
        
        alert('All processed emails cleaned successfully!');
    } catch (error) {
        console.error('Error cleaning emails:', error);
        alert('Error cleaning emails');
    }
}
