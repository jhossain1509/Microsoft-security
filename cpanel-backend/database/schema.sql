-- GoldenIT Microsoft Entra Database Schema
-- MySQL/MariaDB compatible

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id CHAR(36) PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','user') NOT NULL DEFAULT 'user',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login DATETIME NULL,
  INDEX idx_email (email),
  INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Licenses table
CREATE TABLE IF NOT EXISTS licenses (
  id CHAR(36) PRIMARY KEY,
  license_key VARCHAR(128) UNIQUE NOT NULL,
  max_activations INT NOT NULL DEFAULT 1,
  expires_at DATETIME NULL,
  created_by CHAR(36) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  notes TEXT NULL,
  INDEX idx_license_key (license_key),
  INDEX idx_created_by (created_by),
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Activations table
CREATE TABLE IF NOT EXISTS activations (
  id CHAR(36) PRIMARY KEY,
  license_id CHAR(36) NOT NULL,
  machine_id VARCHAR(255) NOT NULL,
  user_id CHAR(36) NULL,
  ip VARCHAR(50) NULL,
  hostname VARCHAR(255) NULL,
  os_info VARCHAR(255) NULL,
  last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
  revoked TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_license_machine (license_id, machine_id),
  INDEX idx_license_id (license_id),
  INDEX idx_machine_id (machine_id),
  INDEX idx_user_id (user_id),
  FOREIGN KEY (license_id) REFERENCES licenses(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Emails added events table
CREATE TABLE IF NOT EXISTS emails_added (
  id CHAR(36) PRIMARY KEY,
  email VARCHAR(320) NOT NULL,
  user_id CHAR(36) NULL,
  account_email VARCHAR(255) NULL,
  machine_id VARCHAR(255) NULL,
  added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50) DEFAULT 'success',
  notes TEXT NULL,
  INDEX idx_user_id (user_id),
  INDEX idx_account_email (account_email),
  INDEX idx_added_at (added_at),
  INDEX idx_email (email),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Screenshots table
CREATE TABLE IF NOT EXISTS screenshots (
  id CHAR(36) PRIMARY KEY,
  user_id CHAR(36) NULL,
  machine_id VARCHAR(255) NULL,
  filename VARCHAR(512) NOT NULL,
  path VARCHAR(1024) NOT NULL,
  file_size INT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_machine_id (machine_id),
  INDEX idx_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Heartbeat / Client status table
CREATE TABLE IF NOT EXISTS heartbeats (
  id CHAR(36) PRIMARY KEY,
  user_id CHAR(36) NULL,
  machine_id VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'online',
  ip VARCHAR(50) NULL,
  last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
  version VARCHAR(50) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_user_machine (user_id, machine_id),
  INDEX idx_user_id (user_id),
  INDEX idx_machine_id (machine_id),
  INDEX idx_last_activity (last_activity),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
  id CHAR(36) PRIMARY KEY,
  user_id CHAR(36) NULL,
  action VARCHAR(128) NOT NULL,
  object_type VARCHAR(64) NULL,
  object_id VARCHAR(64) NULL,
  details TEXT NULL,
  ip VARCHAR(50) NULL,
  user_agent VARCHAR(512) NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_action (action),
  INDEX idx_created_at (created_at),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Refresh tokens table (for JWT refresh token management)
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id CHAR(36) PRIMARY KEY,
  user_id CHAR(36) NOT NULL,
  token_hash VARCHAR(255) NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  revoked TINYINT(1) DEFAULT 0,
  INDEX idx_user_id (user_id),
  INDEX idx_token_hash (token_hash),
  INDEX idx_expires_at (expires_at),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Settings / Config table (for dynamic server-side configuration)
CREATE TABLE IF NOT EXISTS settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  setting_key VARCHAR(128) UNIQUE NOT NULL,
  setting_value TEXT NULL,
  description TEXT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_setting_key (setting_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123 - CHANGE THIS!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (id, email, password_hash, role, is_active) 
VALUES (
  UUID(), 
  'admin@goldenit.local', 
  '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 
  'admin', 
  1
) ON DUPLICATE KEY UPDATE email=email;

-- Insert default settings
INSERT INTO settings (setting_key, setting_value, description) VALUES
  ('screenshot_interval', '300', 'Screenshot upload interval in seconds (default: 5 minutes)'),
  ('heartbeat_interval', '120', 'Heartbeat interval in seconds (default: 2 minutes)'),
  ('emails_per_account', '5', 'Default emails per account'),
  ('max_screenshot_size', '5242880', 'Max screenshot size in bytes (default: 5MB)'),
  ('app_version', '1.0.0', 'Current application version'),
  ('maintenance_mode', '0', 'Maintenance mode (1=on, 0=off)')
ON DUPLICATE KEY UPDATE setting_key=setting_key;
