from datetime import datetime

import gridfs
from werkzeug.utils import secure_filename


class Docs:
    """Class for creating saving and storing documents"""
    def __init__(self, file, db):
        self.version = 0
        self.current_version = file
        self.files = []
        self.db = db
        self.fs = gridfs.GridFS(self.db)
        self.filename = secure_filename(self.current_version.filename)
        self.file_id = self.fs.put(self.current_version, filename=self.filename,
                              content_type=self.current_version.content_type)

    def add_file(self, file_name, file):
        self.files.append({'filename': file_name, 'file': file})

    def to_dict(self):
        return {
            'name': self.filename,
            'file': self.file_id,
            'version': self.version,
            'old_files': self.files,
            'timestamp': datetime.now()
        }
