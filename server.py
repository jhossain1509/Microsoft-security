"""
Flask web server for GoldenIT Microsoft Entra v-1.2
Admin and User Panel with License Management
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import os
import datetime
from database import db
from config import *
import json

# Bug Fix #7 & #9: CSRF Protection and Rate Limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Bug Fix #7: CSRF Protection
csrf = CSRFProtect(app)

# Bug Fix #9: Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Bug Fix #14: Standard error response helper
def error_response(message: str, code: int = 400):
    """Standardized error response"""
    return jsonify({"success": False, "error": message}), code

def success_response(data=None, message=None):
    """Standardized success response"""
    response = {"success": True}
    if data is not None:
        response.update(data)
    if message:
        response["message"] = message
    return jsonify(response)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return error_response("Admin access required", 403)
        return f(*args, **kwargs)
    return decorated_function

# ===== Authentication Routes =====

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = db.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({"success": True, "role": user['role']})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===== Admin Routes =====

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = db.get_all_users()
    return render_template('admin/dashboard.html', users=users)

@app.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    users = db.get_all_users()
    return jsonify(users)

@app.route('/api/admin/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json()
    user_id = db.create_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        role=data.get('role', 'user')
    )
    if user_id:
        return jsonify({"success": True, "user_id": user_id})
    else:
        return jsonify({"success": False, "message": "User already exists"}), 400

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    data = request.get_json()
    success = db.update_user(user_id, **data)
    return jsonify({"success": success})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    success = db.delete_user(user_id)
    return jsonify({"success": success})

@app.route('/api/admin/licenses', methods=['POST'])
@login_required
@admin_required
def create_license():
    data = request.get_json()
    license_key = db.create_license(
        user_id=data['user_id'],
        max_pcs=data.get('max_pcs', 1),
        expires_days=data.get('expires_days', 365)
    )
    return jsonify({"success": True, "license_key": license_key})

@app.route('/api/admin/licenses/<int:license_id>', methods=['PUT'])
@login_required
@admin_required
def update_license(license_id):
    data = request.get_json()
    success = db.update_license(license_id, **data)
    return jsonify({"success": success})

@app.route('/api/admin/licenses/<int:license_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_license(license_id):
    success = db.delete_license(license_id)
    return jsonify({"success": success})

@app.route('/api/admin/user/<int:user_id>/stats')
@login_required
@admin_required
def get_user_stats_admin(user_id):
    days = request.args.get('days', 30, type=int)
    stats = db.get_user_stats(user_id, days)
    licenses = db.get_user_licenses(user_id)
    activities = db.get_user_activities(user_id, limit=100)
    
    return jsonify({
        "stats": stats,
        "licenses": licenses,
        "activities": activities
    })

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    users = db.get_all_users()
    return render_template('admin/reports.html', users=users)

@app.route('/admin/screenshots')
@login_required
@admin_required
def admin_screenshots():
    screenshots = db.get_all_screenshots()
    return render_template('admin/screenshots.html', screenshots=screenshots)

@app.route('/api/screenshots/delete-all', methods=['POST'])
@login_required
@admin_required
def delete_all_screenshots():
    db.delete_all_screenshots()
    return jsonify({"success": True, "message": "All screenshots deleted"})

# ===== User Routes =====

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    user_id = session['user_id']
    licenses = db.get_user_licenses(user_id)
    stats = db.get_user_stats(user_id, days=30)
    return render_template('user/dashboard.html', licenses=licenses, stats=stats)

@app.route('/api/user/activities')
@login_required
def get_user_activities():
    user_id = session['user_id']
    limit = request.args.get('limit', 100, type=int)
    date_filter = request.args.get('date')
    activities = db.get_user_activities(user_id, limit, date_filter)
    return jsonify(activities)

@app.route('/api/user/stats')
@login_required
def get_user_stats():
    user_id = session['user_id']
    days = request.args.get('days', 30, type=int)
    stats = db.get_user_stats(user_id, days)
    return jsonify(stats)

# Bug Fix #3: Real dashboard stats
@app.route('/api/user/dashboard-stats')
@login_required
def get_dashboard_stats():
    user_id = session['user_id']
    stats = db.get_user_dashboard_stats(user_id)
    return success_response(stats)

@app.route('/api/user/screenshots')
@login_required
def get_user_screenshots():
    user_id = session['user_id']
    limit = request.args.get('limit', 50, type=int)
    screenshots = db.get_user_screenshots(user_id, limit)
    return jsonify(screenshots)

# ===== License Validation API (for desktop app) =====

@app.route('/api/validate-license', methods=['POST'])
@csrf.exempt  # Exempt desktop app endpoints from CSRF
def validate_license():
    data = request.get_json()
    license_key = data.get('license_key')
    pc_id = data.get('pc_id')
    pc_name = data.get('pc_name')
    
    result = db.validate_license(license_key, pc_id, pc_name)
    return jsonify(result)

@app.route('/api/log-activity', methods=['POST'])
@csrf.exempt  # Exempt desktop app
def log_activity():
    data = request.get_json()
    db.log_email_activity(
        user_id=data['user_id'],
        account_email=data['account_email'],
        target_email=data['target_email'],
        status=data['status'],
        error_message=data.get('error_message')
    )
    return jsonify({"success": True})

@app.route('/api/upload-screenshot', methods=['POST'])
@csrf.exempt  # Exempt desktop app
def upload_screenshot():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file"}), 400
    
    file = request.files['screenshot']
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({"error": "Invalid file type"}), 400
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"screenshot_{user_id}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Save file
    file.save(filepath)
    
    # Validate it's a real image using PIL
    try:
        from PIL import Image
        img = Image.open(filepath)
        img.verify()  # Verify it's a valid image
        
        # Reopen for thumbnail (verify() closes the file)
        img = Image.open(filepath)
        img.thumbnail(THUMBNAIL_SIZE)
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = os.path.join(SCREENSHOT_DIR, thumbnail_filename)
        img.save(thumbnail_path)
    except Exception as e:
        # If validation fails, remove the file
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": "Invalid image file"}), 400
    
    # Save to database
    db.save_screenshot(user_id, filename, thumbnail_filename)
    
    return jsonify({"success": True, "filename": filename})

@app.route('/api/screenshot/<filename>')
@login_required
def get_screenshot(filename):
    # Sanitize filename to prevent path traversal
    filename = os.path.basename(filename)
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Verify the path is within SCREENSHOT_DIR
    if not os.path.abspath(filepath).startswith(os.path.abspath(SCREENSHOT_DIR)):
        return jsonify({"error": "Invalid filename"}), 400
    
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "File not found"}), 404

@app.route('/api/screenshot/delete/<int:screenshot_id>', methods=['DELETE'])
@login_required
def delete_screenshot(screenshot_id):
    user_id = session['user_id']
    is_admin = session.get('role') == 'admin'
    
    # Bug Fix #5: Delete with ownership check
    success = db.delete_screenshot_safe(screenshot_id, user_id, is_admin)
    
    if success:
        # Bug Fix #12: Audit log
        db.log_audit(user_id, 'delete_screenshot', 'screenshot', screenshot_id, None, request.remote_addr)
        return success_response({"message": "Screenshot deleted"})
    else:
        return error_response("Screenshot not found or unauthorized", 404)

# ===== Export Routes =====

# ===== Feature 2: API System - Account & Email Management =====

@app.route('/api/user/accounts', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_accounts():
    user_id = session['user_id']
    
    if request.method == 'GET':
        accounts = db.get_user_accounts(user_id)
        return jsonify({"success": True, "accounts": accounts})
    
    elif request.method == 'POST':
        data = request.get_json()
        # Support both single account and bulk upload
        if isinstance(data, list):
            # Bulk upload
            for account in data:
                db.add_user_account(
                    user_id=user_id,
                    email=account['email'],
                    password=account['password'],
                    twofa_secret=account.get('2fa_secret', ''),
                    proxy=account.get('proxy', '')
                )
            return jsonify({"success": True, "count": len(data)})
        else:
            # Single account
            db.add_user_account(
                user_id=user_id,
                email=data['email'],
                password=data['password'],
                twofa_secret=data.get('2fa_secret', ''),
                proxy=data.get('proxy', '')
            )
            return jsonify({"success": True})
    
    elif request.method == 'DELETE':
        account_id = request.args.get('account_id', type=int)
        if account_id:
            db.delete_user_account(account_id, user_id)
        return jsonify({"success": True})

@app.route('/api/user/emails', methods=['GET', 'POST', 'DELETE'])
@login_required
@limiter.limit("100 per hour")  # Bug Fix #9: Rate limiting
def manage_emails():
    user_id = session['user_id']
    
    if request.method == 'GET':
        # Bug Fix #6: Pagination support
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if limit > 0:  # If pagination requested
            result = db.get_user_emails_paginated(user_id, True, limit, offset)
            return success_response(result)
        else:
            emails = db.get_user_emails(user_id)
            return success_response({"emails": emails})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        try:
            # Support both single email and bulk upload
            if isinstance(data, list):
                # Bug Fix #11: Transactional bulk upload
                result = db.add_user_emails_transactional(user_id, data)
                
                # Bug Fix #12: Audit log
                db.log_audit(user_id, 'bulk_add_emails', 'email', None, 
                           f"Added {result['added']}, Skipped {result['skipped']}", 
                           request.remote_addr)
                
                return success_response(result)
            else:
                # Bug Fix #2 & #8: Single email with validation
                email = data.get('email')
                if not email:
                    return error_response("Email is required", 400)
                
                success = db.add_user_email(user_id=user_id, email=email)
                
                if success:
                    # Bug Fix #12: Audit log
                    db.log_audit(user_id, 'add_email', 'email', None, email, request.remote_addr)
                    return success_response({"message": "Email added"})
                else:
                    return error_response("Email already exists or invalid", 400)
                    
        except ValueError as e:
            # Bug Fix #8: Email validation error
            return error_response(str(e), 400)
        except Exception as e:
            return error_response(f"Error adding email: {str(e)}", 500)
    
    elif request.method == 'DELETE':
        email_id = request.args.get('email_id', type=int)
        if not email_id:
            return error_response("Email ID required", 400)
        
        # Bug Fix #5: Delete with ownership check
        success = db.delete_user_email(email_id, user_id)
        
        if success:
            # Bug Fix #12: Audit log
            db.log_audit(user_id, 'delete_email', 'email', email_id, None, request.remote_addr)
            return success_response({"message": "Email deleted"})
        else:
            return error_response("Email not found or unauthorized", 404)

# NEW: Done/Processed Emails Endpoints
@app.route('/api/user/emails-done', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_emails_done():
    user_id = session['user_id']
    
    if request.method == 'GET':
        # Get all processed emails
        done_emails = db.get_done_emails(user_id)
        return success_response({"emails": done_emails})
    
    elif request.method == 'POST':
        # Move email to done
        data = request.get_json()
        email = data.get('email')
        account_used = data.get('account_used')
        pc_id = data.get('pc_id')
        db.move_email_to_done(user_id, email, account_used, pc_id)
        
        # Bug Fix #12: Audit log
        db.log_audit(user_id, 'move_email_to_done', 'email', None, email, request.remote_addr)
        
        return success_response({"message": "Email moved to done"})
    
    elif request.method == 'DELETE':
        action = request.args.get('action')
        if action == 'clean':
            # Clean all done emails
            count = db.clean_done_emails(user_id)
            
            # Bug Fix #12: Audit log
            db.log_audit(user_id, 'clean_done_emails', 'email', None, 
                       f"Cleaned {count} emails", request.remote_addr)
            
            return success_response({"deleted": count, "message": f"{count} emails cleaned"})
        else:
            # Delete single done email
            email_id = request.args.get('id', type=int)
            if not email_id:
                return error_response("Email ID required", 400)
            
            db.delete_done_email(email_id)
            
            # Bug Fix #12: Audit log
            db.log_audit(user_id, 'delete_done_email', 'email', email_id, None, request.remote_addr)
            
            return success_response({"message": "Done email deleted"})

@app.route('/api/user/settings', methods=['GET', 'POST'])
@login_required
def manage_settings():
    user_id = session['user_id']
    
    if request.method == 'GET':
        settings = db.get_user_settings(user_id)
        return jsonify({"success": True, "settings": settings})
    
    elif request.method == 'POST':
        data = request.get_json()
        db.update_user_settings(
            user_id=user_id,
            emails_per_account=data.get('emails_per_account', 10),
            interval_minutes=data.get('interval_minutes', 10),
            max_browsers=data.get('max_browsers', 3),
            api_mode_enabled=data.get('api_mode_enabled', True)
        )
        return jsonify({"success": True})

@app.route('/api/desktop/get-work', methods=['POST'])
@csrf.exempt  # Desktop app endpoint - no CSRF needed
def get_desktop_work():
    """API endpoint for desktop app to fetch accounts and emails"""
    data = request.get_json()
    user_id = data.get('user_id')
    pc_id = data.get('pc_id')
    
    if not user_id or not pc_id:
        return jsonify({"error": "user_id and pc_id required"}), 400
    
    # Get user settings
    settings = db.get_user_settings(user_id)
    
    if not settings.get('api_mode_enabled'):
        return jsonify({"api_mode": False})
    
    # Get accounts and emails
    accounts = db.get_user_accounts(user_id)
    emails = db.get_user_emails(user_id, status='pending')
    
    return jsonify({
        "api_mode": True,
        "accounts": accounts,
        "emails": emails,
        "settings": settings
    })

# ===== Feature 4: Auto Pause/Resume =====

@app.route('/api/pc/heartbeat', methods=['POST'])
@csrf.exempt  # Desktop app endpoint - no CSRF needed
def pc_heartbeat():
    """Desktop app sends heartbeat every minute"""
    data = request.get_json()
    user_id = data.get('user_id')
    pc_id = data.get('pc_id')
    pc_name = data.get('pc_name', 'Unknown')
    current_account = data.get('current_account', '')
    
    if not user_id or not pc_id:
        return jsonify({"error": "user_id and pc_id required"}), 400
    
    # Update PC status
    db.update_pc_status(user_id, pc_id, pc_name, current_account)
    
    # Check if PC should be paused
    should_pause = db.should_pc_pause(pc_id)
    
    return jsonify({
        "success": True,
        "should_pause": should_pause
    })

@app.route('/api/pc/status', methods=['GET'])
@login_required
def get_pc_status():
    """Get all PCs status for a user"""
    user_id = request.args.get('user_id', session.get('user_id'), type=int)
    
    # Admin can see any user, users can only see their own
    if session.get('role') != 'admin' and user_id != session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    pcs = db.get_user_pcs(user_id)
    return jsonify({"success": True, "pcs": pcs})

@app.route('/api/pc/pause', methods=['POST'])
@login_required
@admin_required
def pause_pc():
    """Admin can remotely pause a PC"""
    data = request.get_json()
    pc_id = data.get('pc_id')
    pause = data.get('pause', True)
    
    db.set_pc_pause(pc_id, pause)
    return jsonify({"success": True})

# ===== Feature 6: Real-time Monitoring =====

@app.route('/api/monitoring/live-stats', methods=['GET'])
@login_required
def get_live_stats():
    """Get real-time statistics"""
    user_id = request.args.get('user_id', session.get('user_id'), type=int)
    
    # Admin can see any user, users can only see their own
    if session.get('role') != 'admin' and user_id != session.get('user_id'):
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get PC status
    pcs = db.get_user_pcs(user_id)
    
    # Get recent activity count
    activities = db.get_user_activities(user_id, limit=100)
    
    # Calculate stats
    online_pcs = sum(1 for pc in pcs if pc['status'] == 'online')
    total_emails_today = len([a for a in activities if a['created_at'].startswith(datetime.datetime.now().strftime('%Y-%m-%d'))])
    
    return jsonify({
        "success": True,
        "online_pcs": online_pcs,
        "total_pcs": len(pcs),
        "emails_today": total_emails_today,
        "pcs": pcs,
        "recent_activities": activities[:20]
    })

# ===== Feature 8: Notification System =====

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    user_id = session['user_id']
    
    notifications = []
    
    # Check for offline PCs
    pcs = db.get_user_pcs(user_id)
    for pc in pcs:
        if pc['status'] == 'offline':
            notifications.append({
                "type": "warning",
                "message": f"PC {pc['pc_name']} is offline",
                "timestamp": pc['last_heartbeat']
            })
    
    # Check for license expiry (if user)
    if session.get('role') != 'admin':
        user = db.get_user(user_id)
        if user and user.get('licenses'):
            for lic in user['licenses']:
                if lic.get('expires_at'):
                    expires = datetime.datetime.strptime(lic['expires_at'], '%Y-%m-%d %H:%M:%S')
                    days_left = (expires - datetime.datetime.now()).days
                    if days_left <= 7 and days_left >= 0:
                        notifications.append({
                            "type": "warning",
                            "message": f"License expires in {days_left} days",
                            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
    
    return jsonify({"success": True, "notifications": notifications})

@app.route('/api/export/csv')
@login_required
def export_csv():
    user_id = session['user_id']
    date_filter = request.args.get('date')
    
    activities = db.get_user_activities(user_id, limit=10000, date_filter=date_filter)
    
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Account Email', 'Target Email', 'Status', 'Error Message'])
    
    for activity in activities:
        writer.writerow([
            activity['created_at'],
            activity['account_email'],
            activity['target_email'],
            activity['status'],
            activity['error_message'] or ''
        ])
    
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=activities_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
    }

# ==================== Developer Panel Routes ====================

@app.route('/admin/developer')
def admin_developer():
    """Developer panel for editing all system settings"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return "Access denied. Admin only.", 403
    
    return render_template('admin/developer.html')

