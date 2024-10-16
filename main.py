from flask import Flask, redirect, url_for, render_template, jsonify, request, send_file
import os
from xlsxToCsv import xlxsToDf
from Aglomerative.AglomerativeCluster import Solver

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
    csvpath = ""
    for file in os.listdir("./files"):
        if file.split('.')[-1] == "csv":
            csvpath = "./files/"+file
            break

    # здесь заказ проверяет Inspector
    # здесь заказ загружается в БД
    # здесь заказы за месяц выгружаются из БД
    lotter = Solver()
    lotter.get_lots(csvpath, csvpath)
    # здесь заказы за месяц отправляются в autolotting-ml а сформированные лоты попадают в файл по пути csvpath
    # здесь сформироанные лоты загружаются в БД а сами лоты отправляются пользователю
    # здесь Scorer считает целевые бизнес-метрики
    # здесь Analyzer анализирует результаты работы и выдает интересные статистики
    # здесь Canvas строит графики и настраивает dashboard'ы
    # здесь на сайт выводятся метрики, параметры, графики и пр.

    if os.path.exists(csvpath):
        print(csvpath)
        return send_file(csvpath, as_attachment=True, download_name="lots.csv", mimetype='text/csv')
    else:
        return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)
