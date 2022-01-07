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
    ed_flag  = 0
    dut_flag = 0
    desSNo   = 0
    desENo   = -1
    patBin   = re.compile(r'DUT (\d+) : (\w+) :')
    out      = open("temp.csv","w+")

    with open(file, 'rb') as f:

        for line in f:
            line = str(line,'utf-8')
            if not line:
                break
            elif 'ALARM_FAIL' in line:
                temp = line.strip().split()
                Res.set_alarm(temp[0],temp[-1],Pat,Value)
                continue
            if "Start" in line:
                Res = Test_data()
                continue
            elif re.match(r'Test ID\s+Test Description\s+',line):
                desSNo, desENo = Pro.get_des_N(line)
                continue
            elif "Slot Number" in line:
                temp = line.split(":")
                tem_wno = temp[-1].strip()
                dut_flag = 1
            elif dut_flag == 1:
                dut_flag = 0
                temp = line.strip().split()
                for x in temp:
                    p = re.search(r"DUT(\d+):(\d+),(\d+)",x)
                    Res.Input_Value(p.group(1), "WNO",  tem_wno)
                    Res.Input_Value(p.group(1), "XADR", p.group(2))
                    Res.Input_Value(p.group(1), "YADR", p.group(3))
            
            line = Pro.fix_line(line,desSNo,desENo)

            if not re.match(r'\d+\s+', line):
                pb = patBin.match(line)
                if pb and "NONE" not in line:
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
                Dut, Pin = data[-2:]
                Pin = Pin.replace(r'-----', "")
                Pat = Pro.get_Pat(ID, Des, Pin)
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[4:7]+[Pat])
                flag = "DC"
            elif len_data == 8:
                ID, Des = data[:2]
                Dut = data[-1]
                Pin = ""
                Pat = Pro.get_Pat(ID, Des, Pin)
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[4:7]+[Pat])
                flag = "DC"
            elif len_data == 7:
                Dut, Pin = data[-2:]
                Pin = Pin.replace(r'-----', "")
                Pat = Pro.get_Pat(ID, Des, Pin)
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[2:5]+[Pat])
                flag = "DC"
            elif len_data == 6:
                Pin = ""
                Dut = data[-1]
                Pat = Pro.get_Pat(ID, Des, Pin)
                Value, H_Limit, L_Limit, Unit = Pro.get_Value(data[2:5]+[Pat])
                flag = "DC"
            elif len_data == 5:
                ID, Des = data[:2]
                Value, Dut = data[-2:]
                Pin = ""
                Pat = Pro.get_Pat(ID, Des, Pin)
                flag = "FT"
            elif len_data == 3:
                Value, Dut = data[-2:]
                Pin = ""
                flag = "FT"
            else:
                print("Error : Lost line ", line)
                continue

            if flag == "FT":
                H_Limit, L_Limit, Unit = "", "", ""

            T.Input_Data(Pat,H_Limit,L_Limit,Unit,flag)
            Res.Input_Value(Dut, Pat, Value)
            if "FAIL" in line:
                Res.Input_failT(Dut,Pat)

    Res.finish(out)
    del Res
    out.close()

    ind = ""
    base = pd.DataFrame()
    with open("temp.csv") as f:
        for line in f:
            if not line:
                break
            if not ind:
                ind = line
                continue
            else:
                temp_col = ["Wno", "X", "Y", "P/F", "DUT", "FailTest", "BIN", "Alarm"] + ind.strip().split(',')[8:]
                td = line.strip().split(',')
                temp = pd.DataFrame(td, columns=['.'.join(td[:3])], index=Pro.fix_Index(temp_col))
                ind = ""

                base = pd.concat([base, temp], axis=1)

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
    Alarm = []

    def Input_Value(self,Dut,Pat,Value):
        if Dut not in self.D_lst:
            self.D_lst.append(Dut)
            self.Data.append([])
            self.T_lst.append([])
            self.Wno.append("0")
            self.XADR.append("0")
            self.YADR.append("0")
            self.PF.append("0")
            self.FailT.append("")
            self.Bin.append("")
            self.Alarm.append("0")

        D_index = self.D_lst.index(Dut)
        if Pat not in ["WNO","XADR","YADR"]:
            self.Data[D_index].append(Value)
            self.T_lst[D_index].append(str(Test_class.T_dic[Pat][0]))

        if "WNO" in Pat and self.Wno[D_index] == "0":
            self.Wno[D_index]  = '{:.0f}'.format(float(Value))
        elif "XADR" in Pat and self.XADR[D_index] == "0":
            self.XADR[D_index] = '{:.0f}'.format(float(Value))
        elif "YADR" in Pat and self.YADR[D_index] == "0":
            self.YADR[D_index] = '{:.0f}'.format(float(Value))

    def Input_failT(self,Dut,Pat):
        D_index = self.D_lst.index(Dut)
        self.FailT[D_index] = Pat

    def set_res(self,Dut,PF,Bin):
        D_index = self.D_lst.index(Dut)
        if PF == "PASS" or not self.FailT[D_index]:
            self.FailT[D_index] = "0"
        self.PF[D_index] = PF
        self.Bin[D_index] = Bin

    def set_alarm(self,Dut,pin,Pat,Value):
        self.Alarm[self.D_lst.index(Dut)] = "|".join([pin,Pat,Value])

    def finish(self,f):
        for dut in self.D_lst:
            d = self.D_lst.index(dut)
            f.writelines(','.join(["","","","","","","",""]+self.T_lst[d]))
            f.writelines("\n")
            f.writelines(','.join([self.Wno[d],self.XADR[d],self.YADR[d],self.PF[d],dut,self.FailT[d],self.Bin[d],self.Alarm[d]]
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
        self.Alarm.clear()


class Test_class(object):
    T_dic = {}
    T_key = {}
    cnt = 0

    def Input_Data(self,Pat,High,Low,Unit="",Type=""):
        if Pat not in self.T_dic:
            temp = Pat.split('_')
            self.T_dic[Pat] = [str(self.cnt),str(temp[0]),'_'.join(temp[1:]),str(High),str(Low),Unit,Type]
            self.T_key[str(self.cnt)] = Pat
            self.cnt += 1
        self.T_dic[Pat][3] = str(High) if self.T_dic[Pat][3] == "-" else self.T_dic[Pat][3]
        self.T_dic[Pat][4] = str(Low)  if self.T_dic[Pat][4] == "-" else self.T_dic[Pat][4]
        self.T_dic[Pat][5] = str(Unit) if self.T_dic[Pat][5] == "-" else self.T_dic[Pat][5]
        
            

    def final(self,df):
        lst = list(df.index)
        temp = []
        for i in range(len(lst)):
            if lst[i] in ["Wno","X","Y","P/F","DUT","FailTest","BIN","Alarm"]:
                temp.append(["","","","","",""])
                continue
            if '.' in lst[i]:
                lst[i] = self.T_key[re.sub(r'\.\d+','',lst[i])]
            else:
                lst[i] = self.T_key[lst[i]]
            temp.append(self.T_dic[lst[i]][1:])

        return pd.concat([pd.DataFrame(lst,index=df.index),
                          pd.DataFrame(temp,index=df.index,columns=["ID","Des","H-Limit","L-Limit","Unit","type"]),
                          df],axis=1)

    def output(self):
        pd.DataFrame.from_dict(self.T_dic).T.to_csv("Tlist.csv",header=0)


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
    def fix_Index(lst):
        if len(set(lst)) == len(lst):
            return lst
        temp = []
        for x in lst:
            if str(x) not in temp:
                temp.append(str(x))
            else:
                cnt = 1
                while True:
                    if str(x) + "." + str(cnt) in temp:
                        cnt += 1
                    else:
                        temp.append(str(x) + "." + str(cnt))
                        break
        return temp

    @staticmethod
    def fix_list(lst):
        temp = []
        for x in list(lst):
            if x not in temp:
                temp.append(x)
        return temp

    @staticmethod
    def getID(lst):
        return '.'.join(str(int(x)) for x in lst)

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
        Value, High, Low ,Pat = data

        Value, Value_U = self.get_Unit(Value)
        High, High_U   = self.get_Unit(High)
        Low, Low_U     = self.get_Unit(Low)

        if Low_U:
            Unit = Low_U
        elif High_U:
            Unit = High_U
        else:
            Unit = Value_U

        if Test_class.T_dic.get(Pat,0):
            Unit = Test_class.T_dic[Pat][-2] if Test_class.T_dic[Pat][-2] != "-" else Unit

        Value = self.Unit_change(Value_U, Unit, Value)
        High  = self.Unit_change(High_U, Unit, High)
        Low   = self.Unit_change(Low_U, Unit, Low)

        try:
            Value = '{:.4f}'.format(float(Value))
        except ValueError:
            pass

        if Unit == "":
            Unit = "-"
        return Value,High,Low,Unit

    @staticmethod
    def Unit_change(before, after, number):
        if number == r'-' or number is np.nan or not number or number == 0:
            return number
        if before == after or not before or not after:
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

"""
作成日付：　2021/11/01

修正歴 :  2021/11/08 Alarm_Fail抽出ファッション追加
         2021/11/08 大CSVファイル読み取りファッション追加
         2021/11/08 CHIPID読み取りファッション改善
         2021/11/09 大CSVファイル読み取りファッション改善
         2021/11/09 単位変換ファッション修正
         2021/11/11 コーディング順番ミス修正
         2022/01/07 Unit選択ミス修正
"""
