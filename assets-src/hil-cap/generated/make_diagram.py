"""The evaluation harness (EricJGoossen/VLA_benchmarking) as a diagram, drawn from its
README and code: configs, run_eval.py, one policy client over three transports, the
DROID robot, and the results it writes. usage: make_diagram.py <images dir>"""
import os
import sys
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../achilles/generated/scripts"))
from svgchart import STYLE  # noqa: E402

out = sys.argv[1]
b = []


def box(x, y, w, h, title, lines=(), var="--s1", strong=False):
    b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" style="fill:var({var});stroke:var({var})" '
             f'fill-opacity="{0.16 if strong else 0.07}" stroke-opacity="0.7" stroke-width="1.3"/>')
    b.append(f'<text class="b" x="{x + 12}" y="{y + 21}">{escape(title)}</text>')
    for i, line in enumerate(lines):
        b.append(f'<text class="s m" x="{x + 12}" y="{y + 40 + 16 * i}">{escape(line)}</text>')


def arrow(x1, y1, x2, y2, label="", dx=6, dy=-6, anchor="start"):
    b.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke:var(--axis)" stroke-width="1.6" marker-end="url(#a)"/>')
    if label:
        b.append(f'<text class="s m" x="{(x1 + x2) / 2 + dx}" y="{(y1 + y2) / 2 + dy}" text-anchor="{anchor}">{escape(label)}</text>')


b.append('<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
         '<path d="M0,0 L10,5 L0,10 z" style="fill:var(--axis)"/></marker></defs>')
box(16, 16, 180, 86, "YAML configs", ["policy: server, checkpoint,", "action space, chunk size", "task: prompts, rollouts"], "--ref")
box(256, 16, 180, 86, "run_eval.py", ["plans episodes, resumes,", "asks the operator to", "score every rollout"], "--s1", True)
box(526, 16, 180, 86, "DROID robot", ["Franka Panda; NUC robot", "server; ZED 2i scene and", "ZED Mini wrist cameras"], "--s4")
arrow(196, 59, 254, 59)
arrow(436, 46, 524, 46, "actions", 0, -6, "middle")
arrow(524, 74, 438, 74, "images, state", 0, 18, "middle")
box(246, 150, 200, 70, "Policy client", ["one interface: infer(obs, prompt)", "→ a chunk of actions"], "--s1", True)
arrow(346, 102, 346, 148)
for i, (name, transport) in enumerate([("π0, π0.5 (openpi)", "WebSocket"), ("GR00T N1.7", "ZMQ"), ("MolmoAct2", "HTTP")]):
    x = 16 + i * 235
    box(x, 268, 218, 54, name, [f"policy server over {transport}"], "--s5")
    arrow(346, 220, x + 109, 266)
box(16, 360, 330, 78, "results/", ["per rollout: success, step score, recall score,", "comments, scene and wrist video"], "--s3")
box(374, 360, 330, 78, "compute_results.py", ["raw.csv, by_task.csv, by_prompt.csv:", "success rate and scores per policy"], "--s3")
arrow(346, 399, 372, 399)
b.append('<path d="M 256 92 H 242 V 356" style="fill:none;stroke:var(--axis)" stroke-width="1.6" marker-end="url(#a)"/>')
title = "The evaluation harness"
desc = ("YAML configs feed run_eval.py, which drives the DROID Franka robot, asks one policy client for chunks of "
        "actions, and has the operator score each rollout. The client talks to π0 and π0.5 over WebSocket, GR00T "
        "N1.7 over ZMQ and MolmoAct2 over HTTP. Each rollout's scores and camera videos go to a results folder, and "
        "compute_results.py turns them into per-policy CSVs by task and by prompt.")
open(f"{out}/harness-diagram.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 454" role="img" aria-labelledby="t d">\n'
    f'  <title id="t">{escape(title)}</title>\n  <desc id="d">{escape(desc)}</desc>\n' + STYLE + "  " + "\n  ".join(b) + "\n</svg>\n")
print("wrote diagram")
