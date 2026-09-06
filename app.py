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
    n=len(set(num)); return "三不同" if n==3 else ("二同" if n==2 else "三同")

def allowed_shapes(mother_shape, position_name, all_shapes):
    pos=POSITION_MAP[position_name]
    return [s for s in all_shapes if not all(s[p]==mother_shape[p] for p in pos)]

def normalize_rule_text(text):
    text=(text or "").strip()
    for ch in [" ","+","/","／","，",",","；",";","：",":"]: text=text.replace(ch,"")
    return text

def parse_koujing1(text):
    text=normalize_rule_text(text)
    m=re.match(r'^(\d{3})(.*)$',text)
    if not m: return None,"格式无法识别"
    mother,rule=m.group(1),m.group(2)
    if rule in POSITION_MAP:
        return {"mother":mother,"size_pos":rule,"parity_pos":rule,"display_rule":rule},None
    m2=re.fullmatch(r'大小(百十|百个|十个)奇偶(百十|百个|十个)',rule)
    if m2:
        return {"mother":mother,"size_pos":m2.group(1),"parity_pos":m2.group(2),"display_rule":f"大小{m2.group(1)} + 奇偶{m2.group(2)}"},None
    return None,"取位无法识别，例如：818十个 或 888大小百十奇偶十个"

def run_koujing1(mother,size_pos,parity_pos):
    ms,mp=size_shape(mother),parity_shape(mother)
    asize=allowed_shapes(ms,size_pos,SIZE_SHAPES)
    apar=allowed_shapes(mp,parity_pos,PARITY_SHAPES)
    full=[n for n in ALL_NUMBERS if size_shape(n) in asize and parity_shape(n) in apar]
    same=[n for n in full if repeat_type(n)!="三不同"]
    diff=[n for n in full if repeat_type(n)=="三不同"]
    return {"mother_size":ms,"mother_parity":mp,"allowed_size":asize,"allowed_parity":apar,"full":sorted(full),"same23":sorted(same),"different":sorted(diff)}

def run_shape_koujing1(size_mother_shape,size_pos,parity_mother_shape,parity_pos):
    # 与口径1完全同一套“八形态反筛法”。
    # 唯一区别：不再从三位数字推导母号形态，而是直接由用户指定大小母形态和奇偶母形态。
    asize=allowed_shapes(size_mother_shape,size_pos,SIZE_SHAPES)
    apar=allowed_shapes(parity_mother_shape,parity_pos,PARITY_SHAPES)
    full=[n for n in ALL_NUMBERS if size_shape(n) in asize and parity_shape(n) in apar]
    same=[n for n in full if repeat_type(n)!="三不同"]
    diff=[n for n in full if repeat_type(n)=="三不同"]
    return {
        "mother_size":size_mother_shape,
        "mother_parity":parity_mother_shape,
        "allowed_size":asize,
        "allowed_parity":apar,
        "full":sorted(full),
        "same23":sorted(same),
        "different":sorted(diff)
    }

def parse_digit_track(text):
    s=(text or "").replace("数字","").replace(" ",""); out=[]
    for c in s:
        if c.isdigit() and c not in out: out.append(c)
    return out

def run_digit_track(base_nums,target_digits):
    buckets={}
    for num in base_nums:
        c=sum(1 for d in target_digits if d not in num)
        buckets.setdefault(c,[]).append(num)
    bc=sorted(set(buckets.get(2,[]))|set(buckets.get(3,[])))
    return buckets,bc

def classify_shape_token(token):
    if token in SIZE_SHAPES: return "size"
    if token in PARITY_SHAPES: return "parity"
    return None

def run_shape_track(base_nums,shape_tokens):
    valid=[(t,classify_shape_token(t)) for t in shape_tokens if classify_shape_token(t)]
    counts={n:0 for n in base_nums}
    for token,kind in valid:
        for n in base_nums:
            matched=(size_shape(n)==token) if kind=="size" else (parity_shape(n)==token)
            if not matched: counts[n]+=1
    buckets={}
    for n,c in counts.items(): buckets.setdefault(c,[]).append(n)
    cd=sorted(set(buckets.get(3,[]))|set(buckets.get(4,[])))
    return valid,buckets,cd

