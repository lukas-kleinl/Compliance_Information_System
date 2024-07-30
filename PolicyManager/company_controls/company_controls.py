from abc import ABC
from datetime import datetime

class CompanyControls(ABC):
    """Abstract class which defines basic information and methods for the underlying company controls / policies, guidelines"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.last_updated = datetime.now()

    def save(self):
        pass

    def load(self, name):
        pass

    def update(self, mongo_id, values_to_update):
        pass

    def get_dict(self):
        pass
