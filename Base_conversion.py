def main():
    for x in range(100):
        print(dec2AZ(x))


def dec2AZ(num):

    try:
        int(num)
    except ValueError:
        print('Input Error: Not a number')
        exit()
    result = ""
    alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    while num > 0:
        if num % 26 == 0:
            result += "Z"
            num -= 26
        else:
            result += alpha[num%26-1]
        num //= 26
    return result[::-1]


def AZ2dec(string):
    result = 0
    unit = 1
    for x in string[::-1]:
        result += (ord(x)-64)*unit
        unit *= 26
    return result


if __name__ == '__main__':
    main()
