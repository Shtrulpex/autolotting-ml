import pandas as pd
import os
from DataResearch import *
from DataPipeline import *
from datetime import datetime
from Canvas import make_dashboard


data_pipeline = DataPipeline()

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
        
    request_validation = True #ДЛЯ ТОГО, ЧТОБЫ РАБОТАЛО, УБРАТЬ В ПРОДАКШЕНЕ

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
            print(ms_score)
            # mq_score = scorer.mq_score(request_features, lots, human_lots)
            # make_dashboard(request_features, lots, human_lots)
            return lots
        else:
            lots = data_pipeline.get_lots(id)
            return lots
    else:
        packs = data_pipeline.get_packs()
        if packs == None:
            return pd.DataFrame()
        else:
            return packs

def editLot(data):
    df = pd.DataFrame(data)
    try:
        validator.validate_lots(df)
        data_pipeline.update_lots(df)
        return True
    except:
        return False

def putPack(pack_name, lotting_algorytm, lots, from_date, to_date, human_pack_id = None):
    pack_id = data_pipeline.put_pack(pack_name, lotting_algorytm, lots, from_date, to_date, human_pack_id)
    return pack_id

def createPack():

    requests, human_lots = data_pipeline.get_requests_features(...) # аналошгичные фильтры на заявки (заказы)
    # human_lots поа известны, но могут быть пустым ветокром, его пока можно передавать всегда, далее будет классификатор

    # как-то вызов агломеративки или другого алгоритма???
    # lots = aglomerative(requests) здесь посмотреть вызовы формирования лотов у Ильи

    # как-то вызываем классфикатор "как человек"???
    # human_lots = human(requests)

    # каждый раз когда нижимается кнопка "сохранить заказы (в начале и после редактирования)"
    # try:
    #     lots_validation = validator.validate_lots(requests, lots)  # еще не сделал метод(((
    # except ValidationError as ve:
    #     print(ve)
    #     lots_validation = False

    if True:# lots_validation:
        # после вызова алгоритма создаем любое имя, включающее в себя название алгоритма (для поиска по нему)
        pack_name = 'aglomerative_' + str(datetime.now())
        # при получении от алгоритма лоттирования распределения request_id по lots закидываем результат в БД (НО ПОСЛЕ проверки валидатором)
        pack_id = data_pipeline.put_pack(pack_name, lots) # назад получаем id запрошенного пака
        # После этого можно переходить и полученный пак редактировать

        # считаем метрики
        mq, ms = Scorer.mq_score(requests, lots, human_lots), Scorer.ms_score()

        # как-то что-то кидаем и считаем в Анализаторе и в Канвасе

def dfToXlxs(df, name):
    xlsxpath = "./files/"+name+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath