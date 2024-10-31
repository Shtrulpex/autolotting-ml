from DataPreparing import Preparer
from Aglomerative.GeoSolver import GeoSolver
from DataPipeline import DataPipeline
from KMeans import KMeansOnlyRecvV1, KMeansIncDistV1
from DataResearch import Scorer
import pandas as pd


# all_time = pd.read_csv("data/all_time_template.csv")
# all_time.rename(columns={'ID Лота': 'lot_id'}, inplace=True)
# arg1 = all_time.drop("lot_id", axis=1)
# # arg2 = all_time["lot_id"]
# # arg2.info()
#
# datapipe = DataPipeline()
# print(datapipe.put_requests(arg1))




# preparing
# pr = Preparer()
# res = pr.preparing_for_KMeans(pd.read_csv("data/template_init_data_for_model_first_month.csv"),
#                               pd.read_csv('data/all_recievers_coords.csv'),
#                               pd.read_csv("data/all_time_material_supplier.csv"),
#                               pd.read_csv("data/Справочник_поставщиков_с_единицами_и_нанами.csv"),
#                               GeoSolver())
#
# res.to_csv("data/data_for_KMeans.csv", index=False)
#
# # clustering
# df = pd.read_csv("data/data_for_KMeans.csv")
#
# X_train = df.copy()
#
# clf = KMeansOnlyRecvV1(8, 42)
# pred = clf.fit_predict(X_train)
#
# df["id_lot"] = pred
# print(df.sample(n=5))
# df.to_csv("data/KMeans_result_for_1month_only_recievers.csv", index=False)
#
#
# human = pd.read_csv("data/sample_human_lots.csv")
# lots = pd.read_csv("data/sample_lots.csv")
# req_fea = pd.read_csv("data/sample_requests_features.csv")
# human.info()
# lots.info()
# req_fea.info()
# scorer = Scorer()
# print(scorer.mq_score(req_fea, lots, human))

from KMeans import KMeansOnlyRecvV1, KMeansIncDistV1
from DataResearch import Scorer
import pandas as pd


req_fea = pd.read_csv("data/sample_requests_features.csv")

# req_fea.dropna(subset=["human_lot_id"], inplace=True)
# req_fea["human_lot_id"] = req_fea["human_lot_id"].astype('int64')

# human_lots = req_fea[["request_id", "human_lot_id"]]

X_train = req_fea.copy()
X_train.rename(columns={"receiver_address_latitude": "reciever_lat",
                        "receiver_address_longitude": "reciever_long"}, inplace=True)

clf = KMeansOnlyRecvV1(11, 42)
pred = clf.fit_predict(X_train)
X_train["lot_id"] = pred

X_train["lot_id"] = X_train["lot_id"].astype('int64')
X_train["request_id"] = X_train["request_id"].astype('int64')
lots = X_train[["request_id", "lot_id"]]

lots.drop_duplicates(subset="request_id", inplace=True)
lots.to_csv("data/lots_KMeans_result_for_1month_only_recievers.csv", index=False)
lots.info()

# scorer = Scorer()
# scorer.mq_score(req_fea, lots, human_lots)

