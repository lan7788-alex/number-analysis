import re
import streamlit as st

st.set_page_config(page_title="数字分析工具", page_icon="🔢", layout="centered")
st.title("🔢 数字分析工具")
st.caption("每次分析只使用本次输入的条件和附件，不自动调用其他操作的旧数据。")

ALL_NUMBERS = [f"{i:03d}" for i in range(1000)]
SIZE_SHAPES = ["大大大","大大小","大小大","大小小","小大大","小大小","小小大","小小小"]
PARITY_SHAPES = ["奇奇奇","奇奇偶","奇偶奇","奇偶偶","偶奇奇","偶奇偶","偶偶奇","偶偶偶"]
POSITION_MAP = {"百十":[0,1], "百个":[0,2], "十个":[1,2]}

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}

def save_result(name, data): st.session_state.analysis_results[name] = data
def get_result(name): return st.session_state.analysis_results.get(name)

def parse_numbers(text):
    return sorted(set(re.findall(r'(?<!\d)\d{3}(?!\d)', text or "")))

def read_upload(file):
    if file is None: return []
    data = file.getvalue()
    for enc in ["utf-8-sig","utf-8","gb18030","gbk"]:
        try: return parse_numbers(data.decode(enc))
        except Exception: pass
    return []

def format_txt(nums):
    nums = sorted(set(nums))
    return "\n".join(" ".join(nums[i:i+10]) for i in range(0,len(nums),10))

def show_download(label, nums, filename, key):
    st.download_button(label, format_txt(nums).encode("utf-8-sig"), filename, "text/plain", key=key)

def size_shape(num): return "".join("大" if int(d)>=5 else "小" for d in num)
def parity_shape(num): return "".join("奇" if int(d)%2 else "偶" for d in num)

def repeat_type(num):
    n=len(set(num))
    return "三不同" if n==3 else ("二同" if n==2 else "三同")

def allowed_shapes(mother_shape, position_name, all_shapes):
    pos=POSITION_MAP[position_name]
    return [s for s in all_shapes if not all(s[p]==mother_shape[p] for p in pos)]

def normalize_rule_text(text):
    text=(text or "").strip()
    for ch in [" ","+","/","／","，",",","；",";","：",":"]:
        text=text.replace(ch,"")
    return text

def parse_koujing1(text):
    text=normalize_rule_text(text)
    m=re.match(r'^(\d{3})(.*)$',text)
    if not m:
        return None,"格式无法识别"

    mother,rule=m.group(1),m.group(2)

    if rule in POSITION_MAP:
        return {
            "mother":mother,
            "size_pos":rule,
            "parity_pos":rule,
            "display_rule":rule
        },None

    m2=re.fullmatch(r'大小(百十|百个|十个)奇偶(百十|百个|十个)',rule)

    if m2:
        return {
            "mother":mother,
            "size_pos":m2.group(1),
            "parity_pos":m2.group(2),
            "display_rule":f"大小{m2.group(1)} + 奇偶{m2.group(2)}"
        },None

    return None,"取位无法识别，例如：818十个 或 888大小百十奇偶十个"

def run_koujing1(mother,size_pos,parity_pos):
    ms,mp=size_shape(mother),parity_shape(mother)
    asize=allowed_shapes(ms,size_pos,SIZE_SHAPES)
    apar=allowed_shapes(mp,parity_pos,PARITY_SHAPES)

    full=[
        n for n in ALL_NUMBERS
        if size_shape(n) in asize
        and parity_shape(n) in apar
    ]

    same=[
        n for n in full
        if repeat_type(n)!="三不同"
    ]

    diff=[
        n for n in full
        if repeat_type(n)=="三不同"
    ]

    return {
        "mother_size":ms,
        "mother_parity":mp,
        "allowed_size":asize,
        "allowed_parity":apar,
        "full":sorted(full),
        "same23":sorted(same),
        "different":sorted(diff)
    }

def parse_shape_pick(text):
    s=(text or "").replace(" ","").replace("+","").replace("/","").replace("／","").replace(",","").replace("，","")
    a=next((x for x in SIZE_SHAPES if x in s),None)
    b=next((x for x in PARITY_SHAPES if x in s),None)
    return a,b

def run_shape_pick(size_target=None,parity_target=None):
    full=[
        n for n in ALL_NUMBERS
        if (not size_target or size_shape(n)==size_target)
        and (not parity_target or parity_shape(n)==parity_target)
    ]

    same=[
        n for n in full
        if repeat_type(n)!="三不同"
    ]

    diff=[
        n for n in full
        if repeat_type(n)=="三不同"
    ]

    return {
        "full":sorted(full),
        "same23":sorted(same),
        "different":sorted(diff)
    }

def parse_digit_track(text):
    s=(text or "").replace("数字","").replace(" ","")
    out=[]

    for c in s:
        if c.isdigit() and c not in out:
            out.append(c)

    return out

def run_digit_track(base_nums,target_digits):
    buckets={}

    for num in base_nums:
        c=sum(1 for d in target_digits if d not in num)
        buckets.setdefault(c,[]).append(num)

    bc=sorted(
        set(buckets.get(2,[]))
        |
        set(buckets.get(3,[]))
    )

    return buckets,bc

def classify_shape_token(token):
    if token in SIZE_SHAPES: return "size"
    if token in PARITY_SHAPES: return "parity"
    return None

def run_shape_track(base_nums,shape_tokens):
    valid=[
        (t,classify_shape_token(t))
        for t in shape_tokens
        if classify_shape_token(t)
    ]

    counts={n:0 for n in base_nums}

    for token,kind in valid:
        for n in base_nums:
            matched=(size_shape(n)==token) if kind=="size" else (parity_shape(n)==token)
            if not matched:
                counts[n]+=1

    buckets={}

    for n,c in counts.items():
        buckets.setdefault(c,[]).append(n)

    cd=sorted(
        set(buckets.get(3,[]))
        |
        set(buckets.get(4,[]))
    )

    return valid,buckets,cd

