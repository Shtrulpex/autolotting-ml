import pickle
import numpy as np
import pandas as pd


class HumanLotting:
    def __init__(self, path='./HumanLotting/HumanClassifier.pkl'):
        with open(path, 'rb') as file:
            self.__model = pickle.load(file)

    def solve(self, data):
        df = data.drop(columns=['request_id', 'order_dt', 'delivery_dt', 'receiver_id', 'receiver_address_id', 
                                'receiver_address', 'receiver_address_latitude', 'receiver_address_latitude', 
                                'receiver_address_longitude', 'receiver_address_coords_geo_confidence', 
                                'class_name', 'standard_shipping', 'material_name', 'material_name', 'measure_unit',
                                'materials_amount', 'material_price', 'item_cost', 'purchase_method', 'order_id', 
                                'item_id', 'client_id', 'supplier_id', 'supplier_address_id', 'supplier_address', 
                                'supplier_address_coords_geo_confidence'])
        preds = self.__model.predict(df.drop(columns=['request_id']))
        df = df.drop(columns=['material_id', 'class_id',
                              'supplier_address_latitude',
                              'supplier_address_longitude']).assign(lot_id=preds)
        request_to_lot = {}
        for i in np.unique(df['request_id']):
            cnts = df.loc[df['request_id'] == i, 'lot_id'].value_counts()
            request_to_lot[i] = cnts.keys()[cnts.argmax()]
        return pd.DataFrame({'request_id': list(request_to_lot.keys()), 'human_lot_id': list(request_to_lot.values())})
