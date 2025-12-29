<?php
/**
 * GoldenIT Microsoft Entra - Configuration File
 * 
 * IMPORTANT: Keep this file secure and outside public_html if possible
 * Set proper file permissions: chmod 600 config.php
 */

// Error reporting (disable in production)
define('DEBUG_MODE', getenv('DEBUG_MODE') ?: false);
if (DEBUG_MODE) {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}

// Database Configuration
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_NAME', getenv('DB_NAME') ?: 'goldenit_entra');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASS', getenv('DB_PASS') ?: '');
define('DB_CHARSET', 'utf8mb4');

// JWT Configuration
define('JWT_SECRET', getenv('JWT_SECRET') ?: 'CHANGE_THIS_TO_A_VERY_STRONG_SECRET_KEY_MIN_32_CHARS');
define('JWT_ALGORITHM', 'HS256');
define('JWT_ACCESS_EXPIRY', 900); // 15 minutes
define('JWT_REFRESH_EXPIRY', 2592000); // 30 days

// Application Configuration
define('APP_NAME', 'GoldenIT Entra');
define('APP_VERSION', '1.0.0');
define('APP_URL', getenv('APP_URL') ?: 'https://gittoken.store/Microsoft-Entra');
define('API_URL', APP_URL . '/api');

// File Upload Configuration
define('UPLOAD_DIR', __DIR__ . '/uploads');
define('MAX_UPLOAD_SIZE', 5 * 1024 * 1024); // 5MB
define('ALLOWED_IMAGE_TYPES', ['image/jpeg', 'image/png', 'image/gif', 'image/webp']);

// Security Configuration
define('RATE_LIMIT_ENABLED', true);
define('RATE_LIMIT_REQUESTS', 100); // requests per minute
define('BCRYPT_COST', 10);

// CORS Configuration
define('CORS_ALLOWED_ORIGINS', [
    'https://gittoken.store',
    'http://localhost:3000'  // For development
]);

// Timezone
date_default_timezone_set('UTC');

// Database Connection Function
function getDB() {
    static $pdo = null;
    
    if ($pdo === null) {
        try {
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ];
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
        } catch (PDOException $e) {
            if (DEBUG_MODE) {
                die("Database connection failed: " . $e->getMessage());
            } else {
                die("Database connection failed. Please contact administrator.");
            }
        }
    }
    
    return $pdo;
}

// Utility Functions
function generateUUID() {
    return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
        mt_rand(0, 0xffff), mt_rand(0, 0xffff),
        mt_rand(0, 0xffff),
        mt_rand(0, 0x0fff) | 0x4000,
        mt_rand(0, 0x3fff) | 0x8000,
        mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
    );
}

function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function errorResponse($message, $statusCode = 400) {
    jsonResponse(['error' => $message], $statusCode);
}

function successResponse($data = [], $message = 'Success') {
    jsonResponse(['success' => true, 'message' => $message, 'data' => $data]);
}

function getClientIP() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        return $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        return $_SERVER['HTTP_X_FORWARDED_FOR'];
    } else {
        return $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    }
}

function getUserAgent() {
    return $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
}

// CORS Headers
function setCorsHeaders() {
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    
    if (in_array($origin, CORS_ALLOWED_ORIGINS)) {
        header("Access-Control-Allow-Origin: $origin");
    }
    
    header("Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS");
    header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");
    header("Access-Control-Allow-Credentials: true");
    header("Access-Control-Max-Age: 86400");
    
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit;
    }
}

// Call CORS headers on every request
setCorsHeaders();

// Audit Log Function
function logAudit($userId, $action, $objectType = null, $objectId = null, $details = null) {
    try {
        $db = getDB();
        $stmt = $db->prepare("
            INSERT INTO audit_logs (id, user_id, action, object_type, object_id, details, ip, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ");
        $stmt->execute([
            generateUUID(),
            $userId,
            $action,
            $objectType,
            $objectId,
            is_array($details) ? json_encode($details) : $details,
            getClientIP(),
            getUserAgent()
        ]);
    } catch (Exception $e) {
        // Silent fail for audit logs to not break main functionality
        if (DEBUG_MODE) {
            error_log("Audit log failed: " . $e->getMessage());
        }
    }
}
