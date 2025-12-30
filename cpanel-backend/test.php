<!DOCTYPE html>
<html>
<head>
    <title>Backend Test - GoldenIT Entra</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .test-box {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .success { color: #28a745; font-weight: bold; }
        .error { color: #dc3545; font-weight: bold; }
        .warning { color: #ffc107; font-weight: bold; }
        pre {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 0; }
    </style>
</head>
<body>
    <h1>🔧 Backend Setup Test</h1>
    <p>This page tests if your backend is properly configured.</p>

    <?php
    error_reporting(E_ALL);
    ini_set('display_errors', 1);

    echo '<div class="test-box">';
    echo '<h2>Test 1: PHP Version</h2>';
    $phpVersion = phpversion();
    if (version_compare($phpVersion, '7.4', '>=')) {
        echo '<p class="success">✅ PHP Version: ' . $phpVersion . ' (OK)</p>';
    } else {
        echo '<p class="error">❌ PHP Version: ' . $phpVersion . ' (Need 7.4+)</p>';
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 2: Required Files</h2>';
    $required_files = [
        'config.php',
        'vendor/autoload.php',
        'vendor/firebase/php-jwt/src/JWT.php',
        'api/auth.php',
        'middleware/auth.php'
    ];
    $all_files_ok = true;
    foreach ($required_files as $file) {
        if (file_exists($file)) {
            echo '<p class="success">✅ ' . $file . '</p>';
        } else {
            echo '<p class="error">❌ ' . $file . ' (MISSING)</p>';
            $all_files_ok = false;
        }
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 3: JWT Library</h2>';
    try {
        require_once 'vendor/autoload.php';
        if (class_exists('Firebase\\JWT\\JWT')) {
            echo '<p class="success">✅ JWT Library loaded successfully</p>';
            echo '<p>Firebase PHP-JWT is working!</p>';
        } else {
            echo '<p class="error">❌ JWT class not found</p>';
        }
    } catch (Exception $e) {
        echo '<p class="error">❌ Error loading JWT: ' . $e->getMessage() . '</p>';
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 4: Configuration</h2>';
    try {
        require_once 'config.php';
        
        // Check JWT_SECRET
        if (defined('JWT_SECRET')) {
            $secret = JWT_SECRET;
            if (empty($secret)) {
                echo '<p class="error">❌ JWT_SECRET is empty - MUST be set!</p>';
            } elseif (strlen($secret) < 32) {
                echo '<p class="warning">⚠️ JWT_SECRET is too short (need 32+ chars)</p>';
            } else {
                echo '<p class="success">✅ JWT_SECRET is configured (length: ' . strlen($secret) . ')</p>';
            }
        } else {
            echo '<p class="error">❌ JWT_SECRET not defined</p>';
        }
        
        // Check DB config
        echo '<p>Database Configuration:</p>';
        echo '<pre>';
        echo 'DB_HOST: ' . (defined('DB_HOST') ? DB_HOST : 'NOT SET') . "\n";
        echo 'DB_NAME: ' . (defined('DB_NAME') ? DB_NAME : 'NOT SET') . "\n";
        echo 'DB_USER: ' . (defined('DB_USER') ? DB_USER : 'NOT SET') . "\n";
        echo 'DB_PASS: ' . (defined('DB_PASS') ? (DB_PASS ? '***SET***' : 'EMPTY') : 'NOT SET') . "\n";
        echo '</pre>';
        
    } catch (Exception $e) {
        echo '<p class="error">❌ Error loading config: ' . $e->getMessage() . '</p>';
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 5: Database Connection</h2>';
    try {
        if (function_exists('getDB')) {
            $db = getDB();
            echo '<p class="success">✅ Database connection successful!</p>';
            
            // Test query
            $stmt = $db->query("SELECT COUNT(*) as count FROM users");
            $result = $stmt->fetch();
            echo '<p>Users in database: ' . $result['count'] . '</p>';
            
        } else {
            echo '<p class="error">❌ getDB() function not found</p>';
        }
    } catch (Exception $e) {
        echo '<p class="error">❌ Database Error: ' . $e->getMessage() . '</p>';
        echo '<p>Common causes:</p>';
        echo '<ul>';
        echo '<li>Database not created in cPanel</li>';
        echo '<li>Wrong credentials in config.php</li>';
        echo '<li>User doesn\'t have permissions</li>';
        echo '<li>schema.sql not imported</li>';
        echo '</ul>';
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 6: API Endpoint</h2>';
    echo '<p>Test the auth API:</p>';
    echo '<pre>';
    $test_url = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http') . 
                '://' . $_SERVER['HTTP_HOST'] . 
                dirname($_SERVER['SCRIPT_NAME']) . '/api/auth.php?action=login';
    echo 'URL: ' . $test_url;
    echo '</pre>';
    echo '<p><a href="api/auth.php?action=login" target="_blank">Click here to test API</a></p>';
    echo '<p class="warning">Expected: JSON error message (this is normal without credentials)</p>';
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Test 7: Uploads Directory</h2>';
    if (is_dir('uploads')) {
        if (is_writable('uploads')) {
            echo '<p class="success">✅ uploads/ directory exists and is writable</p>';
        } else {
            echo '<p class="warning">⚠️ uploads/ exists but not writable (chmod 755)</p>';
        }
    } else {
        echo '<p class="warning">⚠️ uploads/ directory not found (will be created automatically)</p>';
    }
    echo '</div>';

    echo '<div class="test-box">';
    echo '<h2>Summary</h2>';
    if ($all_files_ok && defined('JWT_SECRET') && !empty(JWT_SECRET) && function_exists('getDB')) {
        echo '<p class="success">✅ Backend appears to be properly configured!</p>';
        echo '<p>Next steps:</p>';
        echo '<ol>';
        echo '<li>Delete this test.php file (for security)</li>';
        echo '<li>Visit <a href="admin/login.html">Admin Panel</a></li>';
        echo '<li>Login with: admin@goldenit.local / admin123</li>';
        echo '<li>Change admin password immediately!</li>';
        echo '<li>Create users and licenses</li>';
        echo '</ol>';
    } else {
        echo '<p class="error">❌ Some tests failed. Please fix the issues above.</p>';
        echo '<p>Check <a href="TROUBLESHOOTING.md" target="_blank">TROUBLESHOOTING.md</a> for help.</p>';
    }
    echo '</div>';
    ?>

    <div class="test-box">
        <h2>📚 Documentation</h2>
        <ul>
            <li><a href="TROUBLESHOOTING.md" target="_blank">Troubleshooting Guide</a></li>
            <li><a href="README.md" target="_blank">Backend README</a></li>
            <li><a href="admin/login.html">Admin Panel</a></li>
        </ul>
    </div>
</body>
</html>
