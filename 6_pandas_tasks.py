import pandas as pd
#import numpy as np
#import matplotlib.pyplot as plt

portfolio = pd.read_csv(
    "portfolio.csv",
    sep=';',
#    decimal=',',
    encoding='utf-8-sig'
)

#portfolio.head(8)
#portfolio.dtypes
#portfolio.info()

try:

    portfolio["Объем транзакции"] = portfolio["Объем транзакции"].str.replace(',','.').astype(float)
    commission = portfolio[portfolio["Операция"].isin(['Брокерская комиссия', 'Услуги сторонних организаций'])]

    #commission.head(12)
    #commission["Объем транзакции"].describe()
    
    sumComission = abs(commission["Объем транзакции"].sum())
    dateTo = commission["Дата"].max()
    dateFrom = commission["Дата"].min()
    print('Общая комиссия за период с ',dateFrom,' по ',dateTo,' составила ',sumComission, 'RUB')
    #print(commission.iloc[2:17, 2:7]) #строки, столбцы
    
    commissionByType = commission.groupby("Операция")["Объем транзакции"].sum() #это сервиес
    course = 70.23

    #df2Commission = pd.DataFrame({'Объем транзакции': commissionByType}) #можно так
    df2Commission = commissionByType.to_frame() #или так

#   commissionByType = commissionByType.T
#   print(commissionByType)
    df2Commission["Валюта"] = 'RUB'
    df2Commission["Сумма в USD"] = round(df2Commission["Объем транзакции"] / course,2)
    df2Commission.to_excel("commissionByType.xlsx", sheet_name="passengers", index=True)
    

except ValueError: 
    print('Битый файл')