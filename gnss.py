import pandas as pd

class Rinex_o():
  def __init__(self, path):
    if path[-1] != 'o':
      raise ValueError("请导入Rinex观测值文件'*.??o'格式")
    self.__obsType(path)
    self.__getObsData(path)

  def getDataFrame(self, system):
    '''
    根据选择的系统类型，返回对应观测值文件数据表

    Arg:
    system:可选值'G'(GPS),'R'(GLONASS), 'C'(Beidou), 'E'(Galileo)
    '''
    if system not in ['G','R','C','E']:
      raise ValueError("参数不在可选值范围内！")
    elif system=='G':
      return pd.DataFrame(self.__getDataFrame(self.g_dict, system))
    elif system=='R':
      return pd.DataFrame(self.__getDataFrame(self.r_dict, system))
    elif system=='C':
      return pd.DataFrame(self.__getDataFrame(self.c_dict, system))
    elif system=='E':
      return pd.DataFrame(self.__getDataFrame(self.e_dict, system))

  # 读取观测值文件中的 SYS / # / OBS TYPES 部分 
  # 读取观测值文件中的 PRN / # OF OBS 部分
  def __obsType(self, path):
    with open(path, 'r') as f:
      while True:
        line = f.readline()
        if line[70:79] == 'OBS TYPES':
          if line[0] == 'G' :
            self.g_dict = self.__splitObsType(line, f) 
          elif line[0] == 'R' :
            self.r_dict = self.__splitObsType(line, f)
          elif line[0] == 'C' :
            self.c_dict = self.__splitObsType(line, f)
          elif line[0] == 'E' :
            self.e_dict = self.__splitObsType(line, f)

        elif line[66:74] == '# OF OBS':
          self.__splitObsNum(line[3:6], line, f) 

        elif line[60:73] == 'END OF HEADER':
          break

        else:
          continue


  # 读取观测值文件中的数据块
  def __getObsData(self, path):
    with open(path, 'r') as f:
      line = f.readline()
      while line:
        if line[0] == '>':
          time = line[2:29]
          line = f.readline()
          while line[0] != '>':
            if line[0] == 'G':
              self.__getDataLine(self.g_dict, line, time, 'G')
            elif line[0] == 'R':
              self.__getDataLine(self.r_dict, line, time, 'R')
            elif line[0] == 'C':
              self.__getDataLine(self.c_dict, line, time, 'C')
            elif line[0] == 'E':
              self.__getDataLine(self.e_dict, line, time, 'E')
            line = f.readline()
            if not line :
              break
        else:
          line = f.readline()


  # 将一行 SYS / # / OBS TYPES 数据分开，写成字典
  def __splitObsType(self, line, f):
    obs_dict = {}
    obs_dict[line[0]] = []
    obs_dict['time'] = []
    obs_dict['obs_types'] = []
    obs_dict['obs_num'] = int(line[3:6].replace(' ',''))
    if obs_dict['obs_num'] <= 13:   #一行最多能写13个观测值类型
      for i in range(0, 4*obs_dict['obs_num'], 4):
        obs_dict[line[6+i:10+i].replace(' ','')] = []   #A4，每4位字符一个观测值类型（包含一个空格），replace方法去掉空格
        obs_dict['obs_types'].append(line[6+i:10+i].replace(' ',''))
    else:
      for i in range(0, 4*13, 4): #超过13个后分两行写，这是第一行
        obs_dict[line[6+i:10+i].replace(' ','')] = []
        obs_dict['obs_types'].append(line[6+i:10+i].replace(' ',''))
      tmp = obs_dict['obs_num'] - 13
      line = f.readline()
      for i in range(0, 4*tmp): #这是第二行
        obs_dict[line[6+i:10+i].replace(' ','')] = []
        obs_dict['obs_types'].append(line[6+i:10+i].replace(' ',''))
    return obs_dict


  # 将一行 PRN / # OF OBS 数据分开，写成字典
  def __splitObsNum(self, prn, line, f):
    if prn[0] == 'G':
      self.g_dict[prn] = self.__getObsNum(self.g_dict, line, f)
    elif prn[0] == 'R':
      self.r_dict[prn] = self.__getObsNum(self.r_dict, line, f)
    elif prn[0] == 'C':
      self.c_dict[prn] = self.__getObsNum(self.c_dict, line, f)
    elif prn[0] == 'E':
      self.e_dict[prn] = self.__getObsNum(self.e_dict, line, f)


  @staticmethod
  def __getDataLine(obs_dict, line, time, prn):
    '''读取数据块的一行数据'''
    obs_dict[prn].append(line[0:3])
    obs_dict['time'].append(time)
    for (i,key) in zip(range(0, 16*len(obs_dict['obs_types']), 16), obs_dict['obs_types']):
      data = line[3+i:17+i].replace(' ','')   #每一行数据的格式：A1 I2 F14.3 I1 I1
      if len(data) == 0:
        obs_dict[key].append(None)  #空数据设置为None
      else:
        obs_dict[key].append(float(data))


  @staticmethod
  def __getObsNum(dic, line, f):
    '''读取一个prn的所有观测值个数'''
    obs_num_dic = {}
    if dic['obs_num'] <=9:  #每行最多写9个观测值个数
      for (i,key) in zip(range(0, 6*dic['obs_num'], 6), dic['obs_types']):  #观测值个数（# OF OBS）的排列顺序根据观测值类型（OBS TYPES）排列
        obs_num_dic[key] = int(line[6+i:12+i].replace(' ',''))
    else:
      for (i,key) in zip(range(0, 6*9, 6), dic['obs_types'][0:9]):  #超过9个分两行写
        obs_num_dic[key] = int(line[6+i:12+i].replace(' ',''))
      line = f.readline()
      for (i, key) in zip(range(0, 6*(dic['obs_num']-9), 6), dic['obs_types'][9:]):
        obs_num_dic[key] = int(line[6+i:12+i].replace(' ',''))
    return obs_num_dic


  @staticmethod
  def __getDataFrame(obs_dict, system):
    '''定义表头为table_title的观测值文件表'''
    tmp = {}
    table_title = ['time', system] + obs_dict['obs_types']
    for key in table_title:
      tmp[key] = obs_dict[key]
    return tmp



if __name__ == '__main__':
  path = './Rinex/D045171B.23o'
  ofile = Rinex_o(path)
  df = ofile.getDataFrame('G')
  print(df)
  # df.to_excel ('test.xlsx')
  
