from flask import Flask, redirect, url_for, render_template, jsonify, request, send_file, json, Response
import os
from main_logic import xlxsToDf, getOrders, editOrder, dfToXlxs, getRequests
from Aglomerative.AglomerativeCluster import Solver

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

FILE_FOLDER = './files'
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)

@app.route("/")
def main():
    return render_template("home.html")

@app.route("/home.html")
def home():
    return redirect(url_for("main"))

@app.route("/order_load_page.html")
def load_order():
    df_orders = getOrders().to_json(orient='records')
    return render_template("order_load_page.html", all_orders=df_orders)

@app.route("/order_page.html")
def orders():
    id = request.args.getlist('id')
    df_orders = getOrders().to_json(orient='records')
    if(id != []):
        id = list(map(int, id[0].split(',')))
        dfdata = getRequests(id).to_json(orient='records')
        return render_template("order_page.html", all_orders=df_orders, data=dfdata)
    else:
        return render_template("order_page.html", all_orders=df_orders)

@app.route("/lots_page.html")
def lots():
    return render_template("lots_page.html")

@app.route("/lots_create_page.html")
def lots_create():
    return render_template("lots_create_page.html")

FILE_FOLDER = './files'
if not os.path.exists(FILE_FOLDER):
    os.makedirs(FILE_FOLDER)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'Ошибка в выборе файла.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'Не выбран файл.'}), 400

    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(FILE_FOLDER, file.filename)
        file.save(filepath)
        success, response = xlxsToDf(filepath)
        if success:
            return jsonify({'message': f'Файл загружен: {file.filename}.', 'ids':response.to_list()}), 200
        else:
            return jsonify({'message': f'Ошибка в содержании файла: {response}'}), 400
    else:
        return jsonify({'message': 'Только .xlsx файлы должны быть загружены.'}), 400

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
    df = getOrders(start_date, end_date).to_json(orient='records')
    return jsonify(df)

@app.route('/api/fetch-dates', methods=['POST'])
def fetch_dates():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    df = getOrders(start_date, end_date)
    return jsonify({'numberOrders': len(df['№ заказа'].unique()), 'numberPositions': len(df)})

if __name__ == "__main__":
    app.run(debug=True)
