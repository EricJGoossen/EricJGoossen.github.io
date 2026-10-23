"""Charts for the HCRL (ARCHITECT) log, in the site's chart style (Achilles' svgchart),
from numbers transcribed from the paper (arXiv 2607.23784v1, Tables 1-3).

usage: make_charts.py <images dir>
"""
import os
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from svgchart import STYLE  # noqa: E402

out = sys.argv[1]

# --- Success rate per task and method (Tables 1 and 2) --------------------------
TASKS = ["Banana → plate", "Block → basket", "Baseball → bucket", "Apple, bread → bowl",
         "Bread from box", "Close drawer", "Fold cloth", "Banana under cloth"]
METHODS = [  # (name, kind, success rate per task)
    ("π0", "VLA", [.80, .40, .00, .40, .40, .10, .00, .10]),
    ("π0.5", "VLA", [.90, 1.0, .20, .40, .40, .00, .00, .00]),
    ("MolmoAct2", "VLA", [.80, .30, .00, .10, .20, .00, .00, .00]),
    ("GR00T N1.7", "VLA", [.40, .00, .00, .00, .00, .00, .00, .00]),
    ("Code as Policies", "code", [.20, .40, .60, .10, .10, .00, .00, .00]),
    ("ARCHITECT", "code", [.80, .70, 1.0, .80, .70, .90, .80, .80]),
]
ml, mt, cw, ch = 160, 74, 100, 34
w, h = ml + cw * len(METHODS) + 16, mt + ch * len(TASKS) + 44
b = []
for j, (name, kind, _) in enumerate(METHODS):
    x = ml + cw * j + cw / 2
    b.append(f'<text class="s b c" x="{x:.0f}" y="{mt - 28}">{escape(name)}</text>')
    b.append(f'<text class="s m c" x="{x:.0f}" y="{mt - 12}">{"VLA" if kind == "VLA" else "LLM code"}</text>')
for i, task in enumerate(TASKS):
    y = mt + ch * i
    b.append(f'<text class="s e" x="{ml - 10}" y="{y + ch / 2 + 4:.0f}">{escape(task)}</text>')
    for j, (_, kind, sr) in enumerate(METHODS):
        v = sr[i]
        x = ml + cw * j
        var = "--s1" if kind == "VLA" else "--s3"
        b.append(f'<rect x="{x + 2}" y="{y + 2}" width="{cw - 4}" height="{ch - 4}" rx="4" '
                 f'style="fill:var({var})" fill-opacity="{0.08 + 0.82 * v:.2f}"/>')
        b.append(f'<text class="s c{" b" if v >= 0.6 else ""}" x="{x + cw / 2:.0f}" y="{y + ch / 2 + 4:.0f}"'
                 f'{" style=&quot;fill:#fff&quot;" if v >= 0.6 else ""}>{v:.1f}</text>'.replace("&quot;", '"'))
b.append(f'<text class="s m" x="{ml}" y="{h - 14}">Success rate over 10 rollouts per task; the objects\' placement and the '
         'wording change every rollout.</text>')
title = "Success rate by task: four VLAs against LLM-written code"
desc = ("Success rates from the paper's real-world benchmark on a Franka Panda, 10 rollouts per task. The four VLAs "
        "(π0, π0.5, MolmoAct2, GR00T N1.7) do well only on simple pick and place, led by π0.5 with 0.9 on banana to "
        "plate and 1.0 on block to basket, and score 0 to 0.1 on closing a drawer, folding a cloth and the banana "
        "under a cloth. Code as Policies scores at most 0.6. ARCHITECT, with human corrections, scores 0.7 to 1.0 on "
        "every task.")
open(f"{out}/sr-by-task.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
    f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE + "  " + "\n  ".join(b) + "\n</svg>\n")

# --- Language ablation: one phrasing per row (Table 3) ---------------------------
ROWS = [  # (perturbation, instruction, pi0.5 success, ARCHITECT success)
    ("canonical", "Put the red apple in the pan.", 1, 1),
    ("synonym", "Grab the apple and set it on the pan.", 1, 1),
    ("synonym", "Take the apple and place it onto the pan.", 0, 1),
    ("synonym", "Move the apple onto the pan.", 0, 1),
    ("synonym", "Lift the apple and rest it on the pan.", 1, 1),
    ("passive", "The apple should be picked up and placed on the pan.", 1, 1),
    ("word order", "Onto the pan, place the apple.", 0, 1),
    ("ambiguity", "Relocate the fruit so that it sits on the pan.", 0, 1),
    ("short", "apple on pan", 1, 1),
    ("medium", "Pick up the apple from the table and place it onto the pan sitting nearby.", 0, 1),
    ("long", "There is a apple resting on the surface in front of you. Pick that apple up, …", 1, 0),
    ("typos", "pickup teh appel an put it on the frying pan", 0, 1),
    ("underspecified", "Put the apple away.", 0, 1),
    ("underspecified", "Move the apple.", 0, 0),
    ("overspecified", "Pick up the red apple and put it on the white pan; approach from directly overhead, …", 0, 1),
]
ml, mt, rh = 128, 58, 27
w, h = 720, mt + rh * len(ROWS) + 30
cx = {"pi": 586, "arch": 668}
b = [f'<text class="s b c" x="{cx["pi"]}" y="{mt - 16}">π0.5</text>',
     f'<text class="s b c" x="{cx["arch"]}" y="{mt - 16}">ARCHITECT</text>']
