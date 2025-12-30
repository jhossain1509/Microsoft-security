// Reports Page JavaScript

let dailyChart, pieChart;

async function loadUserReport() {
    const userId = document.getElementById('userSelect').value;
    const timePeriod = document.getElementById('timePeriod').value;

    if (!userId) {
        document.getElementById('reportContent').style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/admin/user/${userId}/stats?days=${timePeriod}`);
        const data = await response.json();

        document.getElementById('reportContent').style.display = 'block';
        
        // Update summary stats
        updateSummaryStats(data);
        
        // Render tables
        renderLicensesTable(data.licenses);
        renderActivitiesTable(data.activities);
        
        // Render charts
        renderCharts(data.stats);
    } catch (error) {
        console.error('Error loading report:', error);
        alert('Error loading report data');
    }
}

function updateSummaryStats(data) {
    const licenses = data.licenses || [];
    const activePCs = licenses.reduce((sum, l) => sum + (l.active_pcs || 0), 0);
    const totalEmails = data.stats.totals.total_success || 0;
    const totalActivities = data.stats.totals.total_activities || 0;
    const successRate = totalActivities > 0 
        ? Math.round((totalEmails / totalActivities) * 100) 
        : 0;

    document.getElementById('userLicenseCount').textContent = licenses.length;
    document.getElementById('userActivePCs').textContent = activePCs;
    document.getElementById('userTotalEmails').textContent = totalEmails;
    document.getElementById('userSuccessRate').textContent = successRate + '%';
}

function renderLicensesTable(licenses) {
    const tbody = document.getElementById('licensesTableBody');
    if (!licenses || licenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No licenses found</td></tr>';
        return;
    }

    tbody.innerHTML = licenses.map(license => `
        <tr>
            <td><code>${license.license_key}</code></td>
            <td>${license.max_pcs}</td>
            <td>${license.active_pcs || 0}</td>
            <td>${license.expires_at ? formatDate(license.expires_at) : 'Never'}</td>
            <td>
                ${license.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Inactive</span>'}
            </td>
        </tr>
    `).join('');
}

function renderActivitiesTable(activities) {
    const tbody = document.getElementById('activitiesTableBody');
    if (!activities || activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No activities found</td></tr>';
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
            <td>${activity.error_message || '-'}</td>
        </tr>
    `).join('');
}

function renderCharts(stats) {
    const dailyStats = stats.daily_stats || [];
    
    // Prepare data for daily chart
    const dates = dailyStats.map(s => s.date).reverse();
    const emailsAdded = dailyStats.map(s => s.emails_added || 0).reverse();
    const emailsFailed = dailyStats.map(s => s.emails_failed || 0).reverse();

    // Destroy existing charts
    if (dailyChart) dailyChart.destroy();
    if (pieChart) pieChart.destroy();

    // Daily Activity Chart
    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    dailyChart = new Chart(dailyCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Success',
                    data: emailsAdded,
                    borderColor: '#27ae60',
                    backgroundColor: 'rgba(39, 174, 96, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Failed',
                    data: emailsFailed,
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.4
                }
            ]
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

    // Pie Chart
    const totalSuccess = stats.totals.total_success || 0;
    const totalFailed = stats.totals.total_failed || 0;
    
    const pieCtx = document.getElementById('pieChart').getContext('2d');
    pieChart = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: ['Success', 'Failed'],
            datasets: [{
                data: [totalSuccess, totalFailed],
                backgroundColor: ['#27ae60', '#e74c3c']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: { color: '#ecf0f1' }
                }
            }
        }
    });
}

async function exportReport() {
    const userId = document.getElementById('userSelect').value;
    if (!userId) {
        alert('Please select a user first');
        return;
    }

    window.location.href = `/api/export/csv?user_id=${userId}`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}
