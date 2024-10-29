import pandas as pd
import os

def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    # Зесь методы проверки на шаблон df
    # Зесь методы проверки на шаблон df
    # валидация
    #
    csvname = '.'.join(filepath.split('.')[:-1])+'.csv'
    os.remove(filepath)
    df.to_csv(csvname, index=False)
    return csvname

def getOrder():
    df = pd.read_csv("./files/enter.csv")
    # Здесь df выгружается из базы данных для редактирования пользователем
    return df

def editOrder(data):
    df = pd.DataFrame(data)
    # Здесь загружается df со внесенными пользователем изменениями
    df.to_csv("./files/enter.csv", index=False)

def dfToXlxs(filepath):
    # Здесь считывается из бд df для загрузки на сторону пользователя
    df = pd.read_csv(filepath)
    xlsxpath = '.'.join(filepath.split('.')[:-1])+".xlsx"
    df.to_excel(xlsxpath, sheet_name="Sheet1")
    return xlsxpath

# функция вызывать по кнопке и тп