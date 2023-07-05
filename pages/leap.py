import streamlit as st
import numpy as np
import pandas as pd
import mpld3
import streamlit.components.v1 as components
import gnss as gn

if 'path' not in st.session_state:
    st.write('请先导入数据文件！')

else:
  st.title("周跳分析")
  path = 'Rinex/' + st.session_state['path']
  gc = gn.GnssCal(path)
  with st.sidebar:
    sys = st.radio("选择系统",('GPS系统','BDS系统'))
    sys = 'G' if sys == 'GPS系统' else 'C'
    leap = gc.getLeap()
    prn = st.selectbox(
      '选择卫星prn号',
      options=list(leap[sys].keys())
    )
  tab1, tab2, tab3 = st.tabs(['周跳图(含粗差)','周跳图(不含粗差)','周跳探测数据表'])
  with tab1:
    st.write(f"卫星{prn}周跳探测的粗差历元表")
    tmp = leap[sys][prn]
    error = tmp[np.abs(tmp['leap'])>20]
    st.write(error)
    st.write(f"总计有{error.count()[-1]}个粗差历元")
    with st.spinner("加载中，请稍候..."):
      st.write(f"卫星{prn}的周跳图（含粗差）")
      ax = leap[sys][prn].plot(y='leap')
      fig_html = mpld3.fig_to_html(ax.get_figure())
      components.html(fig_html, height=600)

  with tab2:
    tmp = leap[sys][prn]
    tmp = tmp[np.abs(tmp['leap'])<10]
    st.write(f"卫星{prn}周跳探测的周跳历元表")
    st.write(tmp[np.abs(tmp['leap'])>1])
    st.write(f"总计有{tmp[np.abs(tmp['leap'])>1].count()[-1]}个周跳历元")
    with st.spinner("加载中，请稍候..."):
      st.write(f"卫星{prn}的周跳图（不含粗差）")
      ax = tmp.plot(y='leap')
      fig_html = mpld3.fig_to_html(ax.get_figure())
      components.html(fig_html, height=600)

  with tab3:
    st.write(f"卫星{prn}周跳探测结果表")
    all = leap[sys][prn].count()[-1]
    res = pd.DataFrame([[prn,all, all-error.count()[-1],tmp[np.abs(tmp['leap'])>1].count()[-1]]],columns = ['卫星prn号','总历元数','有效历元数','周跳数'])
    st.write(res)
    st.write(f"卫星{prn}周跳探测的数据表")
    st.write(leap[sys][prn])
