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
# так не делаем dateFrom = date.today() и так как сейчас не делаем = делаем через инициализацию в None
dateFrom = date.fromisoformat(rows[0]['Дата'])
dateTo = dateFrom
for row in rows:
    try:
        if (row['Операция'] in ('Брокерская комиссия', 'Услуги сторонних организаций')):
            commision += float(row['Объем транзакции'].replace(',', '.'))
        d = date.fromisoformat(row['Дата'])
        if dateFrom > d:
            dateFrom = d
        if dateTo < d:
            dateTo = d
    except ValueError:
        continue   # явно: строку с нечисловым объёмом пропускаем
commision = abs(round(commision, 2))
print('Общая комиссия за период с ',dateFrom,' по ',dateTo,' составила ',commision, 'RUB')