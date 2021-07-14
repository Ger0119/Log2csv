import pandas as pd
import numpy as np
import sys
import re
import time


def main():

    files = sys.argv[1:]
    dataFrame = log2csv(files[0])
    if len(files) > 1:
        for x in files[1:]:
            dataFrame2 = log2csv(x,0)
            dataFrame2 = dataFrame2.iloc[:,1:]
            #dataFrame2 = dataFrame2.loc[:,lambda x : x.loc["P/F"] == "PASS"]
            for lot in dataFrame2:
                if lot == "0.0.0":
                    continue
                if lot not in dataFrame:
                    dataFrame = pd.concat([dataFrame,dataFrame2.loc[:,lot]],axis=1)
                    continue
                if dataFrame.loc["P/F",lot] == "PASS" and dataFrame2.loc["P/F",lot] != "PASS":
                    continue
                else:
                    dataFrame.update(dataFrame2[lot])

            #dataFrame.update(dataFrame2.iloc[:,1:])

    dataFrame.to_csv(file[0]+'.csv')


def log2csv(file,test_flag=1):
    T_ID    = ""
    T_Des   = ""
    Value   = ""
    L_Limit = ""
    H_Limit = ""
    Unit    = ""
    Dut     = ""
    Pin     = ""
    T_name  = ""

    flag_start = 0

    with open(file, 'r') as f:
        Pro = Solution()
        for data in f.readlines():
            if not data:
                break
            data = data.strip()
            flag = ""

            if 'ALARM_FAIL' in data:
                continue
            if 'Start' in data and flag_start == 0:
                flag_start = 1
                continue
            elif 'Start' in data and flag_start == 1:
                Result.T_finish()
                Result.T_clear()
                continue

            if not re.match(r'\d+\s+',data):
                if re.match(r'DUT\s\d',data):
                    _line = data.split()
                    Dut   = _line[1]
                    PF    = _line[3]
                    if PF == 'PASS':
                        Result.T_Fail('0',Dut)
                    BIN = '_'.join(_line[5:])
                    Result.T_PF(PF,Dut)
                    Result.T_BIN(BIN,Dut)
                continue

            _line = data.split()

            if len(_line) == 9:
                T_ID, T_Des = _line[:2]
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(_line[4:7])
                Dut, Pin = _line[-2:]
                Pin = Pin.replace(r'-----',"")
                flag = 'dc'

            elif len(_line) == 8:
                T_ID, T_Des = _line[:2]
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(_line[4:7])
                Dut = _line[-1]
                flag = 'dc'

            elif len(_line) == 7:
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(_line[2:5])
                Dut, Pin = _line[-2:]
                Pin = Pin.replace(r'-----',"")
                flag = 'dc'

            elif len(_line) == 6:
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(_line[2:5])
                Dut = _line[-1]
                flag = 'dc'

            elif len(_line) == 5:
                T_ID, T_Des = _line[:2]
                Value = _line[3]
                Dut   = _line[-1]
                flag = 'ft'

            elif len(_line) == 3:
                Value, Dut = _line[-2:]
                flag = 'ft'

            else:
                print('Error : Data Process Miss')
                print(data+'\n')
                exit()

            if flag == 'dc':
                T_name = T_ID + '_' + T_Des + '_' + Pin
                if test_flag == 1:
                    T_item = Test_case(T_name,T_ID,T_Des+'_'+ Pin,Unit,L_Limit,H_Limit,flag)

            elif flag == 'ft':
                T_name = T_ID + '_' + T_Des
                if test_flag == 1:
                    T_item = Test_case(T_name, T_ID, T_Des , flag=flag)

            Result = Test_data(T_name,Value,Dut)
            if 'FAIL' in data:
                Result.T_Fail(T_name,Dut)

    Result.T_finish()
    Result.T_clear()
    T_result = pd.DataFrame.from_dict(Result.T_all,orient='index',columns=Result.T_all['Test'])
    if test_flag == 1:
        T_case = T_item.T_finish()
        return pd.concat([T_case,T_result.iloc[1:].T],axis=1)
    else:
        return T_result.T


