<?php
/**
 * Heartbeat API - Client Status Updates
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'POST':
        handleHeartbeat();
        break;
    case 'GET':
        handleList();
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleHeartbeat() {
    $user = AuthMiddleware::getAuthUser();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $machineId = $input['machine_id'] ?? '';
    $status = $input['status'] ?? 'online';
    $version = $input['version'] ?? null;
    
    if (empty($machineId)) {
        errorResponse('Machine ID is required', 400);
    }
    
    $db = getDB();
    
    // Check if heartbeat exists
    $stmt = $db->prepare("SELECT id FROM heartbeats WHERE user_id = ? AND machine_id = ?");
    $stmt->execute([$user['id'], $machineId]);
    $existing = $stmt->fetch();
    
    if ($existing) {
        // Update existing
        $stmt = $db->prepare("
            UPDATE heartbeats 
            SET status = ?, ip = ?, last_activity = NOW(), version = ?
            WHERE id = ?
        ");
        $stmt->execute([$status, getClientIP(), $version, $existing['id']]);
    } else {
        // Create new
        $stmt = $db->prepare("
            INSERT INTO heartbeats (id, user_id, machine_id, status, ip, version)
            VALUES (?, ?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            generateUUID(),
            $user['id'],
            $machineId,
            $status,
            getClientIP(),
            $version
        ]);
    }
    
    jsonResponse(['success' => true, 'message' => 'Heartbeat received']);
}

function handleList() {
    $admin = AuthMiddleware::requireAdmin();
    
    $db = getDB();
    
    // Get active clients (last seen within 5 minutes)
    $stmt = $db->query("
        SELECT h.*, u.email as user_email
        FROM heartbeats h
        LEFT JOIN users u ON h.user_id = u.id
        WHERE h.last_activity > DATE_SUB(NOW(), INTERVAL 5 MINUTE)
        ORDER BY h.last_activity DESC
    ");
    
    $active = $stmt->fetchAll();
    
    // Get all clients
    $stmt = $db->query("
        SELECT h.*, u.email as user_email
        FROM heartbeats h
        LEFT JOIN users u ON h.user_id = u.id
        ORDER BY h.last_activity DESC
        LIMIT 100
    ");
    
    $all = $stmt->fetchAll();
    
    jsonResponse([
        'success' => true,
        'data' => [
            'active' => $active,
            'all' => $all
        ]
    ]);
}
