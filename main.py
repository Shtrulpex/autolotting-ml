from flask import Flask, redirect, url_for, render_template, jsonify, request
import os

app = Flask(__name__)

@app.route("/")
def main():
    return render_template("home.html")

@app.route("/home.html")
def home():
    return redirect(url_for("main"))

@app.route("/orders_page.html")
def orders():
    return render_template("orders_page.html")

@app.route("/lots_page.html")
def lots():
    return render_template("lots_page.html")

@app.route("/print-hello", methods=['POST'])
def print_hello():
    print("Hello")
    return jsonify({"message": "HELLO printed in terminal"}), 200

UPLOAD_FOLDER = './files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)  # Save the file on the server

        return jsonify({'message': f'File successfully uploaded: {file.filename}'}), 200
    else:
        return jsonify({'message': 'Only .xlsx files are allowed'}), 400

if __name__ == "__main__":
    app.run(debug=True)