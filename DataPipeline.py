import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from typing import Optional, Union, List
from tqdm import tqdm


class DBProcessor:
    # Функция для конвертации типов pandas в типы SQLite
    @staticmethod
    def map_dtype_to_sql(dtype):
        if pd.api.types.is_integer_dtype(dtype):
            return 'INTEGER'
        elif pd.api.types.is_float_dtype(dtype):
            return 'FLOAT'
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return 'DATE'
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
                self.run_query(create_table_query)
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

    def update_records(self, table: str, new_records, pk_column: str, updateable_columns: list):
        try:
            with self.engine.connect() as connection:
                for _, row in new_records.iterrows():
                    pk_id = row.get(pk_column)

                    # Cловарь обновляемых значений
                    updates = {col: row[col] for col in updateable_columns if col in row and col != pk_column}

                    # Формируем строку set_clause для SQL-запроса
                    set_clause = ", ".join([f"{col} = :{col}" for col in updates.keys()])
                    query = f"UPDATE {table} SET {set_clause} WHERE {pk_column} = :pk_id"

                    updates['pk_id'] = pk_id
                    self.run_query(query, updates)

        except Exception as e:
            print(f'Error while updating data with query: {text(query)}')

    def run_query(self, query: str, params: dict = None):
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params)
            connection.commit()
            return result


