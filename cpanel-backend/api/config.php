<?php
/**
 * Config API - Dynamic Client Configuration
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'GET':
        handleGet();
        break;
    case 'POST':
        handleUpdate();
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleGet() {
    $user = AuthMiddleware::getAuthUser();
    
    $db = getDB();
    $stmt = $db->query("SELECT setting_key, setting_value FROM settings");
    $settings = $stmt->fetchAll();
    
    $config = [];
    foreach ($settings as $setting) {
        $config[$setting['setting_key']] = $setting['setting_value'];
    }
    
    jsonResponse(['success' => true, 'config' => $config]);
}

function handleUpdate() {
    $admin = AuthMiddleware::requireAdmin();
    
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($input)) {
        errorResponse('No settings provided', 400);
    }
    
    $db = getDB();
    
    foreach ($input as $key => $value) {
        $stmt = $db->prepare("
            INSERT INTO settings (setting_key, setting_value)
            VALUES (?, ?)
            ON DUPLICATE KEY UPDATE setting_value = ?
        ");
        $stmt->execute([$key, $value, $value]);
    }
    
    logAudit($admin['id'], 'config_updated', 'settings', null, $input);
    
    successResponse([], 'Settings updated successfully');
}
