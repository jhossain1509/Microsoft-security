<?php
/**
 * Users Management API (Admin Only)
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];

switch ($method) {
    case 'GET':
        handleList();
        break;
    case 'POST':
        handleCreate();
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
    $admin = AuthMiddleware::requireAdmin();
    
    $db = getDB();
    $stmt = $db->query("
        SELECT u.id, u.email, u.role, u.is_active, u.created_at, u.last_login,
               COUNT(DISTINCT e.id) as emails_count,
               COUNT(DISTINCT s.id) as screenshots_count
        FROM users u
        LEFT JOIN emails_added e ON u.id = e.user_id
        LEFT JOIN screenshots s ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ");
    
    $users = $stmt->fetchAll();
    
    jsonResponse(['success' => true, 'data' => $users]);
}

function handleCreate() {
    // Handled in auth.php register endpoint
    errorResponse('Use /api/auth.php?action=register to create users', 400);
}

function handleUpdate() {
    $admin = AuthMiddleware::requireAdmin();
    
    $userId = $_GET['id'] ?? '';
    $input = json_decode(file_get_contents('php://input'), true);
    
    if (empty($userId)) {
        errorResponse('User ID is required', 400);
    }
    
    $db = getDB();
    $fields = [];
    $values = [];
    
    if (isset($input['email'])) {
        if (!filter_var($input['email'], FILTER_VALIDATE_EMAIL)) {
            errorResponse('Invalid email format', 400);
        }
        $fields[] = 'email = ?';
        $values[] = $input['email'];
    }
    
    if (isset($input['password'])) {
        if (strlen($input['password']) < 8) {
            errorResponse('Password must be at least 8 characters', 400);
        }
        $fields[] = 'password_hash = ?';
        $values[] = password_hash($input['password'], PASSWORD_BCRYPT, ['cost' => BCRYPT_COST]);
    }
    
    if (isset($input['role'])) {
        if (!in_array($input['role'], ['admin', 'user'])) {
            errorResponse('Invalid role', 400);
        }
        $fields[] = 'role = ?';
        $values[] = $input['role'];
    }
    
    if (isset($input['is_active'])) {
        $fields[] = 'is_active = ?';
        $values[] = $input['is_active'] ? 1 : 0;
    }
    
    if (empty($fields)) {
        errorResponse('No fields to update', 400);
    }
    
    $values[] = $userId;
    $sql = "UPDATE users SET " . implode(', ', $fields) . " WHERE id = ?";
    $stmt = $db->prepare($sql);
    $stmt->execute($values);
    
    logAudit($admin['id'], 'user_updated', 'user', $userId, $input);
    
    successResponse([], 'User updated successfully');
}

function handleDelete() {
    $admin = AuthMiddleware::requireAdmin();
    
    $userId = $_GET['id'] ?? '';
    
    if (empty($userId)) {
        errorResponse('User ID is required', 400);
    }
    
    // Prevent self-deletion
    if ($userId === $admin['id']) {
        errorResponse('Cannot delete your own account', 400);
    }
    
    $db = getDB();
    
    // Soft delete - deactivate instead of deleting
    $stmt = $db->prepare("UPDATE users SET is_active = 0 WHERE id = ?");
    $stmt->execute([$userId]);
    
    logAudit($admin['id'], 'user_deleted', 'user', $userId);
    
    successResponse([], 'User deleted successfully');
}