def canonical_pair(pair):
    return "".join(sorted(pair)) if len(pair)==2 and pair.isdigit() else None

def parse_pair_conditions(text):
    return {
        canonical_pair(p)
        for p in re.findall(r'(?<!\d)\d{2}(?!\d)',text or "")
        if canonical_pair(p)
    }

def pair_hit_count(num,pair_set):
    a,b,c=num

    pairs=[
        canonical_pair(a+b),
        canonical_pair(a+c),
        canonical_pair(b+c)
    ]

    return sum(
        1 for p in pairs
        if p in pair_set
    )

def run_pair_filter(base_nums,pair_set,mode):
    sel,rej=[],[]

    for n in base_nums:
        h=pair_hit_count(n,pair_set)

        ok=(
            h>=2
            if mode=="两对命中（至少2对）"
            else (
                h==2
                if mode=="恰好两对命中"
                else h==3
            )
        )

        (sel if ok else rej).append(n)

    return sorted(sel),sorted(rej)

def sequence_type(num):
    d=sorted(int(x) for x in num)

    if len(set(d))!=3:
        return "非半顺"

    if d[1]-d[0]==1 and d[2]-d[1]==1:
        return "全顺"

    if d[1]-d[0]==1 or d[2]-d[1]==1:
        return "半顺"

    return "非半顺"

mode=st.selectbox(
    "选择功能",
    [
        "口径1取号",
        "形态取号",
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
        "半顺以上筛选"
    ]
)
# =========================================================
# 1. 口径1取号
# =========================================================

if mode=="口径1取号":

    st.subheader("口径1正常取号")

    with st.form("k1_form"):

        text=st.text_area(
            "输入条件（可多行）",
            placeholder=(
                "592百个\n"
                "888大小百十奇偶十个"
            ),
            height=140
        )

        submitted=st.form_submit_button(
            "开始取号"
        )

    if submitted:

        lines=[
            x.strip()
            for x in text.splitlines()
            if x.strip()
        ]

        results=[]
        errors=[]

        for line in lines:

            parsed,error=parse_koujing1(line)

            if error:
                errors.append(
                    f"{line}：{error}"
                )
                continue

            r=run_koujing1(
                parsed["mother"],
                parsed["size_pos"],
                parsed["parity_pos"]
            )

            results.append({
                "parsed":parsed,
                "result":r
            })

        save_result(
            "口径1取号",
            {
                "results":results,
                "errors":errors
            }
        )

    data=get_result("口径1取号")

    if data:

        for error in data["errors"]:
            st.error(error)

        for idx,item in enumerate(
            data["results"],
            start=1
        ):

            parsed=item["parsed"]
            r=item["result"]

            full=r["full"]
            same23=r["same23"]
            different=r["different"]

            st.divider()

            st.markdown(
                f"## {parsed['mother']} "
                f"{parsed['display_rule']}"
            )

            st.write(
                f"母号大小："
                f"**{r['mother_size']}**"
            )

            st.write(
                f"母号奇偶："
                f"**{r['mother_parity']}**"
            )

            st.write(
                "大小正常入选6形态："
                +
                "、".join(
                    r["allowed_size"]
                )
            )

            st.write(
                "奇偶正常入选6形态："
                +
                "、".join(
                    r["allowed_parity"]
                )
            )

            st.write(
                f"全量正常出号："
                f"**{len(full)} 注**"
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
                len(full)
            ):

                st.success(
                    f"闭环："
                    f"{len(same23)} + "
                    f"{len(different)} = "
                    f"{len(full)} √"
                )

            base=(
                f"{parsed['mother']}_"
                f"{parsed['size_pos']}_"
                f"{parsed['parity_pos']}"
            )

            show_download(
                "下载全量",
                full,
                f"{base}_全量_{len(full)}注.txt",
                f"k1_full_{idx}"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"{base}_二同三同_{len(same23)}注.txt",
                f"k1_same_{idx}"
            )

            show_download(
                "下载三不同",
                different,
                f"{base}_三不同_{len(different)}注.txt",
                f"k1_diff_{idx}"
            )


# =========================================================
# 2. 形态取号
# =========================================================

elif mode=="形态取号":

    st.subheader(
        "按完整大小 / 奇偶形态取号"
    )

    st.caption(
        "例如：大大小偶偶奇；"
        "也可以只输入大大小或偶偶奇。"
    )

    with st.form("shape_pick_form"):

        shape_text=st.text_area(
            "输入形态（可多行）",
            placeholder=(
                "大大小偶偶奇\n"
                "小小大 奇偶偶\n"
                "大大大"
            ),
            height=150
        )

        submitted=st.form_submit_button(
            "开始形态取号"
        )

    if submitted:

        lines=[
            x.strip()
            for x in shape_text.splitlines()
            if x.strip()
        ]

        results=[]
        errors=[]

        for line in lines:

            size_target,parity_target=(
                parse_shape_pick(line)
            )

            if (
                not size_target
                and
                not parity_target
            ):
                errors.append(
                    f"{line}：无法识别形态"
                )
                continue

            r=run_shape_pick(
                size_target,
                parity_target
            )

            results.append({
                "size_target":size_target,
                "parity_target":parity_target,
                "result":r
            })

        save_result(
            "形态取号",
            {
                "results":results,
                "errors":errors
            }
        )

    data=get_result("形态取号")

    if data:

        for error in data["errors"]:
            st.error(error)

        for idx,item in enumerate(
            data["results"],
            start=1
        ):

            r=item["result"]

            full=r["full"]
            same23=r["same23"]
            different=r["different"]

            title_parts=[]

            if item["size_target"]:
                title_parts.append(
                    item["size_target"]
                )

            if item["parity_target"]:
                title_parts.append(
                    item["parity_target"]
                )

            title=" + ".join(
                title_parts
            )

            st.divider()

            st.markdown(
                f"## {title}"
            )

            st.write(
                f"全量："
                f"**{len(full)} 注**"
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
                len(full)
            ):

                st.success(
                    f"闭环："
                    f"{len(same23)} + "
                    f"{len(different)} = "
                    f"{len(full)} √"
                )

            safe="_".join(
                title_parts
            )

            show_download(
                "下载全量",
                full,
                f"{safe}_全量_{len(full)}注.txt",
                f"shape_pick_full_{idx}"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"{safe}_二同三同_{len(same23)}注.txt",
                f"shape_pick_same_{idx}"
            )

            show_download(
                "下载三不同",
                different,
                f"{safe}_三不同_{len(different)}注.txt",
                f"shape_pick_diff_{idx}"
            )


