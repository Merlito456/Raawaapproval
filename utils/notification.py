from datetime import datetime
import json

class NotificationManager:
    def __init__(self, db):
        self.db = db
    
    def notify_approvers(self, raawa_id, status):
        """Notify approvers about RAAWA status change"""
        raawa = self.db.get_raawa_by_id(raawa_id)
        if not raawa:
            return
        
        if status == 'fm_pending':
            # Notify Facility Manager
            if raawa.get('facility_manager'):
                fm_user = self.db.get_user_by_id(raawa['facility_manager']['user_id'])
                if fm_user:
                    self.db.create_notification(
                        fm_user['id'],
                        f"RAAWA {raawa['raawa_no']} Ready for Approval",
                        f"Please review and sign RAAWA {raawa['raawa_no']} from {raawa['requisitioner_name']}",
                        'approval',
                        f"/raawa/{raawa_id}"
                    )
        
        elif status == 'security_pending':
            # Notify Security
            if raawa.get('security'):
                sec_user = self.db.get_user_by_id(raawa['security']['user_id'])
                if sec_user:
                    self.db.create_notification(
                        sec_user['id'],
                        f"RAAWA {raawa['raawa_no']} Ready for Security Approval",
                        f"Please review and sign RAAWA {raawa['raawa_no']} from {raawa['requisitioner_name']}",
                        'approval',
                        f"/raawa/{raawa_id}"
                    )
    
    def notify_approval(self, raawa_id, approval_type):
        """Notify requester and next approver about approval"""
        raawa = self.db.get_raawa_by_id(raawa_id)
        if not raawa:
            return
        
        # Notify requester
        if raawa.get('created_by'):
            self.db.create_notification(
                raawa['created_by'],
                f"RAAWA {raawa['raawa_no']} {approval_type.replace('_', ' ').title()} Approved",
                f"The {approval_type} has approved your RAAWA {raawa['raawa_no']}",
                'success',
                f"/raawa/{raawa_id}"
            )
        
        # If fully approved, notify both approvers
        if raawa.get('status') == 'approved':
            # Notify Facility Manager
            if raawa.get('facility_manager'):
                fm_user = self.db.get_user_by_id(raawa['facility_manager']['user_id'])
                if fm_user:
                    self.db.create_notification(
                        fm_user['id'],
                        f"RAAWA {raawa['raawa_no']} Fully Approved",
                        f"RAAWA {raawa['raawa_no']} has been fully approved",
                        'success',
                        f"/raawa/{raawa_id}"
                    )
            
            # Notify Security
            if raawa.get('security'):
                sec_user = self.db.get_user_by_id(raawa['security']['user_id'])
                if sec_user:
                    self.db.create_notification(
                        sec_user['id'],
                        f"RAAWA {raawa['raawa_no']} Fully Approved",
                        f"RAAWA {raawa['raawa_no']} has been fully approved",
                        'success',
                        f"/raawa/{raawa_id}"
                    )
    
    def notify_expired(self, raawa_id):
        """Notify that RAAWA has expired"""
        raawa = self.db.get_raawa_by_id(raawa_id)
        if not raawa:
            return
        
        # Notify requester
        if raawa.get('created_by'):
            self.db.create_notification(
                raawa['created_by'],
                f"RAAWA {raawa['raawa_no']} Expired",
                f"RAAWA {raawa['raawa_no']} has expired and needs to be regenerated",
                'danger',
                f"/raawa/{raawa_id}"
            )
        
        # Notify Facility Manager
        if raawa.get('facility_manager'):
            fm_user = self.db.get_user_by_id(raawa['facility_manager']['user_id'])
            if fm_user:
                self.db.create_notification(
                    fm_user['id'],
                    f"RAAWA {raawa['raawa_no']} Expired",
                    f"RAAWA {raawa['raawa_no']} has expired",
                    'danger',
                    f"/raawa/{raawa_id}"
                )
        
        # Notify Security
        if raawa.get('security'):
            sec_user = self.db.get_user_by_id(raawa['security']['user_id'])
            if sec_user:
                self.db.create_notification(
                    sec_user['id'],
                    f"RAAWA {raawa['raawa_no']} Expired",
                    f"RAAWA {raawa['raawa_no']} has expired",
                    'danger',
                    f"/raawa/{raawa_id}"
                )
