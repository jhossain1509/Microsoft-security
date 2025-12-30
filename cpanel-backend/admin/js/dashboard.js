// Dashboard JavaScript
const API_URL = window.location.origin + '/Microsoft-Entra/api';
let accessToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');
let currentUser = JSON.parse(localStorage.getItem('user') || '{}');

// Check authentication on load
if (!accessToken || !currentUser.email) {
    window.location.href = 'login.html';
}

// Display user email
document.getElementById('userEmail').textContent = currentUser.email;

// API Helper Function
async function apiCall(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${accessToken}`;
    options.headers['Content-Type'] = 'application/json';
    
    try {
        let response = await fetch(`${API_URL}/${endpoint}`, options);
        
        // If 401, try to refresh token
        if (response.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                options.headers['Authorization'] = `Bearer ${accessToken}`;
                response = await fetch(`${API_URL}/${endpoint}`, options);
            } else {
                logout();
                return null;
            }
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('Connection error', 'danger');
        return null;
    }
}

// Refresh Access Token
async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_URL}/auth.php?action=refresh`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refreshToken})
        });
        
        const data = await response.json();
        
        if (data.success) {
            accessToken = data.access_token;
            refreshToken = data.refresh_token;
            localStorage.setItem('access_token', accessToken);
            localStorage.setItem('refresh_token', refreshToken);
            return true;
        }
        return false;
    } catch (error) {
        return false;
    }
}

// Logout
function logout() {
    apiCall('auth.php?action=logout', {
        method: 'POST',
        body: JSON.stringify({refresh_token: refreshToken})
    });
    
    localStorage.clear();
    window.location.href = 'login.html';
}

// Show Section
function showSection(section, event) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(el => {
        el.style.display = 'none';
    });
    
    // Remove active from all nav links
    document.querySelectorAll('.sidebar .nav-link').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(`section-${section}`).style.display = 'block';
    
    // Add active to nav link
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load section data
    switch(section) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'users':
            loadUsers();
            break;
        case 'licenses':
            loadLicenses();
            break;
        case 'activity':
            loadActivity();
            break;
        case 'screenshots':
            loadScreenshots();
            break;
        case 'clients':
            loadClients();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Load Dashboard
async function loadDashboard() {
    // Load stats
    const users = await apiCall('users.php');
    const licenses = await apiCall('licenses.php?action=list');
    const events = await apiCall('events.php');
    const clients = await apiCall('heartbeat.php');
    
    if (users && users.data) document.getElementById('stat-users').textContent = users.data.length;
    if (licenses && licenses.data) document.getElementById('stat-licenses').textContent = licenses.data.length;
    if (events && events.data) document.getElementById('stat-emails').textContent = events.data.length;
    if (clients && clients.data && clients.data.active) document.getElementById('stat-clients').textContent = clients.data.active.length;
    
    // Load recent activity
    if (events && events.data && events.data.length > 0) {
        const recentHtml = events.data.slice(0, 10).map(event => `
            <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
                <div>
                    <strong>${event.user_email || 'Unknown'}</strong> added 
                    <span class="badge bg-info">${event.email}</span>
                </div>
                <small class="text-muted">${formatDate(event.added_at)}</small>
            </div>
        `).join('');
        
        document.getElementById('recent-activity-list').innerHTML = recentHtml;
    } else {
        document.getElementById('recent-activity-list').innerHTML = '<p class="text-muted">No recent activity</p>';
    }
}

