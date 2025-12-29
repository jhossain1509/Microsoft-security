<?php
/**
 * Authentication Middleware
 * Handles JWT token verification and user authentication
 */

require_once __DIR__ . '/../config.php';
require_once __DIR__ . '/../vendor/autoload.php';

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

class AuthMiddleware {
    
    /**
     * Verify JWT token and return decoded payload
     */
    public static function verifyToken() {
        $headers = getallheaders();
        $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';
        
        if (empty($authHeader)) {
            errorResponse('Authorization header missing', 401);
        }
        
        if (!preg_match('/Bearer\s+(.*)$/i', $authHeader, $matches)) {
            errorResponse('Invalid authorization header format', 401);
        }
        
        $token = $matches[1];
        
        try {
            $decoded = JWT::decode($token, new Key(JWT_SECRET, JWT_ALGORITHM));
            return $decoded;
        } catch (Exception $e) {
            errorResponse('Invalid or expired token: ' . $e->getMessage(), 401);
        }
    }
    
    /**
     * Get current authenticated user
     */
    public static function getAuthUser() {
        $payload = self::verifyToken();
        
        $db = getDB();
        $stmt = $db->prepare("SELECT id, email, role, is_active FROM users WHERE id = ?");
        $stmt->execute([$payload->sub]);
        $user = $stmt->fetch();
        
        if (!$user) {
            errorResponse('User not found', 404);
        }
        
        if (!$user['is_active']) {
            errorResponse('User account is disabled', 403);
        }
        
        return $user;
    }
    
    /**
     * Require admin role
     */
    public static function requireAdmin() {
        $user = self::getAuthUser();
        
        if ($user['role'] !== 'admin') {
            errorResponse('Admin access required', 403);
        }
        
        return $user;
    }
    
    /**
     * Generate JWT access token
     */
    public static function generateAccessToken($user) {
        $payload = [
            'sub' => $user['id'],
            'email' => $user['email'],
            'role' => $user['role'],
            'iat' => time(),
            'exp' => time() + JWT_ACCESS_EXPIRY
        ];
        
        return JWT::encode($payload, JWT_SECRET, JWT_ALGORITHM);
    }
    
    /**
     * Generate refresh token
     */
    public static function generateRefreshToken($user) {
        $db = getDB();
        
        $payload = [
            'sub' => $user['id'],
            'type' => 'refresh',
            'iat' => time(),
            'exp' => time() + JWT_REFRESH_EXPIRY
        ];
        
        $token = JWT::encode($payload, JWT_SECRET, JWT_ALGORITHM);
        $tokenHash = hash('sha256', $token);
        
        // Store refresh token in database
        $stmt = $db->prepare("
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
            VALUES (?, ?, ?, ?)
        ");
        $stmt->execute([
            generateUUID(),
            $user['id'],
            $tokenHash,
            date('Y-m-d H:i:s', time() + JWT_REFRESH_EXPIRY)
        ]);
        
        return $token;
    }
    
    /**
     * Verify refresh token
     */
    public static function verifyRefreshToken($token) {
        try {
            $decoded = JWT::decode($token, new Key(JWT_SECRET, JWT_ALGORITHM));
            
            if (!isset($decoded->type) || $decoded->type !== 'refresh') {
                throw new Exception('Invalid token type');
            }
            
            $tokenHash = hash('sha256', $token);
            $db = getDB();
            
            $stmt = $db->prepare("
                SELECT * FROM refresh_tokens 
                WHERE token_hash = ? AND revoked = 0 AND expires_at > NOW()
            ");
            $stmt->execute([$tokenHash]);
            $tokenRecord = $stmt->fetch();
            
            if (!$tokenRecord) {
                throw new Exception('Token not found or expired');
            }
            
            // Get user
            $stmt = $db->prepare("SELECT * FROM users WHERE id = ? AND is_active = 1");
            $stmt->execute([$decoded->sub]);
            $user = $stmt->fetch();
            
            if (!$user) {
                throw new Exception('User not found or inactive');
            }
            
            return $user;
        } catch (Exception $e) {
            errorResponse('Invalid refresh token: ' . $e->getMessage(), 401);
        }
    }
    
    /**
     * Revoke refresh token
     */
    public static function revokeRefreshToken($token) {
        $tokenHash = hash('sha256', $token);
        $db = getDB();
        
        $stmt = $db->prepare("UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?");
        $stmt->execute([$tokenHash]);
    }
}
