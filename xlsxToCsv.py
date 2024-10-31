import pandas as pd
import os

def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    print(df)
    # Зесь добавляете соединение со своими методами проверки df
    csvname = '.'.join(filepath.split('.')[:-1])+'.csv'
    os.remove(filepath)
    df.to_csv(csvname, index=False)
    return csvname