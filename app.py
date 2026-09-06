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
    """从文字中提取000-999三位组合，自动去重、升序"""
    nums = re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")
    return sorted(set(nums))


def read_upload(file):
    """读取TXT，兼容常见中文编码"""
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
    """升序，每行10组"""
    nums = sorted(set(nums))

    return "\n".join(
        " ".join(nums[i:i + 10])
        for i in range(0, len(nums), 10)
    )


def txt_bytes(nums):
    return format_txt(nums).encode("utf-8-sig")


def show_download(label, nums, filename, key):
    st.download_button(
        label,
        txt_bytes(nums),
        filename,
        "text/plain",
        key=key
    )


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
    """三不同 / 二同 / 三同"""
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

POSITION_MAP = {
    "百十": [0, 1],
    "百个": [0, 2],
    "十个": [1, 2],
}


# =========================================================
# 口径1核心
# =========================================================

def allowed_shapes(mother_shape, position_name, all_shapes):
    """
    八形态反筛：
    目标两位与母号完全相同的2个形态去掉，
    其余6个为正常入选形态。
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
    """
    支持：
    592百个
    592百十
    592十个

    888大小百十奇偶十个
    592大小十个奇偶百十
    """

    text = normalize_rule_text(text)

    m = re.match(r'^(\d{3})(.*)$', text)

    if not m:
        return None, "格式无法识别"

    mother = m.group(1)
    rule = m.group(2)

    # 普通位法
    if rule in POSITION_MAP:

        return {
            "mother": mother,
            "size_pos": rule,
            "parity_pos": rule,
            "display_rule": rule,
        }, None

    # 混合位法
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
                f"大小{m2.group(1)} + 奇偶{m2.group(2)}",
        }, None

    return None, (
        "取位无法识别，例如："
        "818十个 或 "
        "888大小百十奇偶十个"
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

    same23 = [
        n for n in full
        if repeat_type(n) != "三不同"
    ]

    different = [
        n for n in full
        if repeat_type(n) == "三不同"
    ]

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
# 数字轨
# =========================================================

def parse_digit_track(text):

    s = (
        (text or "")
        .replace("数字", "")
        .replace(" ", "")
    )

    digits = []

    for c in s:

        if c.isdigit() and c not in digits:
            digits.append(c)

    return digits


def run_digit_track(base_nums, target_digits):
    """
    数字轨：
    每个目标数字分别做一次排除。

    例如数字389：
    去掉含3
    去掉含8
    去掉含9

    一个组合在排除后仍保留一次，
    出现频次+1。

    BC = 出现2次 + 出现3次
    """

    buckets = {}

    for num in base_nums:

        count = 0

        for d in target_digits:

            if d not in num:
                count += 1

        buckets.setdefault(count, []).append(num)

    digit_bc = sorted(
        set(buckets.get(2, []))
        |
        set(buckets.get(3, []))
    )

    return buckets, digit_bc


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


def run_shape_track(base_nums, shape_tokens):

    valid = []

    for token in shape_tokens:

        kind = classify_shape_token(token)

        if kind:
            valid.append((token, kind))

    counts = {
        num: 0
        for num in base_nums
    }

    # 每个形态分别排除一次
    for token, kind in valid:

        for num in base_nums:

            if kind == "size":

                matched = (
                    size_shape(num) == token
                )

            else:

                matched = (
                    parity_shape(num) == token
                )

            if not matched:
                counts[num] += 1

    buckets = {}

    for num, count in counts.items():

        buckets.setdefault(
            count,
            []
        ).append(num)

    shape_cd = sorted(
        set(buckets.get(3, []))
        |
        set(buckets.get(4, []))
    )

    return valid, buckets, shape_cd


# =========================================================
# 两位组合
# =========================================================

def canonical_pair(pair):
    """
    两位组合按无序处理：
    10和01视为同一对01
    82和28视为同一对28
    """
    if len(pair) != 2 or not pair.isdigit():
        return None

    return "".join(sorted(pair))


def parse_pair_conditions(text):

    raw = re.findall(
        r'(?<!\d)\d{2}(?!\d)',
        text or ""
    )

    pairs = set()

    for p in raw:

        cp = canonical_pair(p)

        if cp:
            pairs.add(cp)

    return pairs


def three_position_pairs(num):
    """
    三位数组合abc形成：
    ab
    ac
    bc

    每一对按无序方式判断。
    """

    a, b, c = num

    return [
        canonical_pair(a + b),
        canonical_pair(a + c),
        canonical_pair(b + c),
    ]


def pair_hit_count(num, pair_set):

    pairs = three_position_pairs(num)

    return sum(
        1
        for p in pairs
        if p in pair_set
    )


def run_pair_filter(base_nums, pair_set, mode):

    selected = []
    rejected = []

    for num in base_nums:

        hits = pair_hit_count(
            num,
            pair_set
        )

        if mode == "两对命中（至少2对）":
            ok = hits >= 2

        elif mode == "恰好两对命中":
            ok = hits == 2

        else:
            ok = hits == 3

        if ok:
            selected.append(num)

        else:
            rejected.append(num)

    return (
        sorted(selected),
        sorted(rejected)
    )


# =========================================================
# 半顺 / 全顺
# =========================================================

def sequence_type(num):
    """
    全顺：
    三位数字都不同，排序后连续3个。

    例如：
    345 / 354 / 435 / 543

    半顺：
    三位数字都不同，
    至少有一对相邻连续，
    但不是三位全连续。

    例如：
    348 / 384
    """

    digits = sorted(
        int(x) for x in num
    )

    # 有重复数字不算半顺/全顺
    if len(set(digits)) != 3:
        return "非半顺"

    d1, d2, d3 = digits

    if (
        d2 - d1 == 1
        and
        d3 - d2 == 1
    ):
        return "全顺"

    if (
        d2 - d1 == 1
        or
        d3 - d2 == 1
    ):
        return "半顺"

    return "非半顺"


# =========================================================
# 功能菜单
# =========================================================

mode = st.selectbox(
    "选择功能",
    [
        "口径1取号",
        "口径1双条件全量交集",
        "口径1交集后数字形态轨",
        "交集 / 不交集",
        "A分别与多个文件交集",
        "合并去重",
        "形态筛选",
        "二同 / 三同 / 三不同",
        "两位组合命中筛选（按附件）",
        "两位组合命中筛选（000-999）",
        "数字包含 / 去除筛选",
        "半顺以上筛选",
    ]
)


# =========================================================
# 1. 口径1取号
# =========================================================

if mode == "口径1取号":

    st.subheader("口径1正常取号")

    text = st.text_area(
        "输入条件（可多行）",
        placeholder=(
            "592百个\n"
            "888大小百十奇偶十个"
        )
    )

    if st.button("开始取号"):

        lines = [
            x.strip()
            for x in text.splitlines()
            if x.strip()
        ]

        if not lines:

            st.error("请输入条件")

        for idx, line in enumerate(
            lines,
            start=1
        ):

            parsed, error = parse_koujing1(
                line
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

            full = result["full"]
            same23 = result["same23"]
            diff = result["different"]

            st.divider()

            st.markdown(
                f"## {parsed['mother']} "
                f"{parsed['display_rule']}"
            )

            st.write(
                f"母号大小："
                f"**{result['mother_size']}**"
            )

            st.write(
                f"母号奇偶："
                f"**{result['mother_parity']}**"
            )

            st.write(
                "大小正常6形态："
                +
                "、".join(
                    result["allowed_size"]
                )
            )

            st.write(
                "奇偶正常6形态："
                +
                "、".join(
                    result["allowed_parity"]
                )
            )

            st.write(
                f"全量：**{len(full)} 注**"
            )

            st.write(
                f"二同+三同："
                f"**{len(same23)} 注**"
            )

            st.write(
                f"三不同："
                f"**{len(diff)} 注**"
            )

            if (
                len(same23)
                +
                len(diff)
                ==
                len(full)
            ):

                st.success(
                    f"闭环："
                    f"{len(same23)} + "
                    f"{len(diff)} = "
                    f"{len(full)} √"
                )

            base = (
                f"{parsed['mother']}_"
                f"{parsed['size_pos']}_"
                f"{parsed['parity_pos']}"
            )

            show_download(
                "下载全量",
                full,
                f"{base}_全量_"
                f"{len(full)}注.txt",
                f"k1_full_{idx}"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"{base}_二同三同_"
                f"{len(same23)}注.txt",
                f"k1_same_{idx}"
            )

            show_download(
                "下载三不同",
                diff,
                f"{base}_三不同_"
                f"{len(diff)}注.txt",
                f"k1_diff_{idx}"
            )


# =========================================================
# 2. 口径1双条件全量交集
# =========================================================

elif mode == "口径1双条件全量交集":

    st.subheader(
        "两个口径1条件 → 全量交集/独有"
    )

    text_a = st.text_input(
        "条件A",
        placeholder="例如：818十个"
    )

    text_b = st.text_input(
        "条件B",
        placeholder="例如：881十个"
    )

    if st.button(
        "开始全量交集分析"
    ):

        pa, ea = parse_koujing1(
            text_a
        )

        pb, eb = parse_koujing1(
            text_b
        )

        if ea:

            st.error(
                f"A：{ea}"
            )

        elif eb:

            st.error(
                f"B：{eb}"
            )

        else:

            ra = run_koujing1(
                pa["mother"],
                pa["size_pos"],
                pa["parity_pos"]
            )

            rb = run_koujing1(
                pb["mother"],
                pb["size_pos"],
                pb["parity_pos"]
            )

            A = set(ra["full"])
            B = set(rb["full"])

            inter = sorted(A & B)
            a_only = sorted(A - B)
            b_only = sorted(B - A)

            non_inter = sorted(
                (A - B)
                |
                (B - A)
            )

            union = sorted(A | B)

            st.write(
                f"A全量："
                f"**{len(A)} 注**"
            )

            st.write(
                f"B全量："
                f"**{len(B)} 注**"
            )

            st.write(
                f"交集："
                f"**{len(inter)} 注**"
            )

            st.write(
                f"A独有："
                f"**{len(a_only)} 注**"
            )

            st.write(
                f"B独有："
                f"**{len(b_only)} 注**"
            )

            st.write(
                f"不交集合并："
                f"**{len(non_inter)} 注**"
            )

            st.write(
                f"合并去重："
                f"**{len(union)} 注**"
            )

            left = len(A) + len(B)

            right = (
                2 * len(inter)
                +
                len(non_inter)
            )

            if left == right:

                st.success(
                    f"闭环："
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
                "下载A全量",
                sorted(A),
                f"A全量_{len(A)}注.txt",
                "double_full_a"
            )

            show_download(
                "下载B全量",
                sorted(B),
                f"B全量_{len(B)}注.txt",
                "double_full_b"
            )

            show_download(
                "下载交集",
                inter,
                f"交集_{len(inter)}注.txt",
                "double_inter"
            )

            show_download(
                "下载A独有",
                a_only,
                f"A独有_{len(a_only)}注.txt",
                "double_aonly"
            )

            show_download(
                "下载B独有",
                b_only,
                f"B独有_{len(b_only)}注.txt",
                "double_bonly"
            )

            show_download(
                "下载不交集合并",
                non_inter,
                f"不交集合并_"
                f"{len(non_inter)}注.txt",
                "double_non"
            )

            show_download(
                "下载合并去重",
                union,
                f"合并去重_"
                f"{len(union)}注.txt",
                "double_union"
            )


# =========================================================
# 3. 口径1交集后数字形态轨
# =========================================================

elif mode == "口径1交集后数字形态轨":

    st.subheader(
        "口径1 → 三不同交集/独有 "
        "→ 数字形态轨"
    )

    text_a = st.text_input(
        "母号A条件",
        placeholder="例如：983十个"
    )

    text_b = st.text_input(
        "母号B条件",
        placeholder="例如：938十个"
    )

    digit_text = st.text_input(
        "数字轨",
        placeholder="例如：数字389"
    )

    shape_text = st.text_area(
        "形态轨（每行一个）",
        placeholder=(
            "大大小\n"
            "小小小\n"
            "奇偶奇\n"
            "偶奇偶"
        )
    )

    if st.button(
        "开始完整分析"
    ):

        pa, ea = parse_koujing1(
            text_a
        )

        pb, eb = parse_koujing1(
            text_b
        )

        digits = parse_digit_track(
            digit_text
        )

        shapes = [
            x.strip()
            for x in shape_text.splitlines()
            if x.strip()
        ]

        if ea:

            st.error(
                f"A：{ea}"
            )

        elif eb:

            st.error(
                f"B：{eb}"
            )

        elif not digits:

            st.error(
                "请输入数字轨"
            )

        elif len(shapes) != 4:

            st.error(
                "形态轨请输入4个完整形态"
            )

        else:

            invalid = [
                s for s in shapes
                if classify_shape_token(s)
                is None
            ]

            if invalid:

                st.error(
                    "无法识别："
                    +
                    "、".join(invalid)
                )

            else:

                ra = run_koujing1(
                    pa["mother"],
                    pa["size_pos"],
                    pa["parity_pos"]
                )

                rb = run_koujing1(
                    pb["mother"],
                    pb["size_pos"],
                    pb["parity_pos"]
                )

                # 此流程固定使用三不同
                A = set(
                    ra["different"]
                )

                B = set(
                    rb["different"]
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

                st.markdown(
                    "## ① 前置结果"
                )

                st.write(
                    f"A三不同："
                    f"**{len(A)} 注**"
                )

                st.write(
                    f"B三不同："
                    f"**{len(B)} 注**"
                )

                st.write(
                    f"交集："
                    f"**{len(inter)} 注**"
                )

                st.write(
                    f"A独有："
                    f"**{len(a_only)} 注**"
                )

                st.write(
                    f"B独有："
                    f"**{len(b_only)} 注**"
                )

                st.write(
                    f"不交集合并："
                    f"**{len(non_inter)} 注**"
                )

                left = len(A) + len(B)

                right = (
                    2 * len(inter)
                    +
                    len(non_inter)
                )

                if left == right:

                    st.success(
                        f"前置闭环："
                        f"{len(A)} + "
                        f"{len(B)} = "
                        f"2×{len(inter)} + "
                        f"{len(non_inter)} "
                        f"= {left} √"
                    )

                # 下载前置结果
                show_download(
                    "下载A三不同",
                    sorted(A),
                    f"A三不同_{len(A)}注.txt",
                    "track_a"
                )

                show_download(
                    "下载B三不同",
                    sorted(B),
                    f"B三不同_{len(B)}注.txt",
                    "track_b"
                )

                show_download(
                    "下载交集",
                    inter,
                    f"交集_{len(inter)}注.txt",
                    "track_inter"
                )

                show_download(
                    "下载A独有",
                    a_only,
                    f"A独有_{len(a_only)}注.txt",
                    "track_aonly"
                )

                show_download(
                    "下载B独有",
                    b_only,
                    f"B独有_{len(b_only)}注.txt",
                    "track_bonly"
                )

                show_download(
                    "下载不交集合并",
                    non_inter,
                    f"不交集合并_"
                    f"{len(non_inter)}注.txt",
                    "track_non"
                )

                # 数字轨
                digit_buckets, digit_bc = (
                    run_digit_track(
                        non_inter,
                        digits
                    )
                )

                st.markdown(
                    "## ② 数字轨"
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
                    f"数字BC："
                    f"**{len(digit_bc)} 注**"
                )

                show_download(
                    "下载数字BC",
                    digit_bc,
                    f"数字BC_"
                    f"{len(digit_bc)}注.txt",
                    "track_bc"
                )

                # 形态轨
                (
                    valid,
                    shape_buckets,
                    shape_cd
                ) = run_shape_track(
                    non_inter,
                    shapes
                )

                st.markdown(
                    "## ③ 形态轨"
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
                    f"形态CD："
                    f"**{len(shape_cd)} 注**"
                )

                show_download(
                    "下载形态CD",
                    shape_cd,
                    f"形态CD_"
                    f"{len(shape_cd)}注.txt",
                    "track_cd"
                )

                # 最终
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
                    "## ④ 最终"
                )

                st.write(
                    f"最终入选："
                    f"**{len(final_in)} 注**"
                )

                st.write(
                    f"最终不入选："
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
                        f"最终闭环："
                        f"{len(final_in)} + "
                        f"{len(final_out)} = "
                        f"{len(non_inter)} √"
                    )

                show_download(
                    "下载最终入选",
                    final_in,
                    f"最终入选_"
                    f"{len(final_in)}注.txt",
                    "track_final_in"
                )

                show_download(
                    "下载最终不入选",
                    final_out,
                    f"最终不入选_"
                    f"{len(final_out)}注.txt",
                    "track_final_out"
                )


# =========================================================
# 4. 普通交集 / 不交集
# =========================================================

elif mode == "交集 / 不交集":

    st.subheader(
        "两个附件交集 / 不交集"
    )

    file_a = st.file_uploader(
        "上传文件A",
        type=["txt"],
        key="normal_a"
    )

    file_b = st.file_uploader(
        "上传文件B",
        type=["txt"],
        key="normal_b"
    )

    if file_a and file_b:

        A = set(
            read_upload(file_a)
        )

        B = set(
            read_upload(file_b)
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
            f"不交集合并："
            f"**{len(non_inter)} 注**"
        )

        st.write(
            f"合并去重："
            f"**{len(union)} 注**"
        )

        left = len(A) + len(B)

        right = (
            2 * len(inter)
            +
            len(non_inter)
        )

        if left == right:

            st.success(
                f"闭环："
                f"{len(A)} + "
                f"{len(B)} = "
                f"2×{len(inter)} + "
                f"{len(non_inter)} "
                f"= {left} √"
            )

        show_download(
            "下载交集",
            inter,
            f"交集_{len(inter)}注.txt",
            "normal_inter"
        )

        show_download(
            "下载A独有",
            a_only,
            f"A独有_{len(a_only)}注.txt",
            "normal_aonly"
        )

        show_download(
            "下载B独有",
            b_only,
            f"B独有_{len(b_only)}注.txt",
            "normal_bonly"
        )

        show_download(
            "下载不交集合并",
            non_inter,
            f"不交集合并_"
            f"{len(non_inter)}注.txt",
            "normal_non"
        )

        show_download(
            "下载合并去重",
            union,
            f"合并去重_"
            f"{len(union)}注.txt",
            "normal_union"
        )


# =========================================================
# 5. A分别与多个附件交集
# =========================================================

elif mode == "A分别与多个文件交集":

    st.subheader(
        "A分别与多个附件交集"
    )

    file_a = st.file_uploader(
        "上传主文件A",
        type=["txt"],
        key="multi_a"
    )

    files = st.file_uploader(
        "上传B / C / D / E...",
        type=["txt"],
        accept_multiple_files=True,
        key="multi_files"
    )

    if file_a and files:

        A = set(
            read_upload(file_a)
        )

        for idx, f in enumerate(
            files,
            start=1
        ):

            B = set(
                read_upload(f)
            )

            label = chr(
                65 + idx
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

            st.divider()

            st.markdown(
                f"## A 与 {label}"
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
                f"**{len(b_only)} 注**"
            )

            st.write(
                f"不交集合并："
                f"**{len(non_inter)} 注**"
            )

            left = len(A) + len(B)

            right = (
                2 * len(inter)
                +
                len(non_inter)
            )

            if left == right:

                st.success(
                    f"闭环 √ "
                    f"{left} = {right}"
                )

            show_download(
                f"下载A∩{label}",
                inter,
                f"A与{label}交集_"
                f"{len(inter)}注.txt",
                f"multi_inter_{idx}"
            )

            show_download(
                f"下载A独有（相对{label}）",
                a_only,
                f"A对{label}独有_"
                f"{len(a_only)}注.txt",
                f"multi_a_{idx}"
            )

            show_download(
                f"下载{label}独有",
                b_only,
                f"{label}独有_"
                f"{len(b_only)}注.txt",
                f"multi_b_{idx}"
            )

            show_download(
                f"下载A与{label}不交集合并",
                non_inter,
                f"A与{label}不交集合并_"
                f"{len(non_inter)}注.txt",
                f"multi_non_{idx}"
            )


# =========================================================
# 6. 合并去重
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
                "请至少上传2个附件"
            )

        else:

            sets = []
            total = 0

            for f in files:

                nums = set(
                    read_upload(f)
                )

                sets.append(nums)

                total += len(nums)

                st.write(
                    f"{f.name}："
                    f"**{len(nums)} 注**"
                )

            merged = sorted(
                set().union(*sets)
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

            show_download(
                "下载合并去重",
                merged,
                f"合并去重_"
                f"{len(merged)}注.txt",
                "merge_result"
            )


# =========================================================
# 7. 形态筛选
# =========================================================

elif mode == "形态筛选":

    st.subheader(
        "按完整三位形态去除"
    )

    file = st.file_uploader(
        "上传原始附件",
        type=["txt"],
        key="shape_filter_file"
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

        original = read_upload(
            file
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

        show_download(
            "下载剩余组合",
            remain,
            f"剩余_{len(remain)}注.txt",
            "shape_remain"
        )

        show_download(
            "下载被去掉组合",
            removed,
            f"去掉_{len(removed)}注.txt",
            "shape_removed"
        )


# =========================================================
# 8. 二同 / 三同 / 三不同
# =========================================================

elif mode == "二同 / 三同 / 三不同":

    st.subheader(
        "二同 / 三同 / 三不同分类"
    )

    file = st.file_uploader(
        "上传附件",
        type=["txt"],
        key="repeat_file"
    )

    if file:

        original = read_upload(
            file
        )

        two = []
        three = []
        diff = []

        for num in original:

            tp = repeat_type(
                num
            )

            if tp == "二同":
                two.append(num)

            elif tp == "三同":
                three.append(num)

            else:
                diff.append(num)

        same23 = sorted(
            two + three
        )

        st.write(
            f"原始："
            f"**{len(original)} 注**"
        )

        st.write(
            f"二同："
            f"**{len(two)} 注**"
        )

        st.write(
            f"三同："
            f"**{len(three)} 注**"
        )

        st.write(
            f"二同+三同："
            f"**{len(same23)} 注**"
        )

        st.write(
            f"三不同："
            f"**{len(diff)} 注**"
        )

        if (
            len(same23)
            +
            len(diff)
            ==
            len(original)
        ):

            st.success(
                f"闭环："
                f"{len(same23)} + "
                f"{len(diff)} = "
                f"{len(original)} √"
            )

        show_download(
            "下载二同+三同",
            same23,
            f"二同三同_"
            f"{len(same23)}注.txt",
            "repeat_same"
        )

        show_download(
            "下载三不同",
            diff,
            f"三不同_"
            f"{len(diff)}注.txt",
            "repeat_diff"
        )

        show_download(
            "单独下载二同",
            two,
            f"二同_{len(two)}注.txt",
            "repeat_two"
        )

        show_download(
            "单独下载三同",
            three,
            f"三同_{len(three)}注.txt",
            "repeat_three"
        )


# =========================================================
# 9. 两位组合命中筛选（按附件）
# =========================================================

elif mode == "两位组合命中筛选（按附件）":

    st.subheader(
        "附件 + 两位组合条件"
    )

    file = st.file_uploader(
        "上传基础附件",
        type=["txt"],
        key="pair_file"
    )

    pair_text = st.text_area(
        "输入两位组合",
        placeholder=(
            "01 03 05 06 09 13\n"
            "15 16 18 19 34 35"
        ),
        height=150
    )

    pair_mode = st.radio(
        "筛选方式",
        [
            "两对命中（至少2对）",
            "恰好两对命中",
            "三对全命中",
        ],
        key="pair_file_mode"
    )

    if st.button(
        "开始筛选",
        key="pair_file_start"
    ):

        if not file:

            st.error(
                "请上传基础附件"
            )

        else:

            pairs = parse_pair_conditions(
                pair_text
            )

            if not pairs:

                st.error(
                    "请输入两位组合条件"
                )

            else:

                original = read_upload(
                    file
                )

                selected, rejected = (
                    run_pair_filter(
                        original,
                        pairs,
                        pair_mode
                    )
                )

                same23 = [
                    n for n in selected
                    if repeat_type(n)
                    != "三不同"
                ]

                diff = [
                    n for n in selected
                    if repeat_type(n)
                    == "三不同"
                ]

                st.write(
                    f"原附件："
                    f"**{len(original)} 注**"
                )

                st.write(
                    f"符合："
                    f"**{len(selected)} 注**"
                )

                st.write(
                    f"不符合："
                    f"**{len(rejected)} 注**"
                )

                st.write(
                    f"符合中的二同+三同："
                    f"**{len(same23)} 注**"
                )

                st.write(
                    f"符合中的三不同："
                    f"**{len(diff)} 注**"
                )

                if (
                    len(selected)
                    +
                    len(rejected)
                    ==
                    len(original)
                ):

                    st.success(
                        f"总闭环："
                        f"{len(selected)} + "
                        f"{len(rejected)} = "
                        f"{len(original)} √"
                    )

                if (
                    len(same23)
                    +
                    len(diff)
                    ==
                    len(selected)
                ):

                    st.success(
                        f"分类闭环："
                        f"{len(same23)} + "
                        f"{len(diff)} = "
                        f"{len(selected)} √"
                    )

                show_download(
                    "下载符合条件全量",
                    selected,
                    f"两位命中_符合_"
                    f"{len(selected)}注.txt",
                    "pair_file_selected"
                )

                show_download(
                    "下载不符合条件",
                    rejected,
                    f"两位命中_不符合_"
                    f"{len(rejected)}注.txt",
                    "pair_file_rejected"
                )

                show_download(
                    "下载二同+三同",
                    same23,
                    f"两位命中_二同三同_"
                    f"{len(same23)}注.txt",
                    "pair_file_same"
                )

                show_download(
                    "下载三不同",
                    diff,
                    f"两位命中_三不同_"
                    f"{len(diff)}注.txt",
                    "pair_file_diff"
                )


# =========================================================
# 10. 两位组合命中筛选（000-999）
# =========================================================

elif mode == "两位组合命中筛选（000-999）":

    st.subheader(
        "000-999 + 两位组合条件"
    )

    pair_text = st.text_area(
        "输入两位组合",
        placeholder=(
            "01 03 05 06 09 13\n"
            "15 16 18 19 34 35"
        ),
        height=160,
        key="pair_1000_text"
    )

    pair_mode = st.radio(
        "筛选方式",
        [
            "两对命中（至少2对）",
            "恰好两对命中",
            "三对全命中",
        ],
        key="pair_1000_mode"
    )

    if st.button(
        "从000-999开始筛选"
    ):

        pairs = parse_pair_conditions(
            pair_text
        )

        if not pairs:

            st.error(
                "请输入两位条件"
            )

        else:

            selected, rejected = (
                run_pair_filter(
                    ALL_NUMBERS,
                    pairs,
                    pair_mode
                )
            )

            same23 = [
                n for n in selected
                if repeat_type(n)
                != "三不同"
            ]

            diff = [
                n for n in selected
                if repeat_type(n)
                == "三不同"
            ]

            st.write(
                "原始：**1000 注**"
            )

            st.write(
                f"符合："
                f"**{len(selected)} 注**"
            )

            st.write(
                f"不符合："
                f"**{len(rejected)} 注**"
            )

            st.write(
                f"二同+三同："
                f"**{len(same23)} 注**"
            )

            st.write(
                f"三不同："
                f"**{len(diff)} 注**"
            )

            if (
                len(selected)
                +
                len(rejected)
                ==
                1000
            ):

                st.success(
                    f"总闭环："
                    f"{len(selected)} + "
                    f"{len(rejected)} = "
                    f"1000 √"
                )

            if (
                len(same23)
                +
                len(diff)
                ==
                len(selected)
            ):

                st.success(
                    f"分类闭环："
                    f"{len(same23)} + "
                    f"{len(diff)} = "
                    f"{len(selected)} √"
                )

            show_download(
                "下载符合条件全量",
                selected,
                f"000-999两位命中_"
                f"{len(selected)}注.txt",
                "pair_1000_selected"
            )

            show_download(
                "下载不符合条件",
                rejected,
                f"000-999两位不符合_"
                f"{len(rejected)}注.txt",
                "pair_1000_rejected"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"000-999两位命中_二同三同_"
                f"{len(same23)}注.txt",
                "pair_1000_same"
            )

            show_download(
                "下载三不同",
                diff,
                f"000-999两位命中_三不同_"
                f"{len(diff)}注.txt",
                "pair_1000_diff"
            )


# =========================================================
# 11. 数字包含 / 去除筛选
# =========================================================

elif mode == "数字包含 / 去除筛选":

    st.subheader(
        "按数字包含关系筛选"
    )

    file = st.file_uploader(
        "上传基础附件",
        type=["txt"],
        key="digit_filter_file"
    )

    digit_text = st.text_input(
        "输入数字",
        placeholder=(
            "例如：3 或 368"
        )
    )

    match_mode = st.radio(
        "多个数字如何判断",
        [
            "含任意一个",
            "必须同时含全部",
        ]
    )

    action = st.radio(
        "操作方式",
        [
            "筛出符合条件的组合",
            "去掉符合条件的组合",
        ]
    )

    if st.button(
        "开始数字筛选"
    ):

        if not file:

            st.error(
                "请上传附件"
            )

        else:

            digits = []

            for c in digit_text:

                if (
                    c.isdigit()
                    and
                    c not in digits
                ):
                    digits.append(c)

            if not digits:

                st.error(
                    "请输入数字"
                )

            else:

                original = read_upload(
                    file
                )

                matched = []
                unmatched = []

                for num in original:

                    if match_mode == "含任意一个":

                        ok = any(
                            d in num
                            for d in digits
                        )

                    else:

                        ok = all(
                            d in num
                            for d in digits
                        )

                    if ok:
                        matched.append(num)

                    else:
                        unmatched.append(num)

                if action == "筛出符合条件的组合":

                    remain = matched
                    removed = unmatched

                    remain_name = "符合条件"

                    removed_name = "不符合条件"

                else:

                    # 例如：去掉含9
                    remain = unmatched
                    removed = matched

                    remain_name = "去掉后剩余"

                    removed_name = "被去掉"

                st.write(
                    f"原始："
                    f"**{len(original)} 注**"
                )

                st.write(
                    f"{remain_name}："
                    f"**{len(remain)} 注**"
                )

                st.write(
                    f"{removed_name}："
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

                show_download(
                    f"下载{remain_name}",
                    remain,
                    f"{remain_name}_"
                    f"{len(remain)}注.txt",
                    "digit_filter_remain"
                )

                show_download(
                    f"下载{removed_name}",
                    removed,
                    f"{removed_name}_"
                    f"{len(removed)}注.txt",
                    "digit_filter_removed"
                )


# =========================================================
# 12. 半顺以上筛选
# =========================================================

elif mode == "半顺以上筛选":

    st.subheader(
        "从附件筛选半顺 + 全顺"
    )

    st.caption(
        "例如348、384属于半顺；"
        "345、354、435等属于全顺。"
    )

    file = st.file_uploader(
        "上传基础附件",
        type=["txt"],
        key="sequence_file"
    )

    if file:

        original = read_upload(
            file
        )

        half = []
        full_seq = []
        non_seq = []

        for num in original:

            tp = sequence_type(
                num
            )

            if tp == "全顺":
                full_seq.append(num)

            elif tp == "半顺":
                half.append(num)

            else:
                non_seq.append(num)

        half_or_more = sorted(
            half + full_seq
        )

        st.write(
            f"原始："
            f"**{len(original)} 注**"
        )

        st.write(
            f"半顺："
            f"**{len(half)} 注**"
        )

        st.write(
            f"全顺："
            f"**{len(full_seq)} 注**"
        )

        st.write(
            f"半顺以上："
            f"**{len(half_or_more)} 注**"
        )

        st.write(
            f"非半顺以上："
            f"**{len(non_seq)} 注**"
        )

        if (
            len(half)
            +
            len(full_seq)
            ==
            len(half_or_more)
        ):

            st.success(
                f"分类闭环1："
                f"{len(half)} + "
                f"{len(full_seq)} = "
                f"{len(half_or_more)} √"
            )

        if (
            len(half_or_more)
            +
            len(non_seq)
            ==
            len(original)
        ):

            st.success(
                f"分类闭环2："
                f"{len(half_or_more)} + "
                f"{len(non_seq)} = "
                f"{len(original)} √"
            )

        show_download(
            "下载半顺以上",
            half_or_more,
            f"半顺以上_"
            f"{len(half_or_more)}注.txt",
            "seq_all"
        )

        show_download(
            "单独下载半顺",
            half,
            f"半顺_{len(half)}注.txt",
            "seq_half"
        )

        show_download(
            "单独下载全顺",
            full_seq,
            f"全顺_{len(full_seq)}注.txt",
            "seq_full"
        )

        show_download(
            "下载非半顺以上",
            non_seq,
            f"非半顺以上_"
            f"{len(non_seq)}注.txt",
            "seq_non"
        )
