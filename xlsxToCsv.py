import pandas as pd

def xlxsToDf(filepath):
    df = pd.read_excel(filepath, "Sheet1")
    print(df)