class Test_data(object):
    T_lst  = ['Wno', 'X', 'Y', 'DUT', 'P/F', 'FailTest', 'BIN']
    T_all  = {}
    T_data = {}

    def __init__(self, T_name, T_value, Dut):
        self.T_name = T_name
        self.T_value = T_value
        self.Dut = str(Dut)

        if self.T_name not in self.T_lst:
            self.T_lst.append(self.T_name)
        if self.Dut not in self.T_data:
            self.T_data[str(self.Dut)] = ['0', '0', '0', str(Dut), '0', '0', '0']

        Test_data.T_data[str(self.Dut)].append(self.T_value)

        if "WNO" in self.T_name:
            self.T_data[str(self.Dut)][0] = str(int(self.T_value))
        elif "XADR" in self.T_name:
            self.T_data[str(self.Dut)][1] = str(int(self.T_value))
        elif "YADR" in self.T_name:
            self.T_data[str(self.Dut)][2] = str(int(self.T_value))

    def T_clear(self):
        Test_data.T_data.clear()
        self.T_data.clear()

    def T_finish(self):
        self.T_data = self.fix_dic(self.T_data)
        self.T_all['Test'] = self.T_lst
        self.T_all = self.add_dic(self.T_all,self.T_data)

    def T_PF(self,PF,Dut):
        self.T_data[str(Dut)][4] = str(PF)

    def T_Fail(self,Fail,Dut):
        self.T_data[str(Dut)][5] = str(Fail)

    def T_BIN(self,BIN,Dut):
        self.T_data[str(Dut)][6] = str(BIN)

    def add_dic(self,dic1, dic2):
        for x in list(dic2.keys()):
            dic1[x] = dic2[x]
        return dic1

    def fix_dic(self,data):
        dic = {}
        for x in list(data.keys()):
            if x == 'Test':
                dic[x] = data[x]
                continue
            if x != '.'.join(data[x][:3]):
                dic['.'.join(data[x][:3])] = data[x]
            else:
                dic[x] = data[x]
        return dic


class Test_case(object):
    T_lst  = []
    dc_lst = []
    ft_lst = []
    dc     = {}
    ft     = {}
    Test_Item = pd.DataFrame()

    def __init__(self,T_name,TestID,TestDes,Unit='',Low='',High='',flag='0'):
        self.T_name = T_name
        self.T_ID   = TestID
        self.T_Des  = TestDes
        self.U      = Unit
        self.L      = Low
        self.H      = High
        self.flag   = flag

        if flag not in ['dc','ft']:
            print('***** Test Case Catch Error ****')
            exit()
        elif flag == 'dc':
            if self.T_name not in Test_case.dc_lst:
                Test_case.dc_lst.append(self.T_name)
                Test_case.dc[self.T_name] = [TestID,TestDes,Unit,Low,High]
        elif flag == 'ft':
            if self.T_name not in Test_case.ft_lst:
                Test_case.ft_lst.append(self.T_name)
                Test_case.ft[self.T_name] = [TestID,TestDes]

    @staticmethod
    def T_finish():
        Test_case.T_lst = Test_case.dc_lst + Test_case.ft_lst
        title = pd.DataFrame(index=['Wno', 'X', 'Y', 'DUT', 'P/F', 'FailTest', 'BIN'])
        dc_DF = pd.DataFrame.from_dict(Test_case.dc, orient='index',
                                       columns=['TestID', 'TestDes', 'Unit', 'L-Limit', 'H-Limit'])
        ft_DF = pd.DataFrame.from_dict(Test_case.ft, orient='index', columns=['TestID', 'TestDes'])
        return pd.concat([title,dc_DF,ft_DF],axis=0)


class Solution(object):
    @staticmethod
    def get_Unit(data):
        if data == "None":
            return '-', ''
        Unit = np.nan
        pat = re.search(r'^([-\d.]+)', data)
        num = pat.group(0)
        Unit = data.replace(num, '')

        return float(num), Unit

    def get_Value(self,data):
        Value, High, Low = data

        Value, Value_U = self.get_Unit(Value)
        High, High_U   = self.get_Unit(High)
        Low, Low_U     = self.get_Unit(Low)

        if Low_U:
            Unit = Low_U
        elif High_U:
            Unit = High_U
        else:
            Unit = Value_U

        Value = self.Unit_change(Value_U, Unit, Value)
        High  = self.Unit_change(High_U, Unit, High)
        Low   = self.Unit_change(Low_U, Unit, Low)

        return Value,High,Low,Unit

    @staticmethod
    def Unit_change(before, after, number):
        if number == r'-' or number is np.nan or number == '':
            return number
        if before == after:
            return number
        before_U = 0
        after_U = 0
        Udic = {
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

        if before[0] in Udic:
            before_U = Udic[before[0]]

        if after[0] in Udic:
            after_U = Udic[after[0]]

        number = float(number) * 10 ** (before_U - after_U)

        return number


if __name__ == '__main__':
    start_t = time.time()
    main()
    end_t = time.time()
    print('Process took {} seconds'.format(end_t-start_t))