class DataPipeline:
    """
    Класс является связующим звеном между БД и остальной программой.
    Выгружает из БД данные и формируюет pd.DataFrame'ы под определенные нужды программ.
    Загружает в БД pd.DataFrame'ы
    """

    def __init__(self):
        self._db_processor = DBProcessor()

    def put_requests(self, requests: pd.DataFrame, human_lots: pd.Series = None) -> pd.Series:
        """Загружает в БД данные заявки, поданной в формате шаблона"""

        df = requests.copy()
        if human_lots is not None:
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

        # Получаем только новые order_id по только новым request_id
        query_new_ids = f'''
              SELECT DISTINCT order_id FROM requests WHERE request_id > {last_id_before_insert}
          '''
        order_ids = pd.Series(np.array(self._db_processor.run_query(query_new_ids).fetchall()).flatten(), name='order_id')
        return order_ids

    def put_pack(self, pack_name: str, lotting_algorithm: str,
                 lots: pd.DataFrame, from_dt: str, to_dt: str,
                 human_pack_id: int = None) -> int:
        """
            Загружает в БД пак лотов и обновляет зависимые таблицы (packs, lottings)
            Возвращает id пака в БД
            from_dt и to_dt -- характеристика выборки заявок по датам соответствующих заказов, из которых состоит пак лотов
        """

        formation_dttm = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        packs_df = pd.DataFrame({
            'pack_name': [pack_name],
            'lotting_algorithm': [lotting_algorithm],
            'formation_dttm': [formation_dttm],
            'from_dt': [from_dt],
            'to_dt': [to_dt],
            'human_pack_id': [human_pack_id]
        })
        packs_df['formation_dttm'] = packs_df['formation_dttm'].astype('datetime64[ns]')
        packs_df['from_dt'] = packs_df['from_dt'].astype('datetime64[ns]')
        packs_df['to_dt'] = packs_df['to_dt'].astype('datetime64[ns]')
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

    def update_requests(self, new_requests: pd.DataFrame):

        updateable_columns = [
            'order_dt', 'order_id', 'item_id', 'delivery_dt',
            'material_id', 'receiver_id', 'materials_amount',
            'material_price', 'purchase_method', 'client_id'
        ]

        new_requests.rename(columns={
            'Дата заказа': 'order_dt',
            '№ заказа': 'order_id',
            '№ позиции': 'item_id',
            'Срок поставки': 'delivery_dt',
            'Материал': 'material_id',
            'Грузополучатель': 'receiver_id',
            'Общее количество': 'materials_amount',
            'Цена': 'material_price',
            'Способ закупки': 'purchase_method',
            'Клиент': 'client_id',
            '№ заявки': 'request_id'
        }, inplace=True)

        self._db_processor.update_records('requests', new_requests,
                                          pk_column='request_id', updateable_columns=updateable_columns)

    def update_lots(self, new_lots: pd.DataFrame):

        updateable_columns = ['lot_id']

        new_lots.rename(columns={
            '№ лоттировки': 'lotting_id',
            '№ лота': 'lot_id'
        }, inplace=True)

        self._db_processor.update_records('lottings', new_lots,
                                          pk_column='lotting_id', updateable_columns=updateable_columns)

    def get_orders(self, from_dt: Optional[str] = None, to_dt: Optional[str] = None) -> pd.DataFrame:
        """Выгружает все заказы по заданным фильтрам"""

        query = '''
        SELECT 
            DISTINCT requests.order_id AS "№ заказа",
            requests.order_dt AS "Дата заказа",
            requests.client_id AS "Клиент"
        FROM requests
        '''

        conditions = []
        if from_dt:
            conditions.append(f'DATE(requests.order_dt) >= DATE("{from_dt}")')
        if to_dt:
            conditions.append(f'DATE(requests.order_dt) <= DATE("{to_dt}")')

        if conditions:
            query += "\nWHERE\n\t" + "\n\tAND ".join(conditions)

        return self._db_processor.get_df(query)

    def get_requests(self, order_id: Union[int, List[int]]) -> pd.DataFrame:
        """Выгружает все загруженные заявки по заданному/нескольким номеру(ам) заказа."""

        if isinstance(order_id, list):
            order_condition = f"requests.order_id IN ({', '.join(map(str, order_id))})"
        else:
            order_condition = f"requests.order_id = {order_id}"

        query = f'''
        SELECT DISTINCT
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
        WHERE {order_condition}
        '''

        return self._db_processor.get_df(query)

    def get_packs(self, formation_from_dttm: Optional[str] = None, formation_to_dttm: Optional[str] = None,
                  algorithm: Optional[str] = None) -> pd.DataFrame:
        """Выгружает все паки лотов по заданным фильтрам"""

        query = f'''
        SELECT DISTINCT
            packs.pack_id,
            packs.pack_name,
            packs.lotting_algorithm,
            packs.formation_dttm,
            packs.from_dt,
            packs.to_dt,
            packs.human_pack_id,
            packs.mq,
            packs.ms
        FROM packs
        '''
        conditions = []
        if formation_from_dttm:
            conditions.append(f'DATETIME(packs.formation_dttm) >= DATETIME("{formation_from_dttm}")')
        if formation_to_dttm:
            conditions.append(f'DATETIME(packs.formation_dttm) <= DATETIME("{formation_to_dttm}")')
        if algorithm:
            conditions.append(f'packs.lotting_algorithm LIKE %{algorithm}%')

        if conditions:
            query += "\nWHERE\n\t" + "\n\tAND ".join(conditions)

        return self._db_processor.get_df(query)

    def get_lots_features(self, pack_id: int) -> pd.DataFrame:
        query = f'''
                SELECT DISTINCT
                    lottings.lotting_id,
                    lottings.lot_id,
                    requests.request_id
                FROM requests
                INNER JOIN lottings
                    ON lottings.request_id = requests.request_id
                WHERE lottings.pack_id = "{pack_id}"
                '''
        return self._db_processor.get_df(query)

    def get_lots(self, pack_id: int) -> pd.DataFrame:
        """Выгружает лоты пака по id этого пака в формате выходного шаблона + request_id"""

        query = f'''
        SELECT DISTINCT
            lottings.lotting_id AS '№ лоттировки',
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
        WHERE lottings.pack_id = "{pack_id}"
        '''
        return self._db_processor.get_df(query)

    def get_requests_features(self, order_id: Union[int, List[int]], human_lots_essential: bool = False):
        """
        Выгружает все заявки по зад фильтрам (время + другие) в супер-расширенном формате с указанием всех
         поставщиков заявки
        Если human_lots_essential = True, то выгружает только заявки с известными лотами человека, иначе - все заявки
        """

        if isinstance(order_id, list):
            order_condition = f"requests.order_id IN ({', '.join(map(str, order_id))})"
        else:
            order_condition = f"requests.order_id = {order_id}"

        # query_human_lots = f'''
        # SELECT DISTINCT
        #     requests.request_id,
        #     requests.human_lot_id
        # FROM requests
        # WHERE {order_condition}
        # {'AND human_lot_id IS NOT NULL' if human_lots_essential else ''}
        # '''

        query_request_features = f'''
        WITH t1 AS (
            SELECT 
                DISTINCT requests.request_id,
                requests.order_dt,
                requests.delivery_dt,
                requests.receiver_id,
                receivers.address_id AS receiver_address_id,
                receiver_address.address AS receiver_address,
                receiver_address.latitude AS receiver_address_latitude,
                receiver_address.longitude AS receiver_address_longitude,
                receiver_address.geo_coords_confidence AS receiver_address_coords_geo_confidence,
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
            INNER JOIN materials ON requests.material_id = materials.material_id
            INNER JOIN classes ON materials.class_id = classes.class_id
            INNER JOIN receivers ON requests.receiver_id = receivers.receiver_id
            INNER JOIN addresses AS receiver_address ON receivers.address_id = receiver_address.address_id
            WHERE {order_condition}
            {('AND requests.human_lot_id IS NOT NULL') if human_lots_essential else ''}
        ),

        t2 AS (
            SELECT 
                DISTINCT classes_X_suppliers.class_id,
                classes_X_suppliers.supplier_id,
                suppliers.address_id AS supplier_address_id,
                supplier_address.address AS supplier_address,
                supplier_address.latitude AS supplier_address_latitude,
                supplier_address.longitude AS supplier_address_longitude,
                supplier_address.geo_coords_confidence AS supplier_address_coords_geo_confidence
            FROM classes_X_suppliers
            INNER JOIN suppliers ON classes_X_suppliers.supplier_id = suppliers.supplier_id
            INNER JOIN addresses AS supplier_address ON suppliers.address_id = supplier_address.address_id
        )

        SELECT 
            t1.*,
            t2.supplier_id,
            t2.supplier_address_id,
            t2.supplier_address,
            t2.supplier_address_latitude,
            t2.supplier_address_longitude
        FROM t1
        LEFT JOIN t2 ON t1.class_id = t2.class_id;
                '''

        request_features = self._db_processor.get_df(query_request_features)
        request_features['order_dt'] = request_features['order_dt'].astype('datetime64[ns]')
        request_features['delivery_dt'] = request_features['delivery_dt'].astype('datetime64[ns]')
        # human_lots = self._db_processor.get_df(query_human_lots)
        # return request_features, human_lots
        return request_features

    def get_standard_shipping(self):
        """Возвращает стандартые сроки доставки для каждого уникального материала по его классу"""

        query = f'''
        SELECT DISTINCT
            materials.material_id,
            classes.class_id,
            classes.standard_shipping
        FROM materials
        INNER JOIN classes
            ON materials.class_id = classes.class_id
        '''

        return self._db_processor.get_df(query)

