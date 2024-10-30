import pandas as pd
import numpy as np
# from datetime import datetime


from Aglomerative.GeoSolver import *


class ValidationError(Exception):
    pass


class NullValueError(ValidationError):
    def __init__(self, column, index):
        self.column = column
        self.index = index
        super().__init__(f"Ошибка: Null значение в колонке '{column}' в строке {index}")


class ColumnMissingError(ValidationError):
    def __init__(self, column):
        self.column = column
        super().__init__(f"Ошибка: Отсутствует колонка '{column}'")


class ExtraColumnError(ValidationError):
    def __init__(self, column):
        self.column = column
        super().__init__(f"Ошибка: Найдена лишняя колонка '{column}'")


class TypeMismatchError(ValidationError):
    def __init__(self, column, expected_type, actual_type):
        self.column = column
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(f"Ошибка: Тип в колонке '{column}' ожидается '{expected_type}', найден '{actual_type}'")


class DeliveryTimeStandardError(ValidationError):
    def __init__(self, order_id, position_id, remaining_days, standard_days):
        self.order_id = order_id
        self.position_id = position_id
        self.remaining_days = remaining_days
        self.standard_days = standard_days
        super().__init__(f"Ошибка: Мало времени для заказа '{order_id}', позиция '{position_id}'"
                         f" - осталось {remaining_days} дней, \tстандарт {standard_days} дней.")


class DeliveryTimeError(ValidationError):
    def __init__(self, lot_id):
        self.lot_id = lot_id
        super().__init__(f"Лот {lot_id} имеет дату поставки с разбросом более 30 дней.")



class Validator:
    STANDART_INPUT_TEMPLATE = {
        'Клиент': 'int64',
        'Материал': 'int64',
        'Краткий текст материала': 'object',
        'ЕИ': 'object',
        'Общее количество': 'float64',
        'Месяц поставки': 'int64',
        'Год поставки': 'int64',
        'Полугодие': 'int64',
        'Срок поставки': 'datetime64[ns]',
        'Грузополучатель': 'int64',
        'Цена': 'float64',
        'Способ закупки': 'object',
        '№ заказа': 'int64',
        '№ позиции': 'int64',
        'Дата заказа': 'datetime64[ns]'
    }

    def __init__(self, delivery_standards: pd.DataFrame, template_columns: dict = None):
        if template_columns is None:
            self._template_columns = self.STANDART_INPUT_TEMPLATE
        else:
            self._template_columns = template_columns
        self._delivery_standards = delivery_standards

    @staticmethod
    def _check_type(series: pd.Series, expected_type: str) -> bool:
        """Проверяет, могут ли значения в серии быть приведены к ожидаемому типу."""
        try:
            if expected_type == 'datetime64[ns]':
                pd.to_datetime(series, errors='raise')
            else:
                series.astype(expected_type)
            return True
        except (ValueError, TypeError):
            return False

    def validate_requests(self, requests: pd.DataFrame) -> bool:
        """
        Проверяет входные заявки на соответствие следующим критериям:
        - подаются в формате шаблона (все на месте, ничего лишнего, все в нужном типе)
        - сроки поставок соответствуют нормативам класса материала
        """
        # Проверка на наличие необходимых колонок
        for col, expected_type in self._template_columns.items():
            if col not in requests.columns:
                raise ColumnMissingError(col)

        # Проверка на наличие лишних колонок
        extra_columns = set(requests.columns) - set(self._template_columns.keys())
        if extra_columns:
            for col in extra_columns:
                raise ExtraColumnError(col)

        # Проверка на пропущенные значения
        for col in requests.drop(columns=['Способ закупки']).columns:
            if requests[col].isnull().any():
                null_indices = requests.index[requests[col].isnull()].tolist()
                for index in null_indices:
                    raise NullValueError(col, index)

        # Проверка типов данных
        for col, expected_type in self._template_columns.items():
            if col in requests.columns:
                if not self._check_type(requests[col], expected_type):
                    actual_type = requests[col].dtype
                    raise TypeMismatchError(col, expected_type, actual_type)

        # Проверка нормативных сроков поставки
        for index, request in requests.iterrows():
            material_id = request['Материал']
            standard_shipping = self._delivery_standards.loc[self._delivery_standards['material_id'] == material_id,
                                                             'standard_shipping']
            if not standard_shipping.empty:
                standard_time = standard_shipping.values[0]
                delivery_time = pd.to_datetime(request['Срок поставки'])
                # now = pd.Timestamp(datetime.now())
                # time_diff = (delivery_time - now).days
                order_time = pd.to_datetime(request['Дата заказа'])
                time_diff = (delivery_time - order_time).days
                if time_diff < standard_time:
                    raise DeliveryTimeStandardError(request['№ заказа'], request['№ позиции'], time_diff, standard_time)

        return True

    def validate_lots(self, requests: pd.DataFrame, lots: pd.DataFrame) -> bool:
        """
        Проверяет сформированные лоты на соответствие следующим критериям:
        - Даты поставок заявок внутри лота принадлежат окну разбросом не более чем в 30 дней
        """

        # Убираем дубликаты, оставляя первую запись для каждого request_id
        requests = requests.drop_duplicates(subset='request_id', keep='first')

        # Объединяем заявки и лоты по request_id
        request_lots = pd.merge(requests, lots, on='request_id')

        # Получаем минимальные и максимальные даты поставок для каждого лота
        min_delivery_dt = request_lots.groupby('lot_id')['delivery_dt'].min()
        max_delivery_dt = request_lots.groupby('lot_id')['delivery_dt'].max()
        window = (max_delivery_dt - min_delivery_dt).dt.days

        for lot_id, days in window.items():
            if days > 30:
                raise DeliveryTimeError(lot_id)

        return True


class Scorer:
    def __init__(self):
        self._geo_solver = GeoSolver()

    def mq_score(self, requests: pd.DataFrame, lots: pd.DataFrame, human_lots: pd.DataFrame, ) -> float:
        """
            Подсчет метрики MQ -- качество лоттирования МТР по средней стоимости лота и количеству лотов относительно
            лоттироваония человеком (или квазичеловеком)

            :param requests: заявки на закупку МТР с поставщиками
            :param lots: распределение по лотам алгоритмом лоттирования
            :param human_lots: распределение по лотам человеком (или квазичеловеком)
        """

        # Убираем дубликаты, оставляя первую запись для каждого request_id
        requests = requests.drop_duplicates(subset='request_id', keep='first')

        n_lots = lots['lot_id'].nunique()
        n_human_lots = human_lots['human_lot_id'].nunique()

        lot_mean_cost = pd.merge(requests, lots, on='request_id').groupby('lot_id')['item_cost'].sum().mean()
        human_lot_mean_cost = pd.merge(requests, human_lots, on='request_id').groupby('human_lot_id')[
            'item_cost'].sum().mean()

        mq = (1 - (n_lots / n_human_lots) + 1 - (human_lot_mean_cost / lot_mean_cost)) / 2
        return mq

    def ms_score(self, requests: pd.DataFrame, lots: pd.DataFrame) -> float:
        """
        Подсчет метрики MS -- качество кластеризации МТР по пересечениям поставщиков лота
        (Общие поставщики в рамках каждого отдельного лота)

        :param requests: заявки на закупку МТР
        :param lots: распределение по лотам алгоритмом лоттирования
        """

        requests_lots = pd.merge(requests, lots, on='request_id', how='inner')

        total_classes_per_lot = requests_lots.groupby('lot_id')['class_id'].nunique()

        supplier_coverage = (requests_lots.groupby(['lot_id', 'supplier_id'])['class_id'].nunique()
                             / requests_lots['lot_id'].map(total_classes_per_lot))

        n_post50 = supplier_coverage.groupby('lot_id').apply(lambda x: (x > 0.5).sum())
        n_post80 = supplier_coverage.groupby('lot_id').apply(lambda x: (x > 0.8).sum())
        n_post100 = supplier_coverage.groupby('lot_id').apply(lambda x: (x == 1.0).sum())

        n_post = supplier_coverage.groupby('lot_id').size()

        lot_ms_scores = (2 * n_post50 + 3 * n_post80 + 4 * n_post100) / n_post

        return lot_ms_scores.mean() if not lot_ms_scores.empty else 0.0

        # lot_scores = []
        # for _, lot_df in requests_lots.groupby('lot_id'):
        #     supplier_coverage = lot_df.groupby('supplier_id')['class_id'].nunique() / lot_df['class_id'].nunique()
        #
        #     # Пропустим лот, если нет поставщиков
        #     if supplier_coverage.empty:
        #         continue
        #
        #     # Подсчитаем количество поставщиков по категориям
        #     n_post50 = (supplier_coverage > 0.5).sum()
        #     n_post80 = (supplier_coverage > 0.8).sum()
        #     n_post100 = (supplier_coverage == 1.0).sum()
        #
        #     n_post = len(supplier_coverage)
        #
        #     lot_ms_score = (2 * n_post50 + 3 * n_post80 + 4 * n_post100) / n_post
        #     lot_scores.append(lot_ms_score)
        #
        # # Возвращаем среднее значение, если есть оценки
        # return np.array(lot_scores).mean() if lot_scores else 0.0

    def ml_score(self, requests: pd.DataFrame, lots: pd.DataFrame) -> float:
        """
        Оценка качества по аппроксимации средней взвешенной оценки стоимости логистики.
        Метрика считается на основе расстояний между получателями и поставщиками,
         посколько стоимость логистики прямо пропорциональна расстоянию между нач. и конеч. точками
        Подсчитывается среднее взвешанного расстояния от поставщиков
        до получателей лота, где вес каждого поставщика -- его доля "покрытия" классов лота.

        :param requests: DataFrame заявок на закупку МТР с координатами поставщиков и получателей.
        :param lots: DataFrame с распределением по лотам алгоритмом лоттирования.
        :return: Средняя взвешенная оценка логистики для всех лотов.
        """

        requests_lots = pd.merge(requests, lots, on='request_id', how='inner')

        supplier_coverage = (requests_lots.groupby('supplier_id')['class_id'].nunique() / requests_lots['class_id'].nunique())

        # Создаем DataFrame с координатами поставщиков и получателей
        supplier_coords = requests_lots[['supplier_id', 'supplier_address_latitude', 'supplier_address_longitude']]
        receiver_coords = requests_lots[
            ['receiver_id', 'receiver_address_latitude', 'receiver_address_longitude']].drop_duplicates()

        # Переименуем колонки для объединения
        supplier_coords = supplier_coords.rename(columns={
            'supplier_address_latitude': 'latitude',
            'supplier_address_longitude': 'longitude'
        })
        receiver_coords = receiver_coords.rename(columns={
            'receiver_address_latitude': 'latitude',
            'receiver_address_longitude': 'longitude'
        })

        # Создаем все возможные пары (поставщик, получатель)
        merged_coords = pd.merge(supplier_coords, receiver_coords, on='receiver_id',
                                 suffixes=('_supplier', '_receiver'))

        # Вычисляем расстояния для всех пар
        merged_coords['distance'] = merged_coords.apply(
            lambda row: self._geo_solver.find_distance(
                (row['latitude_supplier'], row['longitude_supplier']),
                (row['latitude_receiver'], row['longitude_receiver'])
            ), axis=1
        )

        # Добавляем веса на основе покрытия
        merged_coords['weight'] = merged_coords['supplier_id'].map(supplier_coverage)

        # Рассчитываем среднее взвешенное расстояние для каждого лота
        lot_scores = merged_coords.groupby('lot_id').apply(lambda x: np.average(x['distance'], weights=x['weight']))

        # Возвращаем среднюю оценку логистики для всех лотов
        return lot_scores.mean() if not lot_scores.empty else 0.0


    def ma_score(self, requests: pd.DataFrame, lots: pd.DataFrame, ) -> float:
        """
        Подсчет метрики MA -- качество кластеризации МТР по адресу грузополучателя
        """
        # distances = []
        # for lot_id, group in lots.groupby('ID Лота'):
        #     coords = group[['latitude', 'longitude']].values
        #     if len(coords) > 1:
        #         dist = np.mean([geodesic(coords[i], coords[j]).km
        #                         for i in range(len(coords)) for j in range(i+1, len(coords))])
        #         distances.append(dist)
        #
        # ma = np.mean(distances) if distances else 0
        ma = 0
        return ma
