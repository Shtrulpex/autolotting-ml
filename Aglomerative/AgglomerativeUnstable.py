import numpy as np
import pandas as pd
import copy
from Aglomerative.GeoSolver import GeoSolver
from DataResearch import Scorer


# Модель кластеризации, которая не была полностью sпротестирована

class Lot():
    
    """Описывает один лот"""
    
    def __init__(self, request_id, date, coords, mtr, providers):
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
        self.__providers = providers# {i : 1 for i in providers}
        self.__MTR = set([mtr])
        self.__order_number = 1 # Количество позиций     
    
    def merge(self, other, class_providers_dict):
        """
        Сливает other в теекущий лот
        Обновляет центр, минимальные даты
        Сливает словари
        Добавляет список товаров
        """
        self.__providers = self.__MTR | other.get_MTR() #self.providers_merge(other, class_providers_dict)
        self.__MTR = self.__MTR | other.get_MTR()
        min_date_other, max_date_other = other.get_dates()
        self.__min_date, self.__max_date = min(self.__min_date, min_date_other), max(self.__max_date, max_date_other)
        self.__order_number += other.get_order_number()
        self.__content += other.get_content()
        self.__center = (self.__center + other.get_center()) / 2

    def providers_merge(self, other, class_providers_dict):
        """
        получает словарь поставщиков и сливает его со своим
        """
        merged_providers = copy.deepcopy(self.__providers)
        for el in (other.get_MTR() - self.__MTR):
            for key in class_providers_dict: # .keys()
                if key in merged_providers: # .keys()
                    merged_providers[key] += 1
                else:
                    merged_providers[key] = 1
        return merged_providers
    
    def get_center(self):
        return self.__center
    
    def get_MTR(self):
        return self.__MTR
    
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
    
    def __init__(self, prod_percent = 50, prov_percent = 50, podgon = 1e-4, find_optimal = False, min_lots_percent = None, min_ms = None):
        """
        Модель аггломеративной клстеризации
        Параметры:
        1)  {prod_percent} - процент выкупаемых классов МТР в лоте {prov_percent} процентом поставщиков лота (параметры метрики MS)
            Эта группа параметров задается вместе вручную. Лоттирование останавливается, когда удовлетворять этим параметрам
            уже невозможно.
        2)  podgon - параметр, показывающий, насколько близость грузополучаталей влияет на формирование лотов. 
            0 - полное отсутствие влияния. 
            1e-4 - близость грузополучателей примерно настолько же важна, как и "близость" по классам МТР и поставщикам
        3)  find_optimal - параметр, при установке которого на True алгоритм сам ищет оптимальное лоттирование, не опираясь на
            группу параметров (1)
            3.1) min_lots_percent - параметр, который может быть установлен при find_optimal = True. Это максимальный процент
                 лотов в итоговом лоттировании относительно текущего количества лотов. [0, 100]% - диапазон значений.
            3.2) min_ms - минимальное допустимое значение метрики лоттирование MS [0, 9]
            В случае, есЫли требования (3.1) и (3.2) не могут быть соблюдены одновременно, предпочтение отдается (3.1).
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
        self.__find_optimal = find_optimal

        self.__min_mq = min_lots_percent
        if not min_lots_percent is None:
            self.__min_mq = min_lots_percent if min_lots_percent <= 100 else 100
            self.__min_mq = self.__min_mq if self.__min_mq >= 0 else 0
            self.__min_mq = 1- self.__min_mq/100 
        self.__min_ms = min_ms
        if not self.__min_ms is None:
            self.__min_ms = min_ms if min_ms <= 9 else 9
            self.__min_ms = self.__min_ms if self.__min_ms >= 0 else 0
            
        self.__scorer = Scorer()
        self.__distance = []
        #print(f"min_mq: {self.__min_mq}, ms: {self.__min_ms}")
        
    def get_lots(self, requests_DF):
        """
        Получает датафрейм
        Запускает __df_handler()
        Запускает __construct_lots()
        возвращает то, что лежит в лотах
        """
        
        self.__df_handler(requests_DF)
        self.__construct_lots(requests_DF)
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
        if lot2 is None:
            return None
            
        if (max(lot1.get_dates()[1], lot2.get_dates()[1]) - min(lot1.get_dates()[0], lot2.get_dates()[0])).days > 30:
            return None
            
        if self.__find_optimal == False:
            
            if (np.array(list(lot1.providers_merge(lot2, self.__MTR).values())) >=
                (len((lot1.get_MTR() | lot2.get_MTR())) * self.__prod_percent)).mean() < self.__prov_percent: 
                # Меньше prov_percent выкупают prod_percent
                return None
        
        
        distance_real = self.__geosolver.find_distance(lot1.get_center(), lot2.get_center())
        prov_intersection = lot1.get_MTR() & lot2.get_MTR()#set(lot1.get_providers().keys()) & set(lot2.get_providers().keys())
        #if len(prov_intersection) == 0:# ОШИБКА! Можем слить
        #    return None
        #print(prov_intersection)
        #return (self.__podgon * distance_real ** 2 + 
        #        (len(prov_intersection)/len(set(lot1.get_providers().keys()) | set(lot2.get_providers().keys())) - 1) ** 2) ** 0.5
        return (self.__podgon * distance_real ** 2 + 
               (len(prov_intersection)/len(lot1.get_MTR()| lot2.get_MTR()) - 1) ** 2) ** 0.5
    
    def __df_handler(self, data):
        """
        Проходит последовательно по строкам датафрейма, создавая лоты
        Лоты создаются в список self.__lots
        """
    
        #data['delivery_dt'] = pd.to_datetime(data['delivery_dt'])
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
                
            self.__lots.append(Lot(key, date, coords, mtr_class, self.__MTR[mtr_class]))

        self.__distance = np.zeros((len(self.__lots), len(self.__lots)))
        #self.__mtr_distance_calculate()


    def __mtr_distance_calculate(self):
        for first in self.__MTR.keys():
            self.__MTR_distance[first] = dict()
            for second in self.__MTR.keys():
                self.__MTR_distance[first][second] = len(set(self.__MTR[first]) & set(self.__MTR[second]))/len(set(self.__MTR[first]) | set(self.__MTR[second]))
                #print(f'distance: {first}->{second} = {self.__MTR_distance[first][second]}')
                
                

    
    def __construct_lots(self, df):
        """
        Идет цикл с проверкой удовлетворения условия
        {
        вызввается __calc_min_distance(self)
        если None то мы закончили
        иначе lot[i].merge(lot[j])
        }
        """
        self.__calc_distance()
        best_option = self.__calc_min_distance()
        lots_number = len(self.__lots)-1
        best_lots, best_ms = self.__lots, 4 if self.__min_ms is None else self.__min_ms
        
        while not best_option is None:
            
            if self.__find_optimal:
                lots_df = self.__construct_csv()
                ms = self.__scorer.ms_score(lots_df, df)
                mq = 1 - lots_number / len(self.__lots)
                #print(f"ms: {ms}, mq: {mq}")
                #if ((not self.__min_ms is None) and ms < self.__min_ms) or ((not self.__min_mq is None) and mq > self.__min_mq):
                #    self.__lots = copy.deepcopy(lots)
                #    return

                if ms > best_ms:
                    if ((not self.__min_mq is None) and mq >= self.__min_mq):
                        #print("here")
                        best_lots = copy.deepcopy(self.__lots)
                    if self.__min_mq is None:
                        #print("tther")
                        best_lots = copy.deepcopy(self.__lots)
             
            i, j = best_option[0], best_option[1]
            #self.__bar.value += 1
            #print(f'{i} -- {j}')
            lots = copy.deepcopy(self.__lots)
            self.__lots[i].merge(self.__lots[j], self.__MTR)
            self.__lots[j] = None
            lots_number -= 1
            self.__update_distance(i, j)
            best_option = self.__calc_min_distance()

        if self.__find_optimal:
            self.__lots = best_lots


    def __update_distance(self, new_lot, disappeared_lot):

        self.__distance[disappeared_lot] = [None for _ in self.__distance[0]]
        self.__distance[:, disappeared_lot] = [None for _ in self.__distance[0]]

        for i, second in enumerate(self.__lots):
            dist = self.get_distance(self.__lots[new_lot], second)
            self.__distance[new_lot][i] = dist
            self.__distance[i][new_lot] = dist
    
    def __calc_distance(self):
        for i, first in enumerate(self.__lots):
            for j, second in enumerate(self.__lots[i+1:]):
                self.__distance[i][i+j+1] = self.get_distance(first, second)
                self.__distance[i+j+1][i] = self.__distance[i][i+j+1]

    def __calc_min_distance(self):

        min_dist, opt1, opt2 = 1e10, -1, -1
        for i, first in enumerate(self.__lots):
            if first is None:
                continue
            for j, second in enumerate(self.__lots[i+1:]):
                dist = self.__distance[i][i+j+1]
                if not dist is None and dist < min_dist:
                    min_dist = dist
                    opt1, opt2 = i, j + i + 1                    
        if opt1 == -1:
            return None
        return (opt1, opt2)