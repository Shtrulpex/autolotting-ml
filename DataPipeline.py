import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime


class DBProcessor:
    # Функция для конвертации типов pandas в типы SQLite
    @staticmethod
    def map_dtype_to_sql(dtype):
        if pd.api.types.is_integer_dtype(dtype):
            return 'INTEGER'
        elif pd.api.types.is_float_dtype(dtype):
            return 'FLOAT'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'DATETIME'
        else:
            return 'TEXT'

    def __init__(self, db_filename: str = './data/data.db'):
        self.engine = create_engine(f'sqlite:///{db_filename}')

    def load_df(self, table_name: str, df: pd.DataFrame, pk_column: str):
        try:
            with self.engine.connect() as connection:
                create_table_query = f"""
                                    CREATE TABLE IF NOT EXISTS {table_name} (
                                        {pk_column} INTEGER PRIMARY KEY AUTOINCREMENT,
                                        {', '.join([f'"{col}" {self.map_dtype_to_sql(dtype)}'
                                                    for col, dtype in df.dtypes.items() if col != pk_column])}
                                    );
                                    """
                connection.execute(text(create_table_query))
                if pk_column in df.columns:
                    df.set_index(pk_column, inplace=True)
                    df.to_sql(table_name, con=self.engine, if_exists='append', index=True)
                else:
                    df.to_sql(table_name, con=self.engine, if_exists='append', index=False)
        except SQLAlchemyError as e:
            print(f'Error while loading data to table \"{table_name}\": {e}')

    def get_df(self, query: str) -> pd.DataFrame:
        try:
            return pd.read_sql(query, con=self.engine)
        except SQLAlchemyError as e:
            print(f'Error while getting data with query: {e}')

    def run_query(self, query: str, *values):
        with self.engine.connect() as connection:
            if values:
                return connection.execute(text(query), values)
            return connection.execute(text(query))


