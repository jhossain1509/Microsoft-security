<?php
/**
 * Authentication API Endpoints
 * Handles login, register, refresh, and logout
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

switch ($method) {
    case 'POST':
        switch ($action) {
            case 'login':
                handleLogin();
                break;
            case 'register':
                handleRegister();
                break;
            case 'refresh':
                handleRefresh();
                break;
            case 'logout':
                handleLogout();
                break;
            default:
                errorResponse('Invalid action', 400);
        }
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleLogin() {
    $input = json_decode(file_get_contents('php://input'), true);
    $email = $input['email'] ?? '';
    $password = $input['password'] ?? '';
    
    if (empty($email) || empty($password)) {
        errorResponse('Email and password are required', 400);
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM users WHERE email = ?");
    $stmt->execute([$email]);
    $user = $stmt->fetch();
    
    if (!$user || !password_verify($password, $user['password_hash'])) {
        logAudit(null, 'login_failed', 'user', null, ['email' => $email]);
        errorResponse('Invalid credentials', 401);
    }
    
    if (!$user['is_active']) {
        errorResponse('Account is disabled', 403);
    }
    
    // Update last login
    $stmt = $db->prepare("UPDATE users SET last_login = NOW() WHERE id = ?");
    $stmt->execute([$user['id']]);
    
    // Generate tokens
    $accessToken = AuthMiddleware::generateAccessToken($user);
    $refreshToken = AuthMiddleware::generateRefreshToken($user);
    
    logAudit($user['id'], 'login_success', 'user', $user['id']);
    
    jsonResponse([
        'success' => true,
        'access_token' => $accessToken,
        'refresh_token' => $refreshToken,
        'user' => [
            'id' => $user['id'],
            'email' => $user['email'],
            'role' => $user['role']
        ]
    ]);
}

function handleRegister() {
    // Only admins can register new users
    $admin = AuthMiddleware::requireAdmin();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $email = $input['email'] ?? '';
    $password = $input['password'] ?? '';
    $role = $input['role'] ?? 'user';
    
    if (empty($email) || empty($password)) {
        errorResponse('Email and password are required', 400);
    }
    
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        errorResponse('Invalid email format', 400);
    }
    
    if (strlen($password) < 8) {
        errorResponse('Password must be at least 8 characters', 400);
    }
    
    if (!in_array($role, ['admin', 'user'])) {
        errorResponse('Invalid role', 400);
    }
    
    $db = getDB();
    
    // Check if user exists
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        errorResponse('User already exists', 409);
    }
    
    $userId = generateUUID();
    $passwordHash = password_hash($password, PASSWORD_BCRYPT, ['cost' => BCRYPT_COST]);
    
    $stmt = $db->prepare("
        INSERT INTO users (id, email, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, 1)
    ");
    $stmt->execute([$userId, $email, $passwordHash, $role]);
    
    logAudit($admin['id'], 'user_created', 'user', $userId, ['email' => $email, 'role' => $role]);
    
    successResponse([
        'id' => $userId,
        'email' => $email,
        'role' => $role
    ], 'User created successfully');
}

function handleRefresh() {
    $input = json_decode(file_get_contents('php://input'), true);
    $refreshToken = $input['refresh_token'] ?? '';
    
    if (empty($refreshToken)) {
        errorResponse('Refresh token is required', 400);
    }
    
    $user = AuthMiddleware::verifyRefreshToken($refreshToken);
    
    // Generate new access token
    $accessToken = AuthMiddleware::generateAccessToken($user);
    
    // Optionally generate new refresh token (refresh token rotation)
    $newRefreshToken = AuthMiddleware::generateRefreshToken($user);
    
    // Revoke old refresh token
    AuthMiddleware::revokeRefreshToken($refreshToken);
    
    jsonResponse([
        'success' => true,
        'access_token' => $accessToken,
        'refresh_token' => $newRefreshToken
    ]);
}

function handleLogout() {
    $user = AuthMiddleware::getAuthUser();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $refreshToken = $input['refresh_token'] ?? '';
    
    if (!empty($refreshToken)) {
        AuthMiddleware::revokeRefreshToken($refreshToken);
    }
    
    logAudit($user['id'], 'logout', 'user', $user['id']);
    
    successResponse([], 'Logged out successfully');
}
