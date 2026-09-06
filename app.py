import streamlit as st
import re
import itertools

st.set_page_config(
    page_title="数字分析工具",
    page_icon="🔢",
    layout="centered"
)

st.title("🔢 数字分析工具")


# =========================================================
# 基础函数
# =========================================================

def parse_numbers(text):
    """从TXT中提取000-999三位组合，自动去重、升序"""
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    if file is None:
        return []

    data = file.getvalue()

    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            return parse_numbers(data.decode(enc))
        except:
            pass

    return []


def format_txt(nums):
    """升序，每行10组"""
    nums = sorted(set(nums))

    lines = []

    for i in range(0, len(nums), 10):
        lines.append(" ".join(nums[i:i + 10]))

    return "\n".join(lines)


def txt_bytes(nums):
    return format_txt(nums).encode("utf-8-sig")


def size_shape(num):
    """0-4小，5-9大"""
    return "".join(
        "大" if int(d) >= 5 else "小"
        for d in num
    )


def parity_shape(num):
    """02468偶，13579奇"""
    return "".join(
        "奇" if int(d) % 2 else "偶"
        for d in num
    )


def repeat_type(num):
    count = len(set(num))

    if count == 3:
        return "三不同"
    elif count == 2:
        return "二同"
    else:
        return "三同"


ALL_NUMBERS = [f"{i:03d}" for i in range(1000)]

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


# =========================================================
# 口径1函数
# =========================================================

POSITION_MAP = {
    "百十": [0, 1],
    "百个": [0, 2],
    "十个": [1, 2],
}


def allowed_shapes(mother_shape, position_name, all_shapes):
    """
    八形态反筛法：
    8个完整三位形态中，
    去掉目标两位与母号目标两位完全一致的2个形态，
    保留其余6个形态。
    """
    positions = POSITION_MAP[position_name]

    keep = []

    for shape in all_shapes:

        same = all(
            shape[pos] == mother_shape[pos]
            for pos in positions
        )

        if not same:
            keep.append(shape)

    return keep


def parse_koujing1(text):
    """
    支持：
    592百个
    592百十
    592十个

    592大小十个奇偶百个
    592大小百十奇偶十个
    592大小十个奇偶百十
    592大小百个奇偶十个
    592大小百个奇偶百十
    """

    text = text.strip()
    text = text.replace(" ", "")
    text = text.replace("+", "")

    m = re.match(r'^(\d{3})(.*)$', text)

    if not m:
        return None, "请输入三位母号，例如：592百个"

    mother = m.group(1)
    rule = m.group(2)

    # 简写：百个 / 百十 / 十个
    if rule in POSITION_MAP:
        return {
            "mother": mother,
            "size_pos": rule,
            "parity_pos": rule,
            "display_rule": rule
        }, None

    # 混合位
    m2 = re.fullmatch(
        r'大小(百十|百个|十个)奇偶(百十|百个|十个)',
        rule
    )

    if m2:
        return {
            "mother": mother,
            "size_pos": m2.group(1),
            "parity_pos": m2.group(2),
            "display_rule":
                f"大小{m2.group(1)} + 奇偶{m2.group(2)}"
        }, None

    return None, (
        "无法识别取位方式。例："
        "592百个 或 592大小十个奇偶百十"
    )


def run_koujing1(mother, size_pos, parity_pos):

    mother_size = size_shape(mother)
    mother_parity = parity_shape(mother)

    allowed_size = allowed_shapes(
        mother_size,
        size_pos,
        SIZE_SHAPES
    )

    allowed_parity = allowed_shapes(
        mother_parity,
        parity_pos,
        PARITY_SHAPES
    )

    full = []

    for num in ALL_NUMBERS:

        if (
            size_shape(num) in allowed_size
            and
            parity_shape(num) in allowed_parity
        ):
            full.append(num)

    same23 = []
    different = []

    for num in full:

        if repeat_type(num) == "三不同":
            different.append(num)
        else:
            same23.append(num)

    return {
        "mother_size": mother_size,
        "mother_parity": mother_parity,
        "allowed_size": allowed_size,
        "allowed_parity": allowed_parity,
        "full": sorted(full),
        "same23": sorted(same23),
        "different": sorted(different),
    }


# =========================================================
# 功能菜单
# =========================================================

