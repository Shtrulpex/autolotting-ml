from flask import Flask, redirect, url_for, render_template, jsonify, request, send_file
import os
from xlsxToCsv import xlxsToDf

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

FILE_FOLDER = './files'
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(FILE_FOLDER, file.filename)
        file.save(filepath)
        xlxsToDf(filepath)

        return jsonify({'message': f'File successfully uploaded: {file.filename}'}), 200
    else:
        return jsonify({'message': 'Only .xlsx files are allowed'}), 400

@app.route('/download', methods=['GET'])
def download_file():
    filepath = os.path.join(FILE_FOLDER, 'enter.xlsx')
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name='enter.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)