def canonical_pair(pair):
    return "".join(sorted(pair)) if len(pair)==2 and pair.isdigit() else None

def parse_pair_conditions(text):
    return {canonical_pair(p) for p in re.findall(r'(?<!\d)\d{2}(?!\d)',text or "") if canonical_pair(p)}

def pair_hit_count(num,pair_set):
    a,b,c=num
    pairs=[canonical_pair(a+b),canonical_pair(a+c),canonical_pair(b+c)]
    return sum(1 for p in pairs if p in pair_set)

def run_pair_filter(base_nums,pair_set,mode):
    sel,rej=[],[]
    for n in base_nums:
        h=pair_hit_count(n,pair_set)
        ok=h>=2 if mode=="两对命中（至少2对）" else (h==2 if mode=="恰好两对命中" else h==3)
        (sel if ok else rej).append(n)
    return sorted(sel),sorted(rej)

def split_to_pairs(token):
    """将3-7位数字按任意两位拆分为两位组合；每对内部按升序标准化并去重。"""
    token=(token or "").strip()
    if not (token.isdigit() and 3 <= len(token) <= 7):
        return []
    pairs=set()
    for i in range(len(token)):
        for j in range(i+1,len(token)):
            pairs.add(canonical_pair(token[i]+token[j]))
    return sorted(pairs)

def parse_split_inputs(text):
    # 只识别独立的3-7位数字串，支持空格、换行、逗号等分隔。
    return re.findall(r'(?<!\d)\d{3,7}(?!\d)', text or "")

def sequence_type(num):
    d=sorted(int(x) for x in num)
    if len(set(d))!=3: return "非半顺"
    if d[1]-d[0]==1 and d[2]-d[1]==1: return "全顺"
    if d[1]-d[0]==1 or d[2]-d[1]==1: return "半顺"
    return "非半顺"

mode=st.selectbox("选择功能",[
    "口径1取号","形态取号","口径1双条件全量交集","口径1交集后数字形态轨","交集 / 不交集",
    "A分别与多个文件交集","合并去重","形态筛选","二同 / 三同 / 三不同",
    "两位组合命中筛选（按附件）","两位组合命中筛选（000-999）","数字包含 / 去除筛选","三至七位拆两位组合","半顺以上筛选"
])

if mode=="口径1取号":
    st.subheader("口径1正常取号")
    with st.form("k1"):
        text=st.text_area("输入条件（可多行）",placeholder="592百个\n888大小百十奇偶十个",height=140)
        go=st.form_submit_button("开始取号")
    if go:
        items=[]; errs=[]
        for line in [x.strip() for x in text.splitlines() if x.strip()]:
            p,e=parse_koujing1(line)
            if e: errs.append(f"{line}：{e}"); continue
            items.append((p,run_koujing1(p["mother"],p["size_pos"],p["parity_pos"])))
        save_result(mode,{"items":items,"errs":errs})
    data=get_result(mode)
    if data:
        for e in data["errs"]: st.error(e)
        for i,(p,r) in enumerate(data["items"],1):
            st.divider(); st.markdown(f"## {p['mother']} {p['display_rule']}")
            st.write(f"母号大小：**{r['mother_size']}**"); st.write(f"母号奇偶：**{r['mother_parity']}**")
            st.write("大小正常入选6形态："+"、".join(r["allowed_size"])); st.write("奇偶正常入选6形态："+"、".join(r["allowed_parity"]))
            st.write(f"全量正常出号：**{len(r['full'])} 注**"); st.write(f"二同+三同：**{len(r['same23'])} 注**"); st.write(f"三不同：**{len(r['different'])} 注**")
            st.success(f"闭环：{len(r['same23'])} + {len(r['different'])} = {len(r['full'])} √")
            base=f"{p['mother']}_{p['size_pos']}_{p['parity_pos']}"
            show_download("下载全量",r["full"],f"{base}_全量_{len(r['full'])}注.txt",f"k1f{i}")
            show_download("下载二同+三同",r["same23"],f"{base}_二同三同_{len(r['same23'])}注.txt",f"k1s{i}")
            show_download("下载三不同",r["different"],f"{base}_三不同_{len(r['different'])}注.txt",f"k1d{i}")

