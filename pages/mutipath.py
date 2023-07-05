import numpy as np
import pandas as pd
import streamlit as st
import mpld3
import streamlit.components.v1 as components
import gnss as gn

if 'path' not in st.session_state:
    st.write('请先导入数据文件！')

else:
  st.title("多路径分析")
  path = 'Rinex/' + st.session_state['path']
  gc = gn.GnssCal(path)
  with st.sidebar:
    sys = st.radio("选择系统",('GPS系统','BDS系统'))
    sys = 'G' if sys == 'GPS系统' else 'C'
    mutipath = gc.mutipath(sys)
    prn = st.selectbox(
      '选择卫星prn号',
      options=list(mutipath.keys())
    )
  tab1, tab2 = st.tabs(['多路径图','多路径数据表'])
  with tab1:
    st.write(f"卫星{prn}多路径时序图")
    ax = mutipath[prn].plot(y=["MP1","MP2"])
    fig_html = mpld3.fig_to_html(ax.get_figure())
    components.html(fig_html, height=600)
  with tab2:
    MP1 = np.array(mutipath[prn].loc[:,'MP1'])
    MP1 = np.sqrt(np.mean(np.square(MP1)))
    MP2 = np.array(mutipath[prn].loc[:,'MP2'])
    MP2 = np.sqrt(np.mean(np.square(MP2)))
    st.write(f"卫星{prn}多路径均方根数据表")
    st.write(pd.DataFrame([[prn,MP1,MP2]],columns=['卫星prn','MP1 RMS','MP2 RMS']))
    st.write(f"卫星{prn}多路径分析数据表")
    st.write(mutipath[prn])