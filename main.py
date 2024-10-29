from flask import Flask, redirect, url_for, render_template, jsonify, request, send_file, json, Response
import os
from main_logic import xlxsToDf, getOrders, editOrder, dfToXlxs
from Aglomerative.AglomerativeCluster import Solver

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

ORDER_ID = -1


@app.route("/")
def main():
    return render_template("home.html")


@app.route("/home.html")
def home():
    return redirect(url_for("main"))

@app.route("/order_load_page.html")
def load_order():
    global ORDER_ID
    ORDER_ID = 0
    return render_template("order_load_page.html")

FILE_FOLDER = './files'
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)

@app.route("/order_page.html")
def order():
    global ORDER_ID
    print(ORDER_ID)
    if ORDER_ID == -1:
        df_orders = getOrders().to_json(orient='records')
        return render_template("order_page.html", all_orders=df_orders)
    else:
        # dfdata = getOrders().to_json(orient='records')
        df_orders = getOrders().to_json(orient='records')
        return render_template("order_page.html", all_orders=df_orders)#, data=dfdata)

@app.route("/lots_page.html")
def lots():
    return render_template("lots_page.html")

FILE_FOLDER = './files'
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No file selected for uploading'}), 400

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(FILE_FOLDER, file.filename)
        file.save(filepath)
        success = xlxsToDf(filepath)
        if success:
            return jsonify({'message': f'File successfully uploaded: {file.filename}'}), 200
        else:
            return jsonify({'message': f'File does not match template'}), 400
    else:
        return jsonify({'message': 'Only .xlsx files are allowed'}), 400

@app.route('/api/update_df', methods=['POST'])
def update_df():
    data = request.get_json()
    editOrder(data)
    return jsonify({'status': 'success'}), 200

@app.route('/api/download', methods=['GET'])
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
        xlsxpath = dfToXlxs(csvpath)
        return send_file(xlsxpath, as_attachment=True, download_name="excel.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/submit-dates', methods=['POST'])
def submit_dates():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    print(f"Start Date: {start_date}, End Date: {end_date}")
    df = getOrders().to_json(orient='records')
    return jsonify({"message": df})

if __name__ == "__main__":
    app.run(debug=True)
