import streamlit as st
import re

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
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    if file is None:
        return []

    data = file.getvalue()

    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            return parse_numbers(data.decode(enc))
        except Exception:
            pass

    return []


def format_txt(nums):
    nums = sorted(set(nums))

    return "\n".join(
        " ".join(nums[i:i + 10])
        for i in range(0, len(nums), 10)
    )


def txt_bytes(nums):
    return format_txt(nums).encode("utf-8-sig")


def size_shape(num):
    return "".join(
        "大" if int(d) >= 5 else "小"
        for d in num
    )


def parity_shape(num):
    return "".join(
        "奇" if int(d) % 2 else "偶"
        for d in num
    )


def repeat_type(num):
    n = len(set(num))

    if n == 3:
        return "三不同"
    elif n == 2:
        return "二同"
    else:
        return "三同"


ALL_NUMBERS = [
    f"{i:03d}"
    for i in range(1000)
]


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


POSITION_MAP = {
    "百十": [0, 1],
    "百个": [0, 2],
    "十个": [1, 2],
}


# =========================================================
# 口径1
# =========================================================

def allowed_shapes(
    mother_shape,
    position_name,
    all_shapes
):
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


def normalize_rule_text(text):

    text = (text or "").strip()

    for ch in [
        " ",
        "+",
        "/",
        "／",
        "，",
        ",",
        "；",
        ";",
        "：",
        ":",
    ]:
        text = text.replace(ch, "")

    return text


def parse_koujing1(text):

    text = normalize_rule_text(text)

    m = re.match(
        r'^(\d{3})(.*)$',
        text
    )

    if not m:
        return None, (
            "格式无法识别，例如："
            "592百个 或 "
            "888大小百十奇偶十个"
        )

    mother = m.group(1)
    rule = m.group(2)

    # 简写：
    # 592百个
    # 592百十
    # 592十个
    if rule in POSITION_MAP:

        return {
            "mother": mother,
            "size_pos": rule,
            "parity_pos": rule,
            "display_rule": rule,
        }, None

    # 混合：
    # 888大小百十奇偶十个
    m2 = re.fullmatch(
        r'大小(百十|百个|十个)'
        r'奇偶(百十|百个|十个)',
        rule
    )

    if m2:

        return {
            "mother": mother,
            "size_pos": m2.group(1),
            "parity_pos": m2.group(2),
            "display_rule":
                f"大小{m2.group(1)} + "
                f"奇偶{m2.group(2)}",
        }, None

    return None, (
        "取位无法识别。"
        "例如：百个 / 百十 / 十个 / "
        "大小百十奇偶十个"
    )


def run_koujing1(
    mother,
    size_pos,
    parity_pos
):

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
            size_shape(num)
            in allowed_size
            and
            parity_shape(num)
            in allowed_parity
        ):
            full.append(num)

    same23 = [
        num
        for num in full
        if repeat_type(num)
        != "三不同"
    ]

    different = [
        num
        for num in full
        if repeat_type(num)
        == "三不同"
    ]

    return {
        "mother_size":
            mother_size,

        "mother_parity":
            mother_parity,

        "allowed_size":
            allowed_size,

        "allowed_parity":
            allowed_parity,

        "full":
            sorted(full),

        "same23":
            sorted(same23),

        "different":
            sorted(different),
    }


# =========================================================
# 数字轨
# =========================================================

def parse_digit_track(text):

    s = (
        (text or "")
        .strip()
        .replace("数字", "")
        .replace(" ", "")
    )

    digits = [
        c
        for c in s
        if c.isdigit()
    ]

    unique = []

    for d in digits:
        if d not in unique:
            unique.append(d)

    if not unique:
        return None

    return unique


def run_digit_track(
    base_nums,
    target_digits
):

    buckets = {}

    for num in base_nums:

        hit_count = sum(
            1
            for d in target_digits
            if d in num
        )

        buckets.setdefault(
            hit_count,
            []
        ).append(num)

    digit_bc = sorted(
        set(
            buckets.get(2, [])
        )
        |
        set(
            buckets.get(3, [])
        )
    )

    return (
        buckets,
        digit_bc
    )


# =========================================================
# 形态轨
# =========================================================

def classify_shape_token(token):

    token = token.strip()

    if token in SIZE_SHAPES:
        return "size"

    if token in PARITY_SHAPES:
        return "parity"

    return None


def run_shape_track(
    base_nums,
    shape_tokens
):

    valid = []

    for token in shape_tokens:

        kind = classify_shape_token(
            token
        )

        if kind:
            valid.append(
                (token, kind)
            )

    counts = {
        num: 0
        for num in base_nums
    }

    # 每一个形态分别做一次排除
    # 然后统计组合在4个排除结果里出现几次
    for token, kind in valid:

        for num in base_nums:

            if kind == "size":
                matched = (
                    size_shape(num)
                    == token
                )

            else:
                matched = (
                    parity_shape(num)
                    == token
                )

            if not matched:
                counts[num] += 1

    buckets = {}

    for num, count in counts.items():

        buckets.setdefault(
            count,
            []
        ).append(num)

    # 形态CD：
    # 出现3次 + 出现4次
    shape_cd = sorted(
        set(
            buckets.get(3, [])
        )
        |
        set(
            buckets.get(4, [])
        )
    )

    return (
        valid,
        buckets,
        shape_cd
    )


def show_download(
    label,
    nums,
    filename,
    key
):

    st.download_button(
        label,
        txt_bytes(nums),
        filename,
        "text/plain",
        key=key
    )


# =========================================================
# 菜单
# =========================================================

mode = st.selectbox(
    "选择功能",
    [
        "口径1取号",
        "口径1交集后数字形态轨",
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

    st.subheader(
        "口径1正常取号"
    )

    st.caption(
        "支持："
        "592百个 / "
        "173十个 / "
        "888大小百十奇偶十个 等"
    )

    input_text = st.text_area(
        "输入条件（可一次输入多行）",
        placeholder=(
            "592百个\n"
            "888大小百十奇偶十个"
        ),
        height=120
    )

    if st.button(
        "开始取号",
        key="k1_start"
    ):

        lines = [
            x.strip()
            for x
            in input_text.splitlines()
            if x.strip()
        ]

        if not lines:

            st.error(
                "请输入取号条件"
            )

        else:

            for idx, line in enumerate(
                lines,
                start=1
            ):

                parsed, error = (
                    parse_koujing1(
                        line
                    )
                )

                if error:

                    st.error(
                        f"{line}：{error}"
                    )

                    continue

                result = run_koujing1(
                    parsed["mother"],
                    parsed["size_pos"],
                    parsed["parity_pos"]
                )

                st.divider()

                st.markdown(
                    f"## "
                    f"{parsed['mother']} "
                    f"{parsed['display_rule']}"
                )

                st.write(
                    "母号大小："
                    f"**{result['mother_size']}**"
                )

                st.write(
                    "母号奇偶："
                    f"**{result['mother_parity']}**"
                )

                st.write(
                    "大小正常入选6形态："
                    +
                    "、".join(
                        result[
                            "allowed_size"
                        ]
                    )
                )

                st.write(
                    "奇偶正常入选6形态："
                    +
                    "、".join(
                        result[
                            "allowed_parity"
                        ]
                    )
                )

                full = (
                    result["full"]
                )

                same23 = (
                    result["same23"]
                )

                different = (
                    result["different"]
                )

                st.write(
                    "全量正常出号："
                    f"**{len(full)} 注**"
                )

                st.write(
                    "二同+三同："
                    f"**{len(same23)} 注**"
                )

                st.write(
                    "三不同："
                    f"**{len(different)} 注**"
                )

                if (
                    len(same23)
                    +
                    len(different)
                    ==
                    len(full)
                ):

                    st.success(
                        "闭环正确："
                        f"{len(same23)} + "
                        f"{len(different)} "
                        f"= {len(full)} √"
                    )

                else:

                    st.error(
                        "闭环失败"
                    )

                base_name = (
                    f"{parsed['mother']}_"
                    f"{parsed['size_pos']}_"
                    f"{parsed['parity_pos']}"
                )

                show_download(
                    "下载全量正常出号",
                    full,
                    f"{base_name}_"
                    f"全量_{len(full)}注.txt",
                    f"k1_full_{idx}"
                )

                show_download(
                    "下载二同+三同",
                    same23,
                    f"{base_name}_"
                    f"二同三同_"
                    f"{len(same23)}注.txt",
                    f"k1_same_{idx}"
                )

                show_download(
                    "下载三不同",
                    different,
                    f"{base_name}_"
                    f"三不同_"
                    f"{len(different)}注.txt",
                    f"k1_diff_{idx}"
                )


# =========================================================
# 2. 口径1交集后数字形态轨
# =========================================================

elif mode == "口径1交集后数字形态轨":

    st.subheader(
        "口径1 → 三不同交集/独有 "
        "→ 数字形态轨"
    )

    st.caption(
        "两个母号分别正常出号 → "
        "取三不同 → "
        "交集/A独有/B独有 → "
        "两边独有合并 → "
        "数字BC → "
        "形态CD → "
        "BC∩CD"
    )

    mother_a_text = st.text_input(
        "母号A条件",
        placeholder="例如：000百个",
        key="wf_a"
    )

    mother_b_text = st.text_input(
        "母号B条件",
        placeholder="例如：999百个",
        key="wf_b"
    )

    digit_text = st.text_input(
        "数字轨",
        placeholder="例如：数字067",
        key="wf_digit"
    )

    shape_text = st.text_area(
        "形态轨（每行一个完整三位形态）",
        placeholder=(
            "小大大\n"
            "大大小\n"
            "偶偶偶\n"
            "偶偶奇"
        ),
        height=130,
        key="wf_shape"
    )

    if st.button(
        "开始完整分析",
        key="wf_start"
    ):

        parsed_a, error_a = (
            parse_koujing1(
                mother_a_text
            )
        )

        parsed_b, error_b = (
            parse_koujing1(
                mother_b_text
            )
        )

        if error_a:

            st.error(
                f"母号A：{error_a}"
            )

        elif error_b:

            st.error(
                f"母号B：{error_b}"
            )

        else:

            digits = (
                parse_digit_track(
                    digit_text
                )
            )

            if not digits:

                st.error(
                    "请输入数字轨，"
                    "例如：数字067"
                )

            else:

                shapes = [
                    x.strip()
                    for x
                    in shape_text.splitlines()
                    if x.strip()
                ]

                if len(shapes) != 4:

                    st.error(
                        "形态轨请先输入4个"
                        "完整三位形态，"
                        "每行一个"
                    )

                else:

                    invalid_shapes = [
                        s
                        for s in shapes
                        if classify_shape_token(s)
                        is None
                    ]

                    if invalid_shapes:

                        st.error(
                            "无法识别形态："
                            +
                            "、".join(
                                invalid_shapes
                            )
                        )

                    else:

                        # A口径1
                        result_a = run_koujing1(
                            parsed_a["mother"],
                            parsed_a["size_pos"],
                            parsed_a[
                                "parity_pos"
                            ]
                        )

                        # B口径1
                        result_b = run_koujing1(
                            parsed_b["mother"],
                            parsed_b["size_pos"],
                            parsed_b[
                                "parity_pos"
                            ]
                        )

                        # 只取三不同
                        A = set(
                            result_a[
                                "different"
                            ]
                        )

                        B = set(
                            result_b[
                                "different"
                            ]
                        )

                        # 前置交集/独有
                        inter = sorted(
                            A & B
                        )

                        a_only = sorted(
                            A - B
                        )

                        b_only = sorted(
                            B - A
                        )

                        non_inter = sorted(
                            (A - B)
                            |
                            (B - A)
                        )

                        st.markdown(
                            "## ① 前置母号结果"
                        )

                        st.write(
                            "A三不同："
                            f"**{len(A)} 注**"
                        )

                        st.write(
                            "B三不同："
                            f"**{len(B)} 注**"
                        )

                        st.write(
                            "交集："
                            f"**{len(inter)} 注**"
                        )

                        st.write(
                            "A独有："
                            f"**{len(a_only)} 注**"
                        )

                        st.write(
                            "B独有："
                            f"**{len(b_only)} 注**"
                        )

                        st.write(
                            "不交集合并："
                            f"**{len(non_inter)} 注**"
                        )

                        left = (
                            len(A)
                            +
                            len(B)
                        )

                        right = (
                            2 * len(inter)
                            +
                            len(non_inter)
                        )

                        if left == right:

                            st.success(
                                "前置闭环："
                                f"{len(A)} + "
                                f"{len(B)} = "
                                f"2×{len(inter)} + "
                                f"{len(non_inter)} "
                                f"= {left} √"
                            )

                        else:

                            st.error(
                                "前置闭环失败"
                            )

                        show_download(
                            "下载A三不同",
                            sorted(A),
                            f"A三不同_"
                            f"{len(A)}注.txt",
                            "wf_a_diff"
                        )

                        show_download(
                            "下载B三不同",
                            sorted(B),
                            f"B三不同_"
                            f"{len(B)}注.txt",
                            "wf_b_diff"
                        )

                        show_download(
                            "下载交集",
                            inter,
                            f"交集_"
                            f"{len(inter)}注.txt",
                            "wf_inter"
                        )

                        show_download(
                            "下载A独有",
                            a_only,
                            f"A独有_"
                            f"{len(a_only)}注.txt",
                            "wf_a_only"
                        )

                        show_download(
                            "下载B独有",
                            b_only,
                            f"B独有_"
                            f"{len(b_only)}注.txt",
                            "wf_b_only"
                        )

                        show_download(
                            "下载不交集合并",
                            non_inter,
                            f"不交集合并_"
                            f"{len(non_inter)}注.txt",
                            "wf_non_inter"
                        )


                        # -------------------------
                        # 数字轨
                        # -------------------------

                        digit_buckets, digit_bc = (
                            run_digit_track(
                                non_inter,
                                digits
                            )
                        )

                        st.markdown(
                            "## ② 数字轨"
                        )

                        st.write(
                            "目标数字："
                            +
                            "、".join(
                                digits
                            )
                        )

                        for count in sorted(
                            digit_buckets
                        ):

                            st.write(
                                f"出现{count}次："
                                f"**"
                                f"{len(digit_buckets[count])}"
                                f" 注**"
                            )

                        st.write(
                            "数字BC "
                            "（出现2次+3次）："
                            f"**{len(digit_bc)} 注**"
                        )

                        show_download(
                            "下载数字BC",
                            digit_bc,
                            f"数字BC_"
                            f"{len(digit_bc)}注.txt",
                            "wf_digit_bc"
                        )


                        # -------------------------
                        # 形态轨
                        # -------------------------

                        (
                            valid_shapes,
                            shape_buckets,
                            shape_cd
                        ) = run_shape_track(
                            non_inter,
                            shapes
                        )

                        st.markdown(
                            "## ③ 形态轨"
                        )

                        st.write(
                            "形态："
                            +
                            "、".join(
                                s
                                for s, _
                                in valid_shapes
                            )
                        )

                        for count in sorted(
                            shape_buckets
                        ):

                            st.write(
                                f"出现{count}次："
                                f"**"
                                f"{len(shape_buckets[count])}"
                                f" 注**"
                            )

                        st.write(
                            "形态CD "
                            "（出现3次+4次）："
                            f"**{len(shape_cd)} 注**"
                        )

                        show_download(
                            "下载形态CD",
                            shape_cd,
                            f"形态CD_"
                            f"{len(shape_cd)}注.txt",
                            "wf_shape_cd"
                        )


                        # -------------------------
                        # 最终 BC ∩ CD
                        # -------------------------

                        final_in = sorted(
                            set(digit_bc)
                            &
                            set(shape_cd)
                        )

                        final_out = sorted(
                            set(non_inter)
                            -
                            set(final_in)
                        )

                        st.markdown(
                            "## ④ 最终数字形态轨"
                        )

                        st.write(
                            "最终入选 "
                            "BC∩CD："
                            f"**{len(final_in)} 注**"
                        )

                        st.write(
                            "最终不入选："
                            f"**{len(final_out)} 注**"
                        )

                        if (
                            len(final_in)
                            +
                            len(final_out)
                            ==
                            len(non_inter)
                        ):

                            st.success(
                                "最终闭环："
                                f"{len(final_in)} + "
                                f"{len(final_out)} "
                                f"= {len(non_inter)} √"
                            )

                        else:

                            st.error(
                                "最终闭环失败"
                            )

                        show_download(
                            "下载最终入选",
                            final_in,
                            f"最终入选_"
                            f"{len(final_in)}注.txt",
                            "wf_final_in"
                        )

                        show_download(
                            "下载最终不入选",
                            final_out,
                            f"最终不入选_"
                            f"{len(final_out)}注.txt",
                            "wf_final_out"
                        )


# =========================================================
# 3. 交集 / 不交集
# =========================================================

elif mode == "交集 / 不交集":

    st.subheader(
        "两个附件交集 / 不交集"
    )

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

        A = set(
            read_upload(
                file_a
            )
        )

        B = set(
            read_upload(
                file_b
            )
        )

        inter = sorted(
            A & B
        )

        a_only = sorted(
            A - B
        )

        b_only = sorted(
            B - A
        )

        non_inter = sorted(
            (A - B)
            |
            (B - A)
        )

        union = sorted(
            A | B
        )

        st.write(
            f"A：**{len(A)} 注**"
        )

        st.write(
            f"B：**{len(B)} 注**"
        )

        st.write(
            f"交集：**{len(inter)} 注**"
        )

        st.write(
            f"A独有：**{len(a_only)} 注**"
        )

        st.write(
            f"B独有：**{len(b_only)} 注**"
        )

        st.write(
            "不交集合并："
            f"**{len(non_inter)} 注**"
        )

        st.write(
            "合并去重："
            f"**{len(union)} 注**"
        )

        left = (
            len(A)
            +
            len(B)
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
                f"{len(B)} = "
                f"2×{len(inter)} + "
                f"{len(non_inter)} "
                f"= {left} √"
            )

        else:

            st.error(
                "闭环失败"
            )

        show_download(
            "下载交集",
            inter,
            f"交集_{len(inter)}注.txt",
            "single_inter"
        )

        show_download(
            "下载A独有",
            a_only,
            f"A独有_{len(a_only)}注.txt",
            "single_a"
        )

        show_download(
            "下载B独有",
            b_only,
            f"B独有_{len(b_only)}注.txt",
            "single_b"
        )

        show_download(
            "下载不交集合并",
            non_inter,
            f"不交集合并_"
            f"{len(non_inter)}注.txt",
            "single_non"
        )

        show_download(
            "下载合并去重",
            union,
            f"合并去重_"
            f"{len(union)}注.txt",
            "single_union"
        )


# =========================================================
# 4. A分别与多个文件交集
# =========================================================

elif mode == "A分别与多个文件交集":

    st.subheader(
        "A分别与多个文件做交集"
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
        key="multi_others"
    )

    if file_a and compare_files:

        A = set(
            read_upload(
                file_a
            )
        )

        st.write(
            f"主文件A："
            f"**{len(A)} 注**"
        )

        for idx, f in enumerate(
            compare_files,
            start=1
        ):

            other = set(
                read_upload(
                    f
                )
            )

            inter = sorted(
                A & other
            )

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
                f"{label}文件："
                f"{f.name}"
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
                "A独有："
                f"**{len(a_only)} 注**"
            )

            st.write(
                f"{label}独有："
                f"**{len(other_only)} 注**"
            )

            st.write(
                "不交集合并："
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
                    f"闭环："
                    f"{len(A)} + "
                    f"{len(other)} = "
                    f"2×{len(inter)} + "
                    f"{len(non_inter)} "
                    f"= {left} √"
                )

            else:

                st.error(
                    "闭环失败"
                )

            show_download(
                f"下载 A∩{label}",
                inter,
                f"A与{label}交集_"
                f"{len(inter)}注.txt",
                f"m_inter_{idx}"
            )

            show_download(
                f"下载 A独有（相对{label}）",
                a_only,
                f"A对{label}独有_"
                f"{len(a_only)}注.txt",
                f"m_a_{idx}"
            )

            show_download(
                f"下载 {label}独有",
                other_only,
                f"{label}对A独有_"
                f"{len(other_only)}注.txt",
                f"m_o_{idx}"
            )

            show_download(
                f"下载 A与{label}不交集合并",
                non_inter,
                f"A与{label}不交集合并_"
                f"{len(non_inter)}注.txt",
                f"m_non_{idx}"
            )


# =========================================================
# 5. 合并去重
# =========================================================

elif mode == "合并去重":

    st.subheader(
        "多个附件合并去重"
    )

    files = st.file_uploader(
        "上传两个或多个TXT",
        type=["txt"],
        accept_multiple_files=True,
        key="merge_files"
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
                    read_upload(
                        f
                    )
                )

                all_sets.append(
                    nums
                )

                total += len(
                    nums
                )

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
                f"累计："
                f"**{total} 注**"
            )

            st.write(
                "合并去重："
                f"**{len(merged)} 注**"
            )

            st.write(
                "累计重复计数："
                f"**{duplicate}**"
            )

            st.success(
                f"闭环："
                f"{total} - "
                f"{duplicate} = "
                f"{len(merged)} √"
            )

            show_download(
                "下载合并去重",
                merged,
                f"合并去重_"
                f"{len(merged)}注.txt",
                "merge_download"
            )


