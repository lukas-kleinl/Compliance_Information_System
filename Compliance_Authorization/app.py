"""Python Flask WebApp Auth0 integration example
"""
from enum import Enum
from urllib.parse import quote_plus, urlencode
import requests
from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template, session, url_for, request, abort
from dotenv import load_dotenv
import os

load_dotenv()
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

URL_Recommender = os.getenv("URL_Recommender")
URL_Company_Control_Store = os.getenv("URL_Company_Control_Store")
URL_Chat = os.getenv("URL_Chat")

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration',
)


class Options(Enum):
    """Class for the company controls options"""
    POLICY = "POLICY"
    GUIDELINE = "GUIDELINE"


def check_role(role):
    """Function to check if a user has a specific role"""
    access_token = session['user']['access_token']
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    user_info_url = f"https://{AUTH0_DOMAIN}/userinfo"
    response = requests.get(user_info_url, headers=headers)
    user_info = response.json()
    roles = user_info.get('/roles', 'No roles found')
    if role in roles:
        return True
    return False


# Controllers API
@app.route("/")
def home():
    return render_template(
        "home.html",
        session=session.get("user"),
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + AUTH0_DOMAIN
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        )
    )


@app.route("/graph_home")
def graph_home():
    if 'user' not in session:
        return redirect(url_for('login'))

    r = requests.get(URL_Recommender)
    return r.text


@app.route("/graph")
def graph():
    """Route to the graph endpoint of the GDPR exploration"""
    if 'user' not in session:
        return redirect(url_for('login'))
    query_string = request.query_string.decode()
    new_url = f'{URL_Recommender}graph'
    if query_string:
        new_url += f'?{query_string}'

    r = requests.get(new_url)
    return r.text


@app.route("/node_relationships")
def node_relationships():
    """Route to the node relationship endpoint of the GDPR exploration"""
    if 'user' not in session:
        return redirect(url_for('login'))
    query_string = request.query_string.decode()
    new_url = f'{URL_Recommender}+node_relationships'
    if query_string:
        new_url += '?' + query_string
    r = requests.get(new_url)
    return r.text


@app.route("/query")
def query():
    """Get the response from the LLM based on the MongoDB Atlas Search """
    if 'user' not in session:
        return redirect(url_for('login'))
    query_string = request.query_string.decode()
    new_url = 'http://127.0.0.1:2003/query'
    if query_string:
        new_url += '?' + query_string
    r = requests.get(new_url)
    result = r.json()
    return render_template(
        "home.html",
        session=session.get("user"),
        result=result["result"],
        query=result["query"],
        search=1,
        chat=0,
        Options=Options
    )


@app.route("/chat")
def chat():
    """Get the response from the LLM based on the generative AI with Ollama"""
    if 'user' not in session:
        return redirect(url_for('login'))
    query_string = request.query_string.decode()
    new_url = 'http://127.0.0.1:2003/chat'
    if query_string:
        new_url += '?' + query_string
    r = requests.get(new_url)
    result = r.json()
    return render_template(
        "home.html",
        session=session.get("user"),
        result=result["result"],
        query=result["query"],
        search=0,
        chat=1,
        Options=Options
    )


@app.route("/search_bool")
def search_bool():
    """Route to determine which LLM function is required"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template(
        "home.html",
        session=session.get("user"),
        search=1,
        chat=0,
        Options=Options
    )


@app.route("/chat_bool")
def chat_bool():
    """Route to determine which LLM function is required"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template(
        "home.html",
        session=session.get("user"),
        search=0,
        chat=1,
        Options=Options
    )


@app.route("/company_controls")
def company_controls():
    """Route for handling the company controls creating, editing and deleting """
    if 'user' not in session:
        return redirect(url_for('login'))
    r = requests.get(URL_Company_Control_Store)
    return r.text


@app.route("/document", methods=['GET', 'POST'])
def new_document():
    """Route for creation of new company control"""
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        new_url = 'http://127.0.0.1:2002/document'
        files = request.files
        parameter = request.form
        r = requests.post(new_url, data=parameter, files=files)
        return r.text
    else:
        new_url = 'http://127.0.0.1:2002/document'
        r = requests.get(new_url)
        return r.text


@app.route('/document/<doc_id>')
def view_document(doc_id):
    """Route for viewing the given company control"""
    if 'user' not in session:
        return redirect(url_for('login'))
    new_url = f'http://127.0.0.1:2002/document/{doc_id}'
    r = requests.get(new_url)
    return r.text


@app.route('/document/edit/<doc_id>', methods=['GET', 'POST'])
def edit_document(doc_id):
    """Route for editing the given company control"""
    if 'user' not in session:
        return redirect(url_for('login'))

    if check_role("Data Protection Officer"):
        new_url = f'http://127.0.0.1:2002/document/edit/{doc_id}'
        if request.method == 'POST':
            files = request.files
            parameter = request.form
            r = requests.post(new_url, data=parameter, files=files)
            return r.text
        else:
            query_string = request.query_string.decode()
            if query_string:
                new_url += '?' + query_string
            r = requests.get(new_url)
            return r.text
    else:
        abort(403)  # Forbidden


@app.route('/file/<file_id>')
def file(file_id):
    """Route for loading the PDF of the given company control"""
    if 'user' not in session:
        return redirect(url_for('login'))
    new_url = f'http://127.0.0.1:2002/file/{file_id}'
    query_string = request.query_string.decode()
    if query_string:
        new_url += '?' + query_string
    return redirect(new_url)


@app.route('/document/delete/<doc_id>', methods=['POST'])
def delete_document(doc_id):
    """Route for deletion of the given company control"""
    if 'user' not in session:
        return redirect(url_for('login'))
    if check_role("Data Protection Officer"):
        new_url = f'http://127.0.0.1:2002/document/delete/{doc_id}'
        r = requests.post(new_url)
        return r.text
    else:
        abort(403)


if __name__ == "__main__":
    app.run()
