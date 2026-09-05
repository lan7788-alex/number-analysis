import streamlit as st

st.set_page_config(page_title="数字分析工作台", layout="centered")

st.title("数字分析工作台")

st.write("第一版测试：形态取号")

number = st.text_input("请输入三位数字", value="992", max_chars=3)

size_position = st.selectbox(
    "大小取位",
    ["百十", "百个", "十个"]
)

parity_position = st.selectbox(
    "奇偶取位",
    ["百十", "百个", "十个"]
)

def size_type(d):
    return "大" if int(d) >= 5 else "小"

def parity_type(d):
    return "奇" if int(d) % 2 == 1 else "偶"

if st.button("开始分析"):
    if len(number) != 3 or not number.isdigit():
        st.error("请输入000到999之间的三位数字")
    else:
        size_shape = "".join(size_type(d) for d in number)
        parity_shape = "".join(parity_type(d) for d in number)

        st.success("分析完成")
        st.write("母号：", number)
        st.write("大小形态：", size_shape)
        st.write("奇偶形态：", parity_shape)
        st.write("大小取位：", size_position)
        st.write("奇偶取位：", parity_position)
