def collatz(num):
    if num % 2:
        result = 3 * num + 1
    else:
        result = num // 2
    print(result)
    return result
print('Введите число')
while 1:
    try:
        number = int(input())
        if number <= 0:
            print('Введите натуральное число (целое, больше 0)')
            continue
        while 1:
            number=collatz(number)
            if number == 1:
                break
        break
    except ValueError:
        print('Ошибка. Вы ввели не целое число')     
    print('Введите целое число')
