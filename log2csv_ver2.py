#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:Kin Ketsu

import numpy as np
import pandas as pd
import time
import sys
import re
import os


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ["-sort","-org"]:
        tip()
    flag  = sys.argv[1]
    files = sys.argv[2:]
    file  = files[0]
    for f in files:
        if f not in os.listdir():
            print("No "+f+" in directory")
            exit()

    dataframe = fix_DF(log2csv(files.pop(0),flag))

    while files:
        dataframe2 = log2csv(files.pop(0),flag)

        for l in range(3,len(dataframe2.columns)):
            lot = dataframe2.columns[l]

            if lot == "0.0.0":
                continue
            elif lot not in dataframe:
                dataframe = pd.concat([dataframe, dataframe2.iloc[:, l]], axis=1)
                continue
            elif dataframe.loc["P/F",lot] == "PASS" and dataframe2.iloc[3, l] != "PASS":
                continue
            else:
                dataframe.update(dataframe2.iloc[:,l])
    dataframe.to_csv(file+".csv")


def log2csv(file,tar="-sort"):
    ID      = ""
    Des     = ""
    Pin     = ""
    Pat     = ""
    Dut     = ""
    H_Limit = ""
    L_Limit = ""
    Value   = ""
    Unit    = ""
    PF      = ""
    Bin     = ""
    flag    = ""
    ed_flag = 0
    desSNo  = 0
    desENo  = -1
    patBin = re.compile(r'DUT (\d+) : (\w+) :')

    with open(file, 'r') as f:
        Pro = Solution()
        for line in f.readlines():
            if not line:
                break
            elif 'ALARM_FAIL' in line:
                continue

            if re.match(r'Test ID\s+Test Description\s+',line):
                desSNo, desENo = Pro.get_des_N(line)
                continue

            line = Pro.fix_line(line,desSNo,desENo)

            if not re.match(r'\d+\s+', line):
                pb = patBin.match(line)
                if pb:
                    Dut = pb.group(1)
                    PF  = pb.group(2)
                    Bin = re.sub(pb.group(),"",line)
                    Res.set_res(Dut,PF,Bin)
                if re.match(r'Bins',line):
                    ed_flag = 1
                if ed_flag == 1 and line == "":
                    Res.finish()
                    Res.clear()
                    ed_flag = 0
                continue

            data = line.split()
            len_data = len(data)

            if len_data == 9:
                ID, Des = data[:2]
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[4:7])
                Dut, Pin = data[-2:]
                Pin = Pin.replace(r'-----', "")
                flag = "DC"
            elif len_data == 8:
                ID, Des = data[:2]
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[4:7])
                Dut = data[-1]
                Pin = ""
                flag = "DC"
            elif len_data == 7:
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[2:5])
                Dut, Pin = data[-2:]
                Pin = Pin.replace(r'-----', "")
                flag = "DC"
            elif len_data == 6:
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[2:5])
                Dut = data[-1]
                Pin = ""
                flag = "DC"
            elif len_data == 5:
                ID, Des = data[:2]
                Value, Dut = data[-2:]
                Pin = ""
                flag = "FT"
            elif len_data == 3:
                Value, Dut = data[-2:]
                Pin = ""
                flag = "FT"
            else:
                print("Error : Lost line ",line)
                continue

            Pat = Pro.get_Pat(ID,Des,Pin)

            Res = Test_Data(Pat,Dut,Value,flag,H_Limit,L_Limit,Unit)

            if 'FAIL' in line:
                Res.set_fail(Dut,Pat)

    if ed_flag == 1:
        Res.finish()
        Res.clear()

    return pd.concat([pd.DataFrame(index=Res.fix_index(Res.final(tar))),pd.DataFrame(Res.get_test()),Test_Data.df],axis=1)


