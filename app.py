import os
import random
import string
from flask import Flask, render_template_string, request, redirect, url_for, Response, abort
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Helper function to generate random token (15-20 characters)
def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(15, 20)))

# HTML Templates as strings
CREATE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create File</title>
    <style>
        body {
            font-family: "Tahoma", sans-serif;
            background-color: #C0C0C0;
            color: #000000;
            margin: 0;
            padding: 0;
        }
        h1 {
            background-color: #000080;
            color: white;
            text-align: center;
            padding: 10px 0;
        }
        label {
            display: block;
            margin: 10px 0 5px;
        }
        input, textarea {
            width: 300px;
            padding: 5px;
        }
        .button {
            background-color: #000080;
            color: white;
            padding: 5px 10px;
            border: none;
            cursor: pointer;
        }
        .button:hover {
            background-color: #0000FF;
        }
    </style>
</head>
<body>
    <h1>Create a New File</h1>
    <form method="POST">
        <label for="filename">File Name:</label>
        <input type="text" id="filename" name="filename" required><br>

        <label for="extension">File Extension:</label>
        <input type="text" id="extension" name="extension" required><br><br>

        <label for="code">File Code:</label><br>
        <textarea id="code" name="code" rows="10" required></textarea><br><br>

        <button type="submit" class="button">Create</button>
    </form>
    <br>
    <a href="{{ url_for('index') }}" class="button">Cancel</a>
</body>
</html>
"""

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Storage</title>
    <style>
        body {
            font-family: "Tahoma", sans-serif;
            background-color: #C0C0C0;
            color: #000000;
            margin: 0;
            padding: 0;
        }
        h1 {
            background-color: #000080;
            color: white;
            text-align: center;
            padding: 10px 0;
        }
        a {
            color: #000080;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            background-color: #E0E0E0;
            margin: 5px 0;
            padding: 5px;
            border: 1px solid #A0A0A0;
        }
        .button {
            background-color: #000080;
            color: white;
            padding: 5px 10px;
            border: none;
            cursor: pointer;
        }
        .button:hover {
            background-color: #0000FF;
        }
    </style>
</head>
<body>
    <h1>Created Files</h1>
    <ul>
        {% for file in files %}
            <li>
                <a href="{{ url_for('serve_file', token=file.token, filename=file.filename) }}">{{ file.filename }}</a> 
                <a href="{{ url_for('edit', token=file.token) }}" class="button">Edit</a>
                <a href="{{ url_for('delete', token=file.token) }}" class="button">Delete</a>
            </li>
        {% endfor %}
    </ul>
    <br>
    <a href="{{ url_for('create') }}" class="button">Create New File</a>
    <br>
    <a href="{{ url_for('search') }}" class="button">Search by Token</a>
</body>
</html>
"""

EDIT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit File</title>
    <style>
        body {
            font-family: "Tahoma", sans-serif;
            background-color: #C0C0C0;
            color: #000000;
            margin: 0;
            padding: 0;
        }
        h1 {
            background-color: #000080;
            color: white;
            text-align: center;
            padding: 10px 0;
        }
        label {
            display: block;
            margin: 10px 0 5px;
        }
        textarea, input {
            width: 300px;
            padding: 5px;
        }
        .button {
            background-color: #000080;
            color: white;
            padding: 5px 10px;
            border: none;
            cursor: pointer;
        }
        .button:hover {
            background-color: #0000FF;
        }
    </style>
</head>
<body>
    <h1>Edit File: {{ file['name'] }}</h1>
    <form method="POST">
        <label for="filename">File Name:</label>
        <input type="text" id="filename" name="filename" value="{{ file['name'] }}" disabled><br>

        <label for="extension">File Extension:</label>
        <input type="text" id="extension" name="extension" value="{{ file['extension'] }}" required><br><br>

        <label for="code">File Code:</label><br>
        <textarea id="code" name="code" rows="10" required>{{ file['code'] }}</textarea><br><br>

        <button type="submit" class="button">Save</button>
        <a href="{{ url_for('index') }}" class="button">Cancel</a>
    </form>
</body>
</html>
"""

SEARCH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search File by Token</title>
    <style>
        body {
            font-family: "MS Sans Serif", sans-serif;
            background-color: #C0C0C0;
            color: #000080;
            margin: 0;
            padding: 20px;
        }
        h1 {
            font-size: 24px;
            color: #000080;
        }
        form {
            background-color: #E0E0E0;
            padding: 10px;
            border: 2px solid #000080;
            width: 300px;
        }
        label {
            font-size: 14px;
            display: block;
            margin-top: 5px;
        }
        input, button {
            font-family: "MS Sans Serif", sans-serif;
            font-size: 12px;
            margin-top: 5px;
            padding: 5px;
            width: 100%;
        }
        button {
            background-color: #000080;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #0000A0;
        }
        a {
            color: #000080;
            text-decoration: none;
            font-size: 12px;
            margin-top: 20px;
            display: inline-block;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>Search File by Token</h1>
    <form method="POST">
        <label for="token">Enter Token:</label>
        <input type="text" id="token" name="token" required><br>
        <button type="submit">Search</button>
    </form>
    <br>
    <a href="{{ url_for('index') }}">Back to Home</a>
</body>
</html>
"""

# Home route (List all files created by the user based on IP)
@app.route("/")
def index():
    user_ip = request.remote_addr  # Get user IP
    files_ref = db.collection("files").where("user_ip", "==", user_ip)
    files = files_ref.stream()

    files_list = []
    for file in files:
        file_data = file.to_dict()
        files_list.append({
            "token": file.id,
            "filename": file_data["name"],
            "extension": file_data["extension"]
        })

    return render_template_string(INDEX_HTML, files=files_list)

# Search route (Search file by token)
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        token = request.form["token"]
        file_ref = db.collection("files").document(token)
        file = file_ref.get()

        if file.exists:
            file_data = file.to_dict()
            return render_template_string(EDIT_HTML, file=file_data)
        else:
            return "File not found", 404

    return render_template_string(SEARCH_HTML)

# Create route (Create new file)
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        filename = request.form["filename"]
        extension = request.form["extension"]
        code = request.form["code"]
        user_ip = request.remote_addr
        token = generate_token()

        db.collection("files").document(token).set({
            "name": filename,
            "extension": extension,
            "code": code,
            "user_ip": user_ip
        })

        return redirect(url_for('index'))

    return render_template_string(CREATE_HTML)

# Edit route (Edit file)
@app.route("/edit/<token>", methods=["GET", "POST"])
def edit(token):
    file_ref = db.collection("files").document(token)
    file = file_ref.get()

    if not file.exists:
        abort(404)

    file_data = file.to_dict()

    if request.method == "POST":
        filename = request.form["filename"]
        extension = request.form["extension"]
        code = request.form["code"]

        file_ref.update({
            "name": filename,
            "extension": extension,
            "code": code
        })

        return redirect(url_for('index'))

    return render_template_string(EDIT_HTML, file=file_data)

# Delete route (Delete file)
@app.route("/delete/<token>", methods=["GET", "POST"])
def delete(token):
    file_ref = db.collection("files").document(token)
    file_ref.delete()

    return redirect(url_for('index'))

# Serve file route (View file content)
@app.route("/file/<token>/<filename>")
def serve_file(token, filename):
    file_ref = db.collection("files").document(token)
    file = file_ref.get()

    if not file.exists:
        abort(404)

    file_data = file.to_dict()
    return Response(file_data["code"], content_type="text/plain")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
