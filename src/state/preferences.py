import os
import json
import logging
from src.utils.security import hash_user_id

class UserPreferences:
    """
    Manages user opt-in and opt-out preferences.
    """
    def __init__(self, opt_file="data/user_prefs.json"):
        """
        Initialize the user preferences manager.

        Args:
            opt_file (str): Path to the user preferences file.
        """
        self.opt_file = opt_file
        self.cached_optouts = set()
        self.cached_optins = set()
        self._ensure_file_exists()
        self._load_user_prefs()

    def _ensure_file_exists(self):
        """Ensure the preferences file exists with default values."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.opt_file), exist_ok=True)
        
        if not os.path.exists(self.opt_file):
            with open(self.opt_file, "w") as f:
                json.dump({"opt_out": [], "opt_in": []}, f)

    def _load_user_prefs(self):
        """Load user preferences into memory cache."""
        try:
            with open(self.opt_file) as f:
                prefs = json.load(f)
                # Validate that we have valid lists
                if not isinstance(prefs.get("opt_out", []), list):
                    prefs["opt_out"] = []
                if not isinstance(prefs.get("opt_in", []), list):
                    prefs["opt_in"] = []
                # Validate each entry is a string
                self.cached_optouts = set(str(uid) for uid in prefs.get("opt_out", []) if isinstance(uid, (str, int)))
                self.cached_optins = set(str(uid) for uid in prefs.get("opt_in", []) if isinstance(uid, (str, int)))
                logging.info(f"Loaded user preferences: {len(self.cached_optouts)} opt-outs, {len(self.cached_optins)} opt-ins")
        except Exception as e:
            logging.error(f"Failed to load user preferences: {e}")
            # Initialize with empty sets if loading fails
            self.cached_optouts = set()
            self.cached_optins = set()

    def update_user_prefs(self, user_id: str, action: str):
        """
        Handle opt-in/out with hashed IDs.

        Args:
            user_id (str): The user ID to update.
            action (str): The action to perform ("opt_in" or "opt_out").
        """
        hashed_id = hash_user_id(user_id)
        try:
            with open(self.opt_file, "r+") as f:
                prefs = json.load(f)
                if action == "opt_out" and hashed_id not in prefs["opt_out"]:
                    prefs["opt_out"].append(hashed_id)
                    if hashed_id in prefs["opt_in"]:
                        prefs["opt_in"].remove(hashed_id)
                elif action == "opt_in" and hashed_id not in prefs["opt_in"]:
                    prefs["opt_in"].append(hashed_id)
                    if hashed_id in prefs["opt_out"]:
                        prefs["opt_out"].remove(hashed_id)
                f.seek(0)
                json.dump(prefs, f, indent=2)
                f.truncate()
            # Update the cache
            if action == "opt_out":
                self.cached_optouts.add(hashed_id)
                self.cached_optins.discard(hashed_id)
            elif action == "opt_in":
                self.cached_optins.add(hashed_id)
                self.cached_optouts.discard(hashed_id)
            logging.info(f"User ...{user_id[-4:]} {action.replace('_', '-')}")
        except Exception as e:
            logging.error(f"Failed updating prefs: {e}")

    def is_opted_out(self, user_id: str) -> bool:
        """
        Check if a user is opted out.

        Args:
            user_id (str): The user ID to check.

        Returns:
            bool: True if the user is opted out, False otherwise.
        """
        return hash_user_id(user_id) in self.cached_optouts
