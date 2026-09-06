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
    """
    从文本中提取000-999的三位组合
    自动去重并升序
    """
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    """
    读取TXT，兼容常见编码
    """
    if file is None:
        return []

    data = file.getvalue()

    for enc in ["utf-8", "utf-8-sig", "gb18030", "gbk"]:
        try:
            text = data.decode(enc)
            return parse_numbers(text)
        except:
            pass

    return []


def format_txt(nums):
    """
    升序、每行10组
    """
    nums = sorted(set(nums))
    lines = []

    for i in range(0, len(nums), 10):
        lines.append(" ".join(nums[i:i + 10]))

    return "\n".join(lines)


def txt_bytes(nums):
    return format_txt(nums).encode("utf-8-sig")


def size_shape(num):
    """
    0-4=小
    5-9=大
    """
    return "".join(
        "大" if int(x) >= 5 else "小"
        for x in num
    )


def parity_shape(num):
    """
    奇数=奇
    偶数=偶
    """
    return "".join(
        "奇" if int(x) % 2 == 1 else "偶"
        for x in num
    )


def repeat_type(num):
    """
    三不同 / 二同 / 三同
    """
    unique_count = len(set(num))

    if unique_count == 3:
        return "三不同"
    elif unique_count == 2:
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
# 功能菜单
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


# ============================================================
# 1. 两文件交集 / 不交集
# ============================================================

if mode == "交集 / 不交集":

    st.subheader("两个附件交集 / 不交集")

    file_a = st.file_uploader(
        "上传文件 A",
        type=["txt"],
        key="single_a"
    )

    file_b = st.file_uploader(
        "上传文件 B",
        type=["txt"],
        key="single_b"
    )

    if file_a and file_b:

        A = set(read_upload(file_a))
        B = set(read_upload(file_b))

        inter = sorted(A & B)
        a_only = sorted(A - B)
        b_only = sorted(B - A)
        non_inter = sorted((A - B) | (B - A))
        union = sorted(A | B)

        st.markdown("### 数量")

        st.write(f"A：**{len(A)} 注**")
        st.write(f"B：**{len(B)} 注**")
        st.write(f"交集：**{len(inter)} 注**")
        st.write(f"A独有：**{len(a_only)} 注**")
        st.write(f"B独有：**{len(b_only)} 注**")
        st.write(f"不交集合并：**{len(non_inter)} 注**")
        st.write(f"合并去重：**{len(union)} 注**")

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

        st.markdown("### 下载结果")

        st.download_button(
            "下载交集",
            txt_bytes(inter),
            "交集.txt",
            "text/plain",
            key="single_inter"
        )

        st.download_button(
            "下载A独有",
            txt_bytes(a_only),
            "A独有.txt",
            "text/plain",
            key="single_a_only"
        )

        st.download_button(
            "下载B独有",
            txt_bytes(b_only),
            "B独有.txt",
            "text/plain",
            key="single_b_only"
        )

        st.download_button(
            "下载不交集合并",
            txt_bytes(non_inter),
            "不交集合并.txt",
            "text/plain",
            key="single_non_inter"
        )

        st.download_button(
            "下载合并去重",
            txt_bytes(union),
            "合并去重.txt",
            "text/plain",
            key="single_union"
        )


# ============================================================
# 2. A分别与多个文件交集
# ============================================================

elif mode == "A分别与多个文件交集":

    st.subheader("A分别与多个文件做交集")

    file_a = st.file_uploader(
        "上传主文件 A",
        type=["txt"],
        key="multi_main_a"
    )

    compare_files = st.file_uploader(
        "上传对比文件 B / C / D / E ...",
        type=["txt"],
        accept_multiple_files=True,
        key="multi_compare"
    )

    if file_a and compare_files:

        A = set(read_upload(file_a))

        st.write(f"主文件A：**{len(A)} 注**")

        for idx, file_other in enumerate(compare_files, start=1):

            other = set(read_upload(file_other))

            inter = sorted(A & other)
            a_only = sorted(A - other)
            other_only = sorted(other - A)
            non_inter = sorted((A - other) | (other - A))
            union = sorted(A | other)

            # idx=1 -> B
            # idx=2 -> C
            label = chr(65 + idx)

            st.divider()

            st.markdown(f"## A 与 {label}")
            st.caption(f"{label}文件：{file_other.name}")

            st.write(f"A：**{len(A)} 注**")
            st.write(f"{label}：**{len(other)} 注**")
            st.write(f"A∩{label}：**{len(inter)} 注**")
            st.write(f"A独有：**{len(a_only)} 注**")
            st.write(f"{label}独有：**{len(other_only)} 注**")
            st.write(f"不交集合并：**{len(non_inter)} 注**")
            st.write(f"合并去重：**{len(union)} 注**")

            left = len(A) + len(other)
            right = 2 * len(inter) + len(non_inter)

            if left == right:
                st.success(
                    f"闭环正确：{len(A)} + {len(other)} "
                    f"= 2×{len(inter)} + {len(non_inter)} "
                    f"= {left} √"
                )
            else:
                st.error("闭环失败")

            st.download_button(
                f"下载 A∩{label}",
                txt_bytes(inter),
                f"A与{label}交集.txt",
                "text/plain",
                key=f"multi_inter_{idx}"
            )

            st.download_button(
                f"下载 A独有（相对{label}）",
                txt_bytes(a_only),
                f"A对{label}独有.txt",
                "text/plain",
                key=f"multi_a_only_{idx}"
            )

            st.download_button(
                f"下载 {label}独有",
                txt_bytes(other_only),
                f"{label}对A独有.txt",
                "text/plain",
                key=f"multi_other_only_{idx}"
            )

            st.download_button(
                f"下载 A与{label}不交集合并",
                txt_bytes(non_inter),
                f"A与{label}不交集合并.txt",
                "text/plain",
                key=f"multi_non_inter_{idx}"
            )

            st.download_button(
                f"下载 A与{label}合并去重",
                txt_bytes(union),
                f"A与{label}合并去重.txt",
                "text/plain",
                key=f"multi_union_{idx}"
            )


# ============================================================
# 3. 多文件合并去重
# ============================================================

elif mode == "合并去重":

    st.subheader("多个附件合并去重")

    files = st.file_uploader(
        "上传两个或多个TXT文件",
        type=["txt"],
        accept_multiple_files=True,
        key="merge_files"
    )

    if files:

        if len(files) < 2:
            st.info("请至少上传2个TXT文件")

        else:
            all_sets = []
            total_before = 0

            st.markdown("### 各文件数量")

            for f in files:
                nums = set(read_upload(f))
                all_sets.append(nums)
                total_before += len(nums)

                st.write(
                    f"{f.name}：**{len(nums)} 注**"
                )

            merged = sorted(set().union(*all_sets))

            duplicate_count = total_before - len(merged)

            st.markdown("### 合并结果")

            st.write(f"文件数量：**{len(files)} 个**")
            st.write(f"各文件注数累计：**{total_before} 注**")
            st.write(f"合并去重后：**{len(merged)} 注**")
            st.write(f"累计重复计数：**{duplicate_count}**")

            st.success(
                f"闭环：{total_before} - {duplicate_count} "
                f"= {len(merged)} √"
            )

            st.download_button(
                "下载合并去重结果",
                txt_bytes(merged),
                "合并去重.txt",
                "text/plain",
                key="merge_download"
            )


# ============================================================
# 4. 形态筛选
# ============================================================

elif mode == "形态筛选":

    st.subheader("按完整三位形态筛选")

    file = st.file_uploader(
        "上传原始组合TXT",
        type=["txt"],
        key="shape_file"
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

            remove_by_size = (
                size_shape(n) in selected_size
            )

            remove_by_parity = (
                parity_shape(n) in selected_parity
            )

            if remove_by_size or remove_by_parity:
                removed.append(n)
            else:
                remain.append(n)

        st.markdown("### 数量")

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
            "下载筛选后剩余",
            txt_bytes(remain),
            "筛选后剩余.txt",
            "text/plain",
            key="shape_remain"
        )

        st.download_button(
            "下载被去掉组合",
            txt_bytes(removed),
            "被去掉组合.txt",
            "text/plain",
            key="shape_removed"
        )


# ============================================================
# 5. 二同 / 三同 / 三不同
# ============================================================

elif mode == "二同 / 三同 / 三不同":

    st.subheader("二同 / 三同 / 三不同分类")

    file = st.file_uploader(
        "上传组合TXT",
        type=["txt"],
        key="repeat_file"
    )

    if file:

        original = read_upload(file)

        two_same = []
        three_same = []
        different = []

        for n in original:

            tp = repeat_type(n)

            if tp == "二同":
                two_same.append(n)

            elif tp == "三同":
                three_same.append(n)

            else:
                different.append(n)

        same23 = sorted(two_same + three_same)

        st.markdown("### 数量")

        st.write(f"原始：**{len(original)} 注**")
        st.write(f"二同：**{len(two_same)} 注**")
        st.write(f"三同：**{len(three_same)} 注**")
        st.write(f"二同+三同：**{len(same23)} 注**")
        st.write(f"三不同：**{len(different)} 注**")

        if len(same23) + len(different) == len(original):
            st.success(
                f"闭环正确：{len(same23)} + "
                f"{len(different)} = {len(original)} √"
            )
        else:
            st.error("闭环失败")

        st.download_button(
            "下载二同+三同",
            txt_bytes(same23),
            "二同三同.txt",
            "text/plain",
            key="repeat_same23"
        )

        st.download_button(
            "下载三不同",
            txt_bytes(different),
            "三不同.txt",
            "text/plain",
            key="repeat_diff"
        )

        st.download_button(
            "单独下载二同",
            txt_bytes(two_same),
            "二同.txt",
            "text/plain",
            key="repeat_two"
        )

        st.download_button(
            "单独下载三同",
            txt_bytes(three_same),
            "三同.txt",
            "text/plain",
            key="repeat_three"
        )
