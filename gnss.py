import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



# 根据年月日时分秒计算简化儒略日
def cal2jd(time:str) -> float:
    '''
    年月日时分秒转儒略日
    time 字符串长度为43，年月日时分各占6为，秒占13位
    '''
    length = len(time)
    if length != 43 and length != 27:
      raise ValueError('参数不是指定格式！')
    Y = int(time[0:6].replace(' ','')) if length == 43 else int(time[0:4].replace(' ',''))
    M = int(time[6:12].replace(' ','')) if length == 43 else int(time[5:7].replace(' ',''))
    D = int(time[12:18].replace(' ','')) if length == 43 else int(time[8:10].replace(' ',''))
    h = int(time[18:24].replace(' ','')) if length == 43 else int(time[11:13].replace(' ',''))
    m = int(time[24:30].replace(' ','')) if length == 43 else int(time[14:16].replace(' ',''))
    s = float(time[30:43].replace(' ','')) if length == 43 else float(time[17:-1].replace(' ',''))
    JD = 1721013.5 + 367*Y - int(7/4*(Y+int((M+9)/12))) +\
        D + (h + m/60 + s/3600)/24 + int(275*M/9)
    return  JD-2400000.5



# 根据儒略日计算GPS周和GPS周内秒
def mjd2gpst(mjd:float, year:int=0)->tuple:
    '''
    将简化儒略日转化为GPS时间,即GPS周和GPS周内秒

    参数:
    mjd -- 简化儒略日
    year -- 如果考虑GPS周的翻转问题则需要,目前暂不考虑,传入0即可

    返回值:
    (week,second) -- 元组,week表示GPS周,second表示GPS周内秒
    '''
    # 44244是1980年1月6日0时的简化儒略日
    e = mjd - 44244
    # 获取GPS周和周秒
    week = int(e // 7)
    e = e - week * 7
    second = e * 86400
    # 考虑GPS周的翻转问题
    # if week >=1024:
    #     rollovers = (year -1980) //20 +1
    #     week += rollovers *1024
    return (week, second)



class Rinex_o():
  def __init__(self, path):
    if path[-1] not in ['o', 'O']:
      raise ValueError("请导入Rinex观测值文件'*.??o'格式")
    with open(path, 'r') as f :
      self.__readHeader(f)
    
    with open(path, 'r') as f :
      self.__data = self.__readData(f)

    if path[-1] == 'o':
      dif_gps_week = mjd2gpst(cal2jd(self.last_obs))[0] - mjd2gpst(cal2jd(self.first_obs))[0]
      dif_gps_second = mjd2gpst(cal2jd(self.last_obs))[1] - mjd2gpst(cal2jd(self.first_obs))[1]
      self.obs_time = dif_gps_week*7*3600 + dif_gps_second  #计算观测时长



  # 读取文件头
  def __readHeader(self, f):
    self.obs_type = self.__getObsType(f)
    self.__getTime(f)
    self.obs_type_num = self.__getObsNum(f)



  # 第1步
  # 将 SYS / # / OBS TYPES 每个观测类型分开返回列表
  @staticmethod
  def __splitObsType(line,f):
    obs_num = int(line[3:6].replace(' ',''))
    result = []
    if obs_num <= 13:   #一行最多能写13个观测值类型
      for i in range(0, 4*obs_num, 4):
        result.append(line[6+i:10+i].replace(' ',''))   #A4，每4位字符一个观测值类型（包含一个空格），replace方法去掉空格
    else:
      for i in range(0, 4*13, 4): #超过13个后分两行写，这是第一行
        result.append(line[6+i:10+i].replace(' ',''))
      line = f.readline()
      for i in range(0, 4*(obs_num-13)): #这是第二行
        result.append(line[6+i:10+i].replace(' ',''))
    return result, line #多返回一个line是考虑到观测值类型占两行的情况


  # 读取观测值类型，返回字典
  def __getObsType(self, f):
    tmp_dic = {}
    sys_list = []
    while True:
      line = f.readline()
      if line[70:79] == 'OBS TYPES':
        while line[0] in ['G','R','C','E']:
          sys_list.append(line[0])
          tmp_dic[line[0]],line = self.__splitObsType(line, f)
          line = f.readline()
      if line[60:68] == 'INTERVAL':
        self.interval = float(line[0:10].replace(' ','')) #获取观测值的采样间隔
        self.system = tuple(sys_list)
        return tmp_dic



  # 第2步
  # 获取观测的开始时间和结束时间
  def __getTime(self, f):
      while True:
        line = f.readline()
        if line[60:77] == 'TIME OF FIRST OBS':
          self.first_obs = line[0:43]
        elif line[60:76] == 'TIME OF LAST OBS':
          self.last_obs = line[0:43]
          break
        elif line[60:73] == 'END OF HEADER':
          break



  # 第3 步
  # 将 PRN / # OF OBS 数据按系统分开，返回pandas的DataFrame
  def __splitObsTypeNum(self, line, f, sys):
    result = []
    tmp_list = []
    type_num = len(self.obs_type[sys])
    while line[3] == sys and line[60:74] == 'PRN / # OF OBS':
      if  type_num <=9:  #每行最多写9个观测值个数, 3X A1 I2 9I6
        tmp_list.append(line[3:6])  #读入prn
        for i in range(0, 6*type_num, 6):  #观测值个数（# OF OBS）的排列顺序根据观测值类型（OBS TYPES）排列
          tmp_list.append(int(line[6+i:12+i].replace(' ','')))  #读入数据
      else:
        tmp_list.append(line[3:6])  #读入prn
        for i in range(0, 6*9, 6):  #超过9个分两行写
          tmp_list.append(int(line[6+i:12+i].replace(' ','')))  #读入数据
        line = f.readline()
        for i in range(0, 6*(type_num-9), 6):
          tmp_list.append(int(line[6+i:12+i].replace(' ','')))
      line = f.readline()
      result.append(tmp_list)
      tmp_list = []
    data = pd.DataFrame(result, columns=['prn']+self.obs_type[sys])
    return data, line


  # 读取 PRN / # OF OBS 数据块，返回值是字典，键['G','R','C','E]
  def __getObsNum(self, f):
    tmp_dic = {}
    while True:
      line = f.readline()
      if len(line) < 3:
        break
      if line[60:75] == '# OF SATELLITES':
        self.obs_sat_num = int(line[0:6].replace(' ',''))
      while line[3] in ['G','R','C','E'] and line[60:74] == 'PRN / # OF OBS':
        tmp_dic[line[3]], line = self.__splitObsTypeNum(line, f, line[3])
      if line[60:73] == 'END OF HEADER':
        return tmp_dic



  # 读取观测值文件中的数据块
  def __readData(self, f):
    tmp_dic = {i:[] for i in self.system}
    line = f.readline()
    while line:
      if line[0] == '>' and len(line)>16:
        time = line[2:29]
        line = f.readline()
        while line[0] in ['G','R','C','E']:
          line = self.__getDataLines(tmp_dic[line[0]], time, line, f, line[0])
          if not line:
            return tmp_dic
      else:
        line = f.readline()
        if not line:
          return tmp_dic


  def __getDataLines(self, data_list, time, line, f, sys):
    '''读取数据块的一个历元数据'''
    type_num = len(self.obs_type[sys])
    while True:
      if line[0] != sys :
        return line
      tmp_list = [time, line[0:3]]
      #这个for循环处理一行数据
      for i in range(0, 16*type_num, 16):
        data = float(line[3+i:17+i].replace(' ',''))   #每一行数据的格式：A1 I2 F14.3 I1 I1
        if data == 0:
          tmp_list.append(None)  #空数据设置为None
        else:
          tmp_list.append(data)

      data_list.append(tmp_list)
      line = f.readline()
      if not line:
        break



  def getDataFrame(self, system):
    '''
    根据选择的系统类型，返回对应观测值文件数据表

    Arg:
    system:可选值'G'(GPS),'R'(GLONASS), 'C'(Beidou), 'E'(Galileo)
    '''
    if system not in ['G','R','C','E']:
      raise ValueError("参数不在可选值范围内！")
    else:
      return pd.DataFrame(self.__data[system], columns=['time', 'prn']+self.obs_type[system])



class GnssCal(Rinex_o):
  def __init__(self, path) -> None:
    super().__init__(path)
  


  def integrity(self):
    '''
    此完整性计算暂不考虑格洛纳斯和伽利略
    GPS的系统数据完整性主要分析的是L1，L2
    北斗的系统数据完整性三个频率均分析了

    返回完整性统计表
    '''
    if not self.obs_type_num:
      raise ValueError("o文件版本低于3.04，没有obs_type_num文件头！")
    integrity = {}
    gps_prn, bd_prn = self.obs_type_num['G'].loc[:,'prn'], self.obs_type_num['C'].loc[:,'prn']
    gps_integrity, bd_integrity = [],[]
    gps_data, bd_data = self.getDataFrame('G').iloc[:, 1:5], self.getDataFrame('C').iloc[:,1:5]

    for prn in gps_prn:
      gps = gps_data[gps_data['prn']==prn]
      all = gps.iloc[:,1:3].dropna().count().iloc[0]
      gps_integrity.append([prn]+list(gps.count())+[all])
    for prn in bd_prn:
      bd = bd_data[bd_data['prn']==prn]
      all = bd.iloc[:,1:4].dropna().count().iloc[0]
      bd_integrity.append([prn]+list(bd.count())+[all])
    
    gps_data_title = ['prn', '理论观测值个数','L1实际观测值个数', 'L2实际观测值个数','L5实际观测值个数','L1+L2']
    bd_data_title = ['prn','理论观测值个数','B1实际观测值个数', 'B2b实际观测值个数', 'B3实际观测值个数','B1+B2b+B3']
    gps_integrity = pd.DataFrame(gps_integrity, columns=gps_data_title)
    bd_integrity = pd.DataFrame(bd_integrity, columns=bd_data_title)

    g_Ni, b_Ni = gps_integrity.loc[:,'理论观测值个数'], bd_integrity.loc[:,'理论观测值个数']
    gps_per, bd_per = gps_integrity.iloc[:,2:].div(g_Ni,axis=0), bd_integrity.iloc[:,2:].div(b_Ni,axis=0)
    gps_per.columns = ['L1(%)','L2(%)', 'L5(%)', 'L1+L2(%)']
    bd_per.columns = ['B1(%)','B2b(%)', 'B3(%)', 'B1+B2b+B3(%)']

    integrity['G'] = pd.concat([gps_integrity,gps_per],axis=1)
    integrity['C'] = pd.concat([bd_integrity,bd_per],axis=1)
    return integrity



  def getLeap(self):
    '''
    计算周跳，返回嵌套字典{'G':dict_G, 'C':dict_C}
    '''
    #计算GPS所有观测到的卫星的MW组合观测值
    gps_MW = self.__calMW('G')
    #计算北斗所有观测到的卫星的MW组合观测值
    bd_MW = self.__calMW('C')
    return {'G':gps_MW, 'C':bd_MW}


  def __calMW(self, sys):
    '''计算单系统的MW组合'''
    g_f1, g_f2, c = self.__getConst(sys)
    title = {'G':['time', 'prn', 'C1C','C2W','L1C','L2W'],'C':['time', 'prn', 'C2I','C6I','L2I','L6I']}
    #提取L1,L2频段的伪距和相位观测值
    gps_data = self.getDataFrame(sys).loc[:,title[sys]].dropna()
    gps_MW = {}
    for prn in self.obs_type_num[sys].loc[:, 'prn']:
      data = gps_data[gps_data['prn']==prn]
      time = (data.loc[:,title[sys][0]]).copy()
      time.reset_index(drop=True, inplace=True)
      g_P1 = data.loc[:,title[sys][2]]
      g_P2 = data.loc[:,title[sys][3]]
      g_L1 = data.loc[:,title[sys][4]]
      g_L2 = data.loc[:,title[sys][5]]
      #计算MW组合观测值
      lambda_g = c/(g_f1-g_f2)
      g_MW = (lambda_g*(g_L1-g_L2)-1/(g_f1+g_f2)*(g_f1*g_P1+g_f2*g_P2)).copy()
      g_MW.reset_index(drop=True, inplace=True)
      
      leap = [0]
      #历元间求二次差寻找整周跳变点
      for i in range(1,len(g_MW)):
        leap.append(g_MW[i] - g_MW[i-1])
      tmp = leap[0]
      for i in range(1,len(leap)):
        tmp, leap[i] =leap[i], leap[i] - tmp

      gps_MW[prn] = pd.concat([time, g_MW],axis=1,ignore_index=True).copy()
      gps_MW[prn].reset_index(drop=True,inplace=True)
      gps_MW[prn] = pd.concat([gps_MW[prn], pd.Series(leap)],axis=1,ignore_index=True)
      gps_MW[prn].columns = ['time','MW','leap']
    return gps_MW



  def getSNR(self, sys):
    if sys not in ['G','C']:
      raise ValueError('参数sys可选值G或C')
    sgn = {'G':['S1C','S2W','S5X'],'C':['S2I','S7I','S6I']}
    if sgn[sys] != self.obs_type[sys][6:9]:
      raise ValueError('导入的o文件中没有信号类型的观测值')
    
    result = {}
    data = self.getDataFrame(sys)
    for prn in self.obs_type_num[sys].loc[:,'prn']:
      tmp = data[data['prn']==prn]
      result[prn] = tmp.loc[:,['time']+sgn[sys]].dropna()
      result[prn].reset_index(drop=True, inplace=True)

    return result



  def mutipath(self,sys):
    f1, f2, c = self.__getConst(sys) #lamda_f是MW组合中的lamda
    feature = {'G':['C1C','C2W','L1C','L2W'],'C':['C2I','C6I','L2I','L6I']}

    result = {}
    data = self.getDataFrame(sys)
    for prn in self.obs_type_num[sys].loc[:,'prn']:
      tmp = data[data['prn']==prn].loc[:,['time']+feature[sys]].dropna()
      P1 = tmp.loc[:,feature[sys][0]]
      P2 = tmp.loc[:,feature[sys][1]]
      L1 = tmp.loc[:,feature[sys][2]]
      L2 = tmp.loc[:,feature[sys][3]]
      MP1 = (P1-L1*c/f1)/2
      MP2 = (P2-L2*c/f2)/2
      result[prn] = pd.concat([tmp.loc[:,'time'], MP1, MP2], axis=1, ignore_index=True)
      result[prn].reset_index(drop=True, inplace=True)
      result[prn].columns = ['time','MP1','MP2']
    return result



  @staticmethod
  def __getConst(sys):
    #定义常量，频率
    c = 299792458   #光速
    g_f1 = 1575.42e6
    g_f2 = 1227.60e6
    # lambda_g = c/(g_f1-g_f2)
    b_f1 = 1561.098e6
    b_f2 = 1268.52e6
    # lambda_b = c/(b_f1-b_f2)
    return (g_f1, g_f2, c) if sys=='G' else (b_f1, b_f2, c)



if __name__ == '__main__':
  path = './Rinex/D045171B.23o'
  ofile = Rinex_o(path)
  # print(ofile.getDataFrame('G'))
  gc = GnssCal(path)
  integrity = gc.integrity()

  #绘制完整性分析图
  # integrity = gc.integrity()
  # ax_gps = integrity['G'].plot(x='prn', y=['L1(%)', 'L2(%)','L5(%)','L1+L2(%)'],kind='bar')
  # ax_bd = integrity['C'].plot(x='prn', y=['B1(%)', 'B2b(%)', 'B3(%)','B1+B2b+B3(%)'],kind='bar')
  # # 添加图例和标题
  # ax_gps.legend(['L1', 'L2', 'L5', 'L1+L2'])
  # ax_bd.legend(['B1', 'B2b', 'B3', 'B1+B2b+B3'])
  # # plt.legend()
  # plt.title('integrity analysis')
  # # 显示图形
  # plt.show()

  #绘制整周跳变图
  # leap = gc.getLeap()
  # leap_filter_error = leap['G']['G01']
  # leap_filter_error = leap_filter_error[np.abs(leap_filter_error['leap'])<10]
  # # ax_leap_g1 = leap['G']['G01'].plot(y='leap')
  # ax_leap_g2 = leap_filter_error.plot(y='leap')
  # plt.show()  

  #绘制信噪比图
  # sgn = gc.getSNR('G')
  # ax_sgn1 = sgn['G03'].plot(y='S1C')
  # plt.show()
  
  #绘制多路径图
  # mutipath = gc.mutipath('G')
  # ax_mp = mutipath['G01'].plot(y=['MP1','MP2'])
  # plt.show()