class DataPipeline:
    '''
    Класс является связующим звеном между БД и остальной программой.
    Выгружает из БД данные и формируюет pd.DataFrame'ы под определенные нужды программ.
    Загружает в БД pd.DataFrame'ы
    '''

    TRANSLATE = {
        'client_id': 'Клиент',
        'material_id': 'Материал',
        'material_name': 'Краткий текст материала',
        'measure_unit': 'ЕИ',
        'materials_amount': 'Общее количество',
        'delivery_dt': 'Срок поставки',
        'receiver_id': 'Грузополучатель',
        'material_price': 'Цена',
        'purchase_method': 'Способ закупки',
        'item_id': '№ заказа',
        'order_id': '№ позиции',
        'order_dt': 'Дата заказа'
    }

    def __init__(self):
        self._db_processor = DBProcessor()

    def put_requests(self, requests: pd.DataFrame, human_lots: pd.Series = None) -> pd.Series:
        """Загружает в БД данные заявки, поданной в формате шаблона"""

        df = requests.copy()
        if human_lots:
            df['human_lot_id'] = human_lots.astype('Int64')
        else:
            df['human_lot_id'] = None
        df.rename(columns={'Дата заказа': 'order_dt',
                           '№ заказа': 'order_id',
                           '№ позиции': 'item_id',
                           'Срок поставки': 'delivery_dt',
                           'Материал': 'material_id',
                           'Грузополучатель': 'receiver_id',
                           'Общее количество': 'materials_amount',
                           'Цена': 'material_price',
                           'Способ закупки': 'purchase_method',
                           'Клиент': 'client_id'
                           }, inplace=True)
        df['order_dt'] = pd.to_datetime(df['order_dt'])
        df['delivery_dt'] = pd.to_datetime(df['delivery_dt'])
        df['receiver_id'] = df['receiver_id'].astype('Int64')
        df['client_id'] = df['client_id'].astype('Int64')
        df['order_id'] = df['order_id'].astype('Int64')
        df['item_id'] = df['item_id'].astype('Int64')
        df['material_id'] = df['material_id'].astype('Int64')

        # добавляем столбец с общей стоимостью заявки
        df["item_cost"] = df['materials_amount'] * df['material_price']

        # Находим минимальную дату для каждого заказа и обновляем 'order_dt'
        df['order_dt'] = df.groupby('order_id')['order_dt'].transform('min')

        df = df[['item_id', 'order_id', 'human_lot_id', 'client_id', 'order_dt', 'material_id', 'receiver_id',
                 'materials_amount', 'material_price', 'item_cost', 'purchase_method', 'delivery_dt']]

        # Получаем ID последней записи перед вставкой
        try:
            last_id_before_insert = self._db_processor.run_query('SELECT COALESCE(MAX(request_id), 0) FROM requests').fetchone()[0]
        except SQLAlchemyError:  # Если таблица не существует
            last_id_before_insert = 0
        self._db_processor.load_df('requests', df, 'request_id')

        # Получаем только новые request_id
        query_new_ids = f'''
              SELECT request_id FROM requests WHERE request_id > {last_id_before_insert}
          '''
        request_ids = pd.Series(np.array(self._db_processor.run_query(query_new_ids).fetchall()).flatten())
        return request_ids

    def put_pack(self, pack_name: str, lots: pd.DataFrame) -> int:
        """
            Загружает в БД пак лотов и обновляет зависимые таблицы (packs, lottings)
            Возвращает id пака в БД
        """

        formation_dttm = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        packs_df = pd.DataFrame({
            'pack_name': [pack_name],
            'formation_dttm': [formation_dttm],
        })
        packs_df['formation_dttm'] = packs_df['formation_dttm'].astype('datetime64[ns]')
        self._db_processor.load_df('packs', packs_df, pk_column='pack_id')
        pack_id = self._db_processor.run_query('SELECT last_insert_rowid()').fetchone()[0]

        lottings_df = pd.DataFrame({
            'pack_id': pack_id,
            'lot_id': lots['lot_id'],
            'request_id': lots['request_id'],
        })
        lottings_df['pack_id'] = lottings_df['pack_id'].astype('Int64')
        lottings_df['lot_id'] = lottings_df['lot_id'].astype('Int64')
        lottings_df['request_id'] = lottings_df['request_id'].astype('Int64')
        self._db_processor.load_df('lottings', lottings_df, pk_column='lotting_id')

        return pack_id

    def get_requests(self, **filters) -> pd.DataFrame:
        """Выгружает все загруженные заявки по заданным фильтрам в формате входного шаблона + request_id"""

        query = f'''
        SELECT DISTINCT
            requests.request_id AS '№ заявки',
            requests.client_id AS "Клиент",
            requests.material_id AS "Материал",
            materials.material_name AS "Краткий текст материала",
            materials.measure_unit AS "ЕИ",
            requests.materials_amount AS "Общее количество",
            strftime('%m', requests.delivery_dt) AS "Месяц поставки",
            strftime('%Y', requests.delivery_dt) AS "Год поставки",
            CASE 
            	WHEN strftime('%m', requests.delivery_dt) <= 6 THEN 1
                ELSE 2
            END AS "Полугодие",
            requests.delivery_dt AS "Срок поставки",
            requests.receiver_id AS "Грузополучатель",
            requests.material_price AS "Цена",
            requests.purchase_method AS "Способ закупки",
            requests.order_id AS "№ заказа",
            requests.item_id AS "№ позиции",
            requests.order_dt AS "Дата заказа"
        FROM requests
        INNER JOIN materials
            ON requests.material_id = materials.material_id
        '''
        return self._db_processor.get_df(query)

    def get_packs(self, **filters) -> pd.DataFrame:
        """Выгружает все паки лотов по заданным фильтрам"""

        query = f'''
        SELECT DISTINCT
            packs.pack_id,
            packs.pack_name,
            packs.formation_dttm
        FROM packs
        '''
        return self._db_processor.get_df(query)

    def get_lots(self, pack_id: int) -> pd.DataFrame:
        """Выгружает лоты пака по id этого пака в формате выходного шаблона + request_id"""

        query = f'''
        SELECT DISTINCT
            lottings.lot_id AS "№ лота",
            requests.request_id AS "№ заявки",
            requests.client_id AS "Клиент",
            requests.material_id AS "Материал",
            materials.material_name AS "Краткий текст материала",
            materials.measure_unit AS "ЕИ",
            requests.materials_amount AS "Общее количество",
            strftime('%m', requests.delivery_dt) AS "Месяц поставки",
            strftime('%Y', requests.delivery_dt) AS "Год поставки",
            CASE 
            	WHEN strftime('%m', requests.delivery_dt) <= 6 THEN 1
                ELSE 2
            END AS "Полугодие",
            requests.delivery_dt AS "Срок поставки",
            requests.receiver_id AS "Грузополучатель",
            requests.material_price AS "Цена",
            requests.purchase_method AS "Способ закупки",
            requests.order_id AS "№ заказа",
            requests.item_id AS "№ позиции",
            requests.order_dt AS "Дата заказа"
        FROM requests
        INNER JOIN materials
            ON requests.material_id = materials.material_id
        INNER JOIN lottings
            ON lottings.request_id = requests.request_id
            AND lottings.pack_id = {pack_id}
        '''
        return self._db_processor.get_df(query)

    def get_requests_features(self, human_lots_essential: bool = False, **filters) -> pd.DataFrame:
        """
        Выгружает все заявки по зад фильтрам (время + другие) в супер-расширенном формате с указанием всех
         поставщиков заявки
        Если human_lots_essential = True, то выгружает только заявки с известными лотами человека, иначе - все заявки
        """

        query = f'''
        WITH t1 AS (
            SELECT DISTINCT
                human_lot_id,
                requests.request_id,
                requests.order_dt,
                requests.delivery_dt,
                requests.receiver_id,
                receivers.address_id AS receiver_address_id,
                addresses.address AS receiver_address,
                addresses.latitude AS receiver_address_latitude,
                addresses.longitude AS receiver_address_longitude,
                addresses.geo_coords_confidence AS receiver_address_coords_geo_confidence,
                classes.class_id,
                classes.class_name,
                classes.standard_shipping,
                requests.material_id,
                materials.material_name,
                materials.measure_unit,
                requests.materials_amount,
                requests.material_price,
                requests.item_cost,
                requests.purchase_method,
                requests.order_id,
                requests.item_id,
                requests.client_id
            FROM requests
            INNER JOIN materials
                ON requests.material_id = materials.material_id
            INNER JOIN classes
                ON materials.class_id = classes.class_id
            INNER JOIN receivers
                ON requests.receiver_id = receivers.receiver_id
            INNER JOIN addresses
                ON receivers.address_id = addresses.address_id
            {'WHERE human_lot_id IS NOT NULL' if human_lots_essential else ''}
        ),

        t2 AS (
            SELECT DISTINCT
                classes_X_suppliers.class_id,
                classes_X_suppliers.supplier_id,
                suppliers.address_id AS supplier_address_id,
                addresses.address AS supplier_address,
                addresses.latitude AS supplier_address_latitude,
                addresses.longitude AS supplier_address_longitude,
                addresses.geo_coords_confidence AS supplier_address_coords_geo_confidence
            FROM classes_X_suppliers
            INNER JOIN suppliers
                ON classes_X_suppliers.supplier_id = suppliers.supplier_id
            INNER JOIN addresses
                ON suppliers.address_id = addresses.address_id
        )

        SELECT
            t1.*,
            t2.supplier_id,
            t2.supplier_address_id,
            t2.supplier_address,
            t2.supplier_address_latitude,
            t2.supplier_address_longitude
        FROM t1
        LEFT JOIN t2
            ON t1.class_id = t2.class_id;
        '''
        return self._db_processor.get_df(query)


# КОД ДАЛЕЕ НУЖЕН ТОЛЬКО ДЛЯ ФОРМИРОВАНИЯ БД ИЗ CSV ФАЙЛОВ
# id_columns = {
#     'addresses': 'address_id',
#     'classes': 'class_id',
#     'materials': 'material_id',
#     'classes_X_suppliers': 'connection_id',
#     'suppliers': 'supplier_id',
#     'receivers': 'receiver_id',
#     'lottings': 'lotting_id',
#     'requests': 'request_id',
#     'items': 'item_id',
#     'orders': 'order_id',
#     'lots': 'lot_id',
#     'packs': 'pack_id'
# }
#
# db_proc = DBProcessor()
# for table_name in id_columns.keys():
#     db_proc.run_query(f'DROP TABLE IF EXISTS {table_name};')
#
# dp = DataPipeline()
# dp._db_processor = db_proc
#
# import os
#
# # Указываем путь к директории с CSV-файлами (9 файлов)
# csv_folder = os.path.expanduser('~/Desktop/HakatonData')
# for filename in os.listdir(csv_folder):
#     if filename.endswith('.csv'):
#         file_path = os.path.join(csv_folder, filename)
#         df = pd.read_csv(file_path)
#         table_name = os.path.splitext(filename)[0]
#         if table_name == 'template_init_data_for_model_first_month':
#             # human_lots = df['ID Лота']
#             # df.drop(columns=['ID Лота'], inplace=True)
#             # dp.put_requests(df, human_lots=human_lots)
#             # df = dp.get_requests()
#             # request_ids = df['№ заявки']
#             # request_ids = request_ids.astype('Int64')
#             # df.rename(columns={'№ заявки': 'request_id'}, inplace=True)
#             # df = pd.DataFrame({
#             #     'request_id': request_ids,
#             #     'lot_id': lot_ids
#             # })
#             # dp.put_pack('z2020-2', df)
#             continue
#         elif table_name == 'z2020-2':
#             # lot_ids = df['lot_id']
#             continue
#         db_proc.load_df(table_name, df, pk_column=id_columns.get(table_name, None))



