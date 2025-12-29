<?php
/**
 * License Management API
 * Handles license creation, activation, and validation
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

switch ($method) {
    case 'GET':
        if ($action === 'list') {
            handleList();
        } elseif ($action === 'validate') {
            handleValidate();
        } else {
            errorResponse('Invalid action', 400);
        }
        break;
    case 'POST':
        if ($action === 'create') {
            handleCreate();
        } elseif ($action === 'activate') {
            handleActivate();
        } else {
            errorResponse('Invalid action', 400);
        }
        break;
    case 'PATCH':
        handleUpdate();
        break;
    case 'DELETE':
        handleDelete();
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleList() {
    $user = AuthMiddleware::requireAdmin();
    
    $db = getDB();
    $stmt = $db->query("
        SELECT l.*, 
               COUNT(a.id) as active_activations,
               u.email as created_by_email
        FROM licenses l
        LEFT JOIN activations a ON l.id = a.license_id AND a.revoked = 0
        LEFT JOIN users u ON l.created_by = u.id
        GROUP BY l.id
        ORDER BY l.created_at DESC
    ");
    
    $licenses = $stmt->fetchAll();
    
    jsonResponse(['success' => true, 'data' => $licenses]);
}

function handleCreate() {
    $admin = AuthMiddleware::requireAdmin();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $maxActivations = $input['max_activations'] ?? 1;
    $expiresAt = $input['expires_at'] ?? null;
    $notes = $input['notes'] ?? '';
    
    if ($maxActivations < 1) {
        errorResponse('Max activations must be at least 1', 400);
    }
    
    // Generate license key (format: XXXX-XXXX-XXXX-XXXX)
    $licenseKey = sprintf(
        '%04X-%04X-%04X-%04X',
        mt_rand(0, 0xFFFF),
        mt_rand(0, 0xFFFF),
        mt_rand(0, 0xFFFF),
        mt_rand(0, 0xFFFF)
    );
    
    $licenseId = generateUUID();
    $db = getDB();
    
    $stmt = $db->prepare("
        INSERT INTO licenses (id, license_key, max_activations, expires_at, created_by, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $licenseId,
        $licenseKey,
        $maxActivations,
        $expiresAt,
        $admin['id'],
        $notes
    ]);
    
    logAudit($admin['id'], 'license_created', 'license', $licenseId, [
        'license_key' => $licenseKey,
        'max_activations' => $maxActivations
    ]);
    
    successResponse([
        'id' => $licenseId,
        'license_key' => $licenseKey,
        'max_activations' => $maxActivations,
        'expires_at' => $expiresAt
    ], 'License created successfully');
}

function handleActivate() {
    $user = AuthMiddleware::getAuthUser();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $licenseKey = $input['license_key'] ?? '';
    $machineId = $input['machine_id'] ?? '';
    $hostname = $input['hostname'] ?? null;
    $osInfo = $input['os_info'] ?? null;
    
    if (empty($licenseKey) || empty($machineId)) {
        errorResponse('License key and machine ID are required', 400);
    }
    
    $db = getDB();
    
    // Get license
    $stmt = $db->prepare("SELECT * FROM licenses WHERE license_key = ? AND is_active = 1");
    $stmt->execute([$licenseKey]);
    $license = $stmt->fetch();
    
    if (!$license) {
        errorResponse('Invalid license key', 404);
    }
    
    // Check if expired
    if ($license['expires_at'] && strtotime($license['expires_at']) < time()) {
        errorResponse('License has expired', 403);
    }
    
    // Check if machine already activated
    $stmt = $db->prepare("
        SELECT * FROM activations 
        WHERE license_id = ? AND machine_id = ? AND revoked = 0
    ");
    $stmt->execute([$license['id'], $machineId]);
    $existingActivation = $stmt->fetch();
    
    if ($existingActivation) {
        // Update last seen
        $stmt = $db->prepare("
            UPDATE activations 
            SET last_seen = NOW(), ip = ?, user_id = ?
            WHERE id = ?
        ");
        $stmt->execute([getClientIP(), $user['id'], $existingActivation['id']]);
        
        successResponse([
            'message' => 'License already activated on this machine',
            'activation_id' => $existingActivation['id']
        ]);
    }
    
    // Check activation limit
    $stmt = $db->prepare("
        SELECT COUNT(*) as count FROM activations 
        WHERE license_id = ? AND revoked = 0
    ");
    $stmt->execute([$license['id']]);
    $activationCount = $stmt->fetch()['count'];
    
    if ($activationCount >= $license['max_activations']) {
        errorResponse('License activation limit reached', 403);
    }
    
    // Create activation
    $activationId = generateUUID();
    $stmt = $db->prepare("
        INSERT INTO activations (id, license_id, machine_id, user_id, ip, hostname, os_info)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $activationId,
        $license['id'],
        $machineId,
        $user['id'],
        getClientIP(),
        $hostname,
        $osInfo
    ]);
    
    logAudit($user['id'], 'license_activated', 'activation', $activationId, [
        'license_key' => $licenseKey,
        'machine_id' => $machineId
    ]);
    
    successResponse([
        'activation_id' => $activationId,
        'license_id' => $license['id'],
        'expires_at' => $license['expires_at']
    ], 'License activated successfully');
}

function handleValidate() {
    $user = AuthMiddleware::getAuthUser();
    
    $licenseKey = $_GET['license_key'] ?? '';
    $machineId = $_GET['machine_id'] ?? '';
    
    if (empty($licenseKey) || empty($machineId)) {
        errorResponse('License key and machine ID are required', 400);
    }
    
    $db = getDB();
    
    $stmt = $db->prepare("
        SELECT l.*, a.id as activation_id, a.last_seen, a.revoked
        FROM licenses l
        LEFT JOIN activations a ON l.id = a.license_id AND a.machine_id = ?
        WHERE l.license_key = ? AND l.is_active = 1
    ");
    $stmt->execute([$machineId, $licenseKey]);
    $result = $stmt->fetch();
    
    if (!$result) {
        errorResponse('Invalid license', 404);
    }
    
    // Check if expired
    if ($result['expires_at'] && strtotime($result['expires_at']) < time()) {
        errorResponse('License expired', 403);
    }
    
    // Check if activation exists and not revoked
    if (!$result['activation_id'] || $result['revoked']) {
        errorResponse('License not activated on this machine', 403);
    }
    
    // Update last seen
    $stmt = $db->prepare("UPDATE activations SET last_seen = NOW() WHERE id = ?");
    $stmt->execute([$result['activation_id']]);
    
    jsonResponse([
        'success' => true,
        'valid' => true,
        'expires_at' => $result['expires_at'],
        'last_seen' => $result['last_seen']
    ]);
}

function handleUpdate() {
    $admin = AuthMiddleware::requireAdmin();
    
    $licenseId = $_GET['id'] ?? '';
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($licenseId)) {
        errorResponse('License ID is required', 400);
    }
    
    $db = getDB();
    $fields = [];
    $values = [];
    
    if (isset($input['max_activations'])) {
        $fields[] = 'max_activations = ?';
        $values[] = $input['max_activations'];
    }
    
    if (isset($input['expires_at'])) {
        $fields[] = 'expires_at = ?';
        $values[] = $input['expires_at'];
    }
    
    if (isset($input['is_active'])) {
        $fields[] = 'is_active = ?';
        $values[] = $input['is_active'];
    }
    
    if (isset($input['notes'])) {
        $fields[] = 'notes = ?';
        $values[] = $input['notes'];
    }
    
    if (empty($fields)) {
        errorResponse('No fields to update', 400);
    }
    
    $values[] = $licenseId;
    $sql = "UPDATE licenses SET " . implode(', ', $fields) . " WHERE id = ?";
    $stmt = $db->prepare($sql);
    $stmt->execute($values);
    
    logAudit($admin['id'], 'license_updated', 'license', $licenseId, $input);
    
    successResponse([], 'License updated successfully');
}

function handleDelete() {
    $admin = AuthMiddleware::requireAdmin();
    
    $licenseId = $_GET['id'] ?? '';
    
    if (empty($licenseId)) {
        errorResponse('License ID is required', 400);
    }
    
    $db = getDB();
    
    // Soft delete - just deactivate
    $stmt = $db->prepare("UPDATE licenses SET is_active = 0 WHERE id = ?");
    $stmt->execute([$licenseId]);
    
    logAudit($admin['id'], 'license_deleted', 'license', $licenseId);
    
    successResponse([], 'License deleted successfully');
}
