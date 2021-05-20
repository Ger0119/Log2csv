
def Unit_change(before,after,data,long=3):
    try:
        _data = float(data)
    except(Exception):
        print('Error : Data is not a number!')
        exit()
    U_dict = {
        'f': -15,
        'p': -12,
        'n': -9,
        'u': -6,
        'm': -3,
        'K': 3,
        'M': 6,
        'G': 9,
        '0': 0
    }

    if before[0] in U_dict:
        before_Unit = U_dict[before[0]]
    else:
        before_Unit = U_dict['0']
    if after[0] in U_dict:
        after_Unit = U_dict[after[0]]
    else:
        after_Unit = U_dict['0']

    data = float(data) * 10 ** (before_Unit-after_Unit)
    data = round(data,long)

    return data
