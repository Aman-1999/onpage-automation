import json
import os
from datetime import datetime

DATA_FILE = "clients_data.json"

class DataManager:
    def __init__(self):
        self.file_path = DATA_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            self.save_data({}) # Initialize with empty dict

    def load_data(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_data(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def add_client(self, client_name):
        data = self.load_data()
        if client_name not in data:
            data[client_name] = []
            self.save_data(data)
            return True
        return False

    def add_url(self, client_name, url_data):
        """
        url_data structure:
        {
            "url": "https://...",
            "primary_keyword": "keyword",
            "secondary_keywords": ["k1", "k2"],
            "status": "Pending",
            "priority": "Medium",
            "last_audit": "Never",
            "notes": ""
        }
        """
        data = self.load_data()
        if client_name in data:
            # Check for duplicate URL
            if any(item['url'] == url_data['url'] for item in data[client_name]):
                return False
            data[client_name].append(url_data)
            self.save_data(data)
            return True
        return False
    
    def update_url_status(self, client_name, url_index, field, value):
        data = self.load_data()
        if client_name in data and 0 <= url_index < len(data[client_name]):
            data[client_name][url_index][field] = value
            self.save_data(data)
            return True
        return False

    def remove_client(self, client_name):
        data = self.load_data()
        if client_name in data:
            del data[client_name]
            self.save_data(data)
            return True
        return False

    def remove_url(self, client_name, url_index):
        data = self.load_data()
        if client_name in data and 0 <= url_index < len(data[client_name]):
            data[client_name].pop(url_index)
            self.save_data(data)
            return True
        return False
