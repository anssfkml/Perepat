#!/usr/bin/env python3
"""Generate the HyperFrames composition for the Perepat show-house TikTok edit.

The edit decision list (EDL) below cuts the 1:50 raw walkthrough down to ~1:05:
repeated lines, filler ("Okay", "Alright") and silent walking are removed, and
the price line is pulled to the front as the hook over b-roll of the best rooms.

Run:  python3 tools/build_edit.py      (rewrites index.html + compositions/*.html)
Source times are seconds in assets/tour.mp4 (the portrait 1080x1920 proxy).
"""
import json, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
W, H = 1080, 1920

def r(x):  # round to whole frames
    return round(round(x * FPS) / FPS, 4)

# --------------------------------------------------------------------------
# 1. Transcript (whisper large-v3, Malay) + corrections heard on re-check
# --------------------------------------------------------------------------
raw = json.load(open(os.path.join(ROOT, "tools/transcript.raw.json")))
WORDS = []
for seg in raw:
    for w in seg["words"]:
        WORDS.append({"t": w["w"].strip(), "s": w["s"], "e": w["e"]})

def fix_words(words):
    out = []
    i = 0
    while i < len(words):
        w = dict(words[i])
        nxt = words[i + 1] if i + 1 < len(words) else None
        if w["t"] == "RM360" and nxt and nxt["t"] == ",000":
            w = {"t": "RM360,000", "s": w["s"], "e": nxt["e"]}; i += 1
        elif w["t"] == "RM1" and nxt and nxt["t"].startswith(".7"):
            w = {"t": "RM1.7K.", "s": w["s"], "e": nxt["e"]}; i += 1
        elif w["t"] == "belum" and nxt and nxt["t"] == "minat":
            w = {"t": "berminat,", "s": w["s"], "e": nxt["e"]}; i += 1
        elif w["t"] == "cuba" and nxt and nxt["t"] == "-cuba":
            w = {"t": "cuba-cuba", "s": w["s"], "e": nxt["e"]}; i += 1
        w["t"] = {
            "Perpat": "Perepat", "hole": "whole", "study": "sliding",
            "Petit": "Peti", "ice": "ais", "blend": "lane", "tanah": "tanah.",
            "takde": "takde", "bed": "bed", "room.": "room.",
        }.get(w["t"], w["t"])
        if w["t"] == "sini" and nxt and nxt["t"] == "Washing":
            w["t"] = "sini."
        if w["t"] == "lah" and w["s"] > 96:
            w["t"] = "lah."
        if w["t"] == "bed" and nxt and nxt["t"] == "room.":
            w = {"t": "bedroom.", "s": w["s"], "e": nxt["e"]}; i += 1
        out.append(w)
        i += 1
    return out

WORDS = fix_words(WORDS)
# The closing "Alright" (99.94-100.36) is really "dengan saya ya." on re-listen.
WORDS = [w for w in WORDS if not (w["t"] == "Alright" and w["s"] > 99)]
WORDS += [{"t": "dengan", "s": 99.98, "e": 100.12}, {"t": "saya", "s": 100.12, "e": 100.28},
          {"t": "ya.", "s": 100.28, "e": 100.42}]
WORDS = [w for w in WORDS if w["t"] not in ("-cuba",)]

def words_in(a, b):
    return [w for w in WORDS if w["s"] >= a - 0.02 and w["s"] < b - 0.1]

# --------------------------------------------------------------------------
# 2. EDL
# --------------------------------------------------------------------------
# Hook: voice lines 0.95-12.2 (location + price) over muted b-roll of the best rooms.
HOOK_AUDIO = [(0.95, 3.22), (3.50, 8.52), (9.30, 12.20)]
# b-roll (src_in, duration) cut on the voice beats
HOOK_BROLL = [(31.90, 1.70), (55.00, 1.55), (72.60, 1.75), (100.60, 2.29), (63.20, 1.46), (103.00, None)]

# Tour: synced picture + sound. key, src_in, src_out, transition-in, label
TOUR = [
    ("rumah",   12.40, 16.72, "whoosh"),   # Ini rumah contoh dia. Jom kita tengok ada apa kat dalam.
    ("spec",    17.12, 23.97, "cut"),      # Bukaan 20, darat 60, 3 bilik, 2 bilik air. Open to all...
    ("open",    24.84, 26.72, "zoom"),     # Wow. Open concept.
    ("bilik1",  33.08, 35.00, "whoosh"),   # Ini bilik pertama.
    ("ba1",     38.16, 39.50, "cut"),      # Bilik air pertama.
    ("tamu",    44.58, 45.95, "whoosh"),   # Ruang tamu.
    ("corner",  47.08, 48.62, "punch"),    # Unit corner. Ada sliding door.
    ("makan",   49.22, 50.45, "cut"),      # Ni meja makan.
    ("bilik2",  53.86, 55.55, "whoosh"),   # Bilik kedua. Wow.
    ("ba2",     57.10, 60.20, "punch"),    # Cantik. Bilik air kedua. Bilik ketiga.
    ("bilik3",  60.20, 65.05, "cut"),      # You boleh jadikan dia small office ataupun bed room.
    ("dapur",   65.74, 67.76, "whoosh"),   # Dan ini adalah dapur.
    ("dinding", 68.40, 72.02, "punch"),    # setiap unit ni, tengok dia datang dengan dinding ni.
    ("sliding", 72.02, 80.00, "cut"),      # So, kalau you tak nak orang nampak dapur you ... sliding door
    ("nice",    81.30, 82.25, "punch"),    # Very nice.
    ("peti",    86.76, 89.56, "whoosh"),   # Peti ais dekat sini, washing machine pun dekat sini.
    ("belakang",91.66, 93.36, "punch"),    # Kat belakang takde tanah.
    ("lane",    95.62, 96.95, "cut"),      # Terus back lane lah.
    ("cta",     98.44, 100.55, "whoosh"),  # Kalau berminat, cuba-cuba dengan saya ya.
]
END_BROLL = (104.60, 4.50)  # walk back out to the street, under the end card