elif mode=="形态取号":
    st.subheader("形态取号（直接按给定形态筛选）")
    st.caption("大小、奇偶形态数量可自由搭配。程序直接保留：大小形态在你给出的列表中，并且奇偶形态也在你给出的列表中的000-999组合。")

    with st.form("shape_pick"):
        size_text=st.text_area(
            "输入大小形态",
            placeholder="大大大、大大小、大小大、小大大、大小小、小大小、小小大",
            height=120
        )
        parity_text=st.text_area(
            "输入奇偶形态",
            placeholder="奇奇奇、奇奇偶、奇偶奇、偶奇奇、奇偶偶、偶奇偶、偶偶奇",
            height=120
        )
        go=st.form_submit_button("开始形态取号")

    if go:
        size_selected=[x for x in SIZE_SHAPES if x in (size_text or "")]
        parity_selected=[x for x in PARITY_SHAPES if x in (parity_text or "")]

        if not size_selected:
            save_result(mode,{"error":"请至少输入1个有效的大小形态"})
        elif not parity_selected:
            save_result(mode,{"error":"请至少输入1个有效的奇偶形态"})
        else:
            full=[
                n for n in ALL_NUMBERS
                if size_shape(n) in size_selected
                and parity_shape(n) in parity_selected
            ]
            same23=[n for n in full if repeat_type(n)!="三不同"]
            different=[n for n in full if repeat_type(n)=="三不同"]
            save_result(mode,{
                "error":None,
                "size_selected":size_selected,
                "parity_selected":parity_selected,
                "full":sorted(full),
                "same23":sorted(same23),
                "different":sorted(different)
            })

    d=get_result(mode)
    if d:
        if d.get("error"):
            st.error(d["error"])
        else:
            st.divider()
            st.write(f"大小入选形态：**{len(d['size_selected'])}个**")
            st.write("、".join(d["size_selected"]))
            st.write(f"奇偶入选形态：**{len(d['parity_selected'])}个**")
            st.write("、".join(d["parity_selected"]))
            st.write(f"全量入选：**{len(d['full'])} 注**")
            st.write(f"二同+三同：**{len(d['same23'])} 注**")
            st.write(f"三不同：**{len(d['different'])} 注**")

            if len(d["same23"])+len(d["different"])==len(d["full"]):
                st.success(f"闭环：{len(d['same23'])} + {len(d['different'])} = {len(d['full'])} √")

            base=f"形态取号_大小{len(d['size_selected'])}形态_奇偶{len(d['parity_selected'])}形态"
            show_download("下载全量",d["full"],f"{base}_全量_{len(d['full'])}注.txt","shape_pick_full")
            show_download("下载二同+三同",d["same23"],f"{base}_二同三同_{len(d['same23'])}注.txt","shape_pick_same")
            show_download("下载三不同",d["different"],f"{base}_三不同_{len(d['different'])}注.txt","shape_pick_diff")

elif mode=="口径1双条件全量交集":
    st.subheader("两个口径1条件 → 全量交集")
    with st.form("double_k1"):
        ta=st.text_input("条件A",placeholder="例如：818十个"); tb=st.text_input("条件B",placeholder="例如：881十个")
        go=st.form_submit_button("开始全量交集分析")
    if go:
        pa,ea=parse_koujing1(ta); pb,eb=parse_koujing1(tb)
        if ea or eb: save_result(mode,{"error":f"A：{ea}" if ea else f"B：{eb}"})
        else:
            A=set(run_koujing1(pa["mother"],pa["size_pos"],pa["parity_pos"])["full"]); B=set(run_koujing1(pb["mother"],pb["size_pos"],pb["parity_pos"])["full"])
            save_result(mode,{"A":sorted(A),"B":sorted(B),"inter":sorted(A&B),"ao":sorted(A-B),"bo":sorted(B-A),"non":sorted((A-B)|(B-A)),"union":sorted(A|B)})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"A全量：**{len(d['A'])} 注**"); st.write(f"B全量：**{len(d['B'])} 注**"); st.write(f"交集：**{len(d['inter'])} 注**"); st.write(f"A独有：**{len(d['ao'])} 注**"); st.write(f"B独有：**{len(d['bo'])} 注**"); st.write(f"不交集合并：**{len(d['non'])} 注**"); st.write(f"合并去重：**{len(d['union'])} 注**")
            st.success(f"闭环：{len(d['A'])}+{len(d['B'])}=2×{len(d['inter'])}+{len(d['non'])} √")
            for label,keyname,arr in [("下载A全量","A",d["A"]),("下载B全量","B",d["B"]),("下载交集","I",d["inter"]),("下载A独有","AO",d["ao"]),("下载B独有","BO",d["bo"]),("下载不交集合并","N",d["non"]),("下载合并去重","U",d["union"])]:
                show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",f"dbl{keyname}")

elif mode=="口径1交集后数字形态轨":
    st.subheader("口径1 → 三不同交集/独有 → 数字BC → 形态CD → BC∩CD")
    with st.form("track"):
        ta=st.text_input("母号A条件",placeholder="例如：983十个"); tb=st.text_input("母号B条件",placeholder="例如：938十个")
        dt=st.text_input("数字轨",placeholder="例如：数字389"); sh=st.text_area("形态轨（4个完整三位形态，每行一个）",placeholder="大大小\n小小小\n奇偶奇\n偶奇偶",height=140)
        go=st.form_submit_button("开始完整分析")
    if go:
        pa,ea=parse_koujing1(ta); pb,eb=parse_koujing1(tb); digits=parse_digit_track(dt); shapes=[x.strip() for x in sh.splitlines() if x.strip()]
        err=(f"A：{ea}" if ea else (f"B：{eb}" if eb else ("请输入数字轨" if not digits else ("形态轨必须输入4个完整三位形态" if len(shapes)!=4 else None))))
        if not err:
            bad=[x for x in shapes if classify_shape_token(x) is None]
            if bad: err="无法识别形态："+"、".join(bad)
        if err: save_result(mode,{"error":err})
        else:
            A=set(run_koujing1(pa["mother"],pa["size_pos"],pa["parity_pos"])["different"]); B=set(run_koujing1(pb["mother"],pb["size_pos"],pb["parity_pos"])["different"])
            inter=sorted(A&B); ao=sorted(A-B); bo=sorted(B-A); non=sorted((A-B)|(B-A)); db,bc=run_digit_track(non,digits); vs,sb,cd=run_shape_track(non,shapes); fin=sorted(set(bc)&set(cd)); fout=sorted(set(non)-set(fin))
            save_result(mode,{"A":sorted(A),"B":sorted(B),"inter":inter,"ao":ao,"bo":bo,"non":non,"digits":digits,"db":db,"bc":bc,"vs":vs,"sb":sb,"cd":cd,"fin":fin,"fout":fout})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.markdown("## ① 前置母号结果"); st.write(f"A三不同：**{len(d['A'])} 注**"); st.write(f"B三不同：**{len(d['B'])} 注**"); st.write(f"交集：**{len(d['inter'])} 注**"); st.write(f"A独有：**{len(d['ao'])} 注**"); st.write(f"B独有：**{len(d['bo'])} 注**"); st.write(f"不交集合并：**{len(d['non'])} 注**"); st.success(f"前置闭环：{len(d['A'])}+{len(d['B'])}=2×{len(d['inter'])}+{len(d['non'])} √")
            for label,arr,k in [("下载A三不同",d["A"],"ta"),("下载B三不同",d["B"],"tb"),("下载交集",d["inter"],"ti"),("下载A独有",d["ao"],"tao"),("下载B独有",d["bo"],"tbo"),("下载不交集合并",d["non"],"tn")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",k)
            st.markdown("## ② 数字轨"); st.write("目标数字："+"、".join(d["digits"])); [st.write(f"出现{c}次：**{len(d['db'][c])} 注**") for c in sorted(d["db"])]; st.write(f"数字BC（2次+3次）：**{len(d['bc'])} 注**"); show_download("下载数字BC",d["bc"],f"数字BC_{len(d['bc'])}注.txt","tbc")
            st.markdown("## ③ 形态轨"); st.write("形态："+"、".join(x for x,_ in d["vs"])); [st.write(f"出现{c}次：**{len(d['sb'][c])} 注**") for c in sorted(d["sb"])]; st.write(f"形态CD（3次+4次）：**{len(d['cd'])} 注**"); show_download("下载形态CD",d["cd"],f"形态CD_{len(d['cd'])}注.txt","tcd")
            st.markdown("## ④ 最终数字形态轨"); st.write(f"最终入选 BC∩CD：**{len(d['fin'])} 注**"); st.write(f"最终不入选：**{len(d['fout'])} 注**"); st.success(f"最终闭环：{len(d['fin'])}+{len(d['fout'])}={len(d['non'])} √"); show_download("下载最终入选",d["fin"],f"最终入选_{len(d['fin'])}注.txt","tfi"); show_download("下载最终不入选",d["fout"],f"最终不入选_{len(d['fout'])}注.txt","tfo")

elif mode=="交集 / 不交集":
    st.subheader("两个附件交集 / 不交集")
    with st.form("normal_inter"):
        fa=st.file_uploader("上传文件A",type=["txt"],key="nia"); fb=st.file_uploader("上传文件B",type=["txt"],key="nib"); go=st.form_submit_button("开始分析")
    if go:
        if fa is None or fb is None: save_result(mode,{"error":"请同时上传A和B附件"})
        else:
            A=set(read_upload(fa)); B=set(read_upload(fb)); save_result(mode,{"A":sorted(A),"B":sorted(B),"inter":sorted(A&B),"ao":sorted(A-B),"bo":sorted(B-A),"non":sorted((A-B)|(B-A)),"union":sorted(A|B)})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"A：**{len(d['A'])} 注**"); st.write(f"B：**{len(d['B'])} 注**"); st.write(f"交集：**{len(d['inter'])} 注**"); st.write(f"A独有：**{len(d['ao'])} 注**"); st.write(f"B独有：**{len(d['bo'])} 注**"); st.write(f"不交集合并：**{len(d['non'])} 注**"); st.write(f"合并去重：**{len(d['union'])} 注**"); st.success(f"闭环：{len(d['A'])}+{len(d['B'])}=2×{len(d['inter'])}+{len(d['non'])} √")
            for label,arr,k in [("下载交集",d["inter"],"ni1"),("下载A独有",d["ao"],"ni2"),("下载B独有",d["bo"],"ni3"),("下载不交集合并",d["non"],"ni4"),("下载合并去重",d["union"],"ni5")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",k)

elif mode=="A分别与多个文件交集":
    st.subheader("A分别与B / C / D / E...做交集")
    with st.form("multi_inter"):
        fa=st.file_uploader("上传主文件A",type=["txt"],key="mia"); fs=st.file_uploader("上传B / C / D / E...",type=["txt"],accept_multiple_files=True,key="mio"); go=st.form_submit_button("开始分析")
    if go:
        if fa is None or not fs: save_result(mode,{"error":"请上传A和至少一个比较附件"})
        else:
            A=set(read_upload(fa)); outs=[]
            for i,f in enumerate(fs,1):
                B=set(read_upload(f)); label=chr(65+i); outs.append({"label":label,"name":f.name,"A":sorted(A),"B":sorted(B),"inter":sorted(A&B),"ao":sorted(A-B),"bo":sorted(B-A),"non":sorted((A-B)|(B-A))})
            save_result(mode,{"outs":outs})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            for i,x in enumerate(d["outs"],1):
                st.divider(); st.markdown(f"## A 与 {x['label']}"); st.caption(f"{x['label']}文件：{x['name']}"); st.write(f"A：**{len(x['A'])} 注**"); st.write(f"{x['label']}：**{len(x['B'])} 注**"); st.write(f"交集：**{len(x['inter'])} 注**"); st.write(f"A独有：**{len(x['ao'])} 注**"); st.write(f"{x['label']}独有：**{len(x['bo'])} 注**"); st.write(f"不交集合并：**{len(x['non'])} 注**"); st.success(f"闭环：{len(x['A'])}+{len(x['B'])}=2×{len(x['inter'])}+{len(x['non'])} √")
                for label,arr,s in [(f"下载A∩{x['label']}",x["inter"],"i"),("下载A独有",x["ao"],"a"),(f"下载{x['label']}独有",x["bo"],"b"),("下载不交集合并",x["non"],"n")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",f"mi{i}{s}")

elif mode=="合并去重":
    st.subheader("多个附件合并去重")
    with st.form("merge"):
        fs=st.file_uploader("上传两个或多个TXT",type=["txt"],accept_multiple_files=True,key="mergef"); go=st.form_submit_button("开始合并去重")
    if go:
        if not fs or len(fs)<2: save_result(mode,{"error":"请至少上传两个附件"})
        else:
            sets=[]; details=[]; total=0
            for f in fs:
                s=set(read_upload(f)); sets.append(s); details.append((f.name,len(s))); total+=len(s)
            merged=sorted(set().union(*sets)); save_result(mode,{"details":details,"total":total,"dup":total-len(merged),"merged":merged})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            [st.write(f"{n}：**{c} 注**") for n,c in d["details"]]; st.write(f"累计：**{d['total']} 注**"); st.write(f"合并去重：**{len(d['merged'])} 注**"); st.write(f"重复计数：**{d['dup']}**"); st.success(f"闭环：{d['total']}-{d['dup']}={len(d['merged'])} √"); show_download("下载合并去重",d["merged"],f"合并去重_{len(d['merged'])}注.txt","merge_dl")

elif mode=="形态筛选":
    st.subheader("按完整三位形态删除")
    with st.form("shape_filter"):
        f=st.file_uploader("上传基础附件",type=["txt"],key="sff"); ss=st.multiselect("要去掉的大小形态",SIZE_SHAPES); ps=st.multiselect("要去掉的奇偶形态",PARITY_SHAPES); go=st.form_submit_button("开始筛选")
    if go:
        if f is None: save_result(mode,{"error":"请上传附件"})
        else:
            o=read_upload(f); rem=[]; rm=[]
            for n in o: (rm if size_shape(n) in ss or parity_shape(n) in ps else rem).append(n)
            save_result(mode,{"o":o,"rem":sorted(rem),"rm":sorted(rm)})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"原始：**{len(d['o'])} 注**"); st.write(f"剩余：**{len(d['rem'])} 注**"); st.write(f"去掉：**{len(d['rm'])} 注**"); st.success(f"闭环：{len(d['rem'])}+{len(d['rm'])}={len(d['o'])} √"); show_download("下载剩余组合",d["rem"],f"剩余_{len(d['rem'])}注.txt","sfr"); show_download("下载被去掉组合",d["rm"],f"被去掉_{len(d['rm'])}注.txt","sfx")

elif mode=="二同 / 三同 / 三不同":
    st.subheader("二同 / 三同 / 三不同分类")
    with st.form("repeat"):
        f=st.file_uploader("上传附件",type=["txt"],key="repf"); go=st.form_submit_button("开始分类")
    if go:
        if f is None: save_result(mode,{"error":"请上传附件"})
        else:
            o=read_upload(f); two=[n for n in o if repeat_type(n)=="二同"]; three=[n for n in o if repeat_type(n)=="三同"]; diff=[n for n in o if repeat_type(n)=="三不同"]; save_result(mode,{"o":o,"two":two,"three":three,"same":sorted(two+three),"diff":diff})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"原始：**{len(d['o'])} 注**"); st.write(f"二同：**{len(d['two'])} 注**"); st.write(f"三同：**{len(d['three'])} 注**"); st.write(f"二同+三同：**{len(d['same'])} 注**"); st.write(f"三不同：**{len(d['diff'])} 注**"); st.success(f"闭环：{len(d['same'])}+{len(d['diff'])}={len(d['o'])} √")
            for label,arr,k in [("下载二同+三同",d["same"],"r1"),("下载三不同",d["diff"],"r2"),("单独下载二同",d["two"],"r3"),("单独下载三同",d["three"],"r4")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",k)

elif mode in ["两位组合命中筛选（按附件）","两位组合命中筛选（000-999）"]:
    by_file=mode.endswith("按附件）")
    st.subheader("附件 + 两位组合条件" if by_file else "000-999 + 两位组合条件")
    with st.form("pairf"+str(by_file)):
        f=st.file_uploader("上传基础附件",type=["txt"],key="pairupload") if by_file else None
        txt=st.text_area("输入两位组合",placeholder="01 03 05 06 09 13 15 16 18 19\n34 35 36 37 38 39 48 49 56 58",height=170)
        pm=st.radio("筛选方式",["两对命中（至少2对）","恰好两对命中","三对全命中"],key="pairmode"+str(by_file)); go=st.form_submit_button("开始筛选")
    if go:
        if by_file and f is None: save_result(mode,{"error":"请上传基础附件"})
        else:
            pairs=parse_pair_conditions(txt)
            if not pairs: save_result(mode,{"error":"请输入两位组合条件"})
            else:
                base=read_upload(f) if by_file else ALL_NUMBERS; sel,rej=run_pair_filter(base,pairs,pm); same=[n for n in sel if repeat_type(n)!="三不同"]; diff=[n for n in sel if repeat_type(n)=="三不同"]; save_result(mode,{"base":base,"sel":sel,"rej":rej,"same":same,"diff":diff,"pc":len(pairs),"pm":pm})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"两位条件：**{d['pc']}组**"); st.write(f"模式：**{d['pm']}**"); st.write(f"原始：**{len(d['base'])} 注**"); st.write(f"符合：**{len(d['sel'])} 注**"); st.write(f"不符合：**{len(d['rej'])} 注**"); st.write(f"二同+三同：**{len(d['same'])} 注**"); st.write(f"三不同：**{len(d['diff'])} 注**"); st.success(f"总闭环：{len(d['sel'])}+{len(d['rej'])}={len(d['base'])} √"); st.success(f"分类闭环：{len(d['same'])}+{len(d['diff'])}={len(d['sel'])} √")
            for label,arr,k in [("下载符合条件全量",d["sel"],"p1"),("下载不符合条件",d["rej"],"p2"),("下载二同+三同",d["same"],"p3"),("下载三不同",d["diff"],"p4")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",k+str(by_file))

elif mode=="数字包含 / 去除筛选":
    st.subheader("按数字包含关系筛选")
    with st.form("digit_filter"):
        f=st.file_uploader("上传基础附件",type=["txt"],key="dff"); txt=st.text_input("输入数字",placeholder="例如：3 或 368"); mm=st.radio("多个数字如何判断",["含任意一个","必须同时含全部"]); action=st.radio("操作方式",["筛出符合条件的组合","去掉符合条件的组合"]); go=st.form_submit_button("开始数字筛选")
    if go:
        if f is None: save_result(mode,{"error":"请上传基础附件"})
        else:
            digits=[]
            for c in txt:
                if c.isdigit() and c not in digits: digits.append(c)
            if not digits: save_result(mode,{"error":"请输入数字"})
            else:
                o=read_upload(f); matched=[]; unmatched=[]
                for n in o:
                    ok=any(d in n for d in digits) if mm=="含任意一个" else all(d in n for d in digits)
                    (matched if ok else unmatched).append(n)
                if action=="筛出符合条件的组合": rem,rm,rn,xn=matched,unmatched,"符合条件","不符合条件"
                else: rem,rm,rn,xn=unmatched,matched,"去掉后剩余","被去掉"
                save_result(mode,{"o":o,"rem":sorted(rem),"rm":sorted(rm),"rn":rn,"xn":xn,"digits":digits,"mm":mm,"action":action})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write("数字："+"、".join(d["digits"])); st.write(f"判断：**{d['mm']}**"); st.write(f"操作：**{d['action']}**"); st.write(f"原始：**{len(d['o'])} 注**"); st.write(f"{d['rn']}：**{len(d['rem'])} 注**"); st.write(f"{d['xn']}：**{len(d['rm'])} 注**"); st.success(f"闭环：{len(d['rem'])}+{len(d['rm'])}={len(d['o'])} √"); show_download(f"下载{d['rn']}",d["rem"],f"{d['rn']}_{len(d['rem'])}注.txt","dfr"); show_download(f"下载{d['xn']}",d["rm"],f"{d['xn']}_{len(d['rm'])}注.txt","dfx")

elif mode=="三至七位拆两位组合":
    st.subheader("三至七位数字 → 拆成两位组合")
    st.caption("例如：345 → 34 35 45；4567 → 45 46 47 56 57 67。每个两位组合内部按升序标准化，并自动去重。")

    with st.form("split_pairs_form"):
        text=st.text_area(
            "输入3-7位数字（可输入多组）",
            placeholder="345\n4567\n012579",
            height=160
        )
        go=st.form_submit_button("开始拆分")

    if go:
        tokens=parse_split_inputs(text)
        if not tokens:
            save_result(mode,{"error":"请输入3位、4位、5位、6位或7位数字"})
        else:
            details=[]
            merged=set()
            for token in tokens:
                pairs=split_to_pairs(token)
                merged.update(pairs)
                details.append({"token":token,"pairs":pairs})
            save_result(mode,{
                "error":None,
                "details":details,
                "merged":sorted(merged)
            })

    d=get_result(mode)
    if d:
        if d.get("error"):
            st.error(d["error"])
        else:
            for i,item in enumerate(d["details"],1):
                st.divider()
                st.markdown(f"## {item['token']}")
                st.write(f"拆出：**{len(item['pairs'])} 组**")
                st.code(" ".join(item["pairs"]))
                show_download(
                    f"下载 {item['token']} 的两位组合",
                    item["pairs"],
                    f"{item['token']}_拆两位_{len(item['pairs'])}组.txt",
                    f"split_pair_{i}"
                )

            if len(d["details"])>1:
                st.divider()
                st.markdown("## 多组输入合并去重")
                st.write(f"合并去重后：**{len(d['merged'])} 组**")
                st.code(" ".join(d["merged"]))
                show_download(
                    "下载合并去重后的两位组合",
                    d["merged"],
                    f"多组拆两位_合并去重_{len(d['merged'])}组.txt",
                    "split_pair_merged"
                )

elif mode=="半顺以上筛选":
    st.subheader("附件 → 半顺 / 全顺"); st.caption("348、384属于半顺；345及其排列属于全顺。")
    with st.form("seq"):
        f=st.file_uploader("上传基础附件",type=["txt"],key="seqf"); go=st.form_submit_button("开始筛选")
    if go:
        if f is None: save_result(mode,{"error":"请上传基础附件"})
        else:
            o=read_upload(f); half=[n for n in o if sequence_type(n)=="半顺"]; full=[n for n in o if sequence_type(n)=="全顺"]; non=[n for n in o if sequence_type(n)=="非半顺"]; hm=sorted(half+full); save_result(mode,{"o":o,"half":half,"full":full,"hm":hm,"non":non})
    d=get_result(mode)
    if d:
        if d.get("error"): st.error(d["error"])
        else:
            st.write(f"原始：**{len(d['o'])} 注**"); st.write(f"半顺：**{len(d['half'])} 注**"); st.write(f"全顺：**{len(d['full'])} 注**"); st.write(f"半顺以上：**{len(d['hm'])} 注**"); st.write(f"非半顺以上：**{len(d['non'])} 注**"); st.success(f"分类闭环1：{len(d['half'])}+{len(d['full'])}={len(d['hm'])} √"); st.success(f"分类闭环2：{len(d['hm'])}+{len(d['non'])}={len(d['o'])} √")
            for label,arr,k in [("下载半顺以上",d["hm"],"s1"),("单独下载半顺",d["half"],"s2"),("单独下载全顺",d["full"],"s3"),("下载非半顺以上",d["non"],"s4")]: show_download(label,arr,f"{label.replace('下载','')}_{len(arr)}注.txt",k)
