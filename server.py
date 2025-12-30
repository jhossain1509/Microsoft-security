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

app = Flask(__name__)
app.secret_key = SECRET_KEY

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
            return jsonify({"error": "Admin access required"}), 403
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

@app.route('/api/user/screenshots')
@login_required
def get_user_screenshots():
    user_id = session['user_id']
    limit = request.args.get('limit', 50, type=int)
    screenshots = db.get_user_screenshots(user_id, limit)
    return jsonify(screenshots)

# ===== License Validation API (for desktop app) =====

@app.route('/api/validate-license', methods=['POST'])
def validate_license():
    data = request.get_json()
    license_key = data.get('license_key')
    pc_id = data.get('pc_id')
    pc_name = data.get('pc_name')
    
    result = db.validate_license(license_key, pc_id, pc_name)
    return jsonify(result)

@app.route('/api/log-activity', methods=['POST'])
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
def upload_screenshot():
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot file"}), 400
    
    file = request.files['screenshot']
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"screenshot_{user_id}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    # Save file
    file.save(filepath)
    
    # Create thumbnail
    from PIL import Image
    img = Image.open(filepath)
    img.thumbnail(THUMBNAIL_SIZE)
    thumbnail_filename = f"thumb_{filename}"
    thumbnail_path = os.path.join(SCREENSHOT_DIR, thumbnail_filename)
    img.save(thumbnail_path)
    
    # Save to database
    db.save_screenshot(user_id, filename, thumbnail_filename)
    
    return jsonify({"success": True, "filename": filename})

@app.route('/api/screenshot/<filename>')
@login_required
def get_screenshot(filename):
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "File not found"}), 404

@app.route('/api/screenshot/delete/<int:screenshot_id>', methods=['DELETE'])
@login_required
def delete_screenshot(screenshot_id):
    success = db.delete_screenshot(screenshot_id)
    return jsonify({"success": success})

# ===== Export Routes =====

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

if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)
