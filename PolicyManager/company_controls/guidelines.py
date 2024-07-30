from abc import ABC

from company_controls.company_controls import CompanyControls
from company_controls.documents import Docs


class Guideline(CompanyControls):
    """Guideline class which is defined through abstract class Company Controls"""
    def __init__(self, name, description, db, file):
        super().__init__(name, description)
        self.db = db
        self.file = Docs(file, self.db)

    def save(self):
        guideline_collection = self.db.guideline
        guideline_document = {
            'title': self.name,
            'description': self.description,
            'file': self.file.to_dict()
        }
        mongo_data = guideline_collection.insert_one(guideline_document)
        return mongo_data


    def load(self, name):
        guideline_collection = self.db.guideline
        return guideline_collection.find_one({'name': name})

    def get_dict(self):
        return {"title": self.name, "description": self.description, "file": self.file.to_dict(), "last_updated" : self.last_updated}