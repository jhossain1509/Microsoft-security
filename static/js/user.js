// User Dashboard JavaScript

let activityChart;

document.addEventListener('DOMContentLoaded', () => {
    loadUserActivities();
    loadScreenshots();
    loadStats();
});

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

async function loadScreenshots() {
    try {
        const response = await fetch('/api/user/screenshots');
        const screenshots = await response.json();
        renderScreenshots(screenshots);
    } catch (error) {
        console.error('Error loading screenshots:', error);
    }
}

function renderScreenshots(screenshots) {
    const grid = document.getElementById('screenshotsGrid');
    if (!screenshots || screenshots.length === 0) {
        grid.innerHTML = '<p style="color: #95a5a6;">No screenshots yet</p>';
        return;
    }

    grid.innerHTML = screenshots.map(shot => `
        <div class="screenshot-item" onclick="showScreenshot('${shot.filename}')">
            <img src="/api/screenshot/${shot.thumbnail_filename || shot.filename}" alt="Screenshot">
            <div class="screenshot-overlay">
                ${formatDate(shot.created_at)}
            </div>
        </div>
    `).join('');
}

function showScreenshot(filename) {
    document.getElementById('screenshotPreview').src = '/api/screenshot/' + filename;
    document.getElementById('screenshotModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
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

async function refreshScreenshots() {
    loadScreenshots();
}

async function exportMyData() {
    window.location.href = '/api/export/csv';
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}