# =========================================================
# 3. 口径1双条件全量交集
# =========================================================

elif mode=="口径1双条件全量交集":

    st.subheader(
        "两个口径1条件 → 全量交集"
    )

    with st.form(
        "double_k1_form"
    ):

        text_a=st.text_input(
            "条件A",
            placeholder="例如：818十个"
        )

        text_b=st.text_input(
            "条件B",
            placeholder="例如：881十个"
        )

        submitted=st.form_submit_button(
            "开始全量交集分析"
        )

    if submitted:

        pa,ea=parse_koujing1(
            text_a
        )

        pb,eb=parse_koujing1(
            text_b
        )

        if ea or eb:

            save_result(
                "口径1双条件全量交集",
                {
                    "error_a":ea,
                    "error_b":eb
                }
            )

        else:

            ra=run_koujing1(
                pa["mother"],
                pa["size_pos"],
                pa["parity_pos"]
            )

            rb=run_koujing1(
                pb["mother"],
                pb["size_pos"],
                pb["parity_pos"]
            )

            A=set(
                ra["full"]
            )

            B=set(
                rb["full"]
            )

            inter=sorted(
                A & B
            )

            a_only=sorted(
                A - B
            )

            b_only=sorted(
                B - A
            )

            non_inter=sorted(
                (A - B)
                |
                (B - A)
            )

            union=sorted(
                A | B
            )

            save_result(
                "口径1双条件全量交集",
                {
                    "error_a":None,
                    "error_b":None,
                    "A":sorted(A),
                    "B":sorted(B),
                    "inter":inter,
                    "a_only":a_only,
                    "b_only":b_only,
                    "non_inter":non_inter,
                    "union":union
                }
            )

    data=get_result(
        "口径1双条件全量交集"
    )

    if data:

        if data.get("error_a"):

            st.error(
                f"A：{data['error_a']}"
            )

        elif data.get("error_b"):

            st.error(
                f"B：{data['error_b']}"
            )

        elif "A" in data:

            A=data["A"]
            B=data["B"]

            inter=data["inter"]
            a_only=data["a_only"]
            b_only=data["b_only"]
            non_inter=data["non_inter"]
            union=data["union"]

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

            left=(
                len(A)
                +
                len(B)
            )

            right=(
                2*len(inter)
                +
                len(non_inter)
            )

            if left==right:

                st.success(
                    f"闭环："
                    f"{len(A)} + "
                    f"{len(B)} = "
                    f"2×{len(inter)} + "
                    f"{len(non_inter)} "
                    f"= {left} √"
                )

            show_download(
                "下载A全量",
                A,
                f"A全量_{len(A)}注.txt",
                "double_a"
            )

            show_download(
                "下载B全量",
                B,
                f"B全量_{len(B)}注.txt",
                "double_b"
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
                "double_a_only"
            )

            show_download(
                "下载B独有",
                b_only,
                f"B独有_{len(b_only)}注.txt",
                "double_b_only"
            )

            show_download(
                "下载不交集合并",
                non_inter,
                f"不交集合并_{len(non_inter)}注.txt",
                "double_non"
            )

            show_download(
                "下载合并去重",
                union,
                f"合并去重_{len(union)}注.txt",
                "double_union"
            )
            # =========================================================
# 4. 口径1交集后数字形态轨
# =========================================================

