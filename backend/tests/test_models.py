import pandas as pd
from config import PROCESSED_CSV

df = pd.read_csv(PROCESSED_CSV)

print(df["date"].min())
print(df["date"].max())