# =========================================================
# 6. 形态筛选
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

        original = (
            read_upload(
                file
            )
        )

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
                f"闭环："
                f"{len(remain)} + "
                f"{len(removed)} = "
                f"{len(original)} √"
            )

        else:

            st.error(
                "闭环失败"
            )

        show_download(
            "下载剩余组合",
            remain,
            f"筛选后剩余_"
            f"{len(remain)}注.txt",
            "shape_remain"
        )

        show_download(
            "下载被去掉组合",
            removed,
            f"被去掉_"
            f"{len(removed)}注.txt",
            "shape_removed"
        )


# =========================================================
# 7. 二同 / 三同 / 三不同
# =========================================================

elif mode == "二同 / 三同 / 三不同":

    st.subheader(
        "二同 / 三同 / 三不同分类"
    )

    file = st.file_uploader(
        "上传组合TXT",
        type=["txt"],
        key="repeat_file"
    )

    if file:

        original = (
            read_upload(
                file
            )
        )

        two_same = []
        three_same = []
        different = []

        for num in original:

            tp = (
                repeat_type(
                    num
                )
            )

            if tp == "二同":

                two_same.append(
                    num
                )

            elif tp == "三同":

                three_same.append(
                    num
                )

            else:

                different.append(
                    num
                )

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
                f"闭环："
                f"{len(same23)} + "
                f"{len(different)} = "
                f"{len(original)} √"
            )

        else:

            st.error(
                "闭环失败"
            )

        show_download(
            "下载二同+三同",
            same23,
            f"二同三同_"
            f"{len(same23)}注.txt",
            "r_same23"
        )

        show_download(
            "下载三不同",
            different,
            f"三不同_"
            f"{len(different)}注.txt",
            "r_diff"
        )

        show_download(
            "单独下载二同",
            two_same,
            f"二同_"
            f"{len(two_same)}注.txt",
            "r_two"
        )

        show_download(
            "单独下载三同",
            three_same,
            f"三同_"
            f"{len(three_same)}注.txt",
            "r_three"
        )
