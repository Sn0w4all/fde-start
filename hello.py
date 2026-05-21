print("Привет мир")
print('Пока'+'Мир')
str8 = (5 - 1) * ( (7 + 1) / (3 - 1))
print(str8)
myAge = input('Введите ваш возраст: ')
print('Ваш возраст: '+str(int(myAge)+1))
print((4<6) and (int(myAge) != 9))

if int(myAge) > 18:
    print('Вы совершеннолетний')
    if int(myAge) > 60:
        print('И старый')
    elif int(myAge) < 59:
        print('Ну еще норм')
else:
    print('Вы не совершеннолетний')
  