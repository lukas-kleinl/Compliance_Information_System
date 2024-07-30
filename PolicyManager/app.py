from enum import Enum

import gridfs
from bson import ObjectId
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, abort
from flask.cli import load_dotenv
import os
from pymongo import MongoClient
from werkzeug.utils import secure_filename

from company_controls.guidelines import Guideline
from company_controls.policies import Policy

app = Flask(__name__)
app.secret_key = 'password'

# Configuration
load_dotenv()
uri = os.getenv("MongoDB_URI")
client = MongoClient(uri)
db = client.company_controls
UPLOAD_FOLDER = 'uploads'
VERSION_FOLDER = os.path.join(UPLOAD_FOLDER, 'versions')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VERSION_FOLDER'] = VERSION_FOLDER


class Options(Enum):
    POLICY = "POLICY"
    GUIDELINE = "GUIDELINE"


guidelines = {}
policies = {}

for policy in db.policy.find():
    object_id = policy.pop('_id')
    policies[str(object_id)] = policy

for guideline in db.guideline.find():
    object_id = guideline.pop('_id')
    guidelines[str(object_id)] = guideline

@app.before_request
def limit_remote_addr():
    if request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden


@app.route('/')
def index():
    return render_template('index.html', guidelines=guidelines, policies=policies)


@app.route('/document', methods=['GET', 'POST'])
def new_document():
    """Create a new Document and store it in MongoDB"""
    if request.method == 'POST':
        selected_option = request.form['option']
        if selected_option == Options.GUIDELINE.value:
            title = request.form['title']
            description = request.form['description']
            file1 = request.files['file']
            if file1.filename == '':
                flash('Please provide a file', 'error')
                return redirect(url_for('new_document'))
            new_guideline = Guideline(title, description, db, file1)
            mongo_data = new_guideline.save()
            guidelines[str(mongo_data.inserted_id)] = new_guideline.get_dict()
            if mongo_data.acknowledged is True:
                flash('Saving was successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Saving was not successful!', 'error')
                return redirect(url_for('index'))
        elif selected_option == Options.POLICY.value:
            title = request.form['title']
            description = request.form['description']
            file1 = request.files['file']
            if file1.filename == '':
                return redirect(url_for('index'))
            new_policy = Policy(title, description, db, file1)
            mongo_data, policy_data = new_policy.save()
            policies[str(mongo_data.inserted_id)] = policy_data
            if mongo_data.acknowledged is True:
                flash('Saving was successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Saving was not successful!', 'error')
                return redirect(url_for('index'))
    return render_template('new_document.html', Options=Options, guidelines=guidelines,
                           policies=policies)


@app.route('/document/<doc_id>')
def view_document(doc_id):
    """view for a given company control"""
    guideline_data = guidelines.get(doc_id)
    policy_data = policies.get(doc_id)

    if not guideline_data and not policy_data:
        return "Document not found", 404

    if guideline_data is not None:
        files = {'file': str(guideline_data["file"]["file"]), 'name': guideline_data["file"]["name"],
                 'last_updated': guideline_data["file"]["timestamp"], 'version': guideline_data["file"]["version"],
                 'old_files': guideline_data["file"]["old_files"]}
    else:
        files = {'file': str(policy_data["file"]["file"]), 'name': policy_data["file"]["name"],
                 'last_updated': policy_data["file"]["timestamp"], 'version': policy_data["file"]["version"],
                 'old_files': policy_data["file"]["old_files"]}

    return render_template('view_document.html', doc_id=doc_id, guidelines=guidelines, policies=policies, files=files,
                           guideline_data=guideline_data, policy_data=policy_data)


