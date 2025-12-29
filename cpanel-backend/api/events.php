<?php
/**
 * Events API - Email Added Tracking
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

switch ($method) {
    case 'GET':
        handleList();
        break;
    case 'POST':
        handleCreate();
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleList() {
    $user = AuthMiddleware::getAuthUser();
    
    $db = getDB();
    
    // Admin can see all, users see only their own
    if ($user['role'] === 'admin') {
        $stmt = $db->prepare("
            SELECT e.*, u.email as user_email
            FROM emails_added e
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.added_at DESC
            LIMIT 1000
        ");
        $stmt->execute();
    } else {
        $stmt = $db->prepare("
            SELECT * FROM emails_added
            WHERE user_id = ?
            ORDER BY added_at DESC
            LIMIT 1000
        ");
        $stmt->execute([$user['id']]);
    }
    
    $events = $stmt->fetchAll();
    
    jsonResponse(['success' => true, 'data' => $events]);
}

function handleCreate() {
    $user = AuthMiddleware::getAuthUser();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $email = $input['email'] ?? '';
    $accountEmail = $input['account_email'] ?? '';
    $machineId = $input['machine_id'] ?? '';
    $status = $input['status'] ?? 'success';
    $notes = $input['notes'] ?? null;
    
    if (empty($email)) {
        errorResponse('Email is required', 400);
    }
    
    $db = getDB();
    $eventId = generateUUID();
    
    $stmt = $db->prepare("
        INSERT INTO emails_added (id, email, user_id, account_email, machine_id, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $eventId,
        $email,
        $user['id'],
        $accountEmail,
        $machineId,
        $status,
        $notes
    ]);
    
    // Don't log every email add to audit (too many records)
    // logAudit($user['id'], 'email_added', 'email', $eventId);
    
    jsonResponse([
        'success' => true,
        'event_id' => $eventId
    ], 201);
}
