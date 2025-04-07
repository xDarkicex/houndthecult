# This file makes the state directory a Python package

from .persistence import StateManager
from .preferences import UserPreferences
from .usage import UsageTracker

# Main state class that combines all state functionality
class BotState:
    def __init__(self):
        self.state_manager = StateManager()
        self.preferences = UserPreferences()
        self.usage = UsageTracker()
        
        # Initialize from saved state
        self.state_manager.load_state(self)
    
    # Delegate methods to appropriate components
    def load_state(self):
        self.state_manager.load_state(self)
    
    def save_state(self):
        self.state_manager.save_state(self)
    
    def update_user_prefs(self, user_id, action):
        self.preferences.update_user_prefs(user_id, action)
    
    def is_opted_out(self, user_id):
        return self.preferences.is_opted_out(user_id)
    
    def increment_read(self):
        self.usage.increment_read()
        self.save_state()
    
    def increment_post(self):
        self.usage.increment_post()
        self.save_state()
    
    def update_check_time(self):
        self.usage.update_check_time()
        self.save_state()
    
    def check_reset(self):
        self.usage.check_reset()

# Expose primary classes at the package level
__all__ = [
    'BotState',
    'StateManager',
    'UserPreferences',
    'UsageTracker'
]
