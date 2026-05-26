

animals = ['cat', 'bat', 'rat' , 'elephant']

if animals[3] == 'elephant':
    print('Hell0 ',animals[-1:][0])
#вытаскивает значение
    print('Hell0 ',animals[3])
    print('Hell0 ',animals[-1:])
#вытаскивает список состоящий из последнего элемента
    print(len(animals))

animal1, animal2, animal3 = animals[:3]
print(animal3)
#операция группового присваивания. например распарсить таблицу на строки или столбцы

print(animals.index('bat'))
#ищет номер (не от 0, а от 1) вхождения элемента