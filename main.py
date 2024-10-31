from flask import Flask, redirect, url_for, render_template, jsonify, request, send_file, json, Response
import os
from main_logic import xlxsToDf, getOrders, editOrder, dfToXlxs, getRequests, putPack, getPacks, editLot
from Aglomerative.AglomerativeCluster import Solver
import pandas as pd

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
    id = request.args.getlist('id')
    if(id != []):
        dfdata = getPacks(id[0]).to_json(orient='records')
        lot_id = request.args.getlist('lot_id')
        if(lot_id != []):
            lot_id = list(map(int, lot_id[0].split(',')))
            for i in range(len(lot_id)):
                lot_id[i] = lot_id[i] - 1
            return render_template("lots_page.html", data=dfdata, id=int(id[0]), lot_id=lot_id)
        else:
            return render_template("lots_page.html", data=dfdata, id=int(id[0]))
    else:
        return render_template("lots_page.html")

@app.route("/lots_create_page.html")
def lots_create():
    return render_template("lots_create_page.html")

@app.route("/packs_page.html")
def packs_page():
    id = request.args.getlist('id')
    df_packs = getPacks().to_json(orient='records')
    if(id != []):
        id = list(map(int, id[0].split(',')))
        dfdata = getPacks(id[0], True).to_json(orient='records')
        return render_template("packs_page.html", all_packs=df_packs, data=dfdata, id=id[0])
    else:
        return render_template("packs_page.html", all_packs=df_packs)

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

@app.route('/api/update_order', methods=['POST'])
def update_order():
    data = request.get_json()
    editOrder(data)
    return jsonify({'status': 'success'}), 200

@app.route('/api/update_lot', methods=['POST'])
def update_lot():
    data = request.get_json()
    editLot(data)
    return jsonify({'status': 'success'}), 200

@app.route('/api/upload_lots', methods=['POST'])
def upload_lots():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    name = data.get('name')

    df = pd.read_csv('./files/cold_lots.csv') #Времянка
    # df = getOrders(start_date, end_date)
    # lotter = Solver() #ПОКА НЕ РАБОТАЕТ ФОРМИРОВАНИЕ ЛОТОВ
    # result_df = lotter.get_lots(df)
    # print(result_df)
    pack_id = putPack(name, "none_algorythm_yet", df, start_date, end_date)
    return jsonify({'id': pack_id}), 200

@app.route('/api/download', methods=['POST', 'GET'])
def download_file():
    data = request.get_json()
    id = int(data['id'])
    dfdata = getPacks(id)
    lot_id = data['lot_id']
    if lot_id != '' and ',' not in lot_id:
        lot_id = int(lot_id[1:-1])+1
        xlsxpath = dfToXlxs(dfdata[dfdata['№ лоттировки'] == lot_id], f"Lot_{lot_id}_pack_{id}")
        return send_file(xlsxpath, as_attachment=True, download_name="excel.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        xlsxpath = dfToXlxs(dfdata, f"All_lots_pack_{id}")
        return send_file(xlsxpath, as_attachment=True, download_name="excel.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/api/submit-dates', methods=['POST'])
def submit_dates():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    df = getOrders(start_date, end_date).to_json(orient='records')
    print(df)
    return jsonify(df), 200

@app.route('/api/fetch-dates', methods=['POST'])
def fetch_dates():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    df = getOrders(start_date, end_date)
    if df.empty:
        return jsonify({'numberOrders': 0, 'numberPositions': 0}), 200
    else:
        return jsonify({'numberOrders': len(df['№ заказа'].unique()), 'numberPositions': len(df)}), 200

if __name__ == "__main__":
    app.run(debug=True)
