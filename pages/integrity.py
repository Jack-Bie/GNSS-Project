import streamlit as st
import mpld3
import streamlit.components.v1 as components
import gnss as gn

if 'path' not in st.session_state:
    st.write('请先导入数据文件！')

else:
  path = 'Rinex/' + st.session_state['path']
  gc = gn.GnssCal(path)

  st.title("观测值完整性分析")

  with st.sidebar:
      option = st.radio("选择系统",('GPS系统','BDS系统'))
      option = 'G' if option == 'GPS系统' else 'C'

  tab1, tab2,tab3 = st.tabs(["📈 静态图","📈 可交互图", "🗃 数据表"])

  integrity = gc.integrity()
  y = {'G':['L1(%)', 'L2(%)','L5(%)','L1+L2(%)'],'C':['B1(%)', 'B2b(%)', 'B3(%)','B1+B2b+B3(%)']}
  ax = integrity[option].plot(x='prn', y=y[option],kind='bar')
  # # 添加图例和标题
  ax.legend(y[option])
  fig_html = mpld3.fig_to_html(ax.get_figure())
  with tab1:
    st.write('完整性分析柱状图')
    tab1.pyplot(ax.get_figure())
  with tab2:
    st.write("可交互图")
    components.html(fig_html, height=600)
  with tab3:
    st.write('完整性分析数据表')
    tab3.dataframe(integrity[option])