# Build output timeline ------------------------------------------------------
hook_audio_clips = []
t = 0.0
for a, b in HOOK_AUDIO:
    hook_audio_clips.append({"start": r(t), "dur": r(b - a), "src": a})
    t = r(t + (b - a))
HOOK_END = t

hook_video = []
t = 0.0
for src, dur in HOOK_BROLL:
    d = (HOOK_END - t) if dur is None else dur
    hook_video.append({"start": r(t), "dur": r(d), "src": src})
    t = r(t + d)

def hook_map(src_t):
    for c in hook_audio_clips:
        if c["src"] - 0.02 <= src_t < c["src"] + c["dur"]:
            return r(c["start"] + (src_t - c["src"]))
    return None

tour = []
t = HOOK_END
for key, a, b, trans in TOUR:
    tour.append({"key": key, "start": r(t), "dur": r(b - a), "src": a, "src_end": b, "trans": trans})
    t = r(t + (b - a))
END_START = t
TOTAL = r(END_START + END_BROLL[1])
SEG = {s["key"]: s for s in tour}

def out_t(src_t, key):
    s = SEG[key]
    return r(s["start"] + (src_t - s["src"]))

def word_out(key, word):
    """output time of the first transcript word starting with `word` in segment key"""
    s = SEG[key]
    ws = words_in(s["src"], s["src_end"])
    for w in ws:  # exact token first ("2" must not match "20,")
        if w["t"].lower().strip(".,?!") == word.lower():
            return out_t(w["s"], key)
    for w in ws:
        if w["t"].lower().strip(".,?!").startswith(word.lower()):
            return out_t(w["s"], key)
    raise KeyError((key, word))

# --------------------------------------------------------------------------
# 3. Captions: word list on the output clock
# --------------------------------------------------------------------------
cap_words = []
for c in hook_audio_clips:
    for w in words_in(c["src"], c["src"] + c["dur"]):
        cap_words.append({"t": w["t"], "s": r(c["start"] + w["s"] - c["src"]),
                          "e": r(c["start"] + min(w["e"], c["src"] + c["dur"]) - c["src"]), "seg": "hook%d" % c["start"]})
for s in tour:
    for w in words_in(s["src"], s["src_end"]):
        cap_words.append({"t": w["t"], "s": out_t(w["s"], s["key"]),
                          "e": out_t(min(w["e"], s["src_end"]), s["key"]), "seg": s["key"]})

# group: max 3 words, break on sentence punctuation, pauses >= .15 s or segment change
groups, cur = [], []
for i, w in enumerate(cap_words):
    if cur:
        prev = cur[-1]
        last_of_sentence = w["t"][-1] in ".?!" and len(cur) == 3 and w["s"] - prev["e"] < 0.15 and prev["t"][-1] not in ".?!,"
        if ((len(cur) >= 3 and not last_of_sentence) or prev["seg"] != w["seg"] or w["s"] - prev["e"] >= 0.15
                or prev["t"][-1] in ".?!" or (prev["t"][-1] == "," and len(cur) >= 2)):
            groups.append(cur); cur = []
    cur.append(w)
if cur:
    groups.append(cur)

# --------------------------------------------------------------------------
# 4. SFX cues (peak lands one frame after the picture event)
# --------------------------------------------------------------------------
PEAK = {"whoosh": 0.162, "pop": 0.12, "ping": 0.324, "impact-bass-1": 0.073,
        "sparkle": 0.027, "chime": 0.418, "click-soft": 0.073}
LEN = {"whoosh": 0.575, "pop": 0.72, "ping": 1.32, "impact-bass-1": 2.116,
       "sparkle": 1.802, "chime": 2.544, "click-soft": 0.366}
VOL = {"whoosh": 0.45, "pop": 0.6, "ping": 0.5, "impact-bass-1": 0.3,
       "sparkle": 0.22, "chime": 0.9, "click-soft": 0.6}
sfx = []
def cue(name, at, vol_mul=1.0):
    start = max(0.0, r(at + 1 / FPS - PEAK[name]))
    sfx.append({"name": name, "start": start, "dur": r(LEN[name]), "vol": round(VOL[name] * vol_mul, 3)})

# --------------------------------------------------------------------------
# 5. Overlay timings
# --------------------------------------------------------------------------
T = {}
T["price_in"] = hook_map(4.48)        # "RM360,000"
T["price_land"] = hook_map(7.75)
T["net"] = hook_map(7.88)             # "net."
T["monthly"] = hook_map(10.56)        # "RM1.7K"
T["harga"] = hook_map(3.56)
spec = SEG["spec"]
T["tile1"] = word_out("spec", "Bukaan")
T["tile2"] = word_out("spec", "3")
T["tile3"] = word_out("spec", "2")
T["open_all"] = word_out("spec", "open")
T["open_concept"] = word_out("open", "Open")
T["corner"] = word_out("corner", "corner")
T["office"] = word_out("bilik3", "small")
T["bedroom"] = word_out("bilik3", "bed")
T["sliding"] = word_out("sliding", "sliding")
T["dinding"] = word_out("dinding", "dinding")
T["nice"] = word_out("nice", "Very")
T["peti"] = word_out("peti", "Peti")
T["mesin"] = word_out("peti", "Washing")
T["tanah"] = word_out("belakang", "takde")
T["lane"] = word_out("lane", "back")
T["cta"] = word_out("cta", "Kalau")

# Room chips: (text, start, end)
CHIPS = [
    ("RUMAH CONTOH", SEG["rumah"]["start"] + 0.10, SEG["rumah"]["start"] + SEG["rumah"]["dur"]),
    ("BILIK 1", SEG["bilik1"]["start"] + 0.05, SEG["bilik1"]["start"] + SEG["bilik1"]["dur"]),
    ("BILIK AIR 1", SEG["ba1"]["start"] + 0.05, SEG["ba1"]["start"] + SEG["ba1"]["dur"]),
    ("RUANG TAMU", SEG["tamu"]["start"] + 0.05, SEG["makan"]["start"]),
    ("MEJA MAKAN", SEG["makan"]["start"] + 0.05, SEG["makan"]["start"] + SEG["makan"]["dur"]),
    ("BILIK 2", SEG["bilik2"]["start"] + 0.05, SEG["bilik2"]["start"] + SEG["bilik2"]["dur"] + 0.6),
    ("BILIK AIR 2", word_out("ba2", "Bilik"), word_out("ba2", "ketiga") - 0.55),
    ("BILIK 3", word_out("ba2", "ketiga") - 0.5, SEG["bilik3"]["start"] + SEG["bilik3"]["dur"]),
    ("DAPUR", SEG["dapur"]["start"] + 0.05, SEG["nice"]["start"] + SEG["nice"]["dur"]),
    ("BELAKANG RUMAH", SEG["peti"]["start"] + 0.05, SEG["lane"]["start"] + SEG["lane"]["dur"]),
]
CHIPS = [(a, r(b), r(c)) for a, b, c in CHIPS]

# SFX list
cue("whoosh", HOOK_END - 0.05)                    # hook -> tour
cue("whoosh", hook_video[1]["start"], 0.6)
cue("ping", T["price_in"])
cue("impact-bass-1", T["net"])
cue("pop", T["monthly"])
cue("pop", T["tile1"]); cue("ping", T["tile2"], 0.8); cue("pop", T["tile3"])
cue("impact-bass-1", T["open_all"], 0.8)
cue("sparkle", T["open_concept"])
cue("pop", T["corner"], 0.8)
cue("click-soft", T["office"]); cue("click-soft", T["bedroom"])
cue("pop", T["sliding"])
cue("sparkle", T["nice"], 0.8)
cue("pop", T["peti"], 0.8); cue("pop", T["mesin"], 0.8)
cue("pop", T["tanah"], 0.8)
cue("pop", T["lane"])
cue("chime", T["cta"] + 0.9)
cue("pop", T["cta"] + 0.1 + 1.2)
for s in tour:
    if s["trans"] == "whoosh" and s["key"] not in ("rumah",):
        cue("whoosh", s["start"], 0.75)
for txt, a, b in CHIPS:
    if txt in ("BILIK AIR 2", "BILIK 3", "RUMAH CONTOH"):
        cue("click-soft", a + 0.12, 0.8)
sfx.sort(key=lambda x: x["start"])

# --------------------------------------------------------------------------
# 6. Write index.html
# --------------------------------------------------------------------------
def a(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")

vid_tags, aud_tags, cam_js = [], [], []
z = 1
for i, c in enumerate(hook_video):
    vid_tags.append(
        f'<video id="hv{i+1}" class="clip footage" src="assets/tour.mp4" data-start="{a(c["start"])}" '
        f'data-duration="{a(c["dur"])}" data-media-start="{a(c["src"])}" data-track-index="1" muted playsinline></video>')
    # each b-roll shot lands with a short push-in
    cam_js.append(f'tl.set("#cam", {{scale: 1.14}}, {a(c["start"])});')
    cam_js.append(f'tl.to("#cam", {{scale: 1.04, duration: {a(c["dur"] - 0.02)}, ease: "expo.out"}}, {a(c["start"])});')
for i, c in enumerate(hook_audio_clips):
    aud_tags.append(
        f'<audio id="hook-vo{i+1}" class="clip" src="assets/voice.m4a" data-start="{a(c["start"])}" '
        f'data-duration="{a(c["dur"])}" data-media-start="{a(c["src"])}" data-track-index="2" '
        f'data-volume="1" data-fade-in="0.03" data-fade-out="0.05"></audio>')
alt = False
for s in tour:
    vid_tags.append(
        f'<video id="tv-{s["key"]}" class="clip footage" src="assets/tour.mp4" data-start="{a(s["start"])}" '
        f'data-duration="{a(s["dur"])}" data-media-start="{a(s["src"])}" data-track-index="{1 if len(vid_tags) % 2 else 4}" '
        f'data-has-audio="true" data-volume="1" data-fade-in="0.03" data-fade-out="0.05" playsinline></video>')
    tr = s["trans"]
    if tr in ("whoosh", "zoom"):
        alt = False
        cam_js.append(f'tl.set("#cam", {{scale: 1.22}}, {a(s["start"])});')
        cam_js.append(f'tl.to("#cam", {{scale: 1.0, duration: 0.45, ease: "expo.out"}}, {a(s["start"])});')
    elif tr == "punch":
        alt = not alt
        cam_js.append(f'tl.set("#cam", {{scale: {1.12 if alt else 1.0}}}, {a(s["start"])});')
    else:
        cam_js.append(f'tl.set("#cam", {{scale: {1.12 if alt else 1.0}}}, {a(s["start"])});')
vid_tags.append(
    f'<video id="end-broll" class="clip footage" src="assets/tour.mp4" data-start="{a(END_START)}" '
    f'data-duration="{a(END_BROLL[1])}" data-media-start="{a(END_BROLL[0])}" data-track-index="1" muted playsinline></video>')
cam_js.append(f'tl.set("#cam", {{scale: 1.0}}, {a(END_START)});')
cam_js.append(f'tl.to("#cam", {{scale: 1.08, duration: {a(END_BROLL[1] - 0.05)}, ease: "none"}}, {a(END_START)});')

lane_end = {3: -1, 5: -1, 6: -1}
for f in sfx:
    ln = min(lane_end, key=lambda k: (lane_end[k] > f["start"], lane_end[k]))
    f["track"] = ln; lane_end[ln] = f["start"] + f["dur"]
for i, f in enumerate(sfx):
    aud_tags.append(
        f'<audio id="sfx{i+1:02d}-{f["name"]}" class="clip" src="assets/sfx/{f["name"]}.mp3" data-start="{a(f["start"])}" '
        f'data-duration="{a(min(f["dur"], TOTAL - f["start"]))}" data-track-index="{f["track"]}" data-volume="{f["vol"]}" data-audio-group="sfx"></audio>')

hosts = [
    ("hook", 0, HOOK_END, 10, "graphics"),
    ("labels", 0, TOTAL, 11, "graphics"),
    ("specs", SEG["spec"]["start"], SEG["spec"]["dur"], 12, "graphics"),
    ("endcard", SEG["cta"]["start"], TOTAL - SEG["cta"]["start"], 13, "graphics"),
    ("captions", 0, TOTAL, 14, "captions"),
]
host_tags = []
for hid, st, du, ti, kind in hosts:
    host_tags.append(
        f'<div id="{hid}" data-composition-id="{hid}" data-composition-src="compositions/{hid}.html" '
        f'data-start="{a(st)}" data-duration="{a(du)}" data-track-index="{ti}" data-track-kind="{kind}" '
        f'data-width="{W}" data-height="{H}" style="z-index:{ti}"></div>')

NL = "\n      "
index_html = f"""<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <!-- Generated by tools/build_edit.py from the EDL; edit the EDL there and re-run. -->
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
      #root {{ width: 100%; height: 100%; position: relative; overflow: hidden; background: #000; }}
      #stage {{ position: absolute; inset: 0; overflow: hidden; z-index: 1; }}
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      .footage {{ position: absolute; left: 0; top: 0; width: {W}px; height: {H}px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{a(TOTAL)}"
      data-width="{W}" data-height="{H}" data-fps="{FPS}">
      <div id="stage" data-layout-allow-overflow>
        <div id="cam">
      {NL.join(vid_tags)}
        </div>
      </div>
      {NL.join(aud_tags)}
      <hf-audio-group id="sfx"></hf-audio-group>
      {NL.join(host_tags)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // camera: push-ins on the hook b-roll, zoom-through on room changes,
      // alternating punch-ins to hide jump cuts inside a room
      {NL.join(cam_js)}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(os.path.join(ROOT, "index.html"), "w").write(index_html)

# --------------------------------------------------------------------------
# 7. Shared design tokens for scenes
# --------------------------------------------------------------------------
BASE_CSS = """
      #root { position: absolute; inset: 0; font-family: 'Montserrat', sans-serif; color: #fff; }
      #root, #root * { box-sizing: border-box; }
      :root { --accent: #FFD60A; --ink: #FFFFFF; --dark: rgba(14, 16, 22, 0.88); --green: #128045; --red: #E5383B; }
"""

def scene(cid, css, body, js, dur, extra_attrs=""):
    return f"""<template>
  <style>{BASE_CSS}{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="{W}" data-height="{H}" data-duration="{a(dur)}"{extra_attrs}>
{body}
  </div>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
{js}
      window.__timelines["{cid}"] = tl;
    }})();
  </script>
</template>
"""

# ---- hook -----------------------------------------------------------------
hk_css = """
      .hk-wrap { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
      #hk-shade { position: absolute; left: 0; top: 0; width: 1080px; height: 1000px;
        background: linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0.35) 55%, rgba(0,0,0,0) 100%); }
      #hk-kicker { position: absolute; left: 0; top: 196px; width: 1080px; text-align: center; }
      #hk-kicker span { display: inline-block; background: var(--accent); color: #111; font-weight: 900;
        font-size: 40px; letter-spacing: 0.06em; padding: 12px 28px; border-radius: 999px; }
      #hk-q { position: absolute; left: 60px; top: 290px; width: 960px; text-align: center; font-weight: 900;
        font-size: 88px; line-height: 1.02; letter-spacing: -0.02em; text-transform: uppercase;
        text-shadow: 0 6px 24px rgba(0,0,0,0.55); }
      #hk-q em { font-style: normal; color: var(--accent); }
      #hk-from { position: absolute; left: 0; top: 330px; width: 1080px; text-align: center; font-weight: 800;
        font-size: 50px; letter-spacing: 0.14em; opacity: 0; text-shadow: 0 4px 16px rgba(0,0,0,0.6); }
      #hk-price { position: absolute; left: 0; top: 400px; width: 1080px; text-align: center; opacity: 0;
        font-family: 'Archivo Black', sans-serif; font-size: 178px; line-height: 1; color: var(--accent);
        letter-spacing: -0.03em; text-shadow: 0 10px 40px rgba(0,0,0,0.55); }
      #hk-price small { font-size: 96px; margin-right: 8px; }
      #hk-net { position: absolute; left: 700px; top: 590px; opacity: 0; background: var(--red); color: #fff;
        font-family: 'Archivo Black', sans-serif; font-size: 64px; padding: 6px 26px; border-radius: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
      #hk-monthly { position: absolute; left: 0; top: 720px; width: 1080px; text-align: center; opacity: 0; }
      #hk-monthly span { display: inline-block; background: var(--dark); border: 4px solid var(--accent);
        color: #fff; font-weight: 800; font-size: 54px; padding: 18px 36px; border-radius: 26px; }
      #hk-monthly b { color: var(--accent); font-weight: 900; }
"""
hk_body = f"""    <div id="hk-shade" class="clip" data-start="0" data-duration="{a(HOOK_END)}" data-layout-ignore></div>
    <div id="hk-kicker" class="clip" data-start="0" data-duration="{a(HOOK_END)}"><span>RUMAH TERES &#8226; PEREPAT</span></div>
    <div id="hk-q" class="clip" data-start="0" data-duration="{a(T['harga'])}"><div id="hk-q-in">Rumah macam ni<br/><em>berapa harga?</em></div></div>
    <div id="hk-from" class="clip" data-start="{a(T['harga'])}" data-duration="{a(HOOK_END - T['harga'])}">HARGA DARI</div>
    <div id="hk-price" class="clip" data-start="{a(T['harga'])}" data-duration="{a(HOOK_END - T['harga'])}"><small>RM</small><span id="hk-num">0</span></div>
    <div id="hk-net" class="clip" data-start="{a(T['harga'])}" data-duration="{a(HOOK_END - T['harga'])}">NET</div>
    <div id="hk-monthly" class="clip" data-start="{a(T['harga'])}" data-duration="{a(HOOK_END - T['harga'])}"><span>Bulanan dari <b>~RM1.7K</b></span></div>"""
hk_js = f"""      // frame 0 already carries the question (thumbnail + hook)
      tl.fromTo("#hk-q-in", {{ opacity: 1, scale: 1 }}, {{ opacity: 0, scale: 0.92, filter: "blur(8px)", duration: 0.18, ease: "power3.in" }}, {a(T['harga'] - 0.2)});
      tl.fromTo("#hk-from", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }}, {a(T['harga'])});
      tl.fromTo("#hk-price", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }}, {a(T['price_in'] - 0.05)});
      const num = {{ v: 0 }};
      const el = document.getElementById("hk-num");
      tl.fromTo(num, {{ v: 0 }}, {{ v: 360000, duration: {a(T['price_land'] - T['price_in'])}, ease: "power2.out",
        onUpdate: () => {{ el.textContent = (Math.round(num.v / 1000) * 1000).toLocaleString("en-US"); }} }}, {a(T['price_in'])});
      tl.fromTo("#hk-net", {{ opacity: 0, scale: 2.4, rotation: -14 }}, {{ opacity: 1, scale: 1, rotation: -8, duration: 0.22, ease: "power4.out" }}, {a(T['net'])});
      tl.fromTo("#hk-price", {{ y: 0 }}, {{ y: -10, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.inOut" }}, {a(T['net'] + 0.02)});
      tl.fromTo("#hk-monthly", {{ opacity: 0, y: 60 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }}, {a(T['monthly'] - 0.05)});
      // leave together into the tour
      tl.to(["#hk-from", "#hk-price", "#hk-net", "#hk-monthly", "#hk-kicker span"], {{ opacity: 0, y: -40, duration: 0.2, ease: "power3.in", stagger: 0.02 }}, {a(HOOK_END - 0.28)});
      tl.to("#hk-shade", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {a(HOOK_END - 0.28)});"""
open(os.path.join(ROOT, "compositions/hook.html"), "w").write(scene("hook", hk_css, hk_body, hk_js, HOOK_END))

# ---- labels (room chips + callouts) ----------------------------------------
lb_css = """
      .chip { position: absolute; left: 56px; top: 196px; }
      .chip span { display: inline-flex; align-items: center; gap: 16px; background: var(--dark); color: #fff;
        font-weight: 900; font-size: 44px; letter-spacing: 0.05em; padding: 14px 28px 14px 22px; border-radius: 18px; }
      .chip i { display: inline-block; width: 14px; height: 44px; border-radius: 7px; background: var(--accent); }
      .callout { position: absolute; left: 60px; width: 880px; text-align: center; }
      .callout span { display: inline-block; font-weight: 900; color: #111; background: var(--accent);
        font-size: 58px; padding: 16px 32px; border-radius: 22px; box-shadow: 0 12px 34px rgba(0,0,0,0.35); }
      .callout.dark span { background: var(--dark); color: #fff; border: 4px solid var(--accent); }
      .callout.green span { background: var(--green); color: #fff; }
      .big { position: absolute; left: 60px; width: 960px; text-align: center; font-weight: 900; text-transform: uppercase;
        font-size: 120px; line-height: 0.95; letter-spacing: -0.02em; color: #fff; text-shadow: 0 8px 30px rgba(0,0,0,0.5); }
      .big em { font-style: normal; color: var(--accent); }
      #lb-toggle { position: absolute; left: 60px; top: 330px; width: 880px; text-align: center; }
      #lb-toggle .opt { display: inline-block; font-weight: 900; font-size: 44px; padding: 14px 22px; border-radius: 22px;
        background: var(--dark); color: rgba(255,255,255,0.55); margin: 0 4px; }
      #lb-toggle .or { display: inline-block; font-weight: 900; font-size: 38px; color: #fff; margin: 0 6px;
        text-shadow: 0 3px 12px rgba(0,0,0,0.7); }
"""
lb_body, lb_js = [], []
for i, (txt, st, en) in enumerate(CHIPS):
    cid = f"chip{i+1}"
    lb_body.append(f'    <div id="{cid}" class="clip chip" data-start="{a(st)}" data-duration="{a(en - st)}" data-track-index="{i % 2}"><span id="{cid}-in"><i></i>{html.escape(txt)}</span></div>')
    lb_js.append(f'      tl.fromTo("#{cid}-in", {{ opacity: 0, x: -60 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {a(st)});')
    lb_js.append(f'      tl.to("#{cid}-in", {{ opacity: 0, x: -30, duration: 0.15, ease: "power2.in" }}, {a(en - 0.17)});')

def callout(cid, cls, top, text, st, en, ease_in="back.out(1.7)"):
    lb_body.append(f'    <div id="{cid}" class="clip callout {cls}" style="top:{top}px" data-start="{a(st)}" data-duration="{a(en - st)}" data-track-index="2"><span id="{cid}-in">{text}</span></div>')
    lb_js.append(f'      tl.fromTo("#{cid}-in", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "{ease_in}" }}, {a(st)});')
    lb_js.append(f'      tl.to("#{cid}-in", {{ opacity: 0, scale: 0.9, duration: 0.15, ease: "power2.in" }}, {a(en - 0.17)});')

# Open concept – kinetic title
oc_s, oc_e = T["open_concept"] - 0.05, SEG["open"]["start"] + SEG["open"]["dur"]
lb_body.append(f'    <div id="lb-open" class="clip big" style="top:330px" data-start="{a(oc_s)}" data-duration="{a(oc_e - oc_s)}" data-track-index="2"><div id="lb-open-1">Open</div><div id="lb-open-2"><em>Concept</em></div></div>')
lb_js.append(f'      tl.fromTo("#lb-open-1", {{ opacity: 0, filter: "blur(10px)", y: 30 }}, {{ opacity: 1, filter: "blur(0px)", y: 0, duration: 0.2, ease: "power4.out" }}, {a(oc_s)});')
lb_js.append(f'      tl.fromTo("#lb-open-2", {{ opacity: 0, filter: "blur(10px)", y: 30 }}, {{ opacity: 1, filter: "blur(0px)", y: 0, duration: 0.2, ease: "power4.out" }}, {a(oc_s + 0.3)});')
lb_js.append(f'      tl.to(["#lb-open-1", "#lb-open-2"], {{ opacity: 0, filter: "blur(8px)", duration: 0.15, stagger: 0.05, ease: "power2.in" }}, {a(oc_e - 0.22)});')

callout("lb-corner", "", 320, "UNIT CORNER", T["corner"] - 0.05, SEG["corner"]["start"] + SEG["corner"]["dur"])
# small office / bedroom toggle
tg_s, tg_e = T["office"] - 0.1, SEG["bilik3"]["start"] + SEG["bilik3"]["dur"]
lb_body.append(f'    <div id="lb-toggle" class="clip" data-start="{a(tg_s)}" data-duration="{a(tg_e - tg_s)}" data-track-index="3"><div id="lb-toggle-in"><span id="lb-opt1" class="opt">SMALL OFFICE</span><span class="or">atau</span><span id="lb-opt2" class="opt">BEDROOM</span></div></div>')
lb_js.append(f'      tl.fromTo("#lb-toggle-in", {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, {a(tg_s)});')
lb_js.append(f'      tl.fromTo("#lb-opt1", {{ backgroundColor: "rgba(14,16,22,0.88)", color: "rgba(255,255,255,0.55)" }}, {{ backgroundColor: "#FFD60A", color: "#111111", duration: 0.12 }}, {a(T["office"])});')
lb_js.append(f'      tl.to("#lb-opt1", {{ backgroundColor: "rgba(14,16,22,0.88)", color: "rgba(255,255,255,0.55)", duration: 0.12 }}, {a(T["bedroom"])});')
lb_js.append(f'      tl.fromTo("#lb-opt2", {{ backgroundColor: "rgba(14,16,22,0.88)", color: "rgba(255,255,255,0.55)" }}, {{ backgroundColor: "#FFD60A", color: "#111111", duration: 0.12 }}, {a(T["bedroom"])});')
lb_js.append(f'      tl.to("#lb-toggle-in", {{ opacity: 0, duration: 0.15, ease: "power2.in" }}, {a(tg_e - 0.17)});')

callout("lb-dinding", "dark", 320, "Siap dengan dinding ni", SEG["dinding"]["start"] + 0.1, SEG["dinding"]["start"] + SEG["dinding"]["dur"])
callout("lb-sliding", "", 320, "+ Pasang sliding door", T["sliding"] - 0.05, SEG["sliding"]["start"] + SEG["sliding"]["dur"])
callout("lb-nice", "green", 330, "VERY NICE!", T["nice"] - 0.03, SEG["nice"]["start"] + SEG["nice"]["dur"])
callout("lb-peti", "dark", 320, "Peti ais", T["peti"] - 0.05, T["mesin"] - 0.05)
callout("lb-mesin", "dark", 320, "Mesin basuh", T["mesin"] - 0.05, SEG["peti"]["start"] + SEG["peti"]["dur"])
callout("lb-tanah", "dark", 320, "Takde tanah belakang", SEG["belakang"]["start"] + 0.1, SEG["lane"]["start"] + SEG["lane"]["dur"])
callout("lb-lane", "", 440, "&#8594; Terus back lane", SEG["lane"]["start"] - 0.25, SEG["lane"]["start"] + SEG["lane"]["dur"])

open(os.path.join(ROOT, "compositions/labels.html"), "w").write(
    scene("labels", lb_css, "\n".join(lb_body), "\n".join(lb_js), TOTAL))

# ---- specs card --------------------------------------------------------------
s0 = SEG["spec"]["start"]
sp_dur = SEG["spec"]["dur"]
rel = lambda x: r(x - s0)
sp_css = """
      #sp-row { position: absolute; left: 60px; top: 300px; width: 960px; display: flex; gap: 20px; }
      .tile { flex: 1; background: var(--dark); border-radius: 28px; padding: 26px 10px 24px; text-align: center;
        border-top: 8px solid var(--accent); box-shadow: 0 16px 40px rgba(0,0,0,0.35); opacity: 0; }
      .tile .n { font-family: 'Archivo Black', sans-serif; font-size: 76px; line-height: 1.05; color: #fff; }
      .tile .n small { font-size: 44px; }
      .tile .l { margin-top: 8px; font-weight: 800; font-size: 30px; letter-spacing: 0.06em; color: var(--accent); }
      #sp-stamp { position: absolute; left: 0; top: 590px; width: 1080px; text-align: center; }
      #sp-stamp span { display: inline-block; background: var(--green); color: #fff; font-family: 'Archivo Black', sans-serif;
        font-size: 74px; padding: 14px 40px; border-radius: 20px; border: 6px solid #fff; box-shadow: 0 16px 40px rgba(0,0,0,0.35); }
      #sp-sub { position: absolute; left: 0; top: 740px; width: 1080px; text-align: center; font-weight: 800; font-size: 44px;
        text-shadow: 0 4px 16px rgba(0,0,0,0.8); }
"""
sp_body = f"""    <div id="sp-card" class="clip" data-start="0" data-duration="{a(sp_dur)}" data-layout-allow-overflow>
      <div id="sp-row">
        <div class="tile" id="sp-t1"><div class="n">20<small>'</small>x60<small>'</small></div><div class="l">KELUASAN</div></div>
        <div class="tile" id="sp-t2"><div class="n">3</div><div class="l">BILIK TIDUR</div></div>
        <div class="tile" id="sp-t3"><div class="n">2</div><div class="l">BILIK AIR</div></div>
      </div>
      <div id="sp-stamp"><span id="sp-stamp-in">OPEN TO ALL</span></div>
      <div id="sp-sub"><span id="sp-sub-in">Semua orang boleh beli</span></div>
    </div>"""
sp_js = f"""      tl.fromTo("#sp-t1", {{ opacity: 0, y: 50, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.5)" }}, {a(rel(T['tile1']))});
      tl.fromTo("#sp-t2", {{ opacity: 0, y: 50, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.5)" }}, {a(rel(T['tile2']))});
      tl.fromTo("#sp-t3", {{ opacity: 0, y: 50, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.5)" }}, {a(rel(T['tile3']))});
      tl.fromTo("#sp-stamp-in", {{ opacity: 0, scale: 2.6, rotation: -12 }}, {{ opacity: 1, scale: 1, rotation: -4, duration: 0.24, ease: "power4.out" }}, {a(rel(T['open_all']))});
      tl.fromTo("#sp-sub-in", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {a(rel(T['open_all']) + 0.35)});
      tl.to(["#sp-t1", "#sp-t2", "#sp-t3", "#sp-stamp-in", "#sp-sub-in"], {{ opacity: 0, y: -30, duration: 0.18, stagger: 0.03, ease: "power3.in" }}, {a(sp_dur - 0.32)});"""
open(os.path.join(ROOT, "compositions/specs.html"), "w").write(scene("specs", sp_css, sp_body, sp_js, sp_dur))

# ---- end card ----------------------------------------------------------------
e0 = SEG["cta"]["start"]
ed_dur = TOTAL - e0
erel = lambda x: r(x - e0)
ed_css = """
      #ed-scrim { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; background: rgba(8,10,14,0.62); opacity: 0; }
      #ed-card { position: absolute; left: 60px; top: 300px; width: 880px; text-align: center; }
      #ed-kick { display: inline-block; background: var(--accent); color: #111; font-weight: 900; font-size: 38px;
        letter-spacing: 0.08em; padding: 10px 26px; border-radius: 999px; }
      #ed-title { margin-top: 26px; font-weight: 900; font-size: 92px; line-height: 0.98; text-transform: uppercase; }
      #ed-price { margin-top: 34px; font-family: 'Archivo Black', sans-serif; font-size: 120px; line-height: 1; color: var(--accent); }
      #ed-price small { font-size: 54px; color: #fff; }
      #ed-month { margin-top: 12px; font-weight: 800; font-size: 46px; }
      #ed-specs { margin-top: 30px; font-weight: 800; font-size: 36px; letter-spacing: 0.04em; color: rgba(255,255,255,0.9); }
      #ed-contact { margin: 46px auto 0; width: 820px; display: flex; align-items: center; gap: 30px; text-align: left;
        background: var(--dark); border: 5px solid var(--accent); border-radius: 36px; padding: 26px 34px;
        box-shadow: 0 18px 44px rgba(0,0,0,0.45); }
      #ed-avatar { flex: none; width: 210px; height: 210px; border-radius: 50%; overflow: hidden;
        border: 7px solid var(--accent); box-shadow: 0 8px 24px rgba(0,0,0,0.4); background: #222; }
      #ed-avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
      #ed-who { flex: 1; }
      #ed-ask { font-weight: 900; font-size: 40px; letter-spacing: 0.06em; color: var(--accent); }
      #ed-name { margin-top: 2px; font-weight: 900; font-size: 74px; line-height: 1.05; color: #fff; }
      #ed-phone { margin-top: 12px; display: inline-flex; align-items: center; gap: 14px; background: var(--green);
        color: #fff; font-weight: 900; font-size: 46px; padding: 12px 24px; border-radius: 20px; letter-spacing: 0.02em; }
      #ed-phone svg { width: 40px; height: 40px; flex: none; }
"""
ed_body = f"""    <div id="ed-scrim" class="clip" data-start="{a(erel(T['cta']))}" data-duration="{a(ed_dur - erel(T['cta']))}" data-layout-ignore></div>
    <div id="ed-card" class="clip" data-start="{a(erel(T['cta']))}" data-duration="{a(ed_dur - erel(T['cta']))}">
      <div><span id="ed-kick">RUMAH TERES &#8226; PEREPAT</span></div>
      <div id="ed-price"><small>DARI </small>RM360K<small> NET</small></div>
      <div id="ed-month">Bulanan dari ~RM1.7K</div>
      <div id="ed-specs">3 BILIK &#8226; 2 BILIK AIR &#8226; OPEN TO ALL</div>
      <div id="ed-contact">
        <div id="ed-avatar"><img src="assets/anis.jpg" alt="Anis" /></div>
        <div id="ed-who">
          <div id="ed-ask">BERMINAT?</div>
          <div id="ed-name" data-var-text="contactName">Anis</div>
          <div id="ed-phone"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#fff" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg><span data-var-text="contactPhone">016-602 9067</span></div>
        </div>
      </div>
    </div>"""
es = erel(T["cta"]) + 0.1
ed_js = f"""      tl.fromTo("#ed-scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power2.out" }}, {a(es - 0.05)});
      tl.fromTo("#ed-kick", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, {a(es)});
      tl.fromTo("#ed-price", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }}, {a(es + 0.3)});
      tl.fromTo("#ed-month", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {a(es + 0.5)});
      tl.fromTo("#ed-specs", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {a(es + 0.62)});
      tl.fromTo("#ed-contact", {{ opacity: 0, y: 50 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }}, {a(es + 0.75)});
      tl.fromTo("#ed-avatar", {{ scale: 0.4 }}, {{ scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {a(es + 0.8)});
      tl.fromTo("#ed-name", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }}, {a(es + 1.0)});
      tl.fromTo("#ed-phone", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.7)" }}, {a(es + 1.2)});"""
open(os.path.join(ROOT, "compositions/endcard.html"), "w").write(
    scene("endcard", ed_css, ed_body, ed_js, ed_dur,
          extra_attrs=""" data-composition-variables='[{"id":"contactName","type":"string","label":"Contact name","default":"Anis"},{"id":"contactPhone","type":"string","label":"Contact phone","default":"016-602 9067"}]'"""))

# ---- captions ----------------------------------------------------------------
cp_css = """
      .cap { position: absolute; left: 60px; top: 1110px; width: 880px; text-align: center; overflow: visible; }
      .cap .w { display: inline-block; font-weight: 900; font-size: 72px; line-height: 1.12; margin: 0 9px;
        color: #fff; text-transform: uppercase; letter-spacing: -0.01em;
        -webkit-text-stroke: 12px #000; paint-order: stroke fill; text-shadow: 0 6px 18px rgba(0,0,0,0.45); }
"""
cp_body, cp_js = [], []
for gi, g in enumerate(groups):
    gs = r(max(0.12, g[0]["s"] - 0.04))
    nxt = groups[gi + 1][0]["s"] - 0.04 if gi + 1 < len(groups) else TOTAL
    ge = r(min(g[-1]["e"] + 0.35, nxt))
    if ge - gs < 0.25:
        ge = r(gs + 0.25)
    gid = f"cg{gi+1:03d}"
    spans = "".join(f'<span id="{gid}w{wi}" class="w">{html.escape(w["t"].strip(",."))}</span>' for wi, w in enumerate(g))
    cp_body.append(f'    <div id="{gid}" class="clip cap" data-start="{a(gs)}" data-duration="{a(ge - gs)}" data-track-index="{gi % 2}">{spans}</div>')
    cp_js.append(f'      tl.fromTo("#{gid} .w", {{ scale: 0.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.14, ease: "back.out(2)", stagger: 0.03 }}, {a(gs)});')
    for wi, w in enumerate(g):
        cp_js.append(f'      tl.set("#{gid}w{wi}", {{ color: "#FFD60A" }}, {a(max(gs, w["s"]))});')
        if wi < len(g) - 1:
            cp_js.append(f'      tl.set("#{gid}w{wi}", {{ color: "#FFFFFF" }}, {a(g[wi+1]["s"])});')
open(os.path.join(ROOT, "compositions/captions.html"), "w").write(
    scene("captions", cp_css, "\n".join(cp_body), "\n".join(cp_js), TOTAL))

# --------------------------------------------------------------------------
# 8. Edit report
# --------------------------------------------------------------------------
report = {
    "total": TOTAL, "hook_end": HOOK_END, "end_start": END_START,
    "tour": [{k: s[k] for k in ("key", "start", "dur", "src", "src_end", "trans")} for s in tour],
    "captions": [{"start": g[0]["s"], "text": " ".join(w["t"] for w in g)} for g in groups],
    "sfx": sfx, "overlay_times": T,
}
json.dump(report, open(os.path.join(ROOT, "tools/edit_report.json"), "w"), indent=1, ensure_ascii=False)
print(f"total {TOTAL:.2f}s  hook {HOOK_END:.2f}s  groups {len(groups)}  sfx {len(sfx)}  clips {len(vid_tags)}")
