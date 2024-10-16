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


class Inspector:
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

    # def mq_score(self, lots: pd.DataFrame, human_lots: pd.DataFrame) -> float:
    #     """
    #     Подсчитывает метрику MQ
    #     :param lots: датафрейм сформированных алгоритмом лотов
    #     :param human_lots: датафрейм лотов, сформированных человеком
    #     :return: float — значение метрики MQ in [0, 1]
    #     """
    #     mq = 0
    #     return mq
    #
    # def ms_score(self, lots: pd.DataFrame, class_suppliers: pd.DataFrame) -> float:
    #     """
    #     Подсчитывает метрику MS
    #     :param lots: датафрейм сформированных алгоритмом лотов
    #     :param class_suppliers: датафрейм классов МТР и возможных поставщиков.
    #     :return: float — значение метрики MS
    #     """
    #     # Пример расчета MS: процент классов, которые могут быть покрыты поставщиками
    #     matched_classes = pd.merge(lots[['Класс МТР']], class_suppliers, on='Класс МТР', how='inner')
    #     ms = len(matched_classes['Класс МТР'].unique()) / len(lots['Класс МТР'].unique())
    #     return ms
    #
    # def lot_mean_cost_score(self, lots: pd.DataFrame) -> float:
    #     """
    #     Возвращает среднюю стоимость лотов.
    #     :param lots: датафрейм сформированных лотов.
    #     :return: float — средняя стоимость лотов.
    #     """
    #     return lots['Цена'].mean()
    #
    # def n_lot_score(self, lots: pd.DataFrame) -> int:
    #     """
    #     Возвращает количество лотов.
    #     :param lots: датафрейм сформированных лотов.
    #     :return: int — количество уникальных лотов.
    #     """
    #     return lots['id лота'].nunique()
