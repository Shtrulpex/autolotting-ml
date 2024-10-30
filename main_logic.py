import pandas as pd
import os
from DataResearch import *
from DataPipeline import *
from datetime import datetime


data_pipeline = DataPipeline()
validator = Validator(delivery_standards=data_pipeline.get_standard_shipping())


def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")



    # каждый раз когда нижимается кнопка "сохранить заказы (в начале и после редактирования)"
    try:
        request_validation = validator.validate_requests(df)
    except ValidationError as ve:
        print(ve)
        request_validation = False

    # умно сохраняем заказы в БД
    if request_validation:
        data_pipeline.put_requests(df)



    csvname = '.'.join(filepath.split('.')[:-1])+'.csv'
    os.remove(filepath)
    df.to_csv(csvname, index=False)
    return csvname

def getOrders():
    df = pd.read_csv("./files/enter.csv")

    # перешли на страницу заказов, грузим инфу по заказам в целом (даты заказов от балды)
    orders_df = data_pipeline.get_orders(from_dt='01.11.2020', to_dt='31.11.2020')
    # сортируем заказы по дате заказа (поле order_dt)

    return


def getRequests():
    # при нажатии на конкртеный заказ переходи в список его запросов (позиций) ВНИМАНИЕ, здесь появляется доп колонка -- request_id
    # в том числе для редактирование

    requests = data_pipeline.get_requests(order_id=1)
    # или сразу нескольких, можно даже всех
    requests = data_pipeline.get_requests(order_id=orders_df['№ заказа'].to_list())
    # здесь сортируем полученные запросы по их request_id


def getPacks():
    # при нажатии кнопок "сформировать лоты" и при переходе на страницу паков

    packs = data_pipeline.get_packs(from_dttm='01.11.2020 00:00:00', to_dttm='31.11.2020 23:59:59', algorithm='aglomerative')


def createPack():

    requests, human_lots = data_pipeline.get_requests_features(...) # аналошгичные фильтры на заявки (заказы)
    # human_lots поа известны, но могут быть пустым ветокром, его пока можно передавать всегда, далее будет классификатор

    # как-то вызов агломеративки или другого алгоритма???
    # lots = aglomerative(requests)

    # как-то вызываем классфикатор "как человек"???
    # human_lots = human(requests)

    # каждый раз когда нижимается кнопка "сохранить заказы (в начале и после редактирования)"
    try:
        lots_validation = validator.validate_lots(requests, lots)  # еще не сделал метод(((
    except ValidationError as ve:
        print(ve)
        lots_validation = False

    if lots_validation:
        # после вызова алгоритма создаем любое имя, включающее в себя название алгоритма (для поиска по нему)
        pack_name = 'aglomerative_' + str(datetime.now())
        # при получении от алгоритма лоттирования распределения request_id по lots закидываем результат в БД (НО ПОСЛЕ проверки валидатором)
        pack_id = data_pipeline.put_pack(pack_name, lots) # назад получаем id запрошенного пака

        # считаем метрики
        mq, ms = Scorer.mq_score(requests, lots, human_lots), Scorer.ms_score()

        # как-то что-то кидаем и считаем в Анализаторе и в Канвасе


def editOrder(data):
    df = pd.DataFrame(data)
    # Здесь загружается df со внесенными пользователем изменениями
    # см getRequests()
    df.to_csv("./files/enter.csv", index=False)

def dfToXlxs(filepath):
    # Здесь считывается из бд df для загрузки на сторону пользователя
    df = pd.read_csv(filepath)

    df = data_pipeline.get_lots(pack_id=pack_id) # pack_id можно получить из таблицы по запросу get_packs()


    xlsxpath = '.'.join(filepath.split('.')[:-1])+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath