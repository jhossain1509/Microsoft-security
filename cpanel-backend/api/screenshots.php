<?php
/**
 * Screenshots API - Upload and Management
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../middleware/auth.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = $_GET['action'] ?? '';

switch ($method) {
    case 'GET':
        if ($action === 'list') {
            handleList();
        } elseif ($action === 'download') {
            handleDownload();
        } else {
            errorResponse('Invalid action', 400);
        }
        break;
    case 'POST':
        if ($action === 'upload') {
            handleUpload();
        } elseif ($action === 'cleanup') {
            handleCleanup();
        } else {
            errorResponse('Invalid action', 400);
        }
        break;
    case 'DELETE':
        handleDelete();
        break;
    default:
        errorResponse('Method not allowed', 405);
}

function handleUpload() {
    $user = AuthMiddleware::getAuthUser();
    
    if (!isset($_FILES['file'])) {
        errorResponse('No file uploaded', 400);
    }
    
    $file = $_FILES['file'];
    $machineId = $_POST['machine_id'] ?? '';
    
    // Validate file
    if ($file['error'] !== UPLOAD_ERR_OK) {
        errorResponse('File upload error: ' . $file['error'], 400);
    }
    
    if ($file['size'] > MAX_UPLOAD_SIZE) {
        errorResponse('File too large. Max size: ' . (MAX_UPLOAD_SIZE / 1024 / 1024) . 'MB', 400);
    }
    
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mimeType = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);
    
    if (!in_array($mimeType, ALLOWED_IMAGE_TYPES)) {
        errorResponse('Invalid file type. Only images allowed.', 400);
    }
    
    // Create upload directory if not exists
    $uploadDir = UPLOAD_DIR . '/' . date('Y-m-d');
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0755, true);
    }
    
    // Generate unique filename
    $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
    $filename = time() . '_' . $user['id'] . '_' . uniqid() . '.' . $extension;
    $filepath = $uploadDir . '/' . $filename;
    
    if (!move_uploaded_file($file['tmp_name'], $filepath)) {
        errorResponse('Failed to save file', 500);
    }
    
    // Save to database
    $db = getDB();
    $screenshotId = generateUUID();
    
    $stmt = $db->prepare("
        INSERT INTO screenshots (id, user_id, machine_id, filename, path, file_size)
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([
        $screenshotId,
        $user['id'],
        $machineId,
        $filename,
        $filepath,
        $file['size']
    ]);
    
    jsonResponse([
        'success' => true,
        'screenshot_id' => $screenshotId,
        'filename' => $filename
    ], 201);
}

function handleList() {
    $user = AuthMiddleware::getAuthUser();
    
    $db = getDB();
    
    $page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
    $perPage = isset($_GET['per_page']) ? min((int)$_GET['per_page'], 100) : 50;
    $offset = ($page - 1) * $perPage;
    
    // Admin sees all, users see only their own
    if ($user['role'] === 'admin') {
        $userId = $_GET['user_id'] ?? null;
        
        if ($userId) {
            $stmt = $db->prepare("
                SELECT s.*, u.email as user_email
                FROM screenshots s
                LEFT JOIN users u ON s.user_id = u.id
                WHERE s.user_id = ?
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            ");
            $stmt->execute([$userId, $perPage, $offset]);
        } else {
            $stmt = $db->prepare("
                SELECT s.*, u.email as user_email
                FROM screenshots s
                LEFT JOIN users u ON s.user_id = u.id
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            ");
            $stmt->execute([$perPage, $offset]);
        }
    } else {
        $stmt = $db->prepare("
            SELECT * FROM screenshots
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ");
        $stmt->execute([$user['id'], $perPage, $offset]);
    }
    
    $screenshots = $stmt->fetchAll();
    
    jsonResponse([
        'success' => true,
        'data' => $screenshots,
        'page' => $page,
        'per_page' => $perPage
    ]);
}

function handleDownload() {
    $user = AuthMiddleware::getAuthUser();
    
    $screenshotId = $_GET['id'] ?? '';
    
    if (empty($screenshotId)) {
        errorResponse('Screenshot ID is required', 400);
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM screenshots WHERE id = ?");
    $stmt->execute([$screenshotId]);
    $screenshot = $stmt->fetch();
    
    if (!$screenshot) {
        errorResponse('Screenshot not found', 404);
    }
    
    // Check permissions
    if ($user['role'] !== 'admin' && $screenshot['user_id'] !== $user['id']) {
        errorResponse('Access denied', 403);
    }
    
    if (!file_exists($screenshot['path'])) {
        errorResponse('File not found on disk', 404);
    }
    
    // Serve file
    header('Content-Type: image/png');
    header('Content-Disposition: inline; filename="' . $screenshot['filename'] . '"');
    header('Content-Length: ' . filesize($screenshot['path']));
    readfile($screenshot['path']);
    exit;
}

function handleDelete() {
    $user = AuthMiddleware::getAuthUser();
    
    $screenshotId = $_GET['id'] ?? '';
    
    if (empty($screenshotId)) {
        errorResponse('Screenshot ID is required', 400);
    }
    
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM screenshots WHERE id = ?");
    $stmt->execute([$screenshotId]);
    $screenshot = $stmt->fetch();
    
    if (!$screenshot) {
        errorResponse('Screenshot not found', 404);
    }
    
    // Check permissions - only admin or owner can delete
    if ($user['role'] !== 'admin' && $screenshot['user_id'] !== $user['id']) {
        errorResponse('Access denied', 403);
    }
    
    // Delete file
    if (file_exists($screenshot['path'])) {
        unlink($screenshot['path']);
    }
    
    // Delete from database
    $stmt = $db->prepare("DELETE FROM screenshots WHERE id = ?");
    $stmt->execute([$screenshotId]);
    
    logAudit($user['id'], 'screenshot_deleted', 'screenshot', $screenshotId);
    
    successResponse([], 'Screenshot deleted successfully');
}

function handleCleanup() {
    $admin = AuthMiddleware::requireAdmin();
    
    $input = json_decode(file_get_contents('php://input'), true);
    $olderThanDays = $input['older_than_days'] ?? 30;
    
    if ($olderThanDays < 1) {
        errorResponse('Invalid days parameter', 400);
    }
    
    $db = getDB();
    
    // Get old screenshots
    $stmt = $db->prepare("
        SELECT * FROM screenshots 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL ? DAY)
    ");
    $stmt->execute([$olderThanDays]);
    $screenshots = $stmt->fetchAll();
    
    $deletedCount = 0;
    foreach ($screenshots as $screenshot) {
        if (file_exists($screenshot['path'])) {
            unlink($screenshot['path']);
        }
        $deletedCount++;
    }
    
    // Delete from database
    $stmt = $db->prepare("
        DELETE FROM screenshots 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL ? DAY)
    ");
    $stmt->execute([$olderThanDays]);
    
    logAudit($admin['id'], 'screenshots_cleanup', 'screenshot', null, [
        'older_than_days' => $olderThanDays,
        'deleted_count' => $deletedCount
    ]);
    
    successResponse(['deleted_count' => $deletedCount], 'Cleanup completed');
}
