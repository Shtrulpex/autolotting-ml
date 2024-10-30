import pandas as pd
import os
from DataResearch import *
from DataPipeline import *
from datetime import datetime


data_pipeline = DataPipeline()

db_proc = data_pipeline._db_processor
db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
db_proc.run_query(f'DROP TABLE IF EXISTS lottings;') 
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


def getRequests(order_id):
    request = data_pipeline.get_requests(order_id=order_id)
    if not isinstance(request, pd.DataFrame):
        request = pd.DataFrame()
    return request

def editOrder(data): #Пока не редактируем
    df = pd.DataFrame(data)
    # Здесь загружается df со внесенными пользователем изменениями
    # см getRequests()
    df.to_csv("./files/enter.csv", index=False)

def getPacks():
    # при нажатии кнопок "сформировать лоты" и при переходе на страницу паков

    packs = data_pipeline.get_packs(from_dttm='01.11.2020 00:00:00', to_dttm='31.11.2020 23:59:59', algorithm='aglomerative')


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

def dfToXlxs(filepath):
    # Здесь считывается из бд df для загрузки на сторону пользователя
    df = pd.read_csv(filepath)

    df = data_pipeline.get_lots(pack_id=pack_id) # pack_id можно получить из таблицы по запросу get_packs()


    xlsxpath = '.'.join(filepath.split('.')[:-1])+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath