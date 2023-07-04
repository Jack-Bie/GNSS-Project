import streamlit as st
import gnss as gn

def clear_cache():
  if 'path' not in st.session_state:
    pass
  else:
    del st.session_state['path']

st.title("导入RINEX观测值文件")
file_path = st.file_uploader(label='上传RINEX o文件' ,key='load')

with st.spinner("加载中，请稍候..."):
  try:
    st.session_state['path'] = file_path.name
    path = './Rinex/'+st.session_state['path']
    gc = gn.GnssCal(path)
    tab1, tab2 ,tab3 = st.tabs(['GPS','BDS','GLONASS'])
    tab1.write(gc.getDataFrame('G'))
    tab2.write(gc.getDataFrame('C'))
    tab3.write(gc.getDataFrame('R'))
    st.success(f"文件{st.session_state['path']}加载成功！")
  except:
    if 'path' not in st.session_state:
      pass
    else:
      path = './Rinex/'+st.session_state['path']
      gc = gn.GnssCal(path)
      tab1, tab2 ,tab3 = st.tabs(['GPS','BDS','GLONASS'])
      tab1.write(gc.getDataFrame('G'))
      tab2.write(gc.getDataFrame('C'))
      tab3.write(gc.getDataFrame('R'))
      st.success(f"文件{st.session_state['path']}加载成功！")