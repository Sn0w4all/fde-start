import csv
from datetime import date

with open('portfolio.csv', newline='', encoding = 'utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';') 
    header = reader.fieldnames          # первая строка — названия колонок
    rows = []
    for row in reader:
        rows.append(row) # каждая row — список значений в rows 
#Структура файлов
    # Дата
    # Время
    # Операция
    # Полное наименование операции
    # Краткое наименование ценной бумаги
    # Тикер
    # Идентификатор счета
    # Объем транзакции
    # Валюта
    # Количество
    # Цена за штуку
    # Комментарий 

#Всего строк в rows - 483


#считаем сумму уплавченной комиссии
commision = 0
dateFrom = date.today()
dateTo = dateFrom
for i in range(0, len(rows)-1):
    try:
        if (rows[i]['Операция'] == 'Брокерская комиссия') or (rows[i]['Операция'] == 'Услуги сторонних организаций'):
            commision += float(rows[i]['Объем транзакции'].replace(',', '.'))
            if dateFrom > date.fromisoformat(rows[i]['Дата']):
                dateFrom = date.fromisoformat(rows[i]['Дата'])
    except: 
        ValueError
commision = round(commision, 1)
print('Общая комиссия за период с ',dateFrom,' по ',dateTo,' составила ',-commision, 'RUB')