def main():
    pass


def dec2AZ(num):

    try:
        int(num)
    except ValueError:
        print('Input Error: Not a number')
        exit()

    result = ''
    Dict = {}
    for x in range(1,27):
        Dict[x] = chr(64+x)

    while True:
        if num // 26 == 0:
            result = Dict[num] + result
            break
        if num % 26 == 0:
            if num <= (27*26):
                result += Dict[num/26-1] + Dict[26]
                break
            else: 
                result = Dict[(num/26-1)//26] + result
                num -= ((num/26-1)//26)*26*26
                continue
        if num > 26:
            result = Dict[(num-1) % 26 + 1] + result
        num = num // 26 
    return result


def AZ2dec(string):
    result = 0
    unit = 1
    for x in string[::-1]:
        result += (ord(x)-64)*unit
        unit *= 26
    return result


if __name__ == '__main__':
    main()