@app.route('/document/edit/<doc_id>', methods=['GET', 'POST'])
def edit_document(doc_id):
    """Edit the data from a given company control / policy, guideline..."""
    guideline_data = guidelines.get(doc_id)
    policy_data = policies.get(doc_id)
    if not guideline_data and not policy_data:
        return "Document not found", 404

    if request.method == 'POST':
        if policy_data is not None:
            file1 = request.files['file']
            collection = db["policy"]
            if file1.filename != '':
                fs = gridfs.GridFS(db)
                filename = secure_filename(file1.filename)
                file_id = fs.put(file1, filename=filename, content_type=file1.content_type)
                result = collection.update_one(
                    {'_id': ObjectId(doc_id)},
                    {
                        '$push': {'file.old_files': str(policies[doc_id]['file']['file'])},
                        '$inc': {'file.version': 1},
                        '$set': {'title': request.form['title'], 'description': request.form['description'],
                                 'file.name': filename, 'file.file': file_id}
                    },
                )
            else:
                result = collection.update_one(
                    {'_id': ObjectId(doc_id)},
                    {
                        '$set': {'title': request.form['title'], 'description': request.form['description']}
                    },
                )

            updated_policy = collection.find_one({'_id': ObjectId(doc_id)})
            object_id = updated_policy.pop('_id')
            policies[str(object_id)] = updated_policy
            if result.acknowledged is True:
                flash('Update was successful!', 'success')
                return redirect(url_for('view_document', doc_id=doc_id, guidelines=guidelines, policies=policies,
                                        guideline_data=guideline_data, policy_data=policy_data))
            else:
                flash('Update was not successful!', 'error')
                return redirect(url_for('view_document', doc_id=doc_id, guidelines=guidelines, policies=policies,
                                        guideline_data=guideline_data, policy_data=policy_data))
        else:
            guidelines[doc_id]['title'] = request.form['title']
            guidelines[doc_id]['description'] = request.form['description']
            file1 = request.files['file']
            collection = db["guideline"]
            if file1.filename != '':
                fs = gridfs.GridFS(db)
                filename = secure_filename(file1.filename)
                file_id = fs.put(file1, filename=filename, content_type=file1.content_type)
                result = collection.update_one(
                    {'_id': ObjectId(doc_id)},
                    {
                        '$push': {'file.old_files': str(guidelines[doc_id]['file']['file'])},
                        '$inc': {'file.version': 1},
                        '$set': {'title': request.form['title'], 'description': request.form['description'],
                                 'file.name': filename, 'file.file': file_id}
                    },
                )
            else:
                result = collection.update_one(
                    {'_id': ObjectId(doc_id)},
                    {
                        '$set': {'title': request.form['title'], 'description': request.form['description']}
                    },
                )
            updated_guideline = collection.find_one({'_id': ObjectId(doc_id)})
            object_id = updated_guideline.pop('_id')
            guidelines[str(object_id)] = updated_guideline
            if result.acknowledged is True:
                return redirect(url_for('view_document', doc_id=doc_id, guidelines=guidelines, policies=policies,
                                        guideline_data=guideline_data, policy_data=policy_data))
            else:
                return redirect(url_for('view_document', doc_id=doc_id, guidelines=guidelines, policies=policies,
                                        guideline_data=guideline_data, policy_data=policy_data))

    return render_template('edit_document.html', doc_id=doc_id, guidelines=guidelines, policies=policies,
                           guideline_data=guideline_data, policy_data=policy_data)


@app.route('/file/<file_id>')
def file(file_id):
    """returns the PDF file for the given file"""
    fs = gridfs.GridFS(db)
    file_data = fs.get(ObjectId(file_id))
    return send_file(BytesIO(file_data.read()), mimetype='application/pdf')


@app.route('/document/delete/<doc_id>', methods=['POST'])
def delete_document(doc_id):
    """Delete Document with given ID"""
    guideline_data = guidelines.get(doc_id)
    policy_data = policies.get(doc_id)
    if not guideline_data and not policy_data:
        return "Document not found", 404

    if policy_data is None:
        collection = db["guideline"]
        result = collection.delete_one({'_id': ObjectId(doc_id)})
        del guidelines[doc_id]
        if result.acknowledged is True:
            flash('Successfully deleted!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Could not delete the file!', 'error')
            return redirect(url_for('index'))
    else:
        collection = db["policy"]
        result = collection.delete_one({'_id': ObjectId(doc_id)})
        del policies[doc_id]
        if result.acknowledged is True:
            return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
