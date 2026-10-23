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
print("wrote charts")
