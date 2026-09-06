import streamlit as st
import re
from io import StringIO

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
    """从文本中提取000-999三位组合"""
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    if file is None:
        return []
    data = file.getvalue()

    for enc in ["utf-8", "gb18030", "gbk"]:
        try:
            text = data.decode(enc)
            return parse_numbers(text)
        except:
            pass

    return []


def format_txt(nums):
    nums = sorted(set(nums))
    lines = []

    for i in range(0, len(nums), 10):
        lines.append(" ".join(nums[i:i+10]))

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
        "奇" if int(x) % 2 else "偶"
        for x in num
    )


def repeat_type(num):
    n = len(set(num))

    if n == 3:
        return "三不同"
    elif n == 2:
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
        "合并去重",
        "形态筛选",
        "二同 / 三同 / 三不同",
    ]
)


# =========================
# 1 交集不交集
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
        right = 2 * len(inter) + len(non_inter)

        if left == right:
            st.success(
                f"闭环正确：{len(A)} + {len(B)} "
                f"= 2×{len(inter)} + {len(non_inter)} "
                f"= {left} √"
            )
        else:
            st.error("闭环失败，请检查数据")

        st.download_button(
            "下载交集",
            txt_bytes(inter),
            "交集.txt",
            "text/plain"
        )

        st.download_button(
            "下载A独有",
            txt_bytes(a_only),
            "A独有.txt",
            "text/plain"
        )

        st.download_button(
            "下载B独有",
            txt_bytes(b_only),
            "B独有.txt",
            "text/plain"
        )

        st.download_button(
            "下载不交集合并",
            txt_bytes(non_inter),
            "不交集合并.txt",
            "text/plain"
        )


# =========================
# 2 合并去重
# =========================

elif mode == "合并去重":

    st.subheader("两个附件合并去重")

    file_a = st.file_uploader(
        "上传文件 A",
        type=["txt"],
        key="merge_a"
    )

    file_b = st.file_uploader(
        "上传文件 B",
        type=["txt"],
        key="merge_b"
    )

    if file_a and file_b:

        A = set(read_upload(file_a))
        B = set(read_upload(file_b))

        merged = sorted(A | B)
        inter = A & B

        st.write(f"A：**{len(A)} 注**")
        st.write(f"B：**{len(B)} 注**")
        st.write(f"重复：**{len(inter)} 注**")
        st.write(f"合并去重：**{len(merged)} 注**")

        if len(A) + len(B) == len(merged) + len(inter):
            st.success("数量闭环正确 √")
        else:
            st.error("数量闭环失败")

        st.download_button(
            "下载合并去重结果",
            txt_bytes(merged),
            "合并去重.txt",
            "text/plain"
        )


# =========================
# 3 形态筛选
# =========================

elif mode == "形态筛选":

    st.subheader("按完整三位形态筛选")

    file = st.file_uploader(
        "上传原始组合TXT",
        type=["txt"],
        key="shape"
    )

    selected_size = st.multiselect(
        "要去掉的大小形态",
        SIZE_SHAPES
    )

    selected_parity = st.multiselect(
        "要去掉的奇偶形态",
        PARITY_SHAPES
    )

    if file:

        original = read_upload(file)

        remain = []
        removed = []

        for n in original:

            should_remove = (
                size_shape(n) in selected_size
                or
                parity_shape(n) in selected_parity
            )

            if should_remove:
                removed.append(n)
            else:
                remain.append(n)

        st.write(f"原始：**{len(original)} 注**")
        st.write(f"剩余：**{len(remain)} 注**")
        st.write(f"去掉：**{len(removed)} 注**")

        if len(remain) + len(removed) == len(original):
            st.success(
                f"闭环正确：{len(remain)} + "
                f"{len(removed)} = {len(original)} √"
            )
        else:
            st.error("闭环失败")

        st.download_button(
            "下载剩余组合",
            txt_bytes(remain),
            "筛选后剩余.txt",
            "text/plain"
        )

        st.download_button(
            "下载被去掉组合",
            txt_bytes(removed),
            "被去掉组合.txt",
            "text/plain"
        )


# =========================
# 4 重复类型分类
# =========================

elif mode == "二同 / 三同 / 三不同":

    st.subheader("二同 / 三同 / 三不同分类")

    file = st.file_uploader(
        "上传组合TXT",
        type=["txt"],
        key="repeat"
    )

    if file:

        original = read_upload(file)

        same23 = []
        different = []

        for n in original:

            tp = repeat_type(n)

            if tp in ["二同", "三同"]:
                same23.append(n)
            else:
                different.append(n)

        st.write(f"原始：**{len(original)} 注**")
        st.write(f"二同 + 三同：**{len(same23)} 注**")
        st.write(f"三不同：**{len(different)} 注**")

        if len(same23) + len(different) == len(original):
            st.success("数量闭环正确 √")
        else:
            st.error("数量闭环失败")

        st.download_button(
            "下载二同三同",
            txt_bytes(same23),
            "二同三同.txt",
            "text/plain"
        )

        st.download_button(
            "下载三不同",
            txt_bytes(different),
            "三不同.txt",
            "text/plain"
        )
