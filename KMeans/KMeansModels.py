from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd


class KMeansOnlyRecvV1:
    '''
    ❗ Кластеризует только по расположению грузополучателей
        Количество кластеров(8) подбирал методом локтя

    fit/predict принимают данные, обработанные Preparer'ом методом preparing_for_KMeans
    '''
    def __init__(self, n_clusters=8, rand_st=None):
        self.__pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('clust', KMeans(n_clusters, random_state=rand_st, n_init=10)),
        ])

    def fit(self, X: pd.DataFrame):
        self.__pipe.fit(X[["reciever_lat", "reciever_long"]])

    def predict(self, X: pd.DataFrame):
        return self.__pipe.predict(X[["reciever_lat", "reciever_long"]])

    def fit_predict(self, X: pd.DataFrame):
        self.fit(X)
        return self.predict(X)




class KMeansIncDistV1:
    '''
    ❗ Кластеризует по:
        1)расположению грузополучателей
        2)расстоянию между грузополучателем и ближайшим поставщиком
         (тут лучше подобрать коэф, чтобы это расстояние влияло меньше, я пока взял просто 0.5)
        Количество кластеров(8) подбирал методом локтя

    fit/predict принимают данные, обработанные Preparer'ом методом preparing_for_KMeans
    '''
    def __init__(self, n_clusters=8, rand_st=None):
        self.__pipe = Pipeline([
            ('clust', KMeans(n_clusters, random_state=rand_st, n_init=10)),
        ])

    def prepare_X(self, df):
        to_fit = df[["reciever_lat", "reciever_long", "distance"]]
        to_fit = pd.DataFrame(StandardScaler().fit_transform(to_fit),
                              columns=["reciever_lat", "reciever_long", "distance"])
        to_fit["distance"] *= 0.5
        return to_fit

    def fit(self, X: pd.DataFrame):
        self.__pipe.fit(self.prepare_X(X))

    def predict(self, X: pd.DataFrame):
        return self.__pipe.predict(self.prepare_X(X))

    def fit_predict(self, X: pd.DataFrame):
        self.fit(X)
        return self.predict(X)
