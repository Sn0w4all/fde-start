import numpy as np
import pandas as pd


portfolio = pd.read_csv(
    "portfolio.csv",
    sep=';',
    decimal=',',
    encoding='utf-8-sig'
)

#portfolio.head(8)
portfolio.dtypes
portfolio.info()

commission = portfolio[portfolio["Операция"].isin(['Брокерская комиссия', 'Услуги сторонних организаций'])]
#portfolio.to_excel("titanic.xlsx", sheet_name="passengers", index=False)
#commission.head(12)
#commission["Объем транзакции"].describe()
abs(commission["Объем транзакции"].sum())
commission.groupby("Операция")["Объем транзакции"].sum()

# эксперименты с датафреймами и сериями

s = pd.Series([1, 3, 5, np.nan, 6, 8])
print(s)

# указываем начало временнОго периода и число повторений (дни по умолчанию)
dates = pd.date_range('20130101', periods=6)
print(dates)

df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list('ABCD'))
print(df)

df2 = pd.DataFrame({'A': 1.,
                    'B': pd.Timestamp('20130102'), # временнАя метка
                    'C': pd.Series(range(4), index=list(range(4)), dtype='float32'), # Серия на основе списка
                    'D': np.array([3] * 4, dtype='int32'), # массив целых чисел NumPy 
                    'E': pd.Categorical(["test", "train", "test", "train"]), # категории
                    'F': 'foo'})

print(df)
print('')
#print(df2.head())
#print('')
#print(df2.to_numpy()) #массив с одним типом строк - object c разными типами данных
#print('')
#print(df.to_numpy()) #массив с одним типом строк - object с int-ом (оптимизация типов данных)

#print(df2.dtypes)
#df=df.T
df.sort_values(by='B')
print(df)

df3 = pd.DataFrame(
    {
        "Name": [
            "Braund, Mr. Owen Harris",
            "Allen, Mr. William Henry",
            "Bonnell, Miss. Elizabeth",
        ],
        "Age": [22, 35, 58],
        "Sex": ["male", "male", "female"],
    }
)

print(df3["Age"])