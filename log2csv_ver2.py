#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:Kin Ketsu
# Version 2 : 2021/11/01

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
    file  = files.pop(0)
    dataframe = log2csv(file)
    while files:
        f = files.pop(0)
        dataframe2 = log2csv(f)
        dataframe = pd.concat([dataframe,dataframe2],axis=1)
    lot = Pro.fix_list(dataframe.columns)
    dataframe = dataframe.groupby(dataframe.columns,axis=1).agg(lambda x : Pro.fix_DF(x))   # サンプルごとに纏めない場合、この行をコメントする。
    dataframe = T.final(dataframe.loc[:,lot])

    if flag == "-sort":
        dataframe = pd.concat([dataframe.loc[dataframe.loc[:, "type"] == "", :],
                               dataframe.loc[dataframe.loc[:, "type"] == "DC",:],
                               dataframe.loc[dataframe.loc[:, "type"] == "FT",:]],axis=0)

    dataframe.drop(['type'],axis=1).to_csv(file+".csv",index=False)


def log2csv(file):
    ed_flag = 0

    desSNo  = 0
    desENo  = -1
    patBin  = re.compile(r'DUT (\d+) : (\w+) :')
    out     = open("temp.csv","w+")

    with open(file, 'r') as f:

        for line in f.readlines():
            if not line:
                break
            elif 'ALARM_FAIL' in line:
                continue

            if re.match(r'Test ID\s+Test Description\s+',line):
                desSNo, desENo = Pro.get_des_N(line)
                Res = Test_data()
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
                    ed_flag = 0
                    Res.finish(out)
                    Res.clear()
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
                print("Error : Lost line ", line)
                continue

            Pat = Pro.get_Pat(ID,Des,Pin)
            if flag == "FT":
                H_Limit, L_Limit, Unit = "", "", ""

            T.Input_Data(Pat,H_Limit,L_Limit,Unit,flag)
            Res.Input_Value(Dut, Pat, Value)
            if "FAIL" in line:
                Res.Input_failT(Dut,Pat)

    Res.finish(out)
    del Res
    out.close()

    base = pd.DataFrame()

    try:
        temp = pd.read_csv("temp.csv",dtype=str,header=None,low_memory=False)

        for i in range(0,len(temp.index),2):
            temp_col = ["Wno","X","Y","P/F","DUT","FailTest","BIN"]+ list(temp.iloc[i,7:])
            temp_col = Pro.dropNaN(temp_col)
            temp_d = pd.DataFrame(Pro.dropNaN(list(temp.iloc[i+1,:])),
                                  index=Pro.fix_Index(temp_col),
                                  columns=['.'.join(temp.iloc[i+1,:3])])

            base = pd.concat([base,temp_d],axis=1)
    except:
        f = open("temp.csv", "r")
        data = f.readlines()
        f.close()
        maxn = max(len(x.strip().split(',')) for x in data)
        f = open("temp.csv", "w")
        for x in data:
            x = x.strip()
            num = maxn -len(x.split(','))
            f.writelines(x + ',' * num + "\n")
        f.close()

    temp = pd.read_csv("temp.csv",header=None,low_memory=False,na_values=np.nan,dtype=str)

    for i in range(0,len(temp.index),2):
        temp_col = ["Wno","X","Y","P/F","DUT","FailTest","BIN"]+ list(temp.iloc[i,7:])
        temp_col = Pro.dropNaN(temp_col)
        temp_d = pd.DataFrame(Pro.dropNaN(list(temp.iloc[i+1,:])),
                              index=Pro.fix_Index(temp_col),
                              columns=['.'.join(temp.iloc[i+1,:3])])

        base = pd.concat([base,temp_d],axis=1)

    os.remove("temp.csv")

    return base


class Test_data(object):
    D_lst = []
    Data  = []
    T_lst = []
    Wno   = []
    XADR  = []
    YADR  = []
    FailT = []
    PF    = []
    Bin   = []

    def Input_Value(self,Dut,Pat,Value):
        if Dut not in self.D_lst:
            self.D_lst.append(Dut)
            self.Data.append([])
            self.T_lst.append([])
            self.Wno.append("")
            self.XADR.append("")
            self.YADR.append("")
            self.PF.append("0")
            self.FailT.append("")
            self.Bin.append("")

        D_index = self.D_lst.index(Dut)
        self.Data[D_index].append(Value)
        self.T_lst[D_index].append(str(Test_class.T_dic[Pat][0]))

        if "WNO" in Pat:
            self.Wno[D_index]  = '{:.0f}'.format(float(Value))
        elif "XADR" in Pat:
            self.XADR[D_index] = '{:.0f}'.format(float(Value))
        elif "YADR" in Pat:
            self.YADR[D_index] = '{:.0f}'.format(float(Value))

    def Input_failT(self,Dut,Pat):
        D_index = self.D_lst.index(Dut)
        self.FailT[D_index] = Pat

    def set_res(self,Dut,PF,Bin):
        D_index = self.D_lst.index(Dut)
        if PF == "PASS":
            self.FailT[D_index] = "0"
        self.PF[D_index] = PF
        self.Bin[D_index] = Bin

    def finish(self,f):
        for dut in self.D_lst:
            d = self.D_lst.index(dut)
            f.writelines(','.join(["","","","","","",""]+self.T_lst[d]))
            f.writelines("\n")
            f.writelines(','.join([self.Wno[d],self.XADR[d],self.YADR[d],self.PF[d],dut,self.FailT[d],self.Bin[d]]
                                  +self.Data[d]))
            f.writelines("\n")

    def clear(self):
        self.D_lst.clear()
        self.Data.clear()
        self.T_lst.clear()
        self.Wno.clear()
        self.XADR.clear()
        self.YADR.clear()
        self.PF.clear()
        self.FailT.clear()
        self.Bin.clear()


class Test_class(object):
    T_dic = {}
    T_key = {}
    cnt = 0

    def Input_Data(self,Pat,High,Low,Unit="",Type=""):
        if Pat not in self.T_dic:
            self.T_dic[Pat] = [str(self.cnt),str(High),str(Low),Unit,Type]
            self.T_key[str(self.cnt)] = Pat
            self.cnt += 1

    def final(self,df):
        lst = list(df.index)
        temp = []
        for i in range(len(lst)):
            if lst[i] in ["Wno","X","Y","P/F","DUT","FailTest","BIN"]:
                temp.append(["","","",""])
                continue
            if '.' in lst[i]:
                lst[i] = self.T_key[re.sub(r'\.\d+','',lst[i])]
            else:
                lst[i] = self.T_key[lst[i]]
            temp.append(self.T_dic[lst[i]][1:])

        return pd.concat([pd.DataFrame(lst,index=df.index),
                          pd.DataFrame(temp,index=df.index,columns=["H-Limit","L-Limit","Unit","type"]),
                          df],axis=1)


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
    def fix_DF(df):
        if type(df) == pd.Series:
            return df

        base = pd.DataFrame(df.iloc[:, -1], index=df.index)
        if base.iloc[3, 0] == "PASS":
            flag = "P"
        else:
            flag = "F"
        for x in range(len(df.columns) - 2, -1, -1):
            if df.iloc[3, x] == "PASS":
                if flag == "P":
                    base.loc[base.iloc[:, 0] != "",base.columns[0]].combine_first(df.iloc[:, x])
                else:
                    base.loc[base.iloc[:, 0] != "",base.columns[0]] = df.iloc[:, x].combine_first(base.iloc[:, 0])
                    flag = "P"
            elif df.iloc[3, x] == "FAIL":
                base.iloc[:, 0].combine_first(df.iloc[:, x])
        return base.iloc[:, 0]

    @staticmethod
    def dropNaN(lst):
        temp = pd.Series(lst)
        temp.dropna(inplace=True)
        return temp.values

    @staticmethod
    def fix_Index(lst):
        if len(set(lst)) == len(lst):
            return lst
        temp = []
        for x in lst:
            if x not in temp:
                temp.append(str(x))
            else:
                cnt = 1
                while True:
                    if str(x)+'.'+str(cnt) in lst:
                        cnt += 1
                    else:
                        break
                temp.append(str(x)+'.'+str(cnt))
        return Solution.dropNaN(temp)

    @staticmethod
    def fix_list(lst):
        temp = []
        for x in list(lst):
            if x not in temp:
                temp.append(x)
        return temp

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
        pat  = re.search(r'^([-\d.]+)', data)
        num  = pat.group(0)
        Unit = data.replace(num, '')

        return float(num), Unit

    def get_Value(self,data):
        Value, High, Low = data

        Value, Value_U = self.get_Unit(Value)
        High, High_U   = self.get_Unit(High)
        Low, Low_U     = self.get_Unit(Low)

        if Low_U:
            Unit = Low_U
        elif Value_U and float(Value) != 0:
            Unit = Value_U
        else:
            Unit = High_U

        Value = self.Unit_change(Value_U, Unit, Value)
        High  = self.Unit_change(High_U, Unit, High)
        Low   = self.Unit_change(Low_U, Unit, Low)

        try:
            Value = '{:.3f}'.format(float(Value))
        except ValueError:
            pass

        if Unit == "":
            Unit = "-"
        return Value,High,Low,Unit

    @staticmethod
    def Unit_change(before, after, number):
        if number == r'-' or number is np.nan or number == '' or number == 0:
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
    print("-org : テスト順番そのまま出力")
    exit()


if __name__ == '__main__':
    start_t = time.time()
    T = Test_class()
    Pro = Solution()
    main()
    end_t = time.time()

    print(' The Process took {:.3f} seconds'.format(end_t - start_t))
