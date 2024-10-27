import pandas as pd
import numpy as np


class ValidationError(Exception):
    pass


class NullValueError(ValidationError):
    def __init__(self, column, index):
        self.column = column
        self.index = index
        super().__init__(f"Ошибка: Null значение в колонке '{column}' в строке {index}")


class ColumnMismatchError(ValidationError):
    def __init__(self, column, expected_type, actual_type):
        self.column = column
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(f"Ошибка: Тип данных в колонке '{column}' не соответствует. "
                         f"Ожидалось: {expected_type}, получено: {actual_type}")


class ColumnMissingError(ValidationError):
    def __init__(self, column):
        self.column = column
        super().__init__(f"Ошибка: Отсутствует колонка '{column}'")


class ExtraColumnError(ValidationError):
    def __init__(self, column):
        self.column = column
        super().__init__(f"Ошибка: Найдена лишняя колонка '{column}'")


class Scaler:
    def __init__(self):
        pass

    def output_transform(self, lots: pd.DataFrame, inplace: bool = True) -> pd.DataFrame:
        if not inplace:
            lots = lots.copy()
        lots['Планируемая сумма'] = lots['Общее количество'] * lots['Цена']
        return lots

    def input_transform(self, requests: pd.DataFrame, inplace: bool = True) -> pd.DataFrame:
        if not inplace:
            requests = requests.copy()
        requests['latitude'] = requests['Адрес'].apply(self._get_latitude)
        requests['longitude'] = requests['Адрес'].apply(self._get_longitude)
        return requests

    @staticmethod
    def _get_latitude(address: str) -> float:
        return 0.0

    @staticmethod
    def _get_longitude(address: str) -> float:
        return 0.0


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
        """
        :param template_columns: словарь, где ключ — это название столбца, а значение — тип данных.
        :param delivery_standards: датафрейм с нормативными сроками поставки для каждого класса.
        """
        if template_columns is None:
            self._template_columns = self.STANDART_INPUT_TEMPLATE
        else:
            self._template_columns = template_columns
        self._delivery_standards = delivery_standards

    def validate_requests(self, requests: pd.DataFrame) -> bool:
        """
        Проверяет заявки на соответствие шаблону и нормативность сроков поставок МТР.
        :param requests: датафрейм заявок на закупку МТР.
        :return: bool — True, если заявки соответствуют требованиям, иначе вызывает ошибку.
        """
        # проверка на соответствие
        for col, expected_type in self._template_columns.items():
            if col not in requests.columns:
                raise ColumnMissingError(col)

            actual_type = str(requests[col].dtype)
            if actual_type != expected_type:
                raise ColumnMismatchError(col, expected_type, actual_type)

        # проверка на пропущенные значения
        for col in requests.columns:
            if requests[col].isnull().any():
                null_indices = requests[col][requests[col].isnull()].index.tolist()
                for index in null_indices:
                    raise NullValueError(col, index)

        # проверка на наличие лишних колонок
        extra_columns = set(requests.columns) - set(self._template_columns.keys())
        if extra_columns:
            for col in extra_columns:
                raise ExtraColumnError(col)

        return True

        # # проверка нормативных сроков поставки
        # for idx, row in requests.iterrows():
        #     mtr_class = row['MTR_class']  # Предполагается, что в заявках есть столбец с классом МТР
        #     delivery_time = row['delivery_time']  # И столбец с указанным сроком поставки
        #
        #     # Найдем нормативный срок для


