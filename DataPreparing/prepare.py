import pandas as pd
import numpy as np
import ast

from Aglomerative.GeoSolver import GeoSolver

import datetime
from geopy.geocoders import Nominatim
import pgeocode
import re
import copy
import math
from ipywidgets import IntProgress
from IPython.display import display
import haversine as hs
from haversine import Unit


class Preparer():

    @staticmethod
    def preparing_for_KMeans(template, all_recievers, all_material_supp, spravochnik_supp, geo_solver: GeoSolver):
        '''
        входные:
            template - таблица формата загузочного шаблона
            all_recievers - all_recievers_coords.csv
            all_material_supp - all_time_material_supplier.csv
            spravochnik_supp - Справочник_поставщиков_с_единицами_и_нанами.csv
            geo_solver - обьект класса GeoSolver

        crucial steps:
            1) колонка index, которая соответствует каждой строке(т.е. уникальной комбинации № заказа и № позиции)
            Думаю, что по итогу наши лоты будут состоять из списка индексов, по которым уже можно достучаться до других признаков)
            2) Каждому материалу ставится в соответствие ближайший из возможных поставщиков, основываясь на истор. данных
            3) По п/ндексу или адресу находятся координты поставщиков с помощью GeoSolver
            4) считается расстояние между поставщиком и грузополучателем

        выход: те же колонки, что и в template, только + координаты пост/грузополч и расстояние между ними
        '''

        print("[INFO] warnings it's OK :)")
        def only_coord(adr):
            res = geo_solver.find_coords(adr)
            return res[0]

        # функция для сопоставления Материал -> Поставщики
        def get_post(material_id):
            value = mat_post.loc[mat_post["Материал"] == material_id, "Поставщики"]
            return value.iloc[0] if not value.empty and not pd.isna(value.iloc[0]) else np.nan

        # функция для сопоставления Материал -> Класс
        def get_class(material_id):
            value = mat_post.loc[mat_post["Материал"] == material_id, "Класс"]
            return value.iloc[0] if not value.empty and not pd.isna(value.iloc[0]) else np.nan

        # функция для сопоставления Поставщик -> П/индекс
        def get_addres(id):
            value = post.loc[post["Поставщик"] == id, "П/индекс"]
            return value.iloc[0] if not value.empty and not pd.isna(value.iloc[0]) else np.nan

        # функция для сопоставления Грузополучатель -> Грузополучатель_адрес
        def get_addres2(id):
            value = gruz.loc[gruz["Грузополучатель"] == id, "Грузополучатель_адрес"]
            return value.iloc[0]

        # надо для удобства
        def find_dist(x, y):
            return geo_solver.find_distance(x, y)

        gruz = all_recievers
        gruz['Грузополучатель_адрес'] = gruz['Грузополучатель_адрес'].apply(ast.literal_eval)

        post = spravochnik_supp
        # убираем ошибки в данных
        post = post[post['Город'] != "1"]

        # там в конце строковая дичь
        post.drop(post.tail(4).index, inplace=True)

        # где нет индекса заполняем городом
        post['П/индекс'] = post['П/индекс'].fillna(post['Город'])

        # убираем тех, кого не можем найти по индексу
        post = post[post['П/индекс'].notna()]

        # парочку иностранцев убираем
        post = post[post['П/индекс'] != 'EC3N 2AE']
        post = post[post['П/индекс'] != 'AZ 1033'].reset_index(drop=True)

        # для удоства переименовываем
        post["Поставщик"] = post["Кредитор"]
        post.drop(["Кредитор", "Город", "Unnamed: 0"], axis=1, inplace=True)

        mat_post = all_material_supp
        mat_post = mat_post[["Материал", "Класс", "Поставщики"]]
        mat_post = mat_post[mat_post['Поставщики'].notna()]

        data = template
        data['Материал'] = data['Материал'].astype('Int64')
        data['Грузополучатель'] = data['Грузополучатель'].astype('Int64')

        # добавляю индекс, чтобы структурировать заявки
        data.reset_index(inplace=True)

        # Применяем функцию к каждой строке data
        data["Поставщики"] = data["Материал"].apply(get_post)
        data["Класс"] = data["Материал"].apply(get_class)

        # Удаляем строки с NaN в новой колонке "value", если прокрались
        result_df = data.dropna(subset=["Поставщики"])

        # из "объекта" в список, чтобы потом развернуть его
        result_df['Поставщики'] = result_df['Поставщики'].apply(ast.literal_eval)

        # тут для каждого метриала разворачиается список поставщиков, создается новая строка для каждого поставщика
        data = result_df.explode('Поставщики')

        # для удобства
        data['Поставщик'] = data['Поставщики'].astype('Int64')
        data.drop("Поставщики", inplace=True, axis=1)

        # получаем адрес каждого поставщика
        print("[INFO] need some time... 1-2 min")
        data["Поставщик_адрес"] = data["Поставщик"].apply(get_addres)

        # получаем адрес каждого Грузополучателя
        data["Грузополучатель_адрес"] = data["Грузополучатель"].apply(get_addres2)

        data = data[data['Поставщик_адрес'].notna()]
        data = data[data['Грузополучатель_адрес'].notna()]
        data.reset_index(drop=True, inplace=True)
        # по адресу находим координаты c помощью GeoSolver inside
        data["Поставщик_адрес"] = data["Поставщик_адрес"].apply(only_coord)

        # расписываем отдельно
        data['reciever_lat'] = data['Грузополучатель_адрес'].apply(lambda x: x[0])
        data['reciever_long'] = data['Грузополучатель_адрес'].apply(lambda x: x[1])
        data['supp_lat'] = data['Поставщик_адрес'].apply(lambda x: x[0])
        data['supp_long'] = data['Поставщик_адрес'].apply(lambda x: x[1])

        # считаем расстояние между грузополуч и пост
        data["distance"] = data.apply(lambda row: find_dist(row['Поставщик_адрес'], row['Грузополучатель_адрес']),
                                      axis=1)
        result = data.loc[data.groupby('index')['distance'].idxmin()]

        # print("[INFO] result saved to 'data/data_for_KMeans.csv'")
        # result.to_csv("data/data_for_KMeans.csv", index=False)
        return result


