from bson import ObjectId

from company_controls.company_controls import CompanyControls
from company_controls.documents import Docs


class Policy(CompanyControls):
    """Policy class which is defined through abstract class Company Controls"""
    def __init__(self, name, description, db, file):
        super().__init__(name, description)
        self.db = db
        self.file = Docs(file, self.db)

    def save(self):
        policy_collection = self.db.policy
        policy_document = {
            'title': self.name,
            'description': self.description,
            'file': self.file.to_dict()
        }
        mongo_data = policy_collection.insert_one(policy_document)
        return mongo_data, policy_document

    def load(self, name):
        policy_collection = self.db.policy
        return policy_collection.find_one({'name': name})

    def update(self, mongo_id, values_to_update):
        policy_collection = self.db.policy
        result = policy_collection.updateOne(
            {'_id': ObjectId(mongo_id)},
            {'$set': values_to_update}
        )
        print(result)

    def get_dict(self):
        return {"title": self.name, "description": self.description, "file": self.file.to_dict(),
                "last_updated": self.last_updated}
