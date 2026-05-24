import random, sys, os, math

def collatz(num):
    if num % 2:
        resault = 3 * num + 1
    else:
        resault = num // 2
    print(resault)
    return resault
print('Введите число')
while 1:
    try:
        number = int(input())
        while 1:
            number=collatz(number)
            if number == 1:
                break
        break
    except:
        ValueError
    print('Введите целое число')
