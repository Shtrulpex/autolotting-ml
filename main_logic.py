import pandas as pd
import os
from DataResearch import *
from DataPipeline import *
from datetime import datetime
# from Canvas import make_dashboard


data_pipeline = DataPipeline()
variable = data_pipeline._db_processor
# db_proc = data_pipeline._db_processor
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
# db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
# db_proc.run_query(f'DROP TABLE IF EXISTS lottings;') 
# С ПОМОЩЬЮ ЭТОГО МОЖНО ДРОПНУТЬ ВСЕ ТАБЛИЦЫ ПЕРЕД ЗАПУСКОМ

validator = Validator(delivery_standards=data_pipeline.get_standard_shipping())


def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    os.remove(filepath)
    response = ""
    try:
        request_validation = validator.validate_requests(df)
    except ValidationError as ve:
        response = ve
        request_validation = False
    except:
        response = ValidationError
        request_validation = False
    print(request_validation)
    if request_validation:
        response = data_pipeline.put_requests(df)
        return True, response
    else:
        return False, response

def getOrders(from_date=None, to_date=None):
    if from_date != None:
        from_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
        orders_df = data_pipeline.get_orders(from_dt=from_date, to_dt=to_date)
    else:
        orders_df = data_pipeline.get_orders()
    if not isinstance(orders_df, pd.DataFrame):
        orders_df = pd.DataFrame()
    return orders_df

def getForLots(from_date=None, to_date=None):
    orders_df = data_pipeline.get_orders(from_dt=from_date, to_dt=to_date)
    orders_ids = orders_df['№ заказа'].to_list()
    request_features = data_pipeline.get_requests_features(orders_ids)
    return request_features


def getRequests(order_id):
    request = data_pipeline.get_requests(order_id=order_id)
    if not isinstance(request, pd.DataFrame):
        request = pd.DataFrame()
    return request

def editOrder(data):
    df = pd.DataFrame(data)
    data_pipeline.update_requests(df)

def getPacks(id=None, dates = False):
    if id != None:
        if dates == True:
            packs = data_pipeline.get_packs()
            from_date = datetime.strptime(packs[packs['pack_id'] == id]['from_dt'].reset_index(drop=True)[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
            to_date = datetime.strptime(packs[packs['pack_id'] == id]['to_dt'].reset_index(drop=True)[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d")
            orders_df = data_pipeline.get_orders(from_dt=from_date, to_dt=to_date)
            orders_ids = orders_df['№ заказа'].to_list()
            request_features = data_pipeline.get_requests_features(orders_ids)
            lots = data_pipeline.get_lots_features(id)
            scorer = Scorer()
            ms_score = scorer.ms_score(request_features, lots)
            # mq_score = scorer.mq_score(request_features, lots, human_lots)
            #make_dashboard(request_features, lots, None, ms_score, None)
            return lots
        else:
            lots = data_pipeline.get_lots(id)
            return lots
    else:
        packs = data_pipeline.get_packs()
        if isinstance(packs, pd.DataFrame):
            return packs
        else:
            return pd.DataFrame()

def editLot(data):
    df = pd.DataFrame(data)
    try:
        validator.validate_lots(df)
        data_pipeline.update_lots(df)
        return True
    except:
        return False

def putPack(pack_name, lotting_algorytm, lots, from_date, to_date, human_pack_id = None):
    from_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    to_date = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    pack_id = data_pipeline.put_pack(pack_name, lotting_algorytm, lots, from_date, to_date, human_pack_id)
    return pack_id

def dfToXlxs(df, name):
    xlsxpath = "./files/"+name+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath