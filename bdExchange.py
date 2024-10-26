import pandas as pd
import os

def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    print(df)
    # Зесь добавляете соединение со своими методами проверки df
    csvname = '.'.join(filepath.split('.')[:-1])+'.csv'
    os.remove(filepath)
    df.to_csv(csvname)
    return csvname

def getOrder():
    df = pd.read_csv("./files/template.csv")
    return df