elif mode=="口径1交集后数字形态轨":

    st.subheader(
        "口径1 → 三不同交集/独有 → "
        "数字BC → 形态CD → BC∩CD"
    )

    with st.form(
        "track_form"
    ):

        text_a=st.text_input(
            "母号A条件",
            placeholder="例如：983十个"
        )

        text_b=st.text_input(
            "母号B条件",
            placeholder="例如：938十个"
        )

        digit_text=st.text_input(
            "数字轨",
            placeholder="例如：数字389"
        )

        shape_text=st.text_area(
            "形态轨（4个完整三位形态，每行一个）",
            placeholder=(
                "大大小\n"
                "小小小\n"
                "奇偶奇\n"
                "偶奇偶"
            ),
            height=140
        )

        submitted=st.form_submit_button(
            "开始完整分析"
        )

    if submitted:

        pa,ea=parse_koujing1(
            text_a
        )

        pb,eb=parse_koujing1(
            text_b
        )

        digits=parse_digit_track(
            digit_text
        )

        shapes=[
            x.strip()
            for x in shape_text.splitlines()
            if x.strip()
        ]

        error=None

        if ea:
            error=f"A：{ea}"

        elif eb:
            error=f"B：{eb}"

        elif not digits:
            error="请输入数字轨"

        elif len(shapes)!=4:
            error="形态轨必须输入4个完整三位形态"

        else:

            invalid=[
                s
                for s in shapes
                if classify_shape_token(s)
                is None
            ]

            if invalid:
                error=(
                    "无法识别形态："
                    +
                    "、".join(invalid)
                )

        if error:

            save_result(
                "口径1交集后数字形态轨",
                {
                    "error":error
                }
            )

        else:

            ra=run_koujing1(
                pa["mother"],
                pa["size_pos"],
                pa["parity_pos"]
            )

            rb=run_koujing1(
                pb["mother"],
                pb["size_pos"],
                pb["parity_pos"]
            )

            A=set(
                ra["different"]
            )

            B=set(
                rb["different"]
            )

            inter=sorted(
                A & B
            )

            a_only=sorted(
                A - B
            )

            b_only=sorted(
                B - A
            )

            non_inter=sorted(
                (A - B)
                |
                (B - A)
            )

            digit_buckets,digit_bc=(
                run_digit_track(
                    non_inter,
                    digits
                )
            )

            (
                valid_shapes,
                shape_buckets,
                shape_cd
            )=run_shape_track(
                non_inter,
                shapes
            )

            final_in=sorted(
                set(digit_bc)
                &
                set(shape_cd)
            )

            final_out=sorted(
                set(non_inter)
                -
                set(final_in)
            )

            save_result(
                "口径1交集后数字形态轨",
                {
                    "error":None,
                    "A":sorted(A),
                    "B":sorted(B),
                    "inter":inter,
                    "a_only":a_only,
                    "b_only":b_only,
                    "non_inter":non_inter,
                    "digits":digits,
                    "digit_buckets":digit_buckets,
                    "digit_bc":digit_bc,
                    "valid_shapes":valid_shapes,
                    "shape_buckets":shape_buckets,
                    "shape_cd":shape_cd,
                    "final_in":final_in,
                    "final_out":final_out
                }
            )

    data=get_result(
        "口径1交集后数字形态轨"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        elif "A" in data:

            A=data["A"]
            B=data["B"]
            inter=data["inter"]
            a_only=data["a_only"]
            b_only=data["b_only"]
            non_inter=data["non_inter"]

            st.markdown(
                "## ① 前置母号结果"
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

            left=(
                len(A)
                +
                len(B)
            )

            right=(
                2*len(inter)
                +
                len(non_inter)
            )

            if left==right:

                st.success(
                    f"前置闭环："
                    f"{len(A)} + "
                    f"{len(B)} = "
                    f"2×{len(inter)} + "
                    f"{len(non_inter)} "
                    f"= {left} √"
                )

            show_download(
                "下载A三不同",
                A,
                f"A三不同_{len(A)}注.txt",
                "track_a"
            )

            show_download(
                "下载B三不同",
                B,
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
                "track_a_only"
            )

            show_download(
                "下载B独有",
                b_only,
                f"B独有_{len(b_only)}注.txt",
                "track_b_only"
            )

            show_download(
                "下载不交集合并",
                non_inter,
                f"不交集合并_{len(non_inter)}注.txt",
                "track_non"
            )

            digit_buckets=data[
                "digit_buckets"
            ]

            digit_bc=data[
                "digit_bc"
            ]

            st.markdown(
                "## ② 数字轨"
            )

            st.write(
                "目标数字："
                +
                "、".join(
                    data["digits"]
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
                f"数字BC（2次+3次）："
                f"**{len(digit_bc)} 注**"
            )

            show_download(
                "下载数字BC",
                digit_bc,
                f"数字BC_{len(digit_bc)}注.txt",
                "track_bc"
            )

            shape_buckets=data[
                "shape_buckets"
            ]

            shape_cd=data[
                "shape_cd"
            ]

            st.markdown(
                "## ③ 形态轨"
            )

            st.write(
                "形态："
                +
                "、".join(
                    s
                    for s,_
                    in data["valid_shapes"]
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
                f"形态CD（3次+4次）："
                f"**{len(shape_cd)} 注**"
            )

            show_download(
                "下载形态CD",
                shape_cd,
                f"形态CD_{len(shape_cd)}注.txt",
                "track_cd"
            )

            final_in=data[
                "final_in"
            ]

            final_out=data[
                "final_out"
            ]

            st.markdown(
                "## ④ 最终数字形态轨"
            )

            st.write(
                f"最终入选 BC∩CD："
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
                f"最终入选_{len(final_in)}注.txt",
                "track_final_in"
            )

            show_download(
                "下载最终不入选",
                final_out,
                f"最终不入选_{len(final_out)}注.txt",
                "track_final_out"
            )


# =========================================================
# 5. 交集 / 不交集
# =========================================================

elif mode=="交集 / 不交集":

    st.subheader(
        "两个附件交集 / 不交集"
    )

    with st.form(
        "normal_intersection_form"
    ):

        file_a=st.file_uploader(
            "上传文件A",
            type=["txt"],
            key="normal_a_file"
        )

        file_b=st.file_uploader(
            "上传文件B",
            type=["txt"],
            key="normal_b_file"
        )

        submitted=st.form_submit_button(
            "开始分析"
        )

    if submitted:

        if (
            file_a is None
            or
            file_b is None
        ):

            save_result(
                "交集 / 不交集",
                {
                    "error":
                    "请同时上传A和B附件"
                }
            )

        else:

            A=set(
                read_upload(file_a)
            )

            B=set(
                read_upload(file_b)
            )

            inter=sorted(
                A & B
            )

            a_only=sorted(
                A - B
            )

            b_only=sorted(
                B - A
            )

            non_inter=sorted(
                (A - B)
                |
                (B - A)
            )

            union=sorted(
                A | B
            )

            save_result(
                "交集 / 不交集",
                {
                    "error":None,
                    "A":sorted(A),
                    "B":sorted(B),
                    "inter":inter,
                    "a_only":a_only,
                    "b_only":b_only,
                    "non_inter":non_inter,
                    "union":union
                }
            )

    data=get_result(
        "交集 / 不交集"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        elif "A" in data:

            A=data["A"]
            B=data["B"]

            inter=data["inter"]
            a_only=data["a_only"]
            b_only=data["b_only"]
            non_inter=data["non_inter"]
            union=data["union"]

            st.write(
                f"A：**{len(A)} 注**"
            )

            st.write(
                f"B：**{len(B)} 注**"
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

            left=(
                len(A)
                +
                len(B)
            )

            right=(
                2*len(inter)
                +
                len(non_inter)
            )

            if left==right:

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
                "normal_inter_dl"
            )

            show_download(
                "下载A独有",
                a_only,
                f"A独有_{len(a_only)}注.txt",
                "normal_a_only_dl"
            )

            show_download(
                "下载B独有",
                b_only,
                f"B独有_{len(b_only)}注.txt",
                "normal_b_only_dl"
            )

            show_download(
                "下载不交集合并",
                non_inter,
                f"不交集合并_{len(non_inter)}注.txt",
                "normal_non_dl"
            )

            show_download(
                "下载合并去重",
                union,
                f"合并去重_{len(union)}注.txt",
                "normal_union_dl"
            )


# =========================================================
# 6. A分别与多个文件交集
# =========================================================

elif mode=="A分别与多个文件交集":

    st.subheader(
        "A分别与B / C / D / E...做交集"
    )

    with st.form(
        "multi_inter_form"
    ):

        file_a=st.file_uploader(
            "上传主文件A",
            type=["txt"],
            key="multi_a_file"
        )

        files=st.file_uploader(
            "上传B / C / D / E...",
            type=["txt"],
            accept_multiple_files=True,
            key="multi_other_files"
        )

        submitted=st.form_submit_button(
            "开始分析"
        )

    if submitted:

        if file_a is None:

            save_result(
                "A分别与多个文件交集",
                {
                    "error":
                    "请上传主文件A"
                }
            )

        elif not files:

            save_result(
                "A分别与多个文件交集",
                {
                    "error":
                    "请至少上传一个比较附件"
                }
            )

        else:

            A=set(
                read_upload(file_a)
            )

            outputs=[]

            for idx,f in enumerate(
                files,
                start=1
            ):

                B=set(
                    read_upload(f)
                )

                label=chr(
                    65+idx
                )

                inter=sorted(
                    A & B
                )

                a_only=sorted(
                    A - B
                )

                b_only=sorted(
                    B - A
                )

                non_inter=sorted(
                    (A - B)
                    |
                    (B - A)
                )

                outputs.append({
                    "label":label,
                    "filename":f.name,
                    "A":sorted(A),
                    "B":sorted(B),
                    "inter":inter,
                    "a_only":a_only,
                    "b_only":b_only,
                    "non_inter":non_inter
                })

            save_result(
                "A分别与多个文件交集",
                {
                    "error":None,
                    "outputs":outputs
                }
            )

    data=get_result(
        "A分别与多个文件交集"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            for idx,item in enumerate(
                data["outputs"],
                start=1
            ):

                label=item["label"]

                A=item["A"]
                B=item["B"]

                inter=item["inter"]
                a_only=item["a_only"]
                b_only=item["b_only"]
                non_inter=item["non_inter"]

                st.divider()

                st.markdown(
                    f"## A 与 {label}"
                )

                st.caption(
                    f"{label}文件："
                    f"{item['filename']}"
                )

                st.write(
                    f"A：**{len(A)} 注**"
                )

                st.write(
                    f"{label}："
                    f"**{len(B)} 注**"
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

                left=(
                    len(A)
                    +
                    len(B)
                )

                right=(
                    2*len(inter)
                    +
                    len(non_inter)
                )

                if left==right:

                    st.success(
                        f"闭环："
                        f"{left} = "
                        f"{right} √"
                    )

                show_download(
                    f"下载A∩{label}",
                    inter,
                    f"A与{label}交集_{len(inter)}注.txt",
                    f"multi_inter_dl_{idx}"
                )

                show_download(
                    f"下载A独有（相对{label}）",
                    a_only,
                    f"A对{label}独有_{len(a_only)}注.txt",
                    f"multi_aonly_dl_{idx}"
                )

                show_download(
                    f"下载{label}独有",
                    b_only,
                    f"{label}独有_{len(b_only)}注.txt",
                    f"multi_bonly_dl_{idx}"
                )

                show_download(
                    f"下载A与{label}不交集合并",
                    non_inter,
                    f"A与{label}不交集合并_{len(non_inter)}注.txt",
                    f"multi_non_dl_{idx}"
            )
                # =========================================================
# 7. 合并去重
# =========================================================

elif mode=="合并去重":

    st.subheader(
        "多个附件合并去重"
    )

    with st.form(
        "merge_form"
    ):

        files=st.file_uploader(
            "上传两个或多个TXT",
            type=["txt"],
            accept_multiple_files=True,
            key="merge_files"
        )

        submitted=st.form_submit_button(
            "开始合并去重"
        )

    if submitted:

        if (
            not files
            or
            len(files)<2
        ):

            save_result(
                "合并去重",
                {
                    "error":
                    "请至少上传两个附件"
                }
            )

        else:

            sets=[]
            details=[]
            total=0

            for f in files:

                nums=set(
                    read_upload(f)
                )

                sets.append(
                    nums
                )

                details.append({
                    "name":f.name,
                    "count":len(nums)
                })

                total+=len(nums)

            merged=sorted(
                set().union(
                    *sets
                )
            )

            duplicate=(
                total
                -
                len(merged)
            )

            save_result(
                "合并去重",
                {
                    "error":None,
                    "details":details,
                    "total":total,
                    "duplicate":duplicate,
                    "merged":merged
                }
            )

    data=get_result(
        "合并去重"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            for item in data["details"]:

                st.write(
                    f"{item['name']}："
                    f"**{item['count']} 注**"
                )

            st.write(
                f"累计："
                f"**{data['total']} 注**"
            )

            st.write(
                f"合并去重："
                f"**{len(data['merged'])} 注**"
            )

            st.write(
                f"重复计数："
                f"**{data['duplicate']}**"
            )

            st.success(
                f"闭环："
                f"{data['total']} - "
                f"{data['duplicate']} = "
                f"{len(data['merged'])} √"
            )

            show_download(
                "下载合并去重",
                data["merged"],
                f"合并去重_{len(data['merged'])}注.txt",
                "merge_dl"
            )


# =========================================================
# 8. 形态筛选
# =========================================================

elif mode=="形态筛选":

    st.subheader(
        "按完整三位形态删除"
    )

    with st.form(
        "shape_filter_form"
    ):

        file=st.file_uploader(
            "上传基础附件",
            type=["txt"],
            key="shape_filter_file"
        )

        selected_size=st.multiselect(
            "要去掉的大小形态",
            SIZE_SHAPES
        )

        selected_parity=st.multiselect(
            "要去掉的奇偶形态",
            PARITY_SHAPES
        )

        submitted=st.form_submit_button(
            "开始筛选"
        )

    if submitted:

        if file is None:

            save_result(
                "形态筛选",
                {
                    "error":
                    "请上传附件"
                }
            )

        else:

            original=read_upload(
                file
            )

            remain=[]
            removed=[]

            for num in original:

                remove=(
                    size_shape(num)
                    in selected_size
                    or
                    parity_shape(num)
                    in selected_parity
                )

                if remove:
                    removed.append(
                        num
                    )

                else:
                    remain.append(
                        num
                    )

            save_result(
                "形态筛选",
                {
                    "error":None,
                    "original":original,
                    "remain":sorted(remain),
                    "removed":sorted(removed)
                }
            )

    data=get_result(
        "形态筛选"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            remain=data[
                "remain"
            ]

            removed=data[
                "removed"
            ]

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
                "shape_remain_dl"
            )

            show_download(
                "下载被去掉组合",
                removed,
                f"被去掉_{len(removed)}注.txt",
                "shape_removed_dl"
            )


# =========================================================
# 9. 二同 / 三同 / 三不同
# =========================================================

elif mode=="二同 / 三同 / 三不同":

    st.subheader(
        "二同 / 三同 / 三不同分类"
    )

    with st.form(
        "repeat_form"
    ):

        file=st.file_uploader(
            "上传附件",
            type=["txt"],
            key="repeat_file"
        )

        submitted=st.form_submit_button(
            "开始分类"
        )

    if submitted:

        if file is None:

            save_result(
                "二同 / 三同 / 三不同",
                {
                    "error":
                    "请上传附件"
                }
            )

        else:

            original=read_upload(
                file
            )

            two=[]
            three=[]
            different=[]

            for num in original:

                tp=repeat_type(
                    num
                )

                if tp=="二同":

                    two.append(
                        num
                    )

                elif tp=="三同":

                    three.append(
                        num
                    )

                else:

                    different.append(
                        num
                    )

            same23=sorted(
                two
                +
                three
            )

            save_result(
                "二同 / 三同 / 三不同",
                {
                    "error":None,
                    "original":original,
                    "two":sorted(two),
                    "three":sorted(three),
                    "same23":same23,
                    "different":sorted(different)
                }
            )

    data=get_result(
        "二同 / 三同 / 三不同"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            two=data[
                "two"
            ]

            three=data[
                "three"
            ]

            same23=data[
                "same23"
            ]

            different=data[
                "different"
            ]

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

            show_download(
                "下载二同+三同",
                same23,
                f"二同三同_{len(same23)}注.txt",
                "repeat_same_dl"
            )

            show_download(
                "下载三不同",
                different,
                f"三不同_{len(different)}注.txt",
                "repeat_diff_dl"
            )

            show_download(
                "单独下载二同",
                two,
                f"二同_{len(two)}注.txt",
                "repeat_two_dl"
            )

            show_download(
                "单独下载三同",
                three,
                f"三同_{len(three)}注.txt",
                "repeat_three_dl"
            )


# =========================================================
# 10. 两位组合命中筛选（按附件）
# =========================================================

elif mode=="两位组合命中筛选（按附件）":

    st.subheader(
        "附件 + 两位组合条件"
    )

    with st.form(
        "pair_file_form"
    ):

        file=st.file_uploader(
            "上传基础附件",
            type=["txt"],
            key="pair_base_file"
        )

        pair_text=st.text_area(
            "输入两位组合",
            placeholder=(
                "01 03 05 06 09 13 15 16 18 19\n"
                "34 35 36 37 38 39 48 49 56 58"
            ),
            height=170
        )

        pair_mode=st.radio(
            "筛选方式",
            [
                "两对命中（至少2对）",
                "恰好两对命中",
                "三对全命中"
            ],
            key="pair_file_mode"
        )

        submitted=st.form_submit_button(
            "开始筛选"
        )

    if submitted:

        if file is None:

            save_result(
                "两位组合命中筛选（按附件）",
                {
                    "error":
                    "请上传基础附件"
                }
            )

        else:

            pairs=parse_pair_conditions(
                pair_text
            )

            if not pairs:

                save_result(
                    "两位组合命中筛选（按附件）",
                    {
                        "error":
                        "请输入两位组合条件"
                    }
                )

            else:

                original=read_upload(
                    file
                )

                selected,rejected=(
                    run_pair_filter(
                        original,
                        pairs,
                        pair_mode
                    )
                )

                same23=[
                    n
                    for n in selected
                    if repeat_type(n)
                    !="三不同"
                ]

                different=[
                    n
                    for n in selected
                    if repeat_type(n)
                    =="三不同"
                ]

                save_result(
                    "两位组合命中筛选（按附件）",
                    {
                        "error":None,
                        "original":original,
                        "selected":selected,
                        "rejected":rejected,
                        "same23":sorted(same23),
                        "different":sorted(different),
                        "pair_count":len(pairs),
                        "pair_mode":pair_mode
                    }
                )

    data=get_result(
        "两位组合命中筛选（按附件）"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            selected=data[
                "selected"
            ]

            rejected=data[
                "rejected"
            ]

            same23=data[
                "same23"
            ]

            different=data[
                "different"
            ]

            st.write(
                f"两位条件："
                f"**{data['pair_count']}组**"
            )

            st.write(
                f"模式："
                f"**{data['pair_mode']}**"
            )

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
                f"**{len(different)} 注**"
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
                len(different)
                ==
                len(selected)
            ):

                st.success(
                    f"分类闭环："
                    f"{len(same23)} + "
                    f"{len(different)} = "
                    f"{len(selected)} √"
                )

            show_download(
                "下载符合条件全量",
                selected,
                f"两位命中_符合_{len(selected)}注.txt",
                "pair_file_selected_dl"
            )

            show_download(
                "下载不符合条件",
                rejected,
                f"两位命中_不符合_{len(rejected)}注.txt",
                "pair_file_rejected_dl"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"两位命中_二同三同_{len(same23)}注.txt",
                "pair_file_same_dl"
            )

            show_download(
                "下载三不同",
                different,
                f"两位命中_三不同_{len(different)}注.txt",
                "pair_file_diff_dl"
        )
            # =========================================================
# 11. 两位组合命中筛选（000-999）
# =========================================================

elif mode=="两位组合命中筛选（000-999）":

    st.subheader(
        "000-999 + 两位组合条件"
    )

    with st.form(
        "pair_all_form"
    ):

        pair_text=st.text_area(
            "输入两位组合",
            placeholder=(
                "01 03 05 06 09 13 15 16 18 19\n"
                "34 35 36 37 38 39 48 49 56 58"
            ),
            height=170
        )

        pair_mode=st.radio(
            "筛选方式",
            [
                "两对命中（至少2对）",
                "恰好两对命中",
                "三对全命中"
            ],
            key="pair_all_mode"
        )

        submitted=st.form_submit_button(
            "开始筛选"
        )

    if submitted:

        pairs=parse_pair_conditions(
            pair_text
        )

        if not pairs:

            save_result(
                "两位组合命中筛选（000-999）",
                {
                    "error":
                    "请输入两位组合条件"
                }
            )

        else:

            original=ALL_NUMBERS

            selected,rejected=(
                run_pair_filter(
                    original,
                    pairs,
                    pair_mode
                )
            )

            same23=[
                n
                for n in selected
                if repeat_type(n)
                !="三不同"
            ]

            different=[
                n
                for n in selected
                if repeat_type(n)
                =="三不同"
            ]

            save_result(
                "两位组合命中筛选（000-999）",
                {
                    "error":None,
                    "original":original,
                    "selected":selected,
                    "rejected":rejected,
                    "same23":sorted(same23),
                    "different":sorted(different),
                    "pair_count":len(pairs),
                    "pair_mode":pair_mode
                }
            )

    data=get_result(
        "两位组合命中筛选（000-999）"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            selected=data[
                "selected"
            ]

            rejected=data[
                "rejected"
            ]

            same23=data[
                "same23"
            ]

            different=data[
                "different"
            ]

            st.write(
                f"两位条件："
                f"**{data['pair_count']}组**"
            )

            st.write(
                f"模式："
                f"**{data['pair_mode']}**"
            )

            st.write(
                f"000-999全量："
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
                f"**{len(different)} 注**"
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
                len(different)
                ==
                len(selected)
            ):

                st.success(
                    f"分类闭环："
                    f"{len(same23)} + "
                    f"{len(different)} = "
                    f"{len(selected)} √"
                )

            show_download(
                "下载符合条件全量",
                selected,
                f"000-999两位命中_符合_{len(selected)}注.txt",
                "pair_all_selected_dl"
            )

            show_download(
                "下载不符合条件",
                rejected,
                f"000-999两位命中_不符合_{len(rejected)}注.txt",
                "pair_all_rejected_dl"
            )

            show_download(
                "下载二同+三同",
                same23,
                f"000-999两位命中_二同三同_{len(same23)}注.txt",
                "pair_all_same_dl"
            )

            show_download(
                "下载三不同",
                different,
                f"000-999两位命中_三不同_{len(different)}注.txt",
                "pair_all_diff_dl"
            )


# =========================================================
# 12. 数字包含 / 去除筛选
# =========================================================

elif mode=="数字包含 / 去除筛选":

    st.subheader(
        "按数字包含关系筛选"
    )

    with st.form(
        "digit_filter_form"
    ):

        file=st.file_uploader(
            "上传基础附件",
            type=["txt"],
            key="digit_filter_file"
        )

        digit_text=st.text_input(
            "输入一个或多个数字",
            placeholder="例如：8 或 368"
        )

        match_mode=st.radio(
            "多个数字如何判断",
            [
                "含任意一个",
                "必须同时含全部"
            ]
        )

        action=st.radio(
            "操作方式",
            [
                "筛出符合条件的组合",
                "去掉符合条件的组合"
            ]
        )

        submitted=st.form_submit_button(
            "开始数字筛选"
        )

    if submitted:

        if file is None:

            save_result(
                "数字包含 / 去除筛选",
                {
                    "error":
                    "请上传基础附件"
                }
            )

        else:

            digits=[]

            for c in digit_text:

                if (
                    c.isdigit()
                    and
                    c not in digits
                ):

                    digits.append(
                        c
                    )

            if not digits:

                save_result(
                    "数字包含 / 去除筛选",
                    {
                        "error":
                        "请输入要筛选的数字"
                    }
                )

            else:

                original=read_upload(
                    file
                )

                matched=[]
                unmatched=[]

                for num in original:

                    if match_mode=="含任意一个":

                        ok=any(
                            d in num
                            for d in digits
                        )

                    else:

                        ok=all(
                            d in num
                            for d in digits
                        )

                    if ok:

                        matched.append(
                            num
                        )

                    else:

                        unmatched.append(
                            num
                        )

                if action=="筛出符合条件的组合":

                    result=matched
                    other=unmatched

                    result_name="符合条件"
                    other_name="不符合条件"

                else:

                    result=unmatched
                    other=matched

                    result_name="去掉后剩余"
                    other_name="被去掉"

                save_result(
                    "数字包含 / 去除筛选",
                    {
                        "error":None,
                        "original":original,
                        "result":sorted(result),
                        "other":sorted(other),
                        "result_name":result_name,
                        "other_name":other_name,
                        "digits":digits,
                        "match_mode":match_mode,
                        "action":action
                    }
                )

    data=get_result(
        "数字包含 / 去除筛选"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            result=data[
                "result"
            ]

            other=data[
                "other"
            ]

            st.write(
                "数字："
                +
                "、".join(
                    data["digits"]
                )
            )

            st.write(
                f"判断方式："
                f"**{data['match_mode']}**"
            )

            st.write(
                f"操作："
                f"**{data['action']}**"
            )

            st.write(
                f"原始："
                f"**{len(original)} 注**"
            )

            st.write(
                f"{data['result_name']}："
                f"**{len(result)} 注**"
            )

            st.write(
                f"{data['other_name']}："
                f"**{len(other)} 注**"
            )

            if (
                len(result)
                +
                len(other)
                ==
                len(original)
            ):

                st.success(
                    f"闭环："
                    f"{len(result)} + "
                    f"{len(other)} = "
                    f"{len(original)} √"
                )

            show_download(
                f"下载{data['result_name']}",
                result,
                f"{data['result_name']}_{len(result)}注.txt",
                "digit_result_dl"
            )

            show_download(
                f"下载{data['other_name']}",
                other,
                f"{data['other_name']}_{len(other)}注.txt",
                "digit_other_dl"
            )


# =========================================================
# 13. 半顺以上筛选
# =========================================================

elif mode=="半顺以上筛选":

    st.subheader(
        "半顺 / 全顺筛选"
    )

    st.caption(
        "例如：348、384属于半顺；"
        "345及其排列属于全顺。"
    )

    with st.form(
        "sequence_form"
    ):

        file=st.file_uploader(
            "上传基础附件",
            type=["txt"],
            key="sequence_file"
        )

        submitted=st.form_submit_button(
            "开始筛选"
        )

    if submitted:

        if file is None:

            save_result(
                "半顺以上筛选",
                {
                    "error":
                    "请上传基础附件"
                }
            )

        else:

            original=read_upload(
                file
            )

            half=[
                n
                for n in original
                if sequence_type(n)
                =="半顺"
            ]

            full=[
                n
                for n in original
                if sequence_type(n)
                =="全顺"
            ]

            non=[
                n
                for n in original
                if sequence_type(n)
                =="非半顺"
            ]

            half_or_more=sorted(
                half
                +
                full
            )

            save_result(
                "半顺以上筛选",
                {
                    "error":None,
                    "original":original,
                    "half":sorted(half),
                    "full":sorted(full),
                    "half_or_more":half_or_more,
                    "non":sorted(non)
                }
            )

    data=get_result(
        "半顺以上筛选"
    )

    if data:

        if data.get("error"):

            st.error(
                data["error"]
            )

        else:

            original=data[
                "original"
            ]

            half=data[
                "half"
            ]

            full=data[
                "full"
            ]

            half_or_more=data[
                "half_or_more"
            ]

            non=data[
                "non"
            ]

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
                f"**{len(full)} 注**"
            )

            st.write(
                f"半顺以上："
                f"**{len(half_or_more)} 注**"
            )

            st.write(
                f"非半顺以上："
                f"**{len(non)} 注**"
            )

            if (
                len(half)
                +
                len(full)
                ==
                len(half_or_more)
            ):

                st.success(
                    f"分类闭环1："
                    f"{len(half)} + "
                    f"{len(full)} = "
                    f"{len(half_or_more)} √"
                )

            if (
                len(half_or_more)
                +
                len(non)
                ==
                len(original)
            ):

                st.success(
                    f"分类闭环2："
                    f"{len(half_or_more)} + "
                    f"{len(non)} = "
                    f"{len(original)} √"
                )

            show_download(
                "下载半顺以上",
                half_or_more,
                f"半顺以上_{len(half_or_more)}注.txt",
                "sequence_all_dl"
            )

            show_download(
                "单独下载半顺",
                half,
                f"半顺_{len(half)}注.txt",
                "sequence_half_dl"
            )

            show_download(
                "单独下载全顺",
                full,
                f"全顺_{len(full)}注.txt",
                "sequence_full_dl"
            )

            show_download(
                "下载非半顺以上",
                non,
                f"非半顺以上_{len(non)}注.txt",
                "sequence_non_dl"
            )
