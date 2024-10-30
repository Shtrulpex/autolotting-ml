import numpy as np
import pandas as pd
from Aglomerative.GeoSolver import GeoSolver

class Lot():
    
    """Описывает один лот"""
    
    def __init__(self, request_id, date, coords, mtr):
        """
        Создает объет Position
        Формирует словарь возможных поставщиков и кол-во товаров, которые они могут 
        закупить (мб None!)
        Инициализирует географический центр
        Инициализируется минимальная и максимальная дата доставки
        """
        
        self.__content = [request_id]
        self.__min_date, self.__max_date = date, date
        self.__center = coords
        if len(coords) == 0:
            #print(f'{material} {coords}!!!!!!!')
            self.__center = np.array([0, 0]) # todo: change to ignore
        self.__providers = {mtr : 1}
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
        Инифицализирует пустым списком список лотов
        """
        #self.__coords = pd.read_csv("./Data/coords_test.csv")
        #self.__providers = pd.read_csv("./Data/Кабель-справочник-МТР-refactored.csv")
        self.__lots = []
        self.__geosolver = GeoSolver()
        self.__prod_percent = prod_percent / 100
        self.__prov_percent = prov_percent / 100
        self.__podgon = podgon
        self.__bar = 0
        self.__MTR = dict()
        self.__MTR_distance = dict()
        
    def get_lots(self, requests_DF):
        """
        Получает датафрейм
        Запускает __df_handler()
        Запускает __construct_lots()
        возвращает то, что лежит в лотах
        """
        
        self.__df_handler(requests_DF)
        self.__construct_lots()
        return self.__construct_csv()
        
        
    
    def __construct_csv(self):
        columns = ['request_id', 'lot_id']
        result = []
        lot = 1
        
        for i in self.__lots:
            if not i is None:
                for j in i.get_content():
                    result.append([j, lot])
                lot += 1
        #print(result)
        result = pd.DataFrame(result, columns = columns)
        return result
        
        
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
            # Меньше prov_percent выкупают prod_percent >=
            return None
        #print(lot1.get_center(), lot2.get_center())
        distance_real = self.__geosolver.find_distance(lot1.get_center(), lot2.get_center())
        prov_intersection = set(lot1.get_providers().keys()) & set(lot2.get_providers().keys())
        if len(prov_intersection) == 0:# ОШИБКА! Можем слить
            return None
        return (self.__podgon * distance_real ** 2 + 
                (len(prov_intersection)/len(set(lot1.get_providers().keys()) | set(lot2.get_providers().keys())) - 1) ** 2) ** 0.5
    
    def __df_handler(self, data):
        """
        Проходит последовательно по строкам датафрейма, создавая лоты
        Лоты создаются в список self.__lots
        """
    
        data['delivery_dt'] = pd.to_datetime(data['delivery_dt'])
        data_grouped = data.groupby(by = data['request_id'])
        
        #self.__bar = IntProgress(min=0, max=data.shape[0]+len(data_grouped)) # instantiate the bar
        #display(self.__bar)                                    # display the bar
        
        for key, item in data_grouped:
            
            date, coords = item['delivery_dt'].iloc[0], np.array([item['receiver_address_latitude'].iloc[0], item['receiver_address_longitude'].iloc[0]])
            
            mtr_class = item['class_id'].iloc[0]
            if not mtr_class in self.__MTR:
                providers = []
                for i in item['supplier_id']:
                    providers.append(i)
                self.__MTR[mtr_class] = providers
                
            self.__lots.append(Lot(key, date, coords, mtr_class))
            #self.__bar.value += 1

        self.__mtr_distance_calculate()


    def __mtr_distance_calculate(self):
        for first in self.__MTR.keys():
            self.__MTR_distance[first] = dict()
            for second in self.__MTR.keys():
                self.__MTR_distance[first][second] = len(set(self.__MTR[first]) & set(self.__MTR[second]))/len(set(self.__MTR[first]) | set(self.__MTR[second]))
                
                

    
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
            #self.__bar.value += 1
            print(f'{i} -- {j}')
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