// Load Users
async function loadUsers() {
    const data = await apiCall('users.php');
    
    if (!data || !data.data) return;
    
    const tbody = document.getElementById('users-table-body');
    tbody.innerHTML = data.data.map(user => `
        <tr>
            <td>${user.email}</td>
            <td><span class="badge bg-${user.role === 'admin' ? 'danger' : 'primary'}">${user.role}</span></td>
            <td><span class="badge bg-${user.is_active ? 'success' : 'secondary'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>${user.emails_count || 0}</td>
            <td>${user.last_login ? formatDate(user.last_login) : 'Never'}</td>
            <td>
                <button class="btn btn-sm btn-warning" onclick="editUser('${user.id}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Load Licenses
async function loadLicenses() {
    const data = await apiCall('licenses.php?action=list');
    
    if (!data || !data.data) return;
    
    const tbody = document.getElementById('licenses-table-body');
    tbody.innerHTML = data.data.map(license => `
        <tr>
            <td><code>${license.license_key}</code></td>
            <td>${license.max_activations}</td>
            <td><span class="badge bg-info">${license.active_activations || 0}</span></td>
            <td>${license.expires_at ? formatDate(license.expires_at) : 'Never'}</td>
            <td>${license.created_by_email || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deleteLicense('${license.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

// Load Activity
async function loadActivity() {
    const data = await apiCall('events.php');
    
    if (!data || !data.data) return;
    
    const tbody = document.getElementById('activity-table-body');
    tbody.innerHTML = data.data.map(event => `
        <tr>
            <td>${formatDate(event.added_at)}</td>
            <td>${event.user_email || 'Unknown'}</td>
            <td>${event.email}</td>
            <td>${event.account_email || 'N/A'}</td>
            <td><code>${(event.machine_id || '').substring(0, 8)}...</code></td>
            <td><span class="badge bg-${event.status === 'success' ? 'success' : 'danger'}">${event.status}</span></td>
        </tr>
    `).join('');
}

// Load Screenshots
async function loadScreenshots() {
    const data = await apiCall('screenshots.php?action=list&per_page=50');
    
    if (!data || !data.data) {
        document.getElementById('screenshots-grid').innerHTML = '<div class="col-12"><p class="text-muted">No screenshots available</p></div>';
        return;
    }
    
    const grid = document.getElementById('screenshots-grid');
    grid.innerHTML = data.data.map(screenshot => `
        <div class="col-md-3 mb-3">
            <div class="card screenshot-card">
                <img src="/Microsoft-Entra/api/screenshots.php?action=download&id=${screenshot.id}&token=${accessToken}" 
                     class="card-img-top" alt="Screenshot" style="height: 200px; object-fit: cover;">
                <div class="card-body">
                    <p class="card-text small mb-1">
                        <i class="bi bi-person"></i> ${screenshot.user_email || 'Unknown'}
                    </p>
                    <p class="card-text small mb-2">
                        <i class="bi bi-clock"></i> ${formatDate(screenshot.created_at)}
                    </p>
                    <button class="btn btn-sm btn-danger w-100" onclick="deleteScreenshot('${screenshot.id}')">
                        <i class="bi bi-trash"></i> Delete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Load Clients
async function loadClients() {
    const data = await apiCall('heartbeat.php');
    
    if (!data || !data.data || !data.data.active) {
        document.getElementById('clients-table-body').innerHTML = '<tr><td colspan="6" class="text-muted text-center">No active clients</td></tr>';
        return;
    }
    
    const tbody = document.getElementById('clients-table-body');
    tbody.innerHTML = data.data.active.map(client => `
        <tr>
            <td>${client.user_email || 'Unknown'}</td>
            <td><code>${(client.machine_id || '').substring(0, 12)}...</code></td>
            <td><span class="badge status-${client.status}">${client.status}</span></td>
            <td>${client.ip || 'N/A'}</td>
            <td>${client.version || 'N/A'}</td>
            <td>${formatDate(client.last_activity)}</td>
        </tr>
    `).join('');
}

// Load Settings
async function loadSettings() {
    const data = await apiCall('config.php');
    
    if (!data || !data.config) return;
    
    document.getElementById('setting-screenshot-interval').value = data.config.screenshot_interval || 300;
    document.getElementById('setting-heartbeat-interval').value = data.config.heartbeat_interval || 120;
    document.getElementById('setting-emails-per-account').value = data.config.emails_per_account || 5;
}

// Modal Functions
function showCreateUserModal() {
    new bootstrap.Modal(document.getElementById('createUserModal')).show();
}

function showCreateLicenseModal() {
    new bootstrap.Modal(document.getElementById('createLicenseModal')).show();
}

// Create User
async function createUser() {
    const email = document.getElementById('newUserEmail').value;
    const password = document.getElementById('newUserPassword').value;
    const role = document.getElementById('newUserRole').value;
    
    const result = await apiCall('auth.php?action=register', {
        method: 'POST',
        body: JSON.stringify({email, password, role})
    });
    
    if (result && result.success) {
        showToast('User created successfully', 'success');
        bootstrap.Modal.getInstance(document.getElementById('createUserModal')).hide();
        loadUsers();
    }
}

// Create License
async function createLicense() {
    const maxActivations = parseInt(document.getElementById('newLicenseMaxActivations').value);
    const expiresAt = document.getElementById('newLicenseExpires').value || null;
    const notes = document.getElementById('newLicenseNotes').value;
    
    const result = await apiCall('licenses.php?action=create', {
        method: 'POST',
        body: JSON.stringify({
            max_activations: maxActivations,
            expires_at: expiresAt,
            notes: notes
        })
    });
    
    if (result && result.success) {
        showToast(`License created: ${result.data.license_key}`, 'success');
        bootstrap.Modal.getInstance(document.getElementById('createLicenseModal')).hide();
        loadLicenses();
    }
}

// Delete Functions
async function deleteUser(id) {
    if (!confirm('Are you sure you want to deactivate this user?\n\nNote: This is a soft delete. User data will be preserved but the account will be deactivated.')) return;
    
    const result = await apiCall(`users.php?id=${id}`, {method: 'DELETE'});
    
    if (result) {
        if (result.success) {
            showToast('User deactivated successfully', 'success');
            loadUsers();
        } else if (result.error) {
            showToast(result.error, 'danger');
        }
    }
}

async function deleteLicense(id) {
    if (!confirm('Are you sure you want to delete this license?')) return;
    
    const result = await apiCall(`licenses.php?id=${id}`, {method: 'DELETE'});
    
    if (result && result.success) {
        showToast('License deleted', 'success');
        loadLicenses();
    }
}

async function deleteScreenshot(id) {
    if (!confirm('Delete this screenshot?')) return;
    
    const result = await apiCall(`screenshots.php?id=${id}`, {method: 'DELETE'});
    
    if (result && result.success) {
        showToast('Screenshot deleted', 'success');
        loadScreenshots();
    }
}

// Cleanup Screenshots
async function cleanupScreenshots() {
    if (!confirm('This will delete all screenshots older than 30 days. Continue?')) return;
    
    const result = await apiCall('screenshots.php?action=cleanup', {
        method: 'POST',
        body: JSON.stringify({older_than_days: 30})
    });
    
    if (result && result.success) {
        showToast(`Deleted ${result.data.deleted_count} screenshots`, 'success');
        loadScreenshots();
    }
}

// Save Settings
document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const settings = {
        screenshot_interval: document.getElementById('setting-screenshot-interval').value,
        heartbeat_interval: document.getElementById('setting-heartbeat-interval').value,
        emails_per_account: document.getElementById('setting-emails-per-account').value
    };
    
    const result = await apiCall('config.php', {
        method: 'POST',
        body: JSON.stringify(settings)
    });
    
    if (result && result.success) {
        showToast('Settings saved successfully', 'success');
    }
});

// Utility Functions
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showToast(message, type = 'info') {
    // Simple alert for now - can be replaced with toast library
    const alertClass = type === 'success' ? 'alert-success' : type === 'danger' ? 'alert-danger' : 'alert-info';
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} position-fixed top-0 end-0 m-3`;
    alert.style.zIndex = '9999';
    alert.textContent = message;
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 3000);
}

// Auto-refresh dashboard every 30 seconds
setInterval(() => {
    const currentSection = document.querySelector('.content-section:not([style*="display: none"])');
    if (currentSection && currentSection.id === 'section-dashboard') {
        loadDashboard();
    }
}, 30000);

// Initial load
loadDashboard();