for i, (kind, text, pi, arch) in enumerate(ROWS):
    y = mt + rh * i + rh / 2
    if i % 2 == 0:
        b.append(f'<rect x="8" y="{y - rh / 2:.0f}" width="{w - 16}" height="{rh}" style="fill:var(--grid)" fill-opacity="0.45"/>')
    b.append(f'<text class="s m e" x="{ml - 10}" y="{y + 4:.0f}">{escape(kind)}</text>')
    short = text if len(text) <= 62 else text[:60].rstrip() + "…"
    b.append(f'<text class="s" x="{ml}" y="{y + 4:.0f}">“{escape(short.rstrip("…"))}{"…" if short.endswith("…") else ""}”</text>')
    for key, ok, var in (("pi", pi, "--s1"), ("arch", arch, "--s3")):
        if ok:
            b.append(f'<circle cx="{cx[key]}" cy="{y:.0f}" r="8" style="fill:var({var})"/>')
        else:
            b.append(f'<circle cx="{cx[key]}" cy="{y:.0f}" r="7.5" style="fill:none;stroke:var(--ref)" stroke-width="1.5"/>')
b.append(f'<text class="s m" x="{ml}" y="{h - 10}">Filled: success. Same apple, same pan, same placement; only the words change.</text>')
title = "One task, fifteen ways to say it"
desc = ("The language ablation from the paper: the same apple-to-pan task, with the object held in place, given in "
        "fifteen phrasings. π0.5 succeeds on 6 of them, failing on synonyms such as 'Take the apple and place it onto "
        "the pan', on reordered and ambiguous wording, on typos, and on under- and over-specified instructions. "
        "ARCHITECT succeeds on 13, failing on the longest phrasing and on 'Move the apple.'")
open(f"{out}/language-ablation.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
    f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE + "  " + "\n  ".join(b) + "\n</svg>\n")
# --- Success vs task progression for the two π models (Table 1) ----------------
PROG = {  # task -> (pi0 SR, pi0 NTP, pi0.5 SR, pi0.5 NTP)
    "Banana → plate": (.80, .90, .90, .98), "Block → basket": (.40, .44, 1.0, 1.0),
    "Baseball → bucket": (.00, .16, .20, .50), "Apple, bread → bowl": (.40, .64, .40, .65),
    "Bread from box": (.40, .40, .40, .44), "Close drawer": (.10, .23, .00, .17),
    "Fold cloth": (.00, .40, .00, .04), "Banana under cloth": (.10, .36, .00, .19),
}
ml, mt, rh, pw, gap = 160, 84, 30, 250, 40
w, h = ml + 2 * pw + gap + 16, mt + rh * len(PROG) + 46
b = []
for k, name in enumerate(("π0", "π0.5")):
    x0 = ml + k * (pw + gap)
    X = lambda v, x0=x0: x0 + v * pw  # noqa: E731
    b.append(f'<text class="b" x="{x0}" y="{mt - 26}">{name}</text>')
    for v in (0, .5, 1):
        b.append(f'<line class="grid" x1="{X(v):.0f}" x2="{X(v):.0f}" y1="{mt - 18}" y2="{mt + rh * len(PROG)}"/>')
        b.append(f'<text class="s m c" x="{X(v):.0f}" y="{mt + rh * len(PROG) + 16}">{v:g}</text>')
    for i, (task, vals) in enumerate(PROG.items()):
        y = mt + rh * i + rh / 2
        sr, ntp = vals[2 * k], vals[2 * k + 1]
        if k == 0:
            b.append(f'<text class="s e" x="{ml - 12}" y="{y + 4:.0f}">{escape(task)}</text>')
        b.append(f'<line x1="{X(sr):.1f}" x2="{X(ntp):.1f}" y1="{y:.0f}" y2="{y:.0f}" style="stroke:var(--s1)" stroke-width="3" stroke-opacity="0.35"/>')
        b.append(f'<circle cx="{X(ntp):.1f}" cy="{y:.0f}" r="6" style="fill:none;stroke:var(--s1)" stroke-width="2"/>')
        b.append(f'<circle cx="{X(sr):.1f}" cy="{y:.0f}" r="6" style="fill:var(--s1)"/>')
b.append(f'<circle cx="{ml + 6}" cy="{mt - 66}" r="6" style="fill:var(--s1)"/><text class="s" x="{ml + 18}" y="{mt - 62}">success rate</text>')
b.append(f'<circle cx="{ml + 126}" cy="{mt - 66}" r="6" style="fill:none;stroke:var(--s1)" stroke-width="2"/><text class="s" x="{ml + 138}" y="{mt - 62}">task progression (share of rubric steps done)</text>')
title = "How far the VLAs got, not just whether they finished"
desc = ("For π0 and π0.5 on each of the eight tasks, success rate beside normalized task progression, the share of a "
        "task's rubric steps completed. On the hard tasks success is 0 to 0.1 but progression is often higher: π0 "
        "reaches 0.40 of the cloth fold and 0.36 of the banana under a cloth while succeeding 0 and 0.1 of the time, "
        "and π0.5 gets halfway through the baseball task while succeeding 0.2 of the time.")
open(f"{out}/success-vs-progress.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
    f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE + "  " + "\n  ".join(b) + "\n</svg>\n")
print("wrote charts")
