<?php
/**
 * Analytics API
 * Handles daily/weekly/monthly statistics and reporting
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

header('Content-Type: application/json');

// Handle CORS
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];

try {
    switch ($method) {
        case 'GET':
            handleGet();
            break;
        case 'POST':
            handlePost();
            break;
        default:
            errorResponse('Method not allowed', 405);
    }
} catch (Exception $e) {
    errorResponse('Server error: ' . $e->getMessage(), 500);
}

function handleGet() {
    $user = AuthMiddleware::getAuthUser();
    $action = $_GET['action'] ?? 'summary';
    
    switch ($action) {
        case 'daily':
            getDailyStats($user);
            break;
        case 'weekly':
            getWeeklyStats($user);
            break;
        case 'monthly':
            getMonthlyStats($user);
            break;
        case 'summary':
            getSummary($user);
            break;
        case 'export':
            exportReport($user);
            break;
        default:
            errorResponse('Invalid action', 400);
    }
}

function handlePost() {
    $user = AuthMiddleware::getAuthUser();
    $data = json_decode(file_get_contents('php://input'), true);
    
    if (!$data) {
        errorResponse('Invalid JSON', 400);
    }
    
    $action = $data['action'] ?? '';
    
    switch ($action) {
        case 'log_email':
            logEmailActivity($user, $data);
            break;
        case 'start_session':
            startSession($user, $data);
            break;
        case 'end_session':
            endSession($user, $data);
            break;
        case 'update_daily':
            updateDailyStats($user, $data);
            break;
        default:
            errorResponse('Invalid action', 400);
    }
}

function getDailyStats($user) {
    $db = getDB();
    $days = isset($_GET['days']) ? (int)$_GET['days'] : 30;
    $user_id = ($user['role'] === 'admin' && isset($_GET['user_id'])) ? $_GET['user_id'] : $user['id'];
    
    $stmt = $db->prepare("
        SELECT 
            date,
            emails_added,
            emails_failed,
            accounts_used,
            success_rate,
            total_time_minutes
        FROM daily_stats
        WHERE user_id = ? AND date >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
        ORDER BY date DESC
    ");
    $stmt->execute([$user_id, $days]);
    $stats = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    successResponse(['stats' => $stats]);
}

function getWeeklyStats($user) {
    $db = getDB();
    $weeks = isset($_GET['weeks']) ? (int)$_GET['weeks'] : 12;
    $user_id = ($user['role'] === 'admin' && isset($_GET['user_id'])) ? $_GET['user_id'] : $user['id'];
    
    $stmt = $db->prepare("
        SELECT 
            week_start,
            week_end,
            total_emails_added,
            total_emails_failed,
            total_accounts_used,
            avg_success_rate,
            total_time_minutes
        FROM weekly_stats
        WHERE user_id = ? AND week_start >= DATE_SUB(CURDATE(), INTERVAL ? WEEK)
        ORDER BY week_start DESC
    ");
    $stmt->execute([$user_id, $weeks]);
    $stats = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    successResponse(['stats' => $stats]);
}

function getMonthlyStats($user) {
    $db = getDB();
    $months = isset($_GET['months']) ? (int)$_GET['months'] : 12;
    $user_id = ($user['role'] === 'admin' && isset($_GET['user_id'])) ? $_GET['user_id'] : $user['id'];
    
    $stmt = $db->prepare("
        SELECT 
            month,
            year,
            total_emails_added,
            total_emails_failed,
            total_accounts_used,
            avg_success_rate,
            total_time_minutes,
            peak_day,
            peak_day_count
        FROM monthly_stats
        WHERE user_id = ? 
        ORDER BY year DESC, month DESC
        LIMIT ?
    ");
    $stmt->execute([$user_id, $months]);
    $stats = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    successResponse(['stats' => $stats]);
}

function getSummary($user) {
    $db = getDB();
    $user_id = ($user['role'] === 'admin' && isset($_GET['user_id'])) ? $_GET['user_id'] : $user['id'];
    
    // Today's stats
    $stmt = $db->prepare("
        SELECT 
            emails_added,
            emails_failed,
            accounts_used,
            success_rate
        FROM daily_stats
        WHERE user_id = ? AND date = CURDATE()
    ");
    $stmt->execute([$user_id]);
    $today = $stmt->fetch(PDO::FETCH_ASSOC) ?: [
        'emails_added' => 0,
        'emails_failed' => 0,
        'accounts_used' => 0,
        'success_rate' => 0
    ];
    
    // This week's stats
    $stmt = $db->prepare("
        SELECT 
            SUM(emails_added) as emails_added,
            SUM(emails_failed) as emails_failed,
            SUM(accounts_used) as accounts_used,
            AVG(success_rate) as success_rate
        FROM daily_stats
        WHERE user_id = ? AND date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    ");
    $stmt->execute([$user_id]);
    $week = $stmt->fetch(PDO::FETCH_ASSOC) ?: [
        'emails_added' => 0,
        'emails_failed' => 0,
        'accounts_used' => 0,
        'success_rate' => 0
    ];
    
    // This month's stats
    $stmt = $db->prepare("
        SELECT 
            SUM(emails_added) as emails_added,
            SUM(emails_failed) as emails_failed,
            SUM(accounts_used) as accounts_used,
            AVG(success_rate) as success_rate
        FROM daily_stats
        WHERE user_id = ? AND YEAR(date) = YEAR(CURDATE()) AND MONTH(date) = MONTH(CURDATE())
    ");
    $stmt->execute([$user_id]);
    $month = $stmt->fetch(PDO::FETCH_ASSOC) ?: [
        'emails_added' => 0,
        'emails_failed' => 0,
        'accounts_used' => 0,
        'success_rate' => 0
    ];
    
    // All time stats
    $stmt = $db->prepare("
        SELECT 
            SUM(emails_added) as emails_added,
            SUM(emails_failed) as emails_failed,
            COUNT(DISTINCT date) as active_days
        FROM daily_stats
        WHERE user_id = ?
    ");
    $stmt->execute([$user_id]);
    $allTime = $stmt->fetch(PDO::FETCH_ASSOC) ?: [
        'emails_added' => 0,
        'emails_failed' => 0,
        'active_days' => 0
    ];
    
    successResponse([
        'today' => $today,
        'week' => $week,
        'month' => $month,
        'all_time' => $allTime
    ]);
}

function logEmailActivity($user, $data) {
    $db = getDB();
    $today = date('Y-m-d');
    
    // Check if today's record exists
    $stmt = $db->prepare("SELECT id, emails_added, emails_failed FROM daily_stats WHERE user_id = ? AND date = ?");
    $stmt->execute([$user['id'], $today]);
    $existing = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if ($existing) {
        // Update existing record
        $new_added = $existing['emails_added'] + ($data['success'] ? 1 : 0);
        $new_failed = $existing['emails_failed'] + ($data['success'] ? 0 : 1);
        $total = $new_added + $new_failed;
        $success_rate = $total > 0 ? ($new_added / $total) * 100 : 0;
        
        $stmt = $db->prepare("
            UPDATE daily_stats 
            SET emails_added = ?, 
                emails_failed = ?,
                success_rate = ?,
                updated_at = NOW()
            WHERE id = ?
        ");
        $stmt->execute([$new_added, $new_failed, $success_rate, $existing['id']]);
    } else {
        // Create new record
        $added = $data['success'] ? 1 : 0;
        $failed = $data['success'] ? 0 : 1;
        $success_rate = $data['success'] ? 100 : 0;
        
        $stmt = $db->prepare("
            INSERT INTO daily_stats (id, user_id, date, emails_added, emails_failed, success_rate)
            VALUES (UUID(), ?, ?, ?, ?, ?)
        ");
        $stmt->execute([$user['id'], $today, $added, $failed, $success_rate]);
    }
    
    // Also update weekly and monthly aggregates
    updateWeeklyAggregate($db, $user['id']);
    updateMonthlyAggregate($db, $user['id']);
    
    successResponse(['message' => 'Activity logged successfully']);
}

function updateWeeklyAggregate($db, $user_id) {
    $week_start = date('Y-m-d', strtotime('monday this week'));
    $week_end = date('Y-m-d', strtotime('sunday this week'));
    
    // Calculate week totals from daily stats
    $stmt = $db->prepare("
        SELECT 
            SUM(emails_added) as total_added,
            SUM(emails_failed) as total_failed,
            SUM(accounts_used) as total_accounts,
            AVG(success_rate) as avg_rate,
            SUM(total_time_minutes) as total_time
        FROM daily_stats
        WHERE user_id = ? AND date BETWEEN ? AND ?
    ");
    $stmt->execute([$user_id, $week_start, $week_end]);
    $totals = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$totals || $totals['total_added'] === null) return;
    
    // Upsert weekly record
    $stmt = $db->prepare("
        INSERT INTO weekly_stats (id, user_id, week_start, week_end, total_emails_added, total_emails_failed, total_accounts_used, avg_success_rate, total_time_minutes)
        VALUES (UUID(), ?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            total_emails_added = VALUES(total_emails_added),
            total_emails_failed = VALUES(total_emails_failed),
            total_accounts_used = VALUES(total_accounts_used),
            avg_success_rate = VALUES(avg_success_rate),
            total_time_minutes = VALUES(total_time_minutes),
            updated_at = NOW()
    ");
    $stmt->execute([
        $user_id,
        $week_start,
        $week_end,
        $totals['total_added'] ?: 0,
        $totals['total_failed'] ?: 0,
        $totals['total_accounts'] ?: 0,
        $totals['avg_rate'] ?: 0,
        $totals['total_time'] ?: 0
    ]);
}

function updateMonthlyAggregate($db, $user_id) {
    $month = (int)date('m');
    $year = (int)date('Y');
    
    // Calculate month totals from daily stats
    $stmt = $db->prepare("
        SELECT 
            SUM(emails_added) as total_added,
            SUM(emails_failed) as total_failed,
            SUM(accounts_used) as total_accounts,
            AVG(success_rate) as avg_rate,
            SUM(total_time_minutes) as total_time,
            MAX(emails_added) as peak_count
        FROM daily_stats
        WHERE user_id = ? AND YEAR(date) = ? AND MONTH(date) = ?
    ");
    $stmt->execute([$user_id, $year, $month]);
    $totals = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$totals || $totals['total_added'] === null) return;
    
    // Find peak day
    $stmt = $db->prepare("
        SELECT date FROM daily_stats
        WHERE user_id = ? AND YEAR(date) = ? AND MONTH(date) = ?
        ORDER BY emails_added DESC
        LIMIT 1
    ");
    $stmt->execute([$user_id, $year, $month]);
    $peak_day = $stmt->fetchColumn() ?: null;
    
    // Upsert monthly record
    $stmt = $db->prepare("
        INSERT INTO monthly_stats (id, user_id, month, year, total_emails_added, total_emails_failed, total_accounts_used, avg_success_rate, total_time_minutes, peak_day, peak_day_count)
        VALUES (UUID(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            total_emails_added = VALUES(total_emails_added),
            total_emails_failed = VALUES(total_emails_failed),
            total_accounts_used = VALUES(total_accounts_used),
            avg_success_rate = VALUES(avg_success_rate),
            total_time_minutes = VALUES(total_time_minutes),
            peak_day = VALUES(peak_day),
            peak_day_count = VALUES(peak_day_count),
            updated_at = NOW()
    ");
    $stmt->execute([
        $user_id,
        $month,
        $year,
        $totals['total_added'] ?: 0,
        $totals['total_failed'] ?: 0,
        $totals['total_accounts'] ?: 0,
        $totals['avg_rate'] ?: 0,
        $totals['total_time'] ?: 0,
        $peak_day,
        $totals['peak_count'] ?: 0
    ]);
}

function startSession($user, $data) {
    $db = getDB();
    $machine_id = $data['machine_id'] ?? '';
    
    $stmt = $db->prepare("
        INSERT INTO activity_sessions (id, user_id, machine_id, session_start, status)
        VALUES (UUID(), ?, ?, NOW(), 'active')
    ");
    $stmt->execute([$user['id'], $machine_id]);
    $session_id = $db->lastInsertId();
    
    successResponse(['session_id' => $session_id, 'message' => 'Session started']);
}

function endSession($user, $data) {
    $db = getDB();
    $session_id = $data['session_id'] ?? '';
    $stats = $data['stats'] ?? [];
    
    $stmt = $db->prepare("
        UPDATE activity_sessions
        SET session_end = NOW(),
            emails_processed = ?,
            emails_success = ?,
            emails_failed = ?,
            accounts_used = ?,
            status = 'completed',
            updated_at = NOW()
        WHERE id = ? AND user_id = ?
    ");
    $stmt->execute([
        $stats['processed'] ?? 0,
        $stats['success'] ?? 0,
        $stats['failed'] ?? 0,
        json_encode($stats['accounts'] ?? []),
        $session_id,
        $user['id']
    ]);
    
    successResponse(['message' => 'Session ended']);
}

function updateDailyStats($user, $data) {
    $db = getDB();
    $date = $data['date'] ?? date('Y-m-d');
    
    // Upsert daily stats
    $stmt = $db->prepare("
        INSERT INTO daily_stats (id, user_id, date, emails_added, emails_failed, accounts_used, success_rate, total_time_minutes)
        VALUES (UUID(), ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            emails_added = VALUES(emails_added),
            emails_failed = VALUES(emails_failed),
            accounts_used = VALUES(accounts_used),
            success_rate = VALUES(success_rate),
            total_time_minutes = VALUES(total_time_minutes),
            updated_at = NOW()
    ");
    
    $total = $data['emails_added'] + $data['emails_failed'];
    $success_rate = $total > 0 ? ($data['emails_added'] / $total) * 100 : 0;
    
    $stmt->execute([
        $user['id'],
        $date,
        $data['emails_added'] ?? 0,
        $data['emails_failed'] ?? 0,
        $data['accounts_used'] ?? 0,
        $success_rate,
        $data['total_time_minutes'] ?? 0
    ]);
    
    // Update aggregates
    updateWeeklyAggregate($db, $user['id']);
    updateMonthlyAggregate($db, $user['id']);
    
    successResponse(['message' => 'Daily stats updated']);
}

function exportReport($user) {
    $format = $_GET['format'] ?? 'json';
    $type = $_GET['type'] ?? 'daily';
    $user_id = ($user['role'] === 'admin' && isset($_GET['user_id'])) ? $_GET['user_id'] : $user['id'];
    
    if ($format === 'csv') {
        exportCSV($user_id, $type);
    } else {
        // JSON export (default)
        $db = getDB();
        
        if ($type === 'daily') {
            $stmt = $db->prepare("SELECT * FROM daily_stats WHERE user_id = ? ORDER BY date DESC LIMIT 100");
        } elseif ($type === 'weekly') {
            $stmt = $db->prepare("SELECT * FROM weekly_stats WHERE user_id = ? ORDER BY week_start DESC LIMIT 52");
        } else {
            $stmt = $db->prepare("SELECT * FROM monthly_stats WHERE user_id = ? ORDER BY year DESC, month DESC LIMIT 12");
        }
        
        $stmt->execute([$user_id]);
        $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        successResponse(['data' => $data]);
    }
}

function exportCSV($user_id, $type) {
    $db = getDB();
    
    header('Content-Type: text/csv');
    header('Content-Disposition: attachment; filename="' . $type . '_report_' . date('Y-m-d') . '.csv"');
    
    $output = fopen('php://output', 'w');
    
    if ($type === 'daily') {
        fputcsv($output, ['Date', 'Emails Added', 'Emails Failed', 'Accounts Used', 'Success Rate %', 'Time (min)']);
        $stmt = $db->prepare("SELECT date, emails_added, emails_failed, accounts_used, success_rate, total_time_minutes FROM daily_stats WHERE user_id = ? ORDER BY date DESC");
        $stmt->execute([$user_id]);
        
        while ($row = $stmt->fetch(PDO::FETCH_NUM)) {
            fputcsv($output, $row);
        }
    } elseif ($type === 'weekly') {
        fputcsv($output, ['Week Start', 'Week End', 'Emails Added', 'Emails Failed', 'Accounts Used', 'Avg Success Rate %', 'Time (min)']);
        $stmt = $db->prepare("SELECT week_start, week_end, total_emails_added, total_emails_failed, total_accounts_used, avg_success_rate, total_time_minutes FROM weekly_stats WHERE user_id = ? ORDER BY week_start DESC");
        $stmt->execute([$user_id]);
        
        while ($row = $stmt->fetch(PDO::FETCH_NUM)) {
            fputcsv($output, $row);
        }
    } else {
        fputcsv($output, ['Month', 'Year', 'Emails Added', 'Emails Failed', 'Accounts Used', 'Avg Success Rate %', 'Time (min)', 'Peak Day', 'Peak Count']);
        $stmt = $db->prepare("SELECT month, year, total_emails_added, total_emails_failed, total_accounts_used, avg_success_rate, total_time_minutes, peak_day, peak_day_count FROM monthly_stats WHERE user_id = ? ORDER BY year DESC, month DESC");
        $stmt->execute([$user_id]);
        
        while ($row = $stmt->fetch(PDO::FETCH_NUM)) {
            fputcsv($output, $row);
        }
    }
    
    fclose($output);
    exit;
}

?>
