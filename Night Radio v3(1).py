"""夜班电台小丑牌 v2 · Python 文字原型

你是 AM 404.6 的夜班主持。月亮升起来以后，电话会自己响。
把三张牌推上播出台，凑够每位来电者要的“信号”，别在天亮前断线。

v2：哄睡全部六通之后，天会亮——但 AM 404.6 的太阳只上半天班。
输入 new2 接第二夜：老熟人回访、新面孔上线、胃口更狠，
架子上的小丑跟过去三件新货一起等你；架子满了，最早来的一件会让位。

直接运行：
    python3 夜班电台小丑牌.py

给 AI/脚本玩：
    import importlib.util
    spec = importlib.util.spec_from_file_location("nrj", "夜班电台小丑牌.py")
    nrj = importlib.util.module_from_spec(spec); spec.loader.exec_module(nrj)
    print(nrj.cmd("help"))
    print(nrj.cmd("new"))
    print(nrj.cmd("play 1 2 3"))

存档：优先环境变量 NIGHT_RADIO_SAVE；否则写到系统临时目录。存档失败不会掀桌。
"""
import json, os, tempfile

_SUITS = ["月", "雾", "铁", "花"]
_RANK_TEXT = {1: "A", 11: "J", 12: "Q", 13: "K"}

def _save_path():
    p = os.environ.get("NIGHT_RADIO_SAVE")
    if p:
        return p
    return os.path.join(tempfile.gettempdir(), "night_radio_joker_save.json")

def _load():
    p = _save_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _fresh()