mode = st.selectbox(
    "选择功能",
    [
        "口径1取号",
        "交集 / 不交集",
        "A分别与多个文件交集",
        "合并去重",
        "形态筛选",
        "二同 / 三同 / 三不同",
    ]
)


# =========================================================
# 1. 口径1取号
# =========================================================

if mode == "口径1取号":

    st.subheader("口径1正常取号")

    st.caption(
        "支持：592百个 / 592百十 / 592十个 / "
        "592大小十个奇偶百十 等"
    )

    input_text = st.text_area(
        "输入条件",
        placeholder=(
            "例如：\n"
            "592百个\n"
            "或者：\n"
            "592大小十个奇偶百十"
        ),
        height=110
    )

    if st.button("开始取号"):

        lines = [
            x.strip()
            for x in input_text.splitlines()
            if x.strip()
        ]

        if not lines:

            st.error("请输入取号条件")

        else:

            for idx, line in enumerate(lines, start=1):

                parsed, error = parse_koujing1(line)

                if error:
                    st.error(f"{line}：{error}")
                    continue

                mother = parsed["mother"]
                size_pos = parsed["size_pos"]
                parity_pos = parsed["parity_pos"]

                result = run_koujing1(
                    mother,
                    size_pos,
                    parity_pos
                )

                st.divider()

                st.markdown(
                    f"## {mother} {parsed['display_rule']}"
                )

                st.write(
                    f"母号大小：**{result['mother_size']}**"
                )

                st.write(
                    f"母号奇偶：**{result['mother_parity']}**"
                )

                st.write(
                    "大小正常入选6形态："
                )

                st.write(
                    "、".join(result["allowed_size"])
                )

                st.write(
                    "奇偶正常入选6形态："
                )

                st.write(
                    "、".join(result["allowed_parity"])
                )

                full = result["full"]
                same23 = result["same23"]
                different = result["different"]

                st.markdown("### 数量")

                st.write(
                    f"全量正常出号：**{len(full)} 注**"
                )

                st.write(
                    f"二同 + 三同：**{len(same23)} 注**"
                )

                st.write(
                    f"三不同：**{len(different)} 注**"
                )

                if (
                    len(same23)
                    + len(different)
                    == len(full)
                ):

                    st.success(
                        f"闭环正确："
                        f"{len(same23)} + "
                        f"{len(different)} = "
                        f"{len(full)} √"
                    )

                else:
                    st.error("数量闭环失败")

                st.markdown("### 下载")

                safe_name = (
                    mother
                    + "_"
                    + size_pos
                    + "_"
                    + parity_pos
                )

                st.download_button(
                    "下载全量正常出号",
                    txt_bytes(full),
                    f"{safe_name}_全量_{len(full)}注.txt",
                    "text/plain",
                    key=f"k1_full_{idx}"
                )

                st.download_button(
                    "下载二同+三同",
                    txt_bytes(same23),
                    f"{safe_name}_二同三同_{len(same23)}注.txt",
                    "text/plain",
                    key=f"k1_same_{idx}"
                )

                st.download_button(
                    "下载三不同",
                    txt_bytes(different),
                    f"{safe_name}_三不同_{len(different)}注.txt",
                    "text/plain",
                    key=f"k1_diff_{idx}"
                )


# =========================================================
# 2. 两文件交集 / 不交集
# =========================================================

elif mode == "交集 / 不交集":

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
        non_inter = sorted(
            (A - B) | (B - A)
        )

        union = sorted(A | B)

        st.write(f"A：**{len(A)} 注**")
        st.write(f"B：**{len(B)} 注**")
        st.write(f"交集：**{len(inter)} 注**")
        st.write(f"A独有：**{len(a_only)} 注**")
        st.write(f"B独有：**{len(b_only)} 注**")
        st.write(
            f"不交集合并：**{len(non_inter)} 注**"
        )
        st.write(
            f"合并去重：**{len(union)} 注**"
        )

        left = len(A) + len(B)

        right = (
            2 * len(inter)
            + len(non_inter)
        )

        if left == right:

            st.success(
                f"闭环正确："
                f"{len(A)} + {len(B)} "
                f"= 2×{len(inter)} + "
                f"{len(non_inter)} "
                f"= {left} √"
            )

        else:
            st.error("闭环失败")

        st.download_button(
            "下载交集",
            txt_bytes(inter),
            f"交集_{len(inter)}注.txt",
            "text/plain",
            key="single_inter"
        )

        st.download_button(
            "下载A独有",
            txt_bytes(a_only),
            f"A独有_{len(a_only)}注.txt",
            "text/plain",
            key="single_a_only"
        )

        st.download_button(
            "下载B独有",
            txt_bytes(b_only),
            f"B独有_{len(b_only)}注.txt",
            "text/plain",
            key="single_b_only"
        )

        st.download_button(
            "下载不交集合并",
            txt_bytes(non_inter),
            f"不交集合并_{len(non_inter)}注.txt",
            "text/plain",
            key="single_non"
        )

        st.download_button(
            "下载合并去重",
            txt_bytes(union),
            f"合并去重_{len(union)}注.txt",
            "text/plain",
            key="single_union"
        )


# =========================================================
# 3. A分别与多个文件交集
# =========================================================

elif mode == "A分别与多个文件交集":

    st.subheader(
        "A分别与B / C / D / E做交集"
    )

    file_a = st.file_uploader(
        "上传主文件 A",
        type=["txt"],
        key="multi_a"
    )

    compare_files = st.file_uploader(
        "上传B / C / D / E ...",
        type=["txt"],
        accept_multiple_files=True,
        key="multi_other"
    )

    if file_a and compare_files:

        A = set(read_upload(file_a))

        st.write(
            f"主文件A：**{len(A)} 注**"
        )

        for idx, f in enumerate(
            compare_files,
            start=1
        ):

            other = set(
                read_upload(f)
            )

            inter = sorted(A & other)

            a_only = sorted(
                A - other
            )

            other_only = sorted(
                other - A
            )

            non_inter = sorted(
                (A - other)
                |
                (other - A)
            )

            label = chr(
                65 + idx
            )

            st.divider()

            st.markdown(
                f"## A 与 {label}"
            )

            st.caption(
                f"{label}文件：{f.name}"
            )

            st.write(
                f"A：**{len(A)} 注**"
            )

            st.write(
                f"{label}："
                f"**{len(other)} 注**"
            )

            st.write(
                f"A∩{label}："
                f"**{len(inter)} 注**"
            )

            st.write(
                f"A独有："
                f"**{len(a_only)} 注**"
            )

            st.write(
                f"{label}独有："
                f"**{len(other_only)} 注**"
            )

            st.write(
                f"不交集合并："
                f"**{len(non_inter)} 注**"
            )

            left = (
                len(A)
                +
                len(other)
            )

            right = (
                2 * len(inter)
                +
                len(non_inter)
            )

            if left == right:

                st.success(
                    f"闭环正确："
                    f"{len(A)} + "
                    f"{len(other)} "
                    f"= 2×{len(inter)} + "
                    f"{len(non_inter)} "
                    f"= {left} √"
                )

            else:
                st.error("闭环失败")

            st.download_button(
                f"下载 A∩{label}",
                txt_bytes(inter),
                f"A与{label}交集_"
                f"{len(inter)}注.txt",
                "text/plain",
                key=f"multi_inter_{idx}"
            )

            st.download_button(
                f"下载 A独有（相对{label}）",
                txt_bytes(a_only),
                f"A对{label}独有_"
                f"{len(a_only)}注.txt",
                "text/plain",
                key=f"multi_aonly_{idx}"
            )

            st.download_button(
                f"下载 {label}独有",
                txt_bytes(other_only),
                f"{label}对A独有_"
                f"{len(other_only)}注.txt",
                "text/plain",
                key=f"multi_other_{idx}"
            )

            st.download_button(
                f"下载 A与{label}不交集合并",
                txt_bytes(non_inter),
                f"A与{label}不交集合并_"
                f"{len(non_inter)}注.txt",
                "text/plain",
                key=f"multi_non_{idx}"
            )


# =========================================================
# 4. 多文件合并去重
# =========================================================