class Scorer:
    def __init__(self):
        pass

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

        lot_scores = []
        for _, lot_df in requests_lots.groupby('lot_id'):
            supplier_coverage = lot_df.groupby('supplier_id')['class_id'].nunique() / lot_df['class_id'].nunique()

            # Пропустим лот, если нет поставщиков
            if supplier_coverage.empty:
                continue

            # Подсчитаем количество поставщиков по категориям
            n_post50 = (supplier_coverage > 0.5).sum()
            n_post80 = (supplier_coverage > 0.8).sum()
            n_post100 = (supplier_coverage == 1.0).sum()

            n_post = len(supplier_coverage)

            lot_ms_score = (2 * n_post50 + 3 * n_post80 + 4 * n_post100) / n_post
            lot_scores.append(lot_ms_score)

        # Возвращаем среднее значение, если есть оценки
        return np.array(lot_scores).mean() if lot_scores else 0.0

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

    def ml_score(self, lots: pd.DataFrame, class_suppliers: pd.DataFrame) -> float:
        """Calculate ML (quality of clustering MTR by logistics cost)"""
        # logistic_costs = []
        # for lot_id, group in lots.groupby('ID Лота'):
        #     suppliers = class_suppliers[class_suppliers['ID Лота'] == lot_id]
        #     if not suppliers.empty:
        #         weights = group['weight'].values
        #         total_weight = weights.sum()
        #         if total_weight > 0:
        #             coords_recipient = group[['latitude', 'longitude']].values[0]
        #             distances = [geodesic((sup['latitude'], sup['longitude']), coords_recipient).km
        #                          for _, sup in suppliers.iterrows()]
        #             weighted_dist = np.average(distances, weights=weights)
        #             logistic_costs.append(weighted_dist)
        #

        # ml = np.mean(logistic_costs) if logistic_costs else 0
        ml = 0
        return ml
    #
    # def lot_info(self, requests: pd.DataFrame, lots: pd.DataFrame) -> pd.DataFrame:
    #     # Объединяем DataFrame запросов и лотов
    #     requests_lots = pd.merge(requests, lots, on='request_id', how='inner')
    #
    #     # Определяем квантили, которые хотим рассчитать
    #     quantiles = [0.25, 0.5, 0.75]  # 25-й, 50-й (медиана), 75-й процентиль
    #
    #     # Группируем по идентификатору лота и рассчитываем статистические характеристики
    #     cost_stats = requests_lots.groupby('lot_id')['item_cost'].agg(
    #         mean_cost='mean',
    #         min_cost='min',
    #         max_cost='max',
    #         range_cost=lambda x: x.max() - x.min(),
    #         median_cost='median',
    #         count='count',
    #         q1=lambda x: x.quantile(0.25),  # 25-й процентиль
    #         q3=lambda x: x.quantile(0.75),  # 75-й процентиль
    #         std_dev='std',  # стандартное отклонение
    #         variance='var'  # дисперсия
    #     ).reset_index()
    #
    #     # Рассчитываем дополнительные статистики по распределению
    #     cost_stats['iqr'] = cost_stats['q3'] - cost_stats['q1']  # интерквартильный размах
    #     cost_stats['cv'] = cost_stats['std_dev'] / cost_stats['mean_cost']  # коэффициент вариации
    #
    #     return cost_stats
    #
    # import matplotlib.pyplot as plt
    # import seaborn as sns
    #
    # def lot_quantity_info(self, requests: pd.DataFrame, lots: pd.DataFrame) -> pd.DataFrame:
    #     # Объединяем DataFrame запросов и лотов
    #     requests_lots = pd.merge(requests, lots, on='request_id', how='inner')
    #
    #     # Определяем квантили, которые хотим рассчитать
    #     quantiles = [0.25, 0.5, 0.75]  # 25-й, 50-й (медиана), 75-й процентиль
    #
    #     # Группируем по идентификатору лота и рассчитываем статистические характеристики по количеству предметов
    #     quantity_stats = requests_lots.groupby('lot_id')['item_quantity'].agg(
    #         mean_quantity='mean',
    #         min_quantity='min',
    #         max_quantity='max',
    #         range_quantity=lambda x: x.max() - x.min(),
    #         median_quantity='median',
    #         count='count',
    #         q1=lambda x: x.quantile(0.25),  # 25-й процентиль
    #         q3=lambda x: x.quantile(0.75),  # 75-й процентиль
    #         std_dev='std',  # стандартное отклонение
    #         variance='var'  # дисперсия
    #     ).reset_index()
    #
    #     # Рассчитываем дополнительные статистики по распределению
    #     quantity_stats['iqr'] = quantity_stats['q3'] - quantity_stats['q1']  # интерквартильный размах
    #     quantity_stats['cv'] = quantity_stats['std_dev'] / quantity_stats['mean_quantity']  # коэффициент вариации
    #
    #     # Визуализация
    #     self.visualize_quantity_distribution(requests_lots)
    #
    #     return quantity_stats
    #
    # def visualize_quantity_distribution(self, requests_lots: pd.DataFrame):
    #     plt.figure(figsize=(12, 6))
    #
    #     # Гистограмма
    #     sns.histplot(requests_lots['item_quantity'], bins=30, kde=True)
    #     plt.title('Распределение количества предметов в лотах')
    #     plt.xlabel('Количество предметов')
    #     plt.ylabel('Частота')
    #     plt.grid()
    #     plt.show()
    #
    #     # Ящик с усами (box plot)
    #     plt.figure(figsize=(12, 6))
    #     sns.boxplot(x=requests_lots['item_quantity'])
    #     plt.title('Ящик с усами: Количество предметов в лотах')
    #     plt.xlabel('Количество предметов')
    #     plt.grid()
    #     plt.show()
    #
