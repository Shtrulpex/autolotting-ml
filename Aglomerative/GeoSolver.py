import numpy as np
import pandas as pd
import datetime
from geopy.geocoders import Nominatim
import pgeocode
import re
import copy
import math

import haversine as hs
from haversine import Unit

class GeoSolver():
    
    """
    Определяет координаты места по адресу, записанному
    в произвольном виде, а также расстояние между двумя
    точками. Работает только для России и +- нормально
    отработает только на данных для нашей конкретной 
    задачи.
    """
    
    def __init__(self):
        self.__geolocator = Nominatim(user_agent="Tester")
        self.__postal_codes = pgeocode.Nominatim('RU')
        self.__special_words = [ 'г', 'город',
                                 'пос', 'поселок', 'посёлок', 'п',
                                 'с', 'село',
                                 'ст', 'станция',
                                 'м/р', 'месторождение',
                                 'пгт',
                                 'порт', 'аэропорт',
                                 'район',
                                 'обл', 'область', 
                                 'регион', 'р', 'округ', 'республика', 'респ'
                                 ]
        
    def find_distance(self, loc1, loc2):
        """
        (широта, долгота)
        возвращает расстояние по прямой в км
        """
        return hs.haversine(loc1, loc2, unit=Unit.KILOMETERS)
    
    
    def check_by_special_name(self, words, name, ident = -1):
        """
        words: список из отдельных слов, составляющих адрес, без пробелов и знаков препинания
        names: опозновательные слова: "г", "город", и т.д.
        ident: в каких пределах ищем имя
        return: позицию по широте и долготе или None
        """
        #print('check_by_special_name', words, names)
        ans = self.find_by_special_name(words, name, ident)
        #print(ans)
        if len(ans) > 0:
            for q in ans:
                query = 'Россия' + ', ' + name + ' ' + q
                #print(f'check: {query}')
                ans = self.location_by_query(query)
                if ans is not None:
                    return ans
        
        
    def find_by_special_name(self, words, name, ident = -1):
        """
        words: the list of separated words where to find name
        names_list: list of possible special names
        ident: where to search for the name: before or after the special word, +1 or -1 
        or any possible integer. The program will return all the words in the gap,
        for example for ident = -2 two words will be returned
        returns the whole name without the special word
        """
        #print('find_by_special_name')
        #print(f'names_list: {name}, {ident}')
        query = []
        for i, el in enumerate(words):
            if name == el:
                #print(f'>found {name} in words')
                q = []
                #print(f'i: {i}, ident = {ident}')
                left, right = min(i+1 if i+1 < len(words) else len(words)-1, (i+ident if i+ident >= 0 else 0)), \
                              max(i-1 if i-1 >= 0 else 0, (i+ident if i+ident < len(words) else len(words)-1))
                #print(f'>> [{left}; {right}]')
                while left < right:
                    q.append(words[left])
                    left += 1
                #print(q)
                if len(q) > 0:
                    query.append(''.join(q))
        return query
    
    
    def location_by_query(self, query):
        #print('location_by_query', query)
        try:
            location = self.__geolocator.geocode(query)
            if location is not None:
                return [location.latitude, location.longitude]
        except:
            print(f'Ошибка! {query}')
        return None
    
    
    def find_by_postal_code(self, postal_code, country = 'RU'):
        """
        postal code: str
        country: str, eg 'RU', 'US' (see pgeocode)
        returns latitude and longitude or None
        """
        #print('find_by_postal_code')
        ans = None
        try:
            ans = self.__postal_codes.query_postal_code(postal_code)
        except:
            print(f'Ошибка! postal_code: {postal_code}')
        if ans is None:
            return ans
        lat, lon = ans['latitude'], ans['longitude'] 
        return [lat, lon]
    
    
    def find_coords(self, adress):
        """
        adress: строка. Адрес записан в произвольном формате
        returns: [широта, долгота]
        """
        #print(adress)

        # Возможно, у нас будет несколько вариантов для координат
        lat, lon, postal_code = 0, 0, 0

        #Давайте попытаемся разбить адрес на "слова"
        adr = adress.lower()
        words = re.findall(r'\w+', adr)
        #print(words)

        #Теперь погнали искать почтовый индекс РФ - 6 цифр
        #Делаем это в первую очередь из-за вида данных
        for el in words:
            if el.isdigit() and len(el) == 6:
                postal_code = el
                ans = self.find_by_postal_code(postal_code)
                # Если мы нашли координаты по почтовому индексу, 
                # мы вряд ли найдем что-то лучше
                if (ans[0] is not None) and \
                    (ans[1] is not None) and \
                    (not np.isnan(ans[0]) and not np.isnan(ans[1])):
                    return ans, 1.

        # Почтовый индекс мы не нашли, или по нему ничего нет
        # Дела наши плохи и плачевны, будем тыркать систему запросами

        # Для начала давайте попробуем найти по ключевым словам в порядке
        # убывания точности запроса
        for name in self.__special_words:
            #print(f'------- ident in find_coords: {i}')
            for i in [-2, -1, 1, 2]:
                ans = self.check_by_special_name(words, name, i)
                if ans is not None:
                    return ans, 0.5
                
        # Дела совсем плохи, давайте попробуем найти по отдельным
        # словам, может что-то получится
        # Идем с конца, так как более точные данные обычно
        # лежат в конце
        for el in words[::-1]:
            ans = self.location_by_query(el)
            if ans is not None:
                return ans, 0.
                
        
        return None
    
    
    def pd_calc(self, data):
        """
        Обрабатывает данные из pd.DataFrame и возвращает таблицу с доп. колонками
        широтой и долготой, заточена иключительно под нашу задачу (т.е один конкретный
        файл с грузополучателями)
        """
        #coords = pd.DataFrame(columns = ['Код грузополучателя', 'Адрес грузополучателя', 'Долгота', 'Широта'])
        problematic = []
        coords = []

        for line, code in zip(data['Адрес грузополучателя'], data['Код грузополучателя']):
            res = self.find_coords(line)
            if res is not None:
                if np.isnan(res[0][0]) or np.isnan(res[0][1]):
                    print(f'WARNING! NaN: {line}')
                coords.append([code, line, res[0][1], res[0][0], res[1]])
            else:
                problematic.append(line)

        coords = pd.DataFrame(coords, columns = ['Код грузополучателя', 
                                                 'Адрес грузополучателя', 'Долгота', 
                                                 'Широта', 'Уверенность'])
        coords.to_csv('./Data/coords_test.csv', index = False)
        return problematic
