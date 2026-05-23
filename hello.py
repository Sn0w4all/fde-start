import random, sys, os, math

def spam ():
    print (eggs)
eggs = 42
spam ()
print (eggs)

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
  
myAgeNew = int(myAge)

#while myAgeNew < 100:
#    myAgeNew = myAgeNew + 1
#    print('Вы еще живы. ' + 'Ваш возраст ' + str(myAgeNew))
#    print('Еще год')
#    if myAgeNew == 0:
#        break
#print('Всего доброго')

print('Введите числе больше 10')
cirlce= int(input())

def moreThanTen():
    global cirlce
    while 1:
        cirlce = cirlce - 1
        if cirlce == 20:
            sys.exit()
        if cirlce == 10:
            break
        if cirlce < 10:
            print('Введите числе больше 10')
            cirlce = int(input())
            continue
        print(cirlce)
        print('Всего доброго')
    return (cirlce + 1)



for i in range(0,12,3):
    print(i)

for i in range(3,15):
    print(i)

print ('cats', 'dogs', 'mice', sep=',')

rand = random.randint(1,100000000000000)
print(rand)
cirlce = moreThanTen()
moreThanTen()