def _save(st):
    try:
        with open(_save_path(), "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)
        return True
    except OSError:
        return False

class _Rng:
    def __init__(self, seed=0x4046, calls=0):
        self.state = seed & 0xFFFFFFFF
        self.calls = calls
    def _next(self):
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        self.calls += 1
        return self.state
    def random(self):
        return self._next() / 4294967296.0
    def randint(self, a, b):
        return a + int(self.random() * (b - a + 1))
    def choice(self, seq):
        return seq[int(self.random() * len(seq))]
    def shuffle(self, xs):
        xs = list(xs)
        for i in range(len(xs) - 1, 0, -1):
            j = int(self.random() * (i + 1))
            xs[i], xs[j] = xs[j], xs[i]
        return xs

def _card(rank, suit):
    return {"r": rank, "s": suit}

def _new_deck():
    return [_card(r, s) for s in _SUITS for r in range(1, 14)]

def _ctext(c):
    return f"{_RANK_TEXT.get(c['r'], str(c['r']))}{c['s']}"

def _hand_text(hand):
    return "  ".join(f"{i+1}.{_ctext(c)}" for i, c in enumerate(hand))

_CALLERS = [
    {"name": "无脸司机", "target": 750, "intro": "他说计价器倒着走，问你能不能替他报站。",
     "pass_react": "计价器咔哒一声，开始正着走。", "fail_react": "车门开了很久。没有人下车，也没有人上车。",
     "fav": "顺子", "fav_react": "报站声忽然对齐了：上一站、这一站、别回头。"},
    {"name": "阁楼里的雨", "target": 1000, "intro": "电话那端在下室内雨。每句话都长蘑菇。",
     "pass_react": "雨往回收了一寸。蘑菇没有道歉。", "fail_react": "天花板学会滴水。你的椅子先发霉。",
     "fav": "同花", "fav_react": "同一种颜色落下来，屋里终于像一场雨。"},
    {"name": "月亮维修工", "target": 1300, "intro": "他问你看见月亮背面的螺丝没有。别回答太快。",
     "pass_react": "他在月亮背面拧紧了什么。今晚暂时不掉。", "fail_react": "螺丝滚进话筒。你听见它一路掉到天亮。",
     "fav": "三条", "fav_react": "三枚螺丝同时咬住。维修工第一次没骂型号。"},
    {"name": "迟到的听众", "target": 1600, "intro": "她说她十年前就打进来了，只是现在才接通。",
     "pass_react": "她说『喂』。十年前的电流替你应了一声。", "fail_react": "忙音响起。她重新排队，从十年前开始。",
     "fav": "对子", "fav_react": "两个相同的声音隔着十年碰到一起。她没有挂。"},
    {"name": "雾面镜", "target": 1900, "intro": "镜子里的人先开口。它要你把今晚播成昨天。",
     "pass_react": "镜子起雾又散开。里面的人暂时愿意当你。", "fail_react": "镜面黑了一秒。你不确定刚才是谁在播音。",
     "fav": "异色对", "fav_react": "两种颜色在镜子里换脸。它满意地起雾。"},
    {"name": "天线上的孩子", "target": 2200, "intro": "天亮前最后一通。信号塔在轻轻晃。",
     "pass_react": "孩子笑了一下。整座塔跟着矮了半寸。", "fail_react": "天线轻轻晃。上面没有人，下面全是鞋。",
     "fav": "同花顺", "fav_react": "五张牌排成一线爬上去。塔尖亮了。"},
]

_CALLERS_N2 = [
    {"name": "无脸司机", "target": 1200, "intro": "他又把车停在直播间楼下。这次计价器正着走，但终点那一栏是空的。",
     "pass_react": "计价器吐出一张小票：『已到站』。没有人认领。",
     "fail_react": "雨刮器动了一下。车窗上写出一个地址，又被擦掉了。",
     "fav": "顺子", "fav_react": "报站声响起：这一站、下一站、每一站。他把空着的终点填上了。"},
    {"name": "迟到的听众", "target": 1500, "intro": "她说上次那声『喂』她听见了回音，所以这次提前十年打来。",
     "pass_react": "她说『我在』。十年前的电流这次没有抢答。",
     "fail_react": "忙音变得很有礼貌。它说：请再等一个十年。",
     "fav": "对子", "fav_react": "两个相同的声音终于同时开口。她说：这次不迟。"},
    {"name": "点歌的遗像", "target": 1800, "intro": "相框贴着话筒。它想点一首歌，给谁都可以，给什么都行。",
     "pass_react": "相框上的灰落了一粒。歌播完了，它没有点下一首。",
     "fail_react": "玻璃裂了一道很细的纹。像有人在里面换了个姿势。",
     "fav": "散牌", "fav_react": "没有花样，没有套路。遗像很满意：这样就不会被认出来了。"},
    {"name": "月亮维修工", "target": 2100, "intro": "他直接打进来了：『上次拧的那颗松了。你播你的，我听着数。』",
     "pass_react": "三声扳手，间隔均匀。他说：『这次能撑到下个月圆。』",
     "fail_react": "月亮肉眼可见地歪了一度。他骂了一个不存在的型号。",
     "fav": "三条", "fav_react": "三枚螺丝同时咬住。电话那头安静了三秒：『……内行。』"},
    {"name": "雾面镜", "target": 2000, "intro": "镜子里的人今天心情不错。它说你昨晚播得不错，问你要不要再当一次它。",
     "pass_react": "雾气散开时，你们有一瞬间分不清谁在播音。它说：『合格。』",
     "fail_react": "镜面结了霜。里面的人决定今晚还是由它来当你。",
     "fav": "异色对", "fav_react": "两种颜色在镜子里换完脸，没有换回来。它笑出了雾。"},
    {"name": "404.7 的同行", "target": 2500, "intro": "隔壁频率的夜班主持串线进来：『你那座塔昨晚亮了。我这座，缺一个下播的理由。』",
     "pass_react": "他轻轻说：『明天见。』两个频率同时安静下来。你分不清那是道别，还是排班表。",
     "fail_react": "串线断了。你听见他的频率还在响。一个人，一整夜。",
     "fav": "同花", "fav_react": "三张牌一种颜色落下来。他说：『行，这个信号我转给全频段。』"},
]

def _callers(st):
    return _CALLERS_N2 if st.get("cycle", 1) >= 2 else _CALLERS

_JOKERS = {
    "夜班提词器": {"desc": "每次播出恰好 3 张：倍率 +4。"},
    "雾中听筒": {"desc": "每张【雾】：筹码 +8。"},
    "铁门反光": {"desc": "若三张不成任何牌型：倍率 +5。"},
    "花台备用灯": {"desc": "同花：倍率 +4。"},
    "月相校准器": {"desc": "顺子：筹码 +35。"},
    "静默嘉宾": {"desc": "播出里有 K：筹码 +25。"},
    "旧磁带": {"desc": "对子：倍率 +3。"},
    "断线重拨": {"desc": "每次来电第一次播出：筹码 +20。"},
}

# 第二夜上架的新货：长在设定里的，不只是数值挂件。
_JOKERS_N2 = {
    "导播": {"desc": "每次来电第 3 次播出：倍率 +6，无论是否哄睡。"},
    "信号塔": {"desc": "每张【A】：筹码 +12。"},
    "午夜广告": {"desc": "若三张不成任何牌型：筹码 +30。"},
}

_ALL_JOKERS = {**_JOKERS, **_JOKERS_N2}

_CAP = 4

def _fresh():
    st = {
        "seed": 0x40464046, "calls": 0, "phase": "menu", "cycle": 1,
        "night": 0, "progress": 0, "hands_left": 3, "redraws_left": 1,
        "fuse": 2, "deck": [], "hand": [], "jokers": ["夜班提词器"],
        "pending": [], "played_this_call": 0,
        "cleared": 0, "failed": 0, "best": 0, "total_signal": 0,
        "fog": False, "known_jokers": [],
        "log_tail": "",
    }
    return st

def _draw(st, rng, n=1):
    out = []
    for _ in range(n):
        if len(st["deck"]) < 1:
            st["deck"] = rng.shuffle(_new_deck())
        out.append(st["deck"].pop())
    return out

def _start_call(st, rng, phase="call", deal=True):
    st["deck"] = rng.shuffle(_new_deck())
    # 选小丑/重接等待阶段不发牌：候选决策不该看见下一通手牌。
    st["hand"] = _draw(st, rng, 7) if deal else []
    st["progress"] = 0
    st["hands_left"] = 3
    st["redraws_left"] = 1
    st["played_this_call"] = 0
    st["phase"] = phase

def _deal_hand(st):
    rng = _Rng(st["seed"], st["calls"])
    st["hand"] = _draw(st, rng, 7)
    st["seed"], st["calls"] = rng.state, rng.calls

def _parse_idx(parts, hand, need=None):
    idx = []
    for p in parts[1:]:
        try:
            i = int(p) - 1
        except ValueError:
            return None, f"看不懂序号：{p}"
        if i < 0 or i >= len(hand) or i in idx:
            return None, f"序号不对：{p}"
        idx.append(i)
    if need is not None and len(idx) != need:
        return None, f"需要选 {need} 张。"
    return idx, None

def _chip(c):
    r = c["r"]
    if r == 1: return 11
    if r >= 11: return 10
    return r

def _score(cards, jokers, first_play=False, last_play=False, return_triggered=False):
    ranks = [c["r"] for c in cards]
    suits = [c["s"] for c in cards]
    chips = sum(_chip(c) for c in cards)
    mult = 1
    cnt = {r: ranks.count(r) for r in set(ranks)}
    scnt = {s: suits.count(s) for s in set(suits)}
    pair = any(v == 2 for v in cnt.values())
    three = any(v == 3 for v in cnt.values())
    sr = sorted(ranks)
    straight = len(set(ranks)) == 3 and sr[2] - sr[0] == 2
    flush = len(scnt) == 1
    tags = []
    if three:
        chips += 40; mult += 6; tags.append("三条")
    elif pair:
        chips += 15; mult += 3; tags.append("对子")
    if straight:
        chips += 30; mult += 5; tags.append("顺子")
    if flush:
        chips += 25; mult += 4; tags.append("同花")
    if pair and len(scnt) == 2:
        mult += 2; tags.append("异色对")
    plain = not (pair or three or straight or flush)
    if plain:
        tags.append("散牌")
    trig = []
    for j in jokers:
        used = False
        if j == "夜班提词器":
            mult += 4; used = True
        elif j == "雾中听筒":
            add = 8 * sum(1 for c in cards if c["s"] == "雾")
            if add:
                chips += add; used = True
        elif j == "铁门反光" and plain:
            mult += 5; used = True
        elif j == "花台备用灯" and flush:
            mult += 4; used = True
        elif j == "月相校准器" and straight:
            chips += 35; used = True
        elif j == "静默嘉宾" and any(c["r"] == 13 for c in cards):
            chips += 25; used = True
        elif j == "旧磁带" and pair:
            mult += 3; used = True
        elif j == "断线重拨" and first_play:
            chips += 20; used = True
        elif j == "导播":
            if last_play:
                mult += 6; used = True
        elif j == "信号塔":
            add = 12 * sum(1 for c in cards if c["r"] == 1)
            if add:
                chips += add; used = True
        elif j == "午夜广告" and plain:
            chips += 30; used = True
        if used:
            trig.append(j)
    chips = max(chips, 0); mult = max(mult, 1)
    if return_triggered:
        return chips * mult, chips, mult, tags, trig
    return chips * mult, chips, mult, tags

_RIDDLE = {
    "夜班提词器": "它总在第三张牌落下前清嗓子。",
    "雾中听筒": "雾里有人贴着听筒呼吸。",
    "铁门反光": "门后不是房间，是你的回声。",
    "花台备用灯": "同一种颜色开得太齐，会招东西。",
    "月相校准器": "三张牌连成线时，月亮会低头。",
    "静默嘉宾": "最响的那张脸，通常不说话。",
    "旧磁带": "成双的声音会被倒带。",
    "断线重拨": "第一句问候最贵。",
    "导播": "它只在结束前一分钟开始说话。",
    "信号塔": "最高的那几张牌，先碰到云。",
    "午夜广告": "没人听的时段，反而什么都说。",
}

def _appetite(target):
    if target <= 900: return "小口"
    if target <= 1400: return "正常"
    if target <= 1900: return "很饿"
    if target <= 2300: return "暴食"
    return "别接"

def _meter(progress, target):
    if progress <= 0: return "空麦"
    r = progress / max(target, 1)
    if r < 0.35: return "刚有杂音"
    if r < 0.7: return "过半"
    if r < 0.85: return "贴近喉咙"
    if r < 1.0: return "就差一口"
    return "饱了"

def _dots(n, total, on="●", off="○"):
    n = max(0, min(n, total))
    return on * n + off * (total - n)

def _fog_jokers(st):
    if not st["jokers"]:
        return "无"
    known = set(st.get("known_jokers", []))
    return "、".join(j + ("？" if j not in known else "") for j in st["jokers"])

def _signal_phrase(signal, remaining):
    if remaining <= 0:
        return "电话其实已经饱了，只是还没意识到。"
    r = signal / max(remaining, 1)
    if r >= 1.0: return "这一把像把整座塔推线里。"
    if r >= 0.6: return "很重，电话那头噎了一下。"
    if r >= 0.25: return "有东西顺着线爬过去。"
    return "像往井里丢了一枚纽扣。"

def _table(st, hide=False):
    callers = _callers(st)
    c = callers[st["night"]] if st["night"] < len(callers) else None
    lines = ["┌" + "─" * 46 + "┐"]
    fog = st.get("fog")
    if c:
        tag = "第二夜｜" if st.get("cycle", 1) >= 2 else ""
        if fog:
            lines.append(f"│ {tag}来电 {st['night']+1}/6：{c['name']} ｜ 胃口 {_appetite(c['target'])}")
            lines.append(
                f"│ 信号 {_meter(st['progress'], c['target'])} ｜ 播出 {_dots(st['hands_left'],3)} ｜ "
                f"重抽 {_dots(st['redraws_left'],1)} ｜ 保险丝 {_dots(st['fuse'], 3 if st.get('cycle',1)>=2 else 2,'█','▒')}"
            )
        else:
            lines.append(f"│ {tag}来电 {st['night']+1}/6：{c['name']} ｜ 目标 {c['target']}")
            lines.append(f"│ 信号 {st['progress']}/{c['target']} ｜ 播出 {st['hands_left']} ｜ 重抽 {st['redraws_left']} ｜ 保险丝 {st['fuse']}")
    lines.append("│ 小丑：" + (_fog_jokers(st) if fog else ("、".join(st["jokers"]) if st["jokers"] else "无")))
    lines.append("│ 手牌：" + (_hand_text(st["hand"]) if st["hand"] else "还没发。"))
    if fog:
        lines.append("│ 备注：黑箱开着。数字在装睡。")
    lines.append("└" + "─" * 46 + "┘")
    return "\n".join(lines)

def _offer(st, rng):
    pool = [j for j in _JOKERS if j not in st["jokers"]]
    if not pool or len(st["jokers"]) >= 4:
        st["pending"] = []
        return
    st["pending"] = rng.sample(pool, min(2, len(pool))) if hasattr(rng, "sample") else [pool.pop(int(rng.random()*len(pool))) for _ in range(min(2, len(pool)))]

# _Rng has no sample; keep helper tiny
def _sample(rng, pool, k):
    pool = list(pool)
    out = []
    for _ in range(min(k, len(pool))):
        i = int(rng.random() * len(pool))
        out.append(pool.pop(i))
    return out

def _pool(st):
    base = [j for j in _JOKERS if j not in st["jokers"]]
    if st.get("cycle", 1) >= 2:
        base += [j for j in _JOKERS_N2 if j not in st["jokers"]]
    return base

def _after_call(st, win):
    rng = _Rng(st["seed"], st["calls"])
    callers = _callers(st)
    if win:
        st["cleared"] += 1
        st["night"] += 1
        if st["night"] >= len(callers):
            st["pending"] = []
            if st.get("cycle", 1) >= 2:
                st["phase"] = "victory"
                return "\n天亮了。两座塔都不再冒汗。你把话筒扣下，走廊里没有电话在响——今晚没有，明晚再说。"
            st["phase"] = "dawn"
            return ("\n天亮了。天线停止冒汗。你活到了下播。"
                    "\n……但 AM 404.6 的太阳只上半天班。new2 接第二夜；new 重开第一夜。")
        pool = _pool(st)
        full = len(st["jokers"]) >= _CAP
        # 架子满了也照给机会：收下新货，点名一件让位；不点名则最早来的一件让位。
        if pool:
            st["pending"] = _sample(rng, pool, 2)
            if st["pending"]:
                _start_call(st, rng, phase="pick", deal=False)
                st["seed"], st["calls"] = rng.state, rng.calls
                if full:
                    shelf = "、".join(f"{i+1}.{x}" for i, x in enumerate(st["jokers"]))
                    return (f"\n来电断了。走廊尽头有两张小丑牌在看你。架子满了（{shelf}）——"
                            "收下要请一件让位：pick 1 / pick 2，可加「换 序号或名字」点名；不点名则最早来的一件让位。skip 跳过")
                return "\n来电断了。走廊尽头有两张小丑牌在看你。pick 1 / pick 2 / skip"
        st["pending"] = []
        _start_call(st, rng, phase="between", deal=False)
        st["seed"], st["calls"] = rng.state, rng.calls
        return "\n这档电话被你哄睡了。next 接下一通。"
    st["failed"] += 1
    st["fuse"] -= 1
    if st["fuse"] <= 0:
        st["phase"] = "over"
        st["pending"] = []
        return "\n保险丝全灭。直播间里只剩月亮在试麦。"
    # 烧丝不跳台：同一通电话还在响，重接一次。
    _start_call(st, rng, phase="between", deal=False)
    st["seed"], st["calls"] = rng.state, rng.calls
    return "\n这通电话没挂断，只是把话筒递回来。保险丝少了一根。next 重接同一通。"

def new_game(seed=None):
    old = _load()
    st = _fresh()
    st["fog"] = old.get("fog", False)
    if seed is not None:
        st["seed"] = int(seed) & 0xFFFFFFFF
    rng = _Rng(st["seed"], st["calls"])
    _start_call(st, rng)
    st["seed"], st["calls"] = rng.state, rng.calls
    _save(st)
    c = _CALLERS[0]
    return "AM 404.6 开机。今晚别问月亮问题。\n" + _table(st) + f"\n{c['intro']}\n→ hand / play 1 2 3 / discard 1 2 / status"

def cmd(text="help"):
    text = (text or "").strip()
    parts = text.split()
    c = parts[0].lower() if parts else "help"
    st = _load()
    st.setdefault("fog", False)
    st.setdefault("cycle", 1)
    st.setdefault("known_jokers", list(st.get("jokers", [])))

    if c == "fog":
        if len(parts) < 2 or parts[1].lower() not in ("on", "off"):
            return f"黑箱现在 {'开' if st['fog'] else '关'}。fog on / fog off。"
        st["fog"] = parts[1].lower() == "on"
        _save(st)
        return "你把数字的嘴捂上了。" if st["fog"] else "数字重新开口说人话。"

    if c == "help":
        return (
            "指令：\n"
            "  new            开一夜新节目\n"
            "  status         当前状态\n"
            "  hand           只看手牌\n"
            "  play a b c     播出恰好 3 张\n"
            "  discard a b    每次来电可重抽 1 次，丢 1-3 张\n"
            "  pick 1/2       来电结束后选小丑；skip 跳过\n"
            "  pick 1 换 2    架子满时点名让位（序号或名字）；不点名则最早来的一件让位\n"
            "  next           进入下一通来电\n"
            "  new2           天亮后接第二夜：老熟人回访，小丑保留，胃口更狠\n"
            "  rules          计分规则\n"
            "  jokers         查看小丑效果\n"
            "  fog on/off     黑箱模式：少报数字，多报气氛\n"
            "  reset          删档重开\n"
        )
    if c == "rules":
        return (
            "每次播出必须 3 张。基础筹码：A=11，2-10 按面值，JQK=10。\n"
            "对子 +15 筹码/倍率+3；三条 +40/+6；顺子 +30/+5；同花 +25/+4。\n"
            "对子且正好两种花色：倍率 +2。最终信号 = 筹码 × 倍率。\n"
            "每通来电有 3 次播出、1 次重抽；信号达标就哄睡来电。失败烧 1 根保险丝并重接同一通；保险丝尽，今夜断线。\n"
            "哄睡全部 6 通就天亮下播；new2 可接第二夜——老熟人回访，新面孔上线，小丑保留。\n"
            "架子（4 件）满了也能收新小丑：pick N 换 序号/名字 点名让位，不点名则最早来的一件让位。"
        )
    if c == "jokers":
        if st.get("fog"):
            known = set(st.get("known_jokers", []))
            lines = ["小丑台本（黑箱）："]
            for k in st.get("jokers", []):
                if k in known:
                    lines.append(f" ★ {k}：{_JOKERS[k]['desc']}")
                else:
                    lines.append(f" ★ {k}：还没在你面前亮过相。谜面：{_RIDDLE[k]}")
            lines.append("没上场的小丑不写进黑箱台本。")
            return "\n".join(lines)
        lines = ["小丑牌效果："]
        for k, v in _JOKERS.items():
            mark = "★" if k in st.get("jokers", []) else " "
            lines.append(f" {mark} {k}：{v['desc']}")
        n2 = [(k, v) for k, v in _JOKERS_N2.items()]
        if st.get("cycle", 1) >= 2:
            lines.append("第二夜新上架：")
            for k, v in n2:
                mark = "★" if k in st.get("jokers", []) else " "
                lines.append(f" {mark} {k}：{v['desc']}")
        else:
            lines.append("（听说第二夜会有新货上架。）")
        return "\n".join(lines)
    if c == "reset":
        try:
            os.remove(_save_path())
        except OSError:
            pass
        return "磁带消磁了。new 重新开始。"
    if c == "new":
        return new_game(parts[1] if len(parts) > 1 else None)
    if c == "new2":
        if st.get("phase") != "dawn":
            return "第二夜只在第一夜天亮后开播。先 new 熬过今晚。"
        st["cycle"] = 2
        st["night"] = 0
        st["fuse"] = 3
        rng = _Rng(st["seed"], st["calls"])
        _start_call(st, rng)
        st["seed"], st["calls"] = rng.state, rng.calls
        _save(st)
        c0 = _callers(st)[0]
        return ("第二天夜里。台标重新亮起，走廊比昨晚眼熟了一点。\n"
                "台标旁边多了一根备用保险丝——第二夜的胃口，台里心里有数。\n"
                + _table(st) + f"\n{c0['intro']}\n→ hand / play 1 2 3 / discard 1 2 / status")
    if st.get("phase") == "menu":
        return "台标还黑着。先 new。"
    if c == "status":
        extra = ""
        if st["phase"] == "pick" and st.get("pending"):
            if st.get("fog"):
                extra = "\n可选小丑：" + "；".join(f"{i+1}.{j}——{_RIDDLE[j]}" for i, j in enumerate(st["pending"]))
            else:
                extra = "\n可选小丑：" + "；".join(f"{i+1}.{j}：{_ALL_JOKERS[j]['desc']}" for i, j in enumerate(st["pending"]))
        return _table(st) + extra
    if c == "hand":
        return _hand_text(st.get("hand", []))
    if st["phase"] == "pick":
        if c == "skip":
            st["pending"] = []
            _deal_hand(st)
            st["phase"] = "call"
            _save(st)
            return "你装作没看见那两张牌。\n" + _table(st) + f"\n{_callers(st)[st['night']]['intro']}"
        if c == "pick":
            if len(parts) < 2:
                return "pick 1 或 pick 2。"
            try:
                i = int(parts[1]) - 1
            except ValueError:
                return "没有这个选项。"
            if i < 0 or i >= len(st["pending"]):
                return "没有这个选项。"
            j = st["pending"][i]
            dropped = None
            if len(st["jokers"]) >= _CAP:
                # 「换 序号或名字」点名让位；不点名则最早来的一件让位。
                target = None
                if len(parts) >= 4 and parts[2] in ("换", "换:", "换："):
                    target = parts[3]
                if target is not None:
                    if target.isdigit() and 1 <= int(target) <= len(st["jokers"]):
                        dropped = st["jokers"].pop(int(target) - 1)
                    elif target in st["jokers"]:
                        st["jokers"].remove(target)
                        dropped = target
                    else:
                        return f"架上没有【{target}】。status 看看架子，再点名。"
                else:
                    dropped = st["jokers"].pop(0)
            st["jokers"].append(j)
            st["pending"] = []
            _deal_hand(st)
            st["phase"] = "call"
            _save(st)
            tail = "它没解释自己。" if st.get("fog") else "它在你口袋里轻轻换了个姿势。"
            give_way = f"【{dropped}】把位置让出来，没说什么。\n" if dropped else ""
            return f"{give_way}你收下【{j}】。{tail}\n" + _table(st) + f"\n{_callers(st)[st['night']]['intro']}"
        return "现在只能 pick 1 / pick 2 / skip。"
    if st["phase"] == "between":
        if c == "next":
            _deal_hand(st)
            st["phase"] = "call"
            _save(st)
            return _table(st) + f"\n{_callers(st)[st['night']]['intro']}"
        return "电话在等。next 发牌。"
    if st["phase"] == "dawn":
        return "天已经亮了，话筒是温的。new2 接第二夜；new 重开第一夜；reset 消磁。"
    if st["phase"] in ("over", "victory"):
        return "这一夜已经结束了。new 再开一夜，或 reset 消磁。"
    if st["phase"] != "call":
        return "现在没信号。status 看看。"

    if c == "discard":
        if st["redraws_left"] <= 0:
            return "这通电话只允许重抽一次。"
        idx, err = _parse_idx(parts, st["hand"])
        if err: return err
        if not (1 <= len(idx) <= 3): return "丢 1-3 张。"
        rng = _Rng(st["seed"], st["calls"])
        for i in sorted(idx, reverse=True):
            st["hand"].pop(i)
        st["hand"].extend(_draw(st, rng, len(idx)))
        st["seed"], st["calls"] = rng.state, rng.calls
        st["redraws_left"] -= 1
        _save(st)
        return "你把几张牌塞回夜色，又摸出新的。\n" + _table(st)

    if c == "play":
        idx, err = _parse_idx(parts, st["hand"], need=3)
        if err: return err
        cards = [st["hand"][i] for i in idx]
        first = st["played_this_call"] == 0
        cur = _callers(st)[st["night"]]
        remaining = cur["target"] - st["progress"]
        last = st["hands_left"] == 1
        signal, chips, mult, tags, trig = _score(cards, st["jokers"], first, last, return_triggered=True)
        before_known = set(st.get("known_jokers", []))
        new_trig = [j for j in trig if j not in before_known]
        old_trig = [j for j in trig if j in before_known]
        known = set(before_known)
        for j in trig:
            known.add(j)
        st["known_jokers"] = list(known)
        st["progress"] += signal
        st["total_signal"] += signal
        st["best"] = max(st["best"], signal)
        st["hands_left"] -= 1
        st["played_this_call"] += 1
        rng = _Rng(st["seed"], st["calls"])
        for i in sorted(idx, reverse=True):
            st["hand"].pop(i)
        st["hand"].extend(_draw(st, rng, 3))
        st["seed"], st["calls"] = rng.state, rng.calls
        done = st["progress"] >= cur["target"]
        busted = st["hands_left"] <= 0 and not done
        out = [f"播出：{' '.join(_ctext(x) for x in cards)} ｜ {'/'.join(tags)}"]
        if st.get("fog"):
            out.append(_signal_phrase(signal, remaining))
            if new_trig:
                out.append("台本上新写了一行：" + "、".join(new_trig))
            if old_trig:
                out.append("台本上的名字动了一下：" + "、".join(old_trig))
        else:
            out.append(f"信号 {chips} × {mult} = {signal} ｜ 进度 {min(st['progress'], cur['target'])}/{cur['target']}")
        if cur.get("fav") in tags:
            out.append(cur["fav_react"])
        if done:
            out.append(cur["pass_react"])
            out.append(_after_call(st, True))
        elif busted:
            out.append(cur["fail_react"])
            out.append(_after_call(st, False))
        else:
            out.append(_table(st))
        _save(st)
        return "\n".join(x for x in out if x)

    return "听不懂。help 救场。"

if __name__ == "__main__":
    print("AM 404.6 夜班电台。输入 help 看指令，new 开一夜。")
    try:
        while True:
            line = input("> ").strip()
            if line in ("quit", "exit", "q"):
                print("你把话筒扣下。走廊里还有电话在响。")
                break
            print(cmd(line))
    except (EOFError, KeyboardInterrupt):
        print("\n信号渐弱。别回头。")
