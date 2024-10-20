from DataPreparing import Preparer
from Aglomerative.GeoSolver import GeoSolver
from KMeans import KMeansOnlyRecvV1, KMeansIncDistV1
import pandas as pd

# preparing
pr = Preparer()
res = pr.preparing_for_KMeans(pd.read_csv("data/template_init_data_for_model_first_month.csv"),
                              pd.read_csv('data/all_recievers_coords.csv'),
                              pd.read_csv("data/all_time_material_supplier.csv"),
                              pd.read_csv("data/Справочник_поставщиков_с_единицами_и_нанами.csv"),
                              GeoSolver())

res.to_csv("data/data_for_KMeans.csv", index=False)

# clustering
df = pd.read_csv("data/data_for_KMeans.csv")

X_train = df.copy()

clf = KMeansOnlyRecvV1(8, 42)
pred = clf.fit_predict(X_train)

df["id_lot"] = pred
print(df.sample(n=5))
# df.to_csv("data/KMeans_result_for_1month_only_recievers.csv", index=False)
