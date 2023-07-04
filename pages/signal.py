import streamlit as st
import mpld3
import streamlit.components.v1 as components
import gnss as gn

if 'path' not in st.session_state:
    st.write('请先导入数据文件！')

else:
  st.title("信噪比分析")
  path = 'Rinex/' + st.session_state['path']
  fre = {'G':['S1C','S2W','S5X'],'C':['S2I','S7I','S6I']}
  gc = gn.GnssCal(path)
  with st.sidebar:
    sys = st.radio("选择系统",('GPS系统','BDS系统'))
    sys = 'G' if sys == 'GPS系统' else 'C'
    sgn = gc.getSNR(sys)
    prn = st.selectbox(
      '选择卫星prn号',
      options=list(sgn.keys())
    )
  tab1, tab2, tab3, tab4 = st.tabs(fre[sys]+['数据表'])
  with tab1:
    st.write(f"信噪比{fre[sys][0]}")
    ax = sgn[prn].plot(y=fre[sys][0])
    fig_html = mpld3.fig_to_html(ax.get_figure())
    components.html(fig_html, height=600)
  with tab2:
    st.write(f"信噪比{fre[sys][1]}")
    ax = sgn[prn].plot(y=fre[sys][1])
    fig_html = mpld3.fig_to_html(ax.get_figure())
    components.html(fig_html, height=600)
  with tab3:
    st.write(f"信噪比{fre[sys][2]}")
    ax = sgn[prn].plot(y=fre[sys][2])
    fig_html = mpld3.fig_to_html(ax.get_figure())
    components.html(fig_html, height=600)
  with tab4:
    st.write(f"信噪比数据表")
    st.write(sgn[prn])



