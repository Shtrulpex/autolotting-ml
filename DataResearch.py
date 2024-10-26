import pandas as pd


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

    def mq_score(self, lots: pd.DataFrame, human_lots: pd.DataFrame) -> float:
        """Calculate MQ (quality of lotting)"""

        mq = (self.get_A(lots, human_lots) + self.get_B(lots, human_lots)) / 2
        return mq

    def ms_score(self, lots: pd.DataFrame, class_suppliers: pd.DataFrame) -> float:
        """Calculate MS (quality of clustering MTR by supplier intersection)"""

        merged_df = pd.merge(lots, class_suppliers, on='Материал')
        # Разворачиваем поставщиков (делаем по одной строке для каждого поставщика)
        merged_df = merged_df.explode('Поставщики')
        merged_df = merged_df.rename(columns={'Поставщики': 'Поставщик'})

        # Считаем количество классов МТР для каждого лота
        lot_class_counts = merged_df.groupby('ID Лота')['Класс'].nunique().reset_index()
        lot_class_counts.columns = ['ID Лота', 'Классы МТР']

        # Считаем количество классов внутри лотов, которые покрывают поставщики
        supplier_class_coverage = merged_df.groupby(['ID Лота', 'Поставщик'])['Класс'].nunique().reset_index()
        supplier_class_coverage.columns = ['ID Лота', 'Поставщик', 'Покрытые классы МТР']

        # Объединяем данные о лотах с количеством классов, которые покрывают поставщики
        coverage_df = pd.merge(supplier_class_coverage, lot_class_counts, on='ID Лота')

        # Считаем процент покрытия для каждого поставщика в каждом лоте
        coverage_df['Процент покрытия'] = coverage_df['Покрытые классы МТР'] / coverage_df['Классы МТР']

        # Считаем количество поставщиков, покрывающих более 50%, 80% и 100% классов
        n_50 = coverage_df[coverage_df['Процент покрытия'] > 0.5].groupby('ID Лота')['Поставщик'].nunique()
        n_80 = coverage_df[coverage_df['Процент покрытия'] > 0.8].groupby('ID Лота')['Поставщик'].nunique()
        n_100 = coverage_df[coverage_df['Процент покрытия'] == 1].groupby('ID Лота')['Поставщик'].nunique()

        # Считаем общее количество уникальных поставщиков по лотам
        total_suppliers = coverage_df.groupby('ID Лота')['Поставщик'].nunique()

        ms = ((2 * n_50 + 3 * n_80 + 4 * n_100) / total_suppliers).mean()
        return ms

    def ma_score(self, lots: pd.DataFrame) -> float:
        """Calculate MA (quality of clustering MTR by recipient address)"""
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

    def get_lot_mean_cost(self, lots: pd.DataFrame) -> float:
        """Calculate mean cost of lots"""

        return lots.groupby(['ID Лота'])['Планируемая сумма'].sum().mean()

    def get_n_lot(self, lots: pd.DataFrame) -> int:
        """Get the number of lots"""

        return lots['ID Лота'].nunique()

    def get_A(self, lots: pd.DataFrame, human_lots: pd.DataFrame) -> float:
        """Calculate A (relative number of lots)"""

        n_lots = self.get_n_lot(lots)
        human_n_lots = self.get_n_lot(human_lots)
        A = 1 - (n_lots / human_n_lots)
        return A

    def get_B(self, lots: pd.DataFrame, human_lots: pd.DataFrame) -> float:
        """Calculate B (relative mean cost of lots)"""

        lot_mean_cost = self.get_lot_mean_cost(lots)
        human_lot_mean_cost = self.get_lot_mean_cost(human_lots)
        B = 1 - (human_lot_mean_cost / lot_mean_cost)
        return B