@app.route('/api/admin/settings', methods=['GET'])
def get_settings():
    """Get all system settings"""
    if 'user_id' not in session:
        return error_response("Not authenticated", 401)
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return error_response("Access denied. Admin only.", 403)
    
    settings = db.get_all_settings()
    return success_response({'settings': settings})

@app.route('/api/admin/settings', methods=['POST'])
def update_settings():
    """Update system settings"""
    if 'user_id' not in session:
        return error_response("Not authenticated", 401)
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return error_response("Access denied. Admin only.", 403)
    
    data = request.json
    if not data or 'settings' not in data:
        return error_response("No settings provided", 400)
    
    try:
        # Update each setting
        for key, value in data['settings'].items():
            # Determine category from key prefix
            category = key.split('_')[0] if '_' in key else 'General'
            db.set_system_setting(key, value, category, session['user_id'])
        
        # Log the action
        db.log_audit(
            user_id=session['user_id'],
            action='update_settings',
            entity_type='system_settings',
            entity_id=None,
            details=f"Updated {len(data['settings'])} settings",
            ip_address=request.remote_addr
        )
        
        return success_response(None, "Settings updated successfully")
    
    except Exception as e:
        return error_response(f"Error updating settings: {str(e)}", 500)

@app.route('/api/admin/settings/reset', methods=['POST'])
def reset_settings():
    """Reset all settings to defaults"""
    if 'user_id' not in session:
        return error_response("Not authenticated", 401)
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return error_response("Access denied. Admin only.", 403)
    
    try:
        db.reset_settings_to_default()
        
        # Log the action
        db.log_audit(
            user_id=session['user_id'],
            action='reset_settings',
            entity_type='system_settings',
            entity_id=None,
            details="Reset all settings to defaults",
            ip_address=request.remote_addr
        )
        
        return success_response(None, "Settings reset to defaults")
    
    except Exception as e:
        return error_response(f"Error resetting settings: {str(e)}", 500)

