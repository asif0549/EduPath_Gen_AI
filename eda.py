import pandas as pd

df = pd.read_csv("students_dataset.csv")

print(df.head())
print(df.shape)
print(df.info())