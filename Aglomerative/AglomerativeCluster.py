import numpy as np
import pandas as pd
from Aglomerative.GeoSolver import GeoSolver


class Object():
    """Описывает один материал в заказе"""
    
    def __init__(self, material, count, order, pos):
        """
        материал - колличество
        """
        self.material = material
        self.count = count
        self.order = order
        self.pos = pos


class Lot():
    
    """Описывает один лот"""
    
    def __init__(self, material, count, date, coords, providers, order, pos):
        """
        материал и его кол-во, срок поставки, клиента (грузополучателя)
        Создает объет матерала
        Формирует словарь возможных поставщиков и кол-во товаров, которые они могут 
        закупить из переданной таблцы материал-поставщик (мб None!)
        Инициализирует географический центр
        Инициализируется минимальная и максимальная дата доставки
        """
        
        self.__content = [Object(material, count, order, pos)]
        self.__min_date, self.__max_date = date, date
        self.__center = coords
        if len(coords) == 0:
            self.__center = np.array([0, 0]) # todo: change to ignore
        self.__providers = {p : 1 for p in providers}
        self.__order_number = 1 # Количество позиций     
    
    def merge(self, other):
        """
        Сливает other в теекущий лот
        Обновляет центр, минимальные даты
        Сливает словари
        Добавляет список товаров
        """
        self.__providers = self.providers_merge(other.get_providers())
        min_date_other, max_date_other = other.get_dates()
        self.__min_date, self.__max_date = min(self.__min_date, min_date_other), max(self.__max_date, max_date_other)
        self.__order_number += other.get_order_number()
        self.__content += other.get_content()
        self.__center = (self.__center + other.get_center()) / 2

    def providers_merge(self, other_providers):
        """
        получает словарь поставщиков и сливает его со своим
        """
        for key in self.__providers.keys():
            if key in other_providers.keys():
                other_providers[key] += self.__providers[key]
            else:
                other_providers[key] = self.__providers[key]
        return other_providers
    
    def get_center(self):
        return self.__center
    
    def get_dates(self):
        return self.__min_date, self.__max_date
        
    def get_providers(self):
        return self.__providers
        
    def get_order_number(self):
        return self.__order_number
        
    def get_content(self):
        return self.__content

class Solver():
    """
    Модель 1. Агломеративная кластеризация
    """
    
    def __init__(self, prod_percent = 50, prov_percent = 50, podgon = 1e-8):
        """
        Подгружает таблицу грузополучатель/координаты
        Подгружает справочник материал/поставщик
        Инифицализирует пустым списком список лотов
        """
        self.__coords = pd.read_csv("./Aglomerative/Data/coords_test.csv")
        self.__providers = pd.read_csv("./Aglomerative/Data/Кабель-справочник-МТР-refactored.csv")
        self.__lots = []
        self.__geosolver = GeoSolver()
        self.__prod_percent = prod_percent / 100
        self.__prov_percent = prov_percent / 100
        self.__podgon = podgon

    def get_lots(self, filename, result_filename):
        """
        Получает имя файла в формате csv
        Запускает __file_handler()
        Запускает __construct_lots()
        возвращает то, что лежит в лотах
        """
        
        self.__file_handler(filename)
        self.__construct_lots()
        self.__construct_csv(filename, result_filename)
        
        
    
    def __construct_csv(self, filename, result_filename):
        columns = ['Клиент', 'Материал', 'Краткий текст материала', 'ЕИ',
                                   'Общее количество', 'Месяц поставки', 'Год поставки',
                                   'Полугодие', 'Срок поставки', 'Грузополучатель', 'Цена',
                                   'Способ закупки', '№ заказа', '№ позиции', 'Дата заказа',
                                   'ID Лота']
        data = pd.read_csv(filename)
        print(data.head(1))
        result = []
        lot = 1
        
        for i in self.__lots:
            if not i is None:
                for j in i.get_content():
                    result.append(data[(data['№ заказа'] == j.order) & (data['№ позиции'] == j.pos)].values[0])
                    result[-1][-1] = lot
                lot += 1
        print(len(result[0]), len(result), len(columns))
        print(result)
        result = pd.DataFrame(result, columns = columns)
        result.to_csv(result_filename, index = False)
        
        
    def get_distance(self, lot1, lot2):
        """
        Если None, то None
        Принимает на вход еще один лот, возвращает расстояние между ними
        Смотрит на разницу минимальной и максимальной даты доставки  <= 30
        Проверяется Условие Качества (50% выкупают 50% если объединить)
        Считается расстояние
        Возвращается расстояние 
        """
        if lot2 is None or (max(lot1.get_dates()[1], lot2.get_dates()[1]) - min(lot1.get_dates()[0], lot2.get_dates()[0])).days > 30:
            return None
        if (np.array(list(lot1.providers_merge(lot2.get_providers()).values())) >
            ((lot1.get_order_number() + lot2.get_order_number()) * self.__prod_percent)).mean() < self.__prov_percent: 
            # Меньше prov_percent выкупают prod_percent
            return None
        distance_real = self.__geosolver.find_distance(lot1.get_center(), lot2.get_center())
        prov_intersection = set(lot1.get_providers().keys()) & set(lot2.get_providers().keys())
        if len(prov_intersection) == 0:
            return None
        return (self.__podgon * distance_real ** 2 + 
                (len(set(lot1.get_providers().keys()) | set(lot2.get_providers().keys())) / len(prov_intersection) - 1) ** 2) ** 0.5
    
    def __file_handler(self, filename):
        """
        Открывает csv файл, делает датафрейм
        Проходит последовательно по строкам датафрейма, создавая лоты
        Лоты создаются в список self.__lots
        """
        
        data = pd.read_csv(filename)

        data['Срок поставки'] = pd.to_datetime(data['Срок поставки'])
        for i in data.index:
            material, count, client, date, order, pos = data['Материал'][i], data['Общее количество'][i], \
                                            data['Грузополучатель'][i], data['Срок поставки'][i], \
                                            data['№ заказа'][i], data['№ позиции'][i]
            line = self.__coords[self.__coords['Код грузополучателя'] == client]
            coords = np.concatenate([line['Широта'].values, line['Долгота'].values])
            providers = self.__providers[self.__providers['Материал'] == material]['Поставщики']
            self.__lots.append(Lot(material, count, date, coords, providers, order, pos))
    
    def __construct_lots(self):
        """
        Идет цикл с проверкой удовлетворения условия
        {
        вызввается __calc_min_distance(self)
        если None то мы закончили
        иначе lot[i].merge(lot[j])
        }
        """
        
        best_option = self.__calc_min_distance()
        while not best_option is None:
            i, j = best_option[0], best_option[1]
            self.__lots[i].merge(self.__lots[j])
            self.__lots[j] = None
            best_option = self.__calc_min_distance()
            

    def __calc_min_distance(self):
        """
        Создает булевый список посещенных лотов
        Проходится по списку лотов
        Между каждой парой вызывает lot.get_distance(other)
        Запоминает и возвращает оптимальную пару или None
        """
        min_dist, opt1, opt2 = 1e10, -1, -1
        for i, first in enumerate(self.__lots):
            if first is None:
                continue
            for j, second in enumerate(self.__lots[i+1:]):
                dist = self.get_distance(first, second)
                if not dist is None and dist < min_dist:
                    min_dist = dist
                    opt1, opt2 = i, j + i + 1                    
        if opt1 == -1:
            return None
        return (opt1, opt2)