# КОД ДАЛЕЕ НУЖЕН ТОЛЬКО ДЛЯ ФОРМИРОВАНИЯ БД ИЗ CSV ФАЙЛОВ
id_columns = {
    'addresses': 'address_id',
    'classes': 'class_id',
    'materials': 'material_id',
    'classes_X_suppliers': 'connection_id',
    'suppliers': 'supplier_id',
    'receivers': 'receiver_id',
    'lottings': 'lotting_id',
    'requests': 'request_id',
    'items': 'item_id',
    'orders': 'order_id',
    'lots': 'lot_id',
    'packs': 'pack_id'
}

db_proc = DBProcessor()
# for table_name in id_columns.keys():
#     db_proc.run_query(f'DROP TABLE IF EXISTS {table_name};')
db_proc.run_query(f'DROP TABLE IF EXISTS addresses;')
db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
db_proc.run_query(f'DROP TABLE IF EXISTS lottings;')

dp = DataPipeline()
dp._db_processor = db_proc

import os

# Указываем путь к директории с CSV-файлами (9 файлов)
csv_folder = os.path.expanduser('~/Desktop/HakatonData')
for filename in os.listdir(csv_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(csv_folder, filename)
        df = pd.read_csv(file_path)
        table_name = os.path.splitext(filename)[0]
        if table_name != 'addresses_coords':
            continue
        else:
            table_name = 'addresses'
            db_proc.load_df(table_name, df, pk_column='address_id')
            print(1)
        # if table_name == 'template_init_data_for_model_first_month':
        #     # human_lots = df['ID Лота']
        #     # df.drop(columns=['ID Лота'], inplace=True)
        #     # dp.put_requests(df, human_lots=human_lots)
        #     # df = dp.get_requests()
        #     # request_ids = df['№ заявки']
        #     # request_ids = request_ids.astype('Int64')
        #     # df.rename(columns={'№ заявки': 'request_id'}, inplace=True)
        #     # df = pd.DataFrame({
        #     #     'request_id': request_ids,
        #     #     'lot_id': lot_ids
        #     # })
        #     # dp.put_pack('z2020-2', df)
        #     continue
        # elif table_name == 'z2020-2':
        #     # lot_ids = df['lot_id']
        #     continue



# КОД ДАЛЕЕ НУЖЕН ТОЛЬКО ДЛЯ ПРОВЕРКИ РАБОТЫ DataPipeline
#
# dp = DataPipeline()
# db_proc = dp._db_processor
#
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
# db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
# db_proc.run_query(f'DROP TABLE IF EXISTS lottings;')
#
# df = pd.read_csv('~/Desktop/data-222.csv')
# lots = df['lot_id']
# human_lots = df['human_lot_id']
# df.drop(columns=['human_lot_id', 'lot_id'], inplace=True)
#
# request_ids = dp.put_requests(df, human_lots)
# print(request_ids)
#
# features, human_lots = dp.get_requests_features()
# # features.to_csv('requests_features.csv', mode='w', index=False)
# # human_lots.to_csv('human_lots.csv', mode='w', index=False)
# print(1)
#
# orders = dp.get_orders()
# # orders.to_csv('orders.csv', mode='w', index=False)
# print(orders)
# #
# requests = dp.get_requests(order_id=orders['№ заказа'].iloc[:2].tolist())
# # requests.to_csv('requests.csv', mode='w', index=False)
# print(requests)
# requests.loc[0, '№ позиции'] = 40
# requests.loc[1, 'Клиент'] = 39295
# print(requests)
# dp.update_requests(requests)
# requests = dp.get_requests(order_id=orders['№ заказа'].iloc[:2].tolist())
# print(requests)
#
#
# lots = pd.concat([lots, request_ids], axis=1)
# pack_id = dp.put_pack('aglomerative', lots)
# print(4)
#
# packs = dp.get_packs()
# # packs.to_csv('packs.csv', mode='w', index=False)
# print(5)
#
# lots = dp.get_lots(pack_id=pack_id)
# # lots.to_csv('lots.csv', mode='w', index=False)
# print(6)
#
#
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
# db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
# db_proc.run_query(f'DROP TABLE IF EXISTS lottings;')

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
# ДАЛЕЕ КОД ТОЛЬКО ДЛЯ СОЗДАНИЯ ОООБЩЕГО ТРЕНИРОВОЧНОГО ДАТАСЕТА

# dp = DataPipeline()
# db_proc = dp._db_processor
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
# db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
# db_proc.run_query(f'DROP TABLE IF EXISTS lottings;')
#
# df = pd.read_csv('~/Desktop/data.csv')
# df.rename(columns={'ID Лота': 'lot_id'}, inplace=True)
# human_lots = df[df['Дата заказа'].astype('datetime64[ns]') <= pd.to_datetime('2020-01-31')]['lot_id'].copy()
# human_lots.fillna(value=1, inplace=True)
# df.drop(columns=['lot_id'], inplace=True)
#
# dp.put_requests(df, human_lots=human_lots)
# orders = dp.get_orders(from_dt='2020-01-01', to_dt='2020-01-31')
# requests_month = dp.get_requests(order_id=orders['№ заказа'].to_list())['№ заявки']
# lots = pd.concat([human_lots.astype('int'), requests_month], axis=1)
# print(lots.info())
# print("Before renaming:", lots.columns)
# lots.columns = ['lot_id', 'request_id']
# print("After renaming:", lots.columns)
# print(lots.info())
# lots.to_csv(f'~/Desktop/cold_lots.csv', mode='w', index=False)
#
#
# pack_id = dp.put_pack('example', 'human_lotting', lots, from_dt='2020-01-01', to_dt='2020-01-31')
# lots = dp.get_lots(pack_id)
# print(lots.iloc[:2])
# lots['№ лота'][0] = 234
# print(lots.iloc[:2])
# dp.update_lots(lots)
# print(dp.get_lots(pack_id))
# lots.to_csv(f'~/Desktop/lots.csv', mode='w', index=False)
# #
#
# start_date = '2020-01-01'
# end_date = '2024-01-31'
# month_starts = pd.date_range(start=start_date, end=end_date, freq='MS')
# for month_start in tqdm(month_starts):
#     month_end = month_start + pd.offsets.MonthEnd(1)
#     start = month_start.strftime('%Y-%m-%d')
#     end = month_end.strftime('%Y-%m-%d')
#     orders = dp.get_orders(from_dt=start, to_dt=end)
#
#     request_features_by_month, human_lots_by_month = dp.get_requests_features(order_id=orders['№ заказа'].to_list(), human_lots_essential=True)
#     month_year = month_start.strftime('%m-%Y')
#     request_features_by_month.to_csv(f'~/Desktop/month_request_features/request_features_{month_year}.csv', mode='w', index=False)
#     human_lots_by_month.to_csv(f'~/Desktop/month_request_features/human_lots_by_month_{month_year}.csv', mode='w', index=False)
#
#
# df = dp.get_requests_features(human_lots_essential=False)
# df.to_csv('requests_features.csv', mode='w', index=False)
# print(df)
# print(len(df.columns))
#
# db_proc.run_query(f'DROP TABLE IF EXISTS requests;')
# db_proc.run_query(f'DROP TABLE IF EXISTS packs;')
# db_proc.run_query(f'DROP TABLE IF EXISTS lottings;')

## ДАЛЕЕ КОД ТОЛЬКО ДЛЯ СОЗДАНИЯ МЕСЯЧНОГО ТРЕНИРОВОЧНОГО ДАТАСЕТА
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
# df.drop(columns=['lot_id', 'human_lot_id'], inplace=True)  # остается чисто шаблон
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