class Test_Data(object):
    T_dic  = {}
    lst    = []
    D_lst  = []
    fail   = []
    data   = []
    Tlst   = []
    Wno    = []
    XADR   = []
    YADR   = []
    PF     = []
    BIN    = []
    df = pd.DataFrame()

    def __init__(self,Pat,Dut,Value,flag,H="",L="",U=""):
        if Dut not in self.D_lst:
            self.D_lst.append(Dut)
            self.fail.append("")
            self.Wno.append("")
            self.XADR.append("")
            self.YADR.append("")
            self.PF.append("")
            self.BIN.append("")
            self.data.append([])
            self.Tlst.append([])

        self.data[self.D_lst.index(Dut)].append(Value)
        self.Tlst[self.D_lst.index(Dut)].append(Pat)

        if "CHIPID" in Pat:
            if "WNO" in Pat:
                self.Wno[self.D_lst.index(Dut)] = str(int(Value))
            elif "XADR" in Pat:
                self.XADR[self.D_lst.index(Dut)] = str(int(Value))
            elif "YADR" in Pat:
                self.YADR[self.D_lst.index(Dut)] = str(int(Value))

        if Pat not in Test_Data.T_dic:
            if flag == "FT":
                H, L, U = "", "", ""
            Test_Data.T_dic[Pat] = [str(H), str(L), U, flag]

    def set_fail(self,Dut,Pat):
        self.fail[self.D_lst.index(Dut)] = Pat

    def set_res(self,Dut,PF,Bin):
        self.PF[self.D_lst.index(Dut)] = PF
        self.BIN[self.D_lst.index(Dut)] = Bin
        if PF == "PASS":
            self.fail[self.D_lst.index(Dut)] = "0"

    def finish(self):
        for x in self.Tlst:
            Test_Data.lst = x.copy() if len(x) > len(Test_Data.lst) else Test_Data.lst

        for i in range(len(self.D_lst)):
            temp = pd.DataFrame(self.get_data(i),index=self.get_index(self.fix_index(self.Tlst[i])),columns=[self.get_chipid(i)])
            Test_Data.df = pd.concat([Test_Data.df,temp],axis=1)

    def final(self,tar):
        if tar == "-org":
            return self.fix_index(self.get_index(Test_Data.lst))
        elif tar == "-sort":
            temp_dc = []
            temp_ft = []
            for x in Test_Data.lst:
                if Test_Data.T_dic[x][-1] == "DC":
                    temp_dc.append(x)
                elif Test_Data.T_dic[x][-1] == "FT":
                    temp_ft.append(x)
            return self.get_index(self.fix_index(temp_dc)+temp_ft)

    def get_test(self):
        temp = [[],[],[],[],[],[]]
        for x in Test_Data.lst:
            temp.append(Test_Data.T_dic[x][:-1])
        return pd.DataFrame(temp,index=self.fix_index(Test_Data.get_index(Test_Data.lst)),columns=['H_Limit','L_Limit','Unit'])

    def get_data(self,i):
        return [self.Wno[i],self.XADR[i],self.YADR[i],self.PF[i],self.fail[i],self.BIN[i]]+self.data[i]

    def get_chipid(self,i):
        return '.'.join((self.Wno[i], self.XADR[i], self.YADR[i]))

    def clear(self):
        self.D_lst.clear()
        self.fail.clear()
        self.data.clear()
        self.Tlst.clear()
        self.Wno.clear()
        self.XADR.clear()
        self.YADR.clear()
        self.PF.clear()
        self.BIN.clear()

    @staticmethod
    def get_index(l):
        return ["Wno","X","Y","P/F","FailTest","BIN"]+l

    @staticmethod
    def fix_index(lst):

        for x in (i for i in lst if lst.count(i) > 1):
            cnt = 0
            base = lst.index(x)
            while lst.count(x) != 0:
                lst[lst.index(x)] += "_"+str(cnt)
                cnt +=1
            lst[base] = x
        return lst


class Solution(object):
    @staticmethod
    def fix_line(line,start,end):
        if line.startswith("DUT"):
            return line.strip()
        temp = line[start:end]
        temp = re.sub(r'\s+','_',temp).strip('_')
        line = ''.join((line[:start],temp,line[end:]))
        return line.strip()

    @staticmethod
    def get_des_N(line):
        return line.index('Test Description'), line.index('Index')

    @staticmethod
    def get_Pat(ID,Des,Pin):
        return '_'.join((ID,Des,Pin)).strip('_')

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

        if str(Value).isalnum():
            Value = '{:.3f}'.format(Value)
        if Unit == "":
            Unit = "-"
        return Value,High,Low,Unit

    @staticmethod
    def Unit_change(before, after, number):
        if number == r'-' or number is np.nan or number == '' :
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
            '0': 0,
        }

        if before[0] in Udic:
            before_U = Udic[before[0]]

        if after[0] in Udic:
            after_U = Udic[after[0]]

        number = float(number) * 10 ** (before_U - after_U)

        return number


def tip():
    print("log2csv.py [-sort/-org] [file1] [file2] ...")
    print("-sort 　:　DCテストが前　Functionテストが後")
    print("-nosort : テスト順番そのまま出力")
    exit()


def fix_DF(df):
    lst = list(df.columns)
    mul = [x for x in lst if lst.count(x) > 1]
    if len(mul) == 0:
        return df
    nu = []
    for x in lst:
        if x not in nu:
            nu.append(x)

    return df.groupby(df.columns,axis=1).agg(lambda x:x.iloc[:,-1]).loc[:,nu]


if __name__ == '__main__':
    start_t = time.time()
    main()
    end_t = time.time()

    print('Process took {:.3f} seconds'.format(end_t - start_t))