# КОД ДАЛЕЕ НУЖЕН ТОЛЬКО ДЛЯ ПРОВЕРКИ РАБОТЫ DataPipeline
# df = dp.get_requests_features()
# df.to_csv('requests_features.csv', mode='w', index=False)
# print(df)
# print(len(df.columns))
#
# df = dp.get_requests()
# df.to_csv('requests_features.csv', mode='w', index=False)
# print(df)
# print(len(df.columns))

# df = dp.get_packs()
# print(df)
#
# pack_id = df['pack_id'].iloc[-1]
# df = dp.get_lots(pack_id)
# print(df)
# print(df.info())
# df.to_csv('requests_features.csv', mode='w', index=False)


'''
ВСЕ ВОЗВРАЩАЕТСЯ В df

ДЛЯ ВЕБА
загрузить заявки в формате входного шаблона
# put_requests

выгрузить все загруженные заявки в формате входного шаблона
+ фильтрация по дате заказа
// + другие фильтры
# get_requests

выгрузить все паки лотов с указанием их id
+ фильтрация по дате создания
# get_packs

выгрузить лоты пака по id этого пака в формате выходного шаблона
# get_lots

ДЛЯ ВНУТРЯНКИ
выгрузить все заявки по зад фильтрам (время + другие) в супер-расширенном формате с указанием всех поставщиков заявки
# get_requests_features

загрузить распределение по лотам в рамках пака по его имени
# put_lots
'''

#
# # ДАЛЕЕ КОД ТОЛЬКО ДЛЯ СОЗДАНИЯ ОООБЩЕГО ТРЕНИРОВОЧНОГО ДАТАСЕТА
#
# dp = DataPipeline()
# db_proc = dp._db_processor
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
#
# df = pd.read_csv('~/Desktop/data.csv')
# df.rename(columns={'ID Лота': 'lot_id'}, inplace=True)
# human_lots = df['lot_id']
# df.drop(columns=['lot_id'], inplace=True)
#
# dp.put_requests(df, human_lots=human_lots)
# print(1)
#
# df = dp.get_requests_features(human_lots_essential=False)
# df.to_csv('requests_features.csv', mode='w', index=False)
# print(df)
# print(len(df.columns))
#
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')


# # ДАЛЕЕ КОД ТОЛЬКО ДЛЯ СОЗДАНИЯ МЕСЯЧНОГО ТРЕНИРОВОЧНОГО ДАТАСЕТА
#
#
# dp = DataPipeline()
# db_proc = dp._db_processor
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
#
# df = pd.read_csv('~/Desktop/data-222.csv')
# # df.rename(columns={'ID Лота': 'lot_id'}, inplace=True)
# human_lots = df['human_lot_id']
# lots = df['lot_id']
# df.drop(columns=['lot_id', 'human_lot_id'], inplace=True)
#
# dp.put_requests(df, human_lots=human_lots)
# print(1)
#
# df = dp.get_requests_features(human_lots_essential=False)
# df.to_csv('requests_features.csv', mode='w', index=False)
# print(df)
# print(len(df.columns))
# #
# requests = dp.get_requests()
# requests.rename(columns={'№ заявки': 'request_id'}, inplace=True)
# requests = requests['request_id']
# # df = pd.read_csv('~/Desktop/2020-2.csv')
# # df.rename(columns={'ID Лота': 'lot_id'}, inplace=True)
# # lots = df['lot_id']
# lots = pd.concat([requests, lots], axis=1, ignore_index=True)
# human_lots = pd.concat([requests, human_lots], axis=1, ignore_index=True)
# lots.to_csv('lots.csv', mode='w', index=False)
# human_lots.to_csv('human_lots.csv', mode='w', index=False)
# #
# #
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')