@app.route('/api/admin/settings/export', methods=['GET'])
def export_settings():
    """Export settings to JSON file"""
    if 'user_id' not in session:
        return error_response("Not authenticated", 401)
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return error_response("Access denied. Admin only.", 403)
    
    try:
        settings_data = db.export_settings()
        
        # Log the action
        db.log_audit(
            user_id=session['user_id'],
            action='export_settings',
            entity_type='system_settings',
            entity_id=None,
            details="Exported all settings",
            ip_address=request.remote_addr
        )
        
        return jsonify(settings_data), 200, {
            'Content-Type': 'application/json',
            'Content-Disposition': f'attachment; filename=settings-{datetime.datetime.now().strftime("%Y%m%d")}.json'
        }
    
    except Exception as e:
        return error_response(f"Error exporting settings: {str(e)}", 500)

@app.route('/api/admin/settings/import', methods=['POST'])
def import_settings():
    """Import settings from JSON file"""
    if 'user_id' not in session:
        return error_response("Not authenticated", 401)
    
    user = db.get_user_by_id(session['user_id'])
    if not user or user['role'] != 'admin':
        return error_response("Access denied. Admin only.", 403)
    
    data = request.json
    if not data:
        return error_response("No data provided", 400)
    
    try:
        db.import_settings(data, session['user_id'])
        
        # Log the action
        db.log_audit(
            user_id=session['user_id'],
            action='import_settings',
            entity_type='system_settings',
            entity_id=None,
            details=f"Imported settings (version: {data.get('version', 'unknown')})",
            ip_address=request.remote_addr
        )
        
        return success_response(None, "Settings imported successfully")
    
    except Exception as e:
        return error_response(f"Error importing settings: {str(e)}", 500)

if __name__ == '__main__':
    # Only enable debug in development
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    if debug_mode:
        print("WARNING: Running in DEBUG mode. Do NOT use in production!")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=debug_mode)
