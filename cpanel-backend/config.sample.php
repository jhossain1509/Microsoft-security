<?php
/**
 * Sample Configuration File
 * 
 * Copy this file to config.php and update with your settings
 * NEVER commit config.php to version control!
 */

// Error reporting (disable in production)
define('DEBUG_MODE', false);

// Database Configuration
define('DB_HOST', 'localhost');
define('DB_NAME', 'your_database_name');
define('DB_USER', 'your_database_user');
define('DB_PASS', 'your_database_password');
define('DB_CHARSET', 'utf8mb4');

// JWT Configuration
// CRITICAL: Generate a strong random secret (minimum 32 characters)
// You can use: php -r "echo bin2hex(random_bytes(32));"
define('JWT_SECRET', '');  // MUST BE SET - see instructions above
define('JWT_ALGORITHM', 'HS256');
define('JWT_ACCESS_EXPIRY', 900); // 15 minutes
define('JWT_REFRESH_EXPIRY', 2592000); // 30 days

// Application Configuration
define('APP_NAME', 'GoldenIT Entra');
define('APP_VERSION', '1.0.0');
// Leave empty for auto-detection or set manually:
// define('APP_URL', 'https://yourdomain.com/Microsoft-Entra');
define('APP_URL', '');

// File Upload Configuration
define('UPLOAD_DIR', __DIR__ . '/uploads');
define('MAX_UPLOAD_SIZE', 5 * 1024 * 1024); // 5MB
define('ALLOWED_IMAGE_TYPES', ['image/jpeg', 'image/png', 'image/gif', 'image/webp']);

// Security Configuration
define('RATE_LIMIT_ENABLED', true);
define('RATE_LIMIT_REQUESTS', 100); // requests per minute
define('BCRYPT_COST', 10);

// CORS Configuration
// Add your domains here
define('CORS_ALLOWED_ORIGINS', [
    'https://yourdomain.com',
    'http://localhost:3000'  // For development only
]);

// Timezone
date_default_timezone_set('UTC');

// Rest of the configuration is loaded from the main config.php
// Include the main config functions here
