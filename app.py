import streamlit as st
import re

st.set_page_config(
    page_title="数字分析工具",
    page_icon="🔢",
    layout="centered"
)

st.title("🔢 数字分析工具")


# =========================
# 基础函数
# =========================

def parse_numbers(text):
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    if file is None:
        return []

    data = file.getvalue()

    for enc in ["utf-8", "utf-8-sig", "gb18030", "gbk"]:
        try:
            return parse_numbers(data.decode(enc))
        except:
            pass

    return []


def format_txt(nums):
    nums = sorted(set(nums))
    lines = []

    for i in range(0, len(nums), 10):
        lines.append(" ".join(nums[i:i + 10]))

    return "\n".join(lines)


def txt_bytes(nums):
    return format_txt(nums).encode("utf-8-sig")


def size_shape(num):
    return "".join(
        "大" if int(x) >= 5 else "小"
        for x in num
    )


def parity_shape(num):
    return "".join(
        "奇" if int(x) % 2 == 1 else "偶"
        for x in num
    )


def repeat_type(num):
    count = len(set(num))

    if count == 3:
        return "三不同"
    elif count == 2:
        return "二同"
    else:
        return "三同"


SIZE_SHAPES = [
    "大大大",
    "大大小",
    "大小大",
    "大小小",
    "小大大",
    "小大小",
    "小小大",
    "小小小",
]

PARITY_SHAPES = [
    "奇奇奇",
    "奇奇偶",
    "奇偶奇",
    "奇偶偶",
    "偶奇奇",
    "偶奇偶",
    "偶偶奇",
    "偶偶偶",
]


# =========================
# 功能选择
# =========================

mode = st.selectbox(
    "选择功能",
    [
        "交集 / 不交集",
        "A分别与多个文件交集",
        "合并去重",
        "形态筛选",
        "二同 / 三同 / 三不同",
    ]
)


# =========================
# 1. 交集 / 不交集
# =========================

if mode == "交集 / 不交集":

    st.subheader("两个附件交集 / 不交集")

    file_a = st.file_uploader(
        "上传文件 A",
        type=["txt"],
        key="a"
    )

    file_b = st.file_uploader(
        "上传文件 B",
        type=["txt"],
        key="b"
    )

    if file_a and file_b:

        A = set(read_upload(file_a))
        B = set(read_upload(file_b))

        inter = sorted(A & B)
        a_only = sorted(A - B)
        b_only = sorted(B - A)
        non_inter = sorted((A - B) | (B - A))

        st.write(f"A：**{len(A)} 注**")
        st.write(f"B：**{len(B)} 注**")
        st.write(f"交集：**{len(inter)} 注**")
        st.write(f"A独有：**{len(a_only)} 注**")
        st.write(f"B独有：**{len(b_only)} 注**")
        st.write(f"不交集合并：**{len(non_inter)} 注**")

        left = len(A) + len(B)
