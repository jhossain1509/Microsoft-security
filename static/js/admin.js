// Admin Dashboard JavaScript

let users = [];

// Load users on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    updateStats();
});

async function loadUsers() {
    try {
        const response = await fetch('/api/admin/users');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        users = await response.json();
        renderUsersTable();
        updateStats();
    } catch (error) {
        console.error('Error loading users:', error);
        alert('Failed to load users. Please refresh the page.');
    }
}

function renderUsersTable() {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td><span class="badge ${user.role === 'admin' ? 'badge-warning' : 'badge-success'}">${user.role}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                ${user.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Inactive</span>'}
            </td>
            <td>
                <button class="btn btn-primary" onclick="showUserStats(${user.id})">📊 Stats</button>
                <button class="btn btn-success" onclick="showLicenseModal(${user.id})">🔑 License</button>
                <button class="btn btn-danger" onclick="deleteUser(${user.id})">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function updateStats() {
    document.getElementById('totalUsers').textContent = users.length;
    // Add more stats calculations here
}

function showCreateUserModal() {
    document.getElementById('createUserModal').style.display = 'block';
}

function showLicenseModal(userId) {
    document.getElementById('licenseUserId').value = userId;
    document.getElementById('licenseResult').style.display = 'none';
    document.getElementById('licenseModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Create User Form
document.getElementById('createUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            alert('User created successfully!');
            closeModal('createUserModal');
            e.target.reset();
            loadUsers();
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        alert('Error creating user: ' + error.message);
    }
});

// Create License Form
document.getElementById('createLicenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    data.user_id = parseInt(data.user_id);
    data.max_pcs = parseInt(data.max_pcs);
    data.expires_days = parseInt(data.expires_days);

    try {
        const response = await fetch('/api/admin/licenses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success) {
            document.getElementById('generatedLicenseKey').textContent = result.license_key;
            document.getElementById('licenseResult').style.display = 'block';
        } else {
            alert('Error generating license');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            alert('User deleted successfully');
            loadUsers();
        }
    } catch (error) {
        alert('Error deleting user: ' + error.message);
    }
}

function showUserStats(userId) {
    window.location.href = `/admin/reports?user=${userId}`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
