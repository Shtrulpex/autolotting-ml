import pandas as pd
import os

def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    # Зесь добавляете соединение со своими методами проверки df
    csvname = '.'.join(filepath.split('.')[:-1])+'.csv'
    os.remove(filepath)
    df.to_csv(csvname, index=False)
    return csvname

def getOrder():
    df = pd.read_csv("./files/enter.csv")
    return df

def editOrder(data):
    df = pd.DataFrame(data)
    df.to_csv("./files/enter.csv", index=False)

def dfToXlxs(filepath):
    df = pd.read_csv(filepath)
    xlsxpath = '.'.join(filepath.split('.')[:-1])+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath