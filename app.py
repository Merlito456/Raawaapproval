from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from datetime import datetime, timedelta
import secrets
import hashlib
import json
import os
import base64
import re
from functools import wraps
from config import Config, DevelopmentConfig, ProductionConfig

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import utilities
from utils.db_utils import SupabaseDB
from utils.raawa_generator import RAAWAGenerator
from utils.notification import NotificationManager
from utils.auth import role_required, superadmin_required, approver_required

# Initialize database and utilities
try:
    db = SupabaseDB()
    notification_manager = NotificationManager(db)
    raawa_generator = RAAWAGenerator(db)
    print("✅ All services initialized successfully")
except Exception as e:
    print(f"❌ Error initializing services: {e}")
    # Create a placeholder db to prevent crashes
    db = None
    notification_manager = None
    raawa_generator = None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.full_name = user_data['full_name']
        self.role = user_data['role']
        self.company = user_data.get('company', '')
        self.position = user_data.get('position', '')
        self.is_active = user_data.get('is_active', True)
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_approver(self):
        return self.role == 'approver'
    
    @property
    def is_user(self):
        return self.role == 'user'

@login_manager.user_loader
def load_user(user_id):
    if db:
        user_data = db.get_user_by_id(user_id)
        if user_data:
            return User(user_data)
    return None

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')
        
        if db:
            user = db.authenticate_user(username, password)
            if user:
                login_user(User(user))
                db.log_activity(user['id'], 'login', {'method': 'web'}, 
                              ip=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    if db:
        db.log_activity(current_user.id, 'logout', {}, 
                       ip=request.remote_addr, user_agent=request.headers.get('User-Agent'))
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        company = request.form.get('company')
        position = request.form.get('position')
        
        # Validation
        if not all([username, email, password, full_name]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        # Validate password strength
        from utils.auth import validate_password_strength
        valid, message = validate_password_strength(password)
        if not valid:
            flash(message, 'danger')
            return render_template('register.html')
        
        if db:
            success, message = db.register_user(username, email, password, full_name, company, position)
            if success:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'danger')
    
    return render_template('register.html')

# ==================== HEALTH CHECK ====================

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {}
    }
    
    # Check database connection
    if db:
        try:
            db.supabase.table('users').select('count').limit(1).execute()
            status['services']['database'] = 'connected'
        except Exception as e:
            status['services']['database'] = f'error: {str(e)}'
            status['status'] = 'degraded'
    else:
        status['services']['database'] = 'not initialized'
        status['status'] = 'degraded'
    
    return jsonify(status)

# ==================== MAIN ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    if not db:
        flash('Database connection unavailable', 'danger')
        return render_template('dashboard.html', raawas=[], notifications=[], unread_count=0, stats={})
    
    # Get RAAWAs based on user role
    raawas = db.get_raawas_for_user(current_user.id, current_user.role)
    
    # Get notifications
    notifications = db.get_notifications(current_user.id)
    unread_count = db.get_unread_notification_count(current_user.id)
    
    # Get statistics
    stats = db.get_dashboard_stats(current_user.id, current_user.role)
    
    return render_template('dashboard.html', 
                         raawas=raawas,
                         notifications=notifications,
                         unread_count=unread_count,
                         stats=stats)

