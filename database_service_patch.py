#!/usr/bin/env python3
"""
Patch for database service to add missing increment_user_interaction method
"""

def add_increment_method_to_database_service():
    """Add the missing method to database_service.py"""
    
    method_code = '''
    def increment_user_interaction(self, user_id: str):
        """Increment user interaction count for familiarity scoring"""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.interaction_count = (user.interaction_count or 0) + 1
                user.last_seen = datetime.utcnow()
                # Update familiarity score based on interactions
                if user.interaction_count <= 10:
                    user.familiarity_score = min(30, user.interaction_count * 3)
                elif user.interaction_count <= 30:
                    user.familiarity_score = min(60, 30 + (user.interaction_count - 10) * 1.5)
                else:
                    user.familiarity_score = min(100, 60 + (user.interaction_count - 30) * 0.8)
                session.commit()
        finally:
            session.close()
'''
    
    # Append to database_service.py
    with open('/data/jj/proj/hoorii/database_service.py', 'a') as f:
        f.write(method_code)
    
    print("✅ Added increment_user_interaction method to DatabaseService")

if __name__ == "__main__":
    add_increment_method_to_database_service()