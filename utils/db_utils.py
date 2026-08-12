from supabase import create_client
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import os
from config import Config

class SupabaseDB:
    def __init__(self):
        # Validate credentials before creating client
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError(
                "Supabase credentials not configured. "
                "Please set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
        
        try:
            self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase client: {e}")
            raise
        
        self._ensure_superadmin()
    
    def _ensure_superadmin(self):
        """Ensure superadmin account exists on first run"""
        try:
            # Check if superadmin exists
            response = self.supabase.table('users')\
                .select('*')\
                .eq('role', 'superadmin')\
                .execute()
            
            if not response.data or len(response.data) == 0:
                # Create superadmin with plain text password
                user_data = {
                    'username': Config.SUPERADMIN_USERNAME,
                    'email': Config.SUPERADMIN_EMAIL,
                    'password_hash': Config.SUPERADMIN_PASSWORD,  # Plain text
                    'full_name': Config.SUPERADMIN_FULLNAME,
                    'role': 'superadmin',
                    'is_active': True
                }
                
                response = self.supabase.table('users')\
                    .insert(user_data)\
                    .execute()
                
                if response.data:
                    print("✅ Superadmin account created successfully!")
                    print(f"   Username: {Config.SUPERADMIN_USERNAME}")
                    print(f"   Password: {Config.SUPERADMIN_PASSWORD}")
                else:
                    print("⚠️ Failed to create superadmin account")
        except Exception as e:
            print(f"⚠️ Error ensuring superadmin: {e}")
    
    def hash_password(self, password):
        """Return plain text password (no hashing)"""
        return password  # Disabled hashing
    
    def verify_password(self, stored_password, password):
        """Verify plain text password"""
        return stored_password == password  # Direct comparison
    
    # ============ USER AUTHENTICATION ============
    def authenticate_user(self, username, password):
        """Authenticate user with username and password"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                # Plain text password verification
                if user['password_hash'] == password:
                    return user
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('id', user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def register_user(self, username, email, password, full_name, company, position):
        """Register a new user with plain text password"""
        try:
            # Check if username exists
            existing = self.get_user_by_username(username)
            if existing:
                return False, "Username already exists"
            
            # Check if email exists
            response = self.supabase.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()
            if response.data and len(response.data) > 0:
                return False, "Email already registered"
            
            # Store password as plain text
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password,  # Plain text
                'full_name': full_name,
                'company': company or '',
                'position': position or '',
                'role': 'user',
                'is_active': True
            }
            
            response = self.supabase.table('users')\
                .insert(user_data)\
                .execute()
            
            if response.data:
                return True, "User registered successfully"
            return False, "Registration failed"
        except Exception as e:
            return False, str(e)
    
    def update_user(self, user_id, user_data):
        """Update user information"""
        try:
            # If password is being updated, store as plain text
            if 'password' in user_data:
                user_data['password_hash'] = user_data.pop('password')
            
            user_data['updated_at'] = datetime.now().isoformat()
            response = self.supabase.table('users')\
                .update(user_data)\
                .eq('id', user_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    # ============ APPROVERS MANAGEMENT ============
    def create_approver(self, approver_data):
        """Create a new approver with plain text password"""
        try:
            # Check if username exists
            existing = self.get_user_by_username(approver_data['username'])
            if existing:
                return False, "Username already exists"
            
            # Store password as plain text
            password = approver_data['password']
            
            # Create user account first
            user_data = {
                'username': approver_data['username'],
                'email': f"{approver_data['username']}@raawa.com",
                'password_hash': password,  # Plain text
                'full_name': f"{approver_data['first_name']} {approver_data['last_name']}",
                'role': 'approver',
                'is_active': True
            }
            
            user_response = self.supabase.table('users')\
                .insert(user_data)\
                .execute()
            
            if not user_response.data:
                return False, "Failed to create user account"
            
            user_id = user_response.data[0]['id']
            
            # Create approver record
            approver_record = {
                'last_name': approver_data['last_name'],
                'first_name': approver_data['first_name'],
                'contact_no': approver_data.get('contact_no', ''),
                'username': approver_data['username'],
                'password_hash': password,  # Plain text
                'role_type': approver_data['role_type'],
                'region': approver_data.get('region', ''),
                'created_by': approver_data['created_by'],
                'user_id': user_id,
                'is_active': True
            }
            
            response = self.supabase.table('approvers')\
                .insert(approver_record)\
                .execute()
            
            if response.data:
                return True, "Approver created successfully"
            return False, "Failed to create approver"
            
        except Exception as e:
            return False, str(e)
    
    def get_all_approvers(self):
        """Get all approvers"""
        try:
            response = self.supabase.table('approvers')\
                .select('*')\
                .order('created_at', desc=True)\
                .execute()
            
            approvers = response.data if response.data else []
            
            # Get user info for each approver
            for approver in approvers:
                user = self.get_user_by_id(approver.get('user_id'))
                if user:
                    approver['user'] = user
            
            return approvers
        except Exception as e:
            print(f"Error getting approvers: {e}")
            return []
    
    def get_approvers_by_type(self, approval_type):
        """Get approvers by role type"""
        try:
            response = self.supabase.table('approvers')\
                .select('*')\
                .eq('role_type', approval_type)\
                .eq('is_active', True)\
                .execute()
            
            approvers = response.data if response.data else []
            
            # Get user info for each approver
            for approver in approvers:
                user = self.get_user_by_id(approver.get('user_id'))
                if user:
                    approver['user'] = user
            
            return approvers
        except Exception as e:
            print(f"Error getting approvers by type: {e}")
            return []
    
    def get_approver_by_user_id(self, user_id):
        """Get approver by user ID"""
        try:
            response = self.supabase.table('approvers')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting approver: {e}")
            return None
    
    def get_approver_name(self, approver_id):
        """Get approver full name by ID"""
        if not approver_id:
            return "Not Assigned"
        
        try:
            response = self.supabase.table('approvers')\
                .select('first_name, last_name')\
                .eq('id', approver_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                approver = response.data[0]
                return f"{approver['first_name']} {approver['last_name']}"
            return "Unknown"
        except Exception as e:
            print(f"Error getting approver name: {e}")
            return "Unknown"
    
    def update_approver(self, approver_id, approver_data):
        """Update approver information"""
        try:
            # If password is being updated, store as plain text
            if 'password' in approver_data:
                approver_data['password_hash'] = approver_data.pop('password')
            
            approver_data['updated_at'] = datetime.now().isoformat()
            response = self.supabase.table('approvers')\
                .update(approver_data)\
                .eq('id', approver_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error updating approver: {e}")
            return False
    
    # ============ RAAWA MANAGEMENT ============
    def generate_raawa_number(self, region):
        """Generate unique RAAWA number"""
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            
            # Count existing RAAWAs for today in this region
            response = self.supabase.table('raawa')\
                .select('raawa_no')\
                .like('raawa_no', f'{region}-{date_str}-%')\
                .execute()
            
            count = len(response.data) if response.data else 0
            count += 1
            
            return f"{region}-{date_str}-{str(count).zfill(4)}"
        except Exception as e:
            print(f"Error generating RAAWA number: {e}")
            # Fallback with timestamp
            timestamp = datetime.now().strftime('%H%M%S')
            return f"{region}-{timestamp}-{secrets.token_hex(4)}"
    
    def create_raawa(self, raawa_data):
        """Create a new RAAWA"""
        try:
            # Insert RAAWA
            raawa_record = {
                'raawa_no': raawa_data['raawa_no'],
                'requisitioner_name': raawa_data['requisitioner_name'],
                'id_no': raawa_data['id_no'],
                'department_group': raawa_data.get('department_group', ''),
                'contact_no': raawa_data.get('contact_no', ''),
                'region': raawa_data['region'],
                'facility_manager_id': raawa_data.get('facility_manager_id'),
                'security_id': raawa_data.get('security_id'),
                'created_by': raawa_data['created_by'],
                'status': 'draft',
                'expires_at': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            response = self.supabase.table('raawa')\
                .insert(raawa_record)\
                .execute()
            
            if not response.data:
                raise Exception("Failed to create RAAWA")
            
            raawa_id = response.data[0]['id']
            
            # Insert personnel
            for person in raawa_data.get('personnel', []):
                person_data = {
                    'raawa_id': raawa_id,
                    'name': person['name'],
                    'company': person.get('company', ''),
                    'sec_id': person.get('sec_id', '')
                }
                self.supabase.table('raawa_personnel')\
                    .insert(person_data)\
                    .execute()
            
            return raawa_id
            
        except Exception as e:
            print(f"Error creating RAAWA: {e}")
            raise
    
    def get_raawa_by_id(self, raawa_id):
        """Get RAAWA by ID with all relations"""
        try:
            # Get RAAWA
            response = self.supabase.table('raawa')\
                .select('*')\
                .eq('id', raawa_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return None
            
            raawa = response.data[0]
            
            # Get facility manager details
            if raawa.get('facility_manager_id'):
                fm_response = self.supabase.table('approvers')\
                    .select('*')\
                    .eq('id', raawa['facility_manager_id'])\
                    .execute()
                if fm_response.data:
                    raawa['facility_manager'] = fm_response.data[0]
                    # Get user details
                    user = self.get_user_by_id(fm_response.data[0].get('user_id'))
                    if user:
                        raawa['facility_manager']['user'] = user
            
            # Get security details
            if raawa.get('security_id'):
                sec_response = self.supabase.table('approvers')\
                    .select('*')\
                    .eq('id', raawa['security_id'])\
                    .execute()
                if sec_response.data:
                    raawa['security'] = sec_response.data[0]
                    user = self.get_user_by_id(sec_response.data[0].get('user_id'))
                    if user:
                        raawa['security']['user'] = user
            
            # Get creator details
            if raawa.get('created_by'):
                creator = self.get_user_by_id(raawa['created_by'])
                if creator:
                    raawa['creator'] = creator
            
            return raawa
            
        except Exception as e:
            print(f"Error getting RAAWA: {e}")
            return None
    
    def get_raawa_by_number(self, raawa_no):
        """Get RAAWA by number"""
        try:
            response = self.supabase.table('raawa')\
                .select('*')\
                .eq('raawa_no', raawa_no)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting RAAWA by number: {e}")
            return None
    
    def get_raawa_personnel(self, raawa_id):
        """Get all personnel for a RAAWA"""
        try:
            response = self.supabase.table('raawa_personnel')\
                .select('*')\
                .eq('raawa_id', raawa_id)\
                .order('created_at')\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting personnel: {e}")
            return []
    
    def get_raawas_for_user(self, user_id, role):
        """Get RAAWAs accessible to a user"""
        try:
            if role == 'superadmin':
                # Superadmin sees all
                response = self.supabase.table('raawa')\
                    .select('*')\
                    .order('created_at', desc=True)\
                    .execute()
                return response.data if response.data else []
            
            elif role == 'user':
                # User sees only their own
                response = self.supabase.table('raawa')\
                    .select('*')\
                    .eq('created_by', user_id)\
                    .order('created_at', desc=True)\
                    .execute()
                return response.data if response.data else []
            
            elif role == 'approver':
                # Approver sees assigned RAAWAs
                approver = self.get_approver_by_user_id(user_id)
                if not approver:
                    return []
                
                approver_id = approver['id']
                response = self.supabase.table('raawa')\
                    .select('*')\
                    .or_(f'facility_manager_id.eq.{approver_id},security_id.eq.{approver_id}')\
                    .order('created_at', desc=True)\
                    .execute()
                return response.data if response.data else []
            
            return []
            
        except Exception as e:
            print(f"Error getting RAAWAs for user: {e}")
            return []
    
    def update_raawa(self, raawa_id, update_data):
        """Update RAAWA"""
        try:
            update_data['updated_at'] = datetime.now().isoformat()
            response = self.supabase.table('raawa')\
                .update(update_data)\
                .eq('id', raawa_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error updating RAAWA: {e}")
            return False
    
    def approve_raawa(self, raawa_id, approver_user_id, approval_type, signature_data, esig_ref_no):
        """Approve RAAWA with signature"""
        try:
            # Get approver ID
            approver = self.get_approver_by_user_id(approver_user_id)
            if not approver:
                return False
            
            approver_id = approver['id']
            
            # Update RAAWA
            update_data = {
                'esig_ref_no': esig_ref_no,
                'updated_at': datetime.now().isoformat()
            }
            
            if approval_type == 'facility_manager':
                update_data['facility_manager_signature'] = signature_data
                update_data['status'] = 'security_pending'
                update_data['fm_approved_at'] = datetime.now().isoformat()
            elif approval_type == 'security':
                update_data['security_signature'] = signature_data
                update_data['status'] = 'approved'
                update_data['approved_at'] = datetime.now().isoformat()
            else:
                return False
            
            response = self.supabase.table('raawa')\
                .update(update_data)\
                .eq('id', raawa_id)\
                .execute()
            
            if not response.data:
                return False
            
            # If fully approved, generate PDF
            if update_data.get('status') == 'approved':
                try:
                    from utils.raawa_generator import RAAWAGenerator
                    generator = RAAWAGenerator(self)
                    generator.generate_raawa_pdf(raawa_id)
                except Exception as e:
                    print(f"Error generating PDF: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error approving RAAWA: {e}")
            return False
    
    def get_raawa_by_esig_ref(self, esig_ref):
        """Get RAAWA by ESig reference number"""
        try:
            response = self.supabase.table('raawa')\
                .select('*')\
                .eq('esig_ref_no', esig_ref)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting RAAWA by ESig ref: {e}")
            return None
    
    def mark_raawa_expired(self, raawa_id):
        """Mark RAAWA as expired"""
        try:
            response = self.supabase.table('raawa')\
                .update({'status': 'expired', 'updated_at': datetime.now().isoformat()})\
                .eq('id', raawa_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error marking RAAWA expired: {e}")
            return False
    
    # ============ DASHBOARD STATISTICS ============
    def get_dashboard_stats(self, user_id, role):
        """Get dashboard statistics for a user"""
        stats = {
            'total': 0,
            'pending': 0,
            'approved': 0,
            'expired': 0,
            'fm_pending': 0,
            'security_pending': 0
        }
        
        raawas = self.get_raawas_for_user(user_id, role)
        stats['total'] = len(raawas)
        
        for r in raawas:
            if r.get('status') == 'approved':
                stats['approved'] += 1
            elif r.get('status') == 'expired':
                stats['expired'] += 1
            elif r.get('status') == 'fm_pending':
                stats['fm_pending'] += 1
                stats['pending'] += 1
            elif r.get('status') == 'security_pending':
                stats['security_pending'] += 1
                stats['pending'] += 1
            elif r.get('status') == 'draft':
                stats['pending'] += 1
        
        return stats
    
    # ============ NOTIFICATIONS ============
    def create_notification(self, user_id, title, message, type, link=None):
        """Create a notification"""
        try:
            notification = {
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': type,
                'link': link,
                'is_read': False
            }
            
            response = self.supabase.table('notifications')\
                .insert(notification)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    def get_notifications(self, user_id, limit=50):
        """Get notifications for a user"""
        try:
            response = self.supabase.table('notifications')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []
    
    def get_unread_notification_count(self, user_id):
        """Get count of unread notifications"""
        try:
            response = self.supabase.table('notifications')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('is_read', False)\
                .execute()
            
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error getting unread notification count: {e}")
            return 0
    
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            response = self.supabase.table('notifications')\
                .update({'is_read': True, 'read_at': datetime.now().isoformat()})\
                .eq('id', notification_id)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error marking notification read: {e}")
            return False
    
    def mark_all_notifications_read(self, user_id):
        """Mark all notifications as read for a user"""
        try:
            response = self.supabase.table('notifications')\
                .update({'is_read': True, 'read_at': datetime.now().isoformat()})\
                .eq('user_id', user_id)\
                .eq('is_read', False)\
                .execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error marking all notifications read: {e}")
            return False
    
    # ============ MESSAGES ============
    def create_message(self, message_data):
        """Create a new message"""
        try:
            message = {
                'sender_id': message_data['sender_id'],
                'recipient_id': message_data.get('recipient_id'),
                'message_type': message_data['message_type'],
                'region': message_data.get('region'),
                'content': message_data['content'],
                'is_read': False
            }
            
            response = self.supabase.table('messages')\
                .insert(message)\
                .execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"Error creating message: {e}")
            return None
    
    def get_messages(self, user_id, limit=100):
        """Get messages for a user"""
        try:
            # Get messages
            response = self.supabase.table('messages')\
                .select('*')\
                .or_(f'message_type.eq.global,recipient_id.eq.{user_id},sender_id.eq.{user_id}')\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            messages = response.data if response.data else []
            
            # Get sender details
            for msg in messages:
                if msg.get('sender_id'):
                    sender = self.get_user_by_id(msg['sender_id'])
                    if sender:
                        msg['sender'] = sender
            
            return messages
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def get_message(self, message_id):
        """Get a single message"""
        try:
            response = self.supabase.table('messages')\
                .select('*')\
                .eq('id', message_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                message = response.data[0]
                if message.get('sender_id'):
                    sender = self.get_user_by_id(message['sender_id'])
                    if sender:
                        message['sender'] = sender
                return message
            return None
        except Exception as e:
            print(f"Error getting message: {e}")
            return None
    
    # ============ ACTIVITY LOGS ============
    def log_activity(self, user_id, action, details=None, ip=None, user_agent=None):
        """Log user activity"""
        try:
            activity = {
                'user_id': user_id,
                'action': action,
                'details': json.dumps(details) if details else None,
                'ip_address': ip,
                'user_agent': user_agent
            }
            
            response = self.supabase.table('activity_logs')\
                .insert(activity)\
                .execute()
            
            return bool(response.data)
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False
    
    # ============ USERS ============
    def get_all_users(self):
        """Get all users"""
        try:
            response = self.supabase.table('users')\
                .select('id, username, email, full_name, role, company, position, is_active')\
                .order('created_at')\
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
