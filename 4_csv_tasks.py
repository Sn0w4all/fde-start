import csv
with open('portfolio.csv', newline='', encoding = 'utf-8-sig') as f:
    reader = csv.DictReader(f, delimiter=';') 
    header = reader.fieldnames          # первая строка — названия колонок
    rows = []
    for row in reader:
        rows.append(row) # каждая row — список значений 
#Структура файлов
    # Дата;
    # Время;
    # Операция;
    # Полное наименование операции;
    # Краткое наименование ценной бумаги;
    # Тикер;
    # Идентификатор счета;
    # Объем транзакции;
    # Валюта;
    # Количество;
    # Цена за штуку;
    # Комментарий


#print(header)
print(rows[0]['Дата'])
print(len(rows))