elif mode == "合并去重":

    st.subheader("多个附件合并去重")

    files = st.file_uploader(
        "上传两个或多个TXT",
        type=["txt"],
        accept_multiple_files=True,
        key="merge"
    )

    if files:

        if len(files) < 2:

            st.info(
                "请至少上传2个TXT"
            )

        else:

            all_sets = []
            total = 0

            for f in files:

                nums = set(
                    read_upload(f)
                )

                all_sets.append(
                    nums
                )

                total += len(nums)

                st.write(
                    f"{f.name}："
                    f"**{len(nums)} 注**"
                )

            merged = sorted(
                set().union(
                    *all_sets
                )
            )

            duplicate = (
                total
                -
                len(merged)
            )

            st.write(
                f"累计：**{total} 注**"
            )

            st.write(
                f"合并去重："
                f"**{len(merged)} 注**"
            )

            st.write(
                f"重复计数："
                f"**{duplicate}**"
            )

            st.success(
                f"闭环："
                f"{total} - "
                f"{duplicate} = "
                f"{len(merged)} √"
            )

            st.download_button(
                "下载合并去重",
                txt_bytes(merged),
                f"合并去重_"
                f"{len(merged)}注.txt",
                "text/plain",
                key="merge_download"
            )


# =========================================================
# 5. 形态筛选
# =========================================================

elif mode == "形态筛选":

    st.subheader(
        "按完整三位形态去除"
    )

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

        for num in original:

            remove = (
                size_shape(num)
                in selected_size
                or
                parity_shape(num)
                in selected_parity
            )

            if remove:
                removed.append(num)
            else:
                remain.append(num)

        st.write(
            f"原始："
            f"**{len(original)} 注**"
        )

        st.write(
            f"剩余："
            f"**{len(remain)} 注**"
        )

        st.write(
            f"去掉："
            f"**{len(removed)} 注**"
        )

        if (
            len(remain)
            +
            len(removed)
            ==
            len(original)
        ):

            st.success(
                f"闭环正确："
                f"{len(remain)} + "
                f"{len(removed)} = "
                f"{len(original)} √"
            )

        else:
            st.error("闭环失败")

        st.download_button(
            "下载剩余组合",
            txt_bytes(remain),
            f"筛选后剩余_"
            f"{len(remain)}注.txt",
            "text/plain",
            key="shape_remain"
        )

        st.download_button(
            "下载被去掉组合",
            txt_bytes(removed),
            f"被去掉_"
            f"{len(removed)}注.txt",
            "text/plain",
            key="shape_removed"
        )


# =========================================================
# 6. 二同 / 三同 / 三不同
# =========================================================

elif mode == "二同 / 三同 / 三不同":

    st.subheader(
        "二同 / 三同 / 三不同分类"
    )

    file = st.file_uploader(
        "上传组合TXT",
        type=["txt"],
        key="repeat"
    )

    if file:

        original = read_upload(file)

        two_same = []
        three_same = []
        different = []

        for num in original:

            tp = repeat_type(num)

            if tp == "二同":
                two_same.append(num)

            elif tp == "三同":
                three_same.append(num)

            else:
                different.append(num)

        same23 = sorted(
            two_same
            +
            three_same
        )

        st.write(
            f"原始："
            f"**{len(original)} 注**"
        )

        st.write(
            f"二同："
            f"**{len(two_same)} 注**"
        )

        st.write(
            f"三同："
            f"**{len(three_same)} 注**"
        )

        st.write(
            f"二同+三同："
            f"**{len(same23)} 注**"
        )

        st.write(
            f"三不同："
            f"**{len(different)} 注**"
        )

        if (
            len(same23)
            +
            len(different)
            ==
            len(original)
        ):

            st.success(
                f"闭环正确："
                f"{len(same23)} + "
                f"{len(different)} = "
                f"{len(original)} √"
            )

        else:
            st.error(
                "数量闭环失败"
            )

        st.download_button(
            "下载二同+三同",
            txt_bytes(same23),
            f"二同三同_"
            f"{len(same23)}注.txt",
            "text/plain",
            key="same23"
        )

        st.download_button(
            "下载三不同",
            txt_bytes(different),
            f"三不同_"
            f"{len(different)}注.txt",
            "text/plain",
            key="different"
        )

        st.download_button(
            "单独下载二同",
            txt_bytes(two_same),
            f"二同_"
            f"{len(two_same)}注.txt",
            "text/plain",
            key="two_same"
        )

        st.download_button(
            "单独下载三同",
            txt_bytes(three_same),
            f"三同_"
            f"{len(three_same)}注.txt",
            "text/plain",
            key="three_same"
        )