@app.route('/generate_raawa', methods=['GET', 'POST'])
@login_required
def generate_raawa():
    if not db:
        flash('Database connection unavailable', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            requisitioner_name = request.form.get('requisitioner_name')
            id_no = request.form.get('id_no')
            department_group = request.form.get('department_group')
            contact_no = request.form.get('contact_no')
            region = request.form.get('region')
            facility_manager_id = request.form.get('facility_manager')
            security_id = request.form.get('security')
            personnel_list_str = request.form.get('personnel_list', '')
            
            # Validate required fields
            if not all([requisitioner_name, id_no, region, facility_manager_id, security_id]):
                flash('Please fill in all required fields', 'danger')
                return render_template('generate_raawa.html', 
                                     facility_managers=db.get_approvers_by_type('facility_manager'),
                                     security_officers=db.get_approvers_by_type('security'),
                                     regions=Config.REGIONS)
            
            # Parse personnel list
            personnel = []
            if personnel_list_str:
                for p in personnel_list_str.split('::'):
                    if p.strip():
                        parts = p.split(',')
                        if len(parts) >= 3:
                            personnel.append({
                                'name': parts[0].strip(),
                                'company': parts[1].strip(),
                                'sec_id': parts[2].strip()
                            })
            
            if len(personnel) > Config.MAX_PERSONNEL:
                flash(f'Maximum {Config.MAX_PERSONNEL} personnel allowed', 'danger')
                return render_template('generate_raawa.html', 
                                     facility_managers=db.get_approvers_by_type('facility_manager'),
                                     security_officers=db.get_approvers_by_type('security'),
                                     regions=Config.REGIONS)
            
            # Generate RAAWA number
            raawa_no = db.generate_raawa_number(region)
            
            # Create RAAWA
            raawa_data = {
                'raawa_no': raawa_no,
                'requisitioner_name': requisitioner_name,
                'id_no': id_no,
                'department_group': department_group,
                'contact_no': contact_no,
                'region': region,
                'facility_manager_id': facility_manager_id,
                'security_id': security_id,
                'personnel': personnel,
                'created_by': current_user.id
            }
            
            raawa_id = db.create_raawa(raawa_data)
            
            # Generate Excel file
            if raawa_generator:
                file_path = raawa_generator.generate_raawa_excel(raawa_id, raawa_data)
            
            # Notify Facility Manager
            if notification_manager:
                notification_manager.notify_approvers(raawa_id, 'fm_pending')
            
            db.log_activity(current_user.id, 'generate_raawa', 
                          {'raawa_no': raawa_no, 'region': region},
                          ip=request.remote_addr, user_agent=request.headers.get('User-Agent'))
            
            flash(f'RAAWA {raawa_no} generated successfully!', 'success')
            return redirect(url_for('raawa_details', raawa_id=raawa_id))
            
        except Exception as e:
            print(f"Error generating RAAWA: {e}")
            flash(f'Error generating RAAWA: {str(e)}', 'danger')
    
    # GET request - show form
    facility_managers = db.get_approvers_by_type('facility_manager')
    security_officers = db.get_approvers_by_type('security')
    
    return render_template('generate_raawa.html',
                         facility_managers=facility_managers,
                         security_officers=security_officers,
                         regions=Config.REGIONS)

@app.route('/raawa/<raawa_id>')
@login_required
def raawa_details(raawa_id):
    if not db:
        flash('Database connection unavailable', 'danger')
        return redirect(url_for('dashboard'))
    
    raawa = db.get_raawa_by_id(raawa_id)
    if not raawa:
        flash('RAAWA not found', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check if user has access
    from utils.auth import can_view_raawa
    if not can_view_raawa(current_user, raawa):
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    personnel = db.get_raawa_personnel(raawa_id)
    
    # Check if RAAWA is expired
    if raawa.get('expires_at'):
        expires_at = datetime.fromisoformat(raawa['expires_at'])
        if expires_at < datetime.now() and raawa['status'] != 'approved':
            db.mark_raawa_expired(raawa_id)
            flash('This RAAWA has expired', 'warning')
    
    return render_template('raawa_details.html', 
                         raawa=raawa,
                         personnel=personnel)

@app.route('/approve_raawa/<raawa_id>', methods=['POST'])
@login_required
def approve_raawa(raawa_id):
    if not db:
        return jsonify({'error': 'Database connection unavailable'}), 500
    
    if current_user.role not in ['approver', 'superadmin']:
        return jsonify({'error': 'Only approvers can approve RAAWAs'}), 403
    
    raawa = db.get_raawa_by_id(raawa_id)
    if not raawa:
        return jsonify({'error': 'RAAWA not found'}), 404
    
    # Check if user can approve
    from utils.auth import can_approve_raawa
    if not can_approve_raawa(current_user, raawa):
        return jsonify({'error': 'You are not authorized to approve this RAAWA'}), 403
    
    # Get signature data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    signature_data = data.get('signature')
    esig_ref_no = data.get('esig_ref_no')
    
    if not signature_data or not esig_ref_no:
        return jsonify({'error': 'Signature and ESig reference required'}), 400
    
    # Determine approval type
    approver = db.get_approver_by_user_id(current_user.id)
    if not approver:
        return jsonify({'error': 'Approver record not found'}), 404
    
    if raawa['facility_manager_id'] == approver['id']:
        approval_type = 'facility_manager'
    elif raawa['security_id'] == approver['id']:
        approval_type = 'security'
    else:
        return jsonify({'error': 'You are not assigned to approve this RAAWA'}), 403
    
    # Process approval
    success = db.approve_raawa(raawa_id, current_user.id, approval_type, signature_data, esig_ref_no)
    
    if success:
        # Notify next approver or requester
        if notification_manager:
            notification_manager.notify_approval(raawa_id, approval_type)
        db.log_activity(current_user.id, 'approve_raawa', 
                      {'raawa_no': raawa['raawa_no'], 'type': approval_type},
                      ip=request.remote_addr, user_agent=request.headers.get('User-Agent'))
        
        return jsonify({'success': True, 'message': 'RAAWA approved successfully'})
    else:
        return jsonify({'error': 'Failed to approve RAAWA'}), 500

@app.route('/verify_raawa', methods=['GET', 'POST'])
@login_required
def verify_raawa():
    if request.method == 'POST':
        if not db:
            return jsonify({'error': 'Database connection unavailable'}), 500
        
        raawa_no = request.form.get('raawa_no')
        if not raawa_no:
            return jsonify({'error': 'RAAWA number required'}), 400
        
        raawa = db.get_raawa_by_number(raawa_no)
        
        if raawa:
            facility_manager = db.get_approver_name(raawa.get('facility_manager_id'))
            security = db.get_approver_name(raawa.get('security_id'))
            
            return jsonify({
                'found': True,
                'status': raawa['status'],
                'requisitioner': raawa['requisitioner_name'],
                'region': raawa['region'],
                'created_at': raawa['created_at'],
                'facility_manager': facility_manager,
                'security': security,
                'expires_at': raawa.get('expires_at')
            })
        else:
            return json
