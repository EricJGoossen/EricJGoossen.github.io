"""Lines of code Eric added per site entry, from the commits each entry links to.

Counts added lines (git numstat, renames detected, no merge commits) in code
files, only in commits authored by Eric (or by Claude in his own repos).
"""
import os, re, subprocess, sys, json

R = os.environ.get("LOC_REPOS", os.path.join(os.path.dirname(__file__), "repos"))  # clones of every repo below
ERIC = {"fada@uw.edu", "96024993+ericjgoossen@users.noreply.github.com", "fadago@outlook.com", "fada3259@gmail.com",
        "fada@outlook.com", "root@ericsvivobook.localdomain", "ericjgoossen@gmail.com", "noreply@anthropic.com"}
CODE = re.compile(r"\.(c|cc|cpp|cxx|h|hh|hpp|hxx|ipp|inl|cu|cuh|py|pyx|java|kt|kts|js|mjs|ts|tsx|jsx|rs|go|glsl|vert|frag|comp|sh|bash|cmake|yaml|yml|toml|html|css|launch|ino)$|(^|/)(CMakeLists\.txt|Dockerfile|Makefile)$", re.I)
SKIP = re.compile(r"(^|/)(third_party|thirdparty|vendor|external|extern|_deps|build|node_modules|generated|\.github|site-packages|lib/ftc)(/|$)|openarm_(left|right)_ik\.py$|package-lock|\.min\.(js|css)$|pnpm-lock|poetry\.lock|uv\.lock", re.I)


def git(repo, *args):
    return subprocess.run(["git", "-C", os.path.join(R, repo), *args], capture_output=True, text=True, check=True).stdout


def commits(repo, spec):
    """spec: 'sha' (one commit; a merge means its branch's commits), 'a..b', or ['sha', ...]."""
    if isinstance(spec, list):
        return [c for s in spec for c in commits(repo, s)]
    if ".." in spec:
        return git(repo, "rev-list", "--no-merges", spec).split()
    parents = git(repo, "log", "-1", "--format=%P", spec).split()
    if len(parents) > 1:
        return git(repo, "rev-list", "--no-merges", f"{parents[0]}..{spec}").split()
    return [git(repo, "rev-parse", spec).strip()]


SEEN = {}  # repo -> Counter of (file, line) already credited to an earlier entry


def count(repo, spec, path=None, show=False):
    """Non-blank lines Eric added in code files; a line already credited to an
    earlier entry in the same repo (a squash merge of a branch counted before)
    isn't counted again."""
    from collections import Counter
    seen = SEEN.setdefault(repo, Counter())
    total, files = 0, Counter()
    for c in dict.fromkeys(commits(repo, spec)):
        email = git(repo, "log", "-1", "--format=%ae", c).strip().lower()
        if email not in ERIC:
            continue
        out = git(repo, "show", "-M", "--format=", "--unified=0", c, *(["--", path] if path else []))
        f = None
        for line in out.splitlines():
            if line.startswith("+++ "):
                f = line[6:] if line != "+++ /dev/null" else None
                if f and not (CODE.search(f) and not SKIP.search(f)):
                    f = None
            elif f and line.startswith("+") and line[1:].strip():
                key = (f, line[1:].strip())
                if seen[key] > 0:
                    seen[key] -= 1
                    continue
                total += 1
                files[f] += 1
                SEEN.setdefault(repo + "#new", Counter())[key] += 1
    if show:
        for f, n in files.most_common(8):
            print(f"      {n:6} {f}")
    return total


def settle(repo):
    """After an entry: what it added counts as seen for the entries after it."""
    from collections import Counter
    SEEN.setdefault(repo, Counter()).update(SEEN.pop(repo + "#new", Counter()))


ENTRIES = {
    "achilles/where-it-started": [("Achilles", "0dc8cfb")],
    "achilles/v2": [("Achilles", "0dc8cfb..39f1713")],
    "achilles/v3-design": [("Achilles", "2c91aac")],
    "achilles/simd": [("Achilles", "74307df")],
    "achilles/renderer": [("Achilles", "c68ad1b")],
    "achilles/dynamics": [("Achilles", "98b23d5")],
    "achilles/integrators": [("Achilles", "9caef5c")],
    "achilles/mujoco-comparison": [("Achilles", "9caef5c..355a392")],
    "achilles/collisions": [("Achilles", "feb1611")],
    "achilles/collision-response": [("Achilles", "feb1611..223af7c")],
    "aruw/kalman-filter": [("aruw-mcb", "57dd3eb62f9330f57eea4b856fb0c3f8f6fe5a7d"), ("aruw-mcb", "32612de587558ed10e7d0453618395ba06c242d3")],
    "aruw/odin-characterization": [("odin-characterization", "aa1cefe")],
    "aruw/odin-error-model": [("odin-characterization", "aa1cefe..2cf113f")],
    "aruw/ld19-lidar": [("odin-characterization", "5244122", "odin_char/sensors/ld19")],
    "fleet-rl/automatic-reset": [("fleet_so101_infra", "7aa4d7f")],
    "ftc/live-view": [("Live-View", "d2a550a")],
    "ftc/skidaddle-library": [("SKIDADDLE", "7d3240c")],
    "ftc/skidaddle-rework": [("SKIDADDLE", "7d3240c..4b3fdb9")],
    "hil-cap/experiment-design": [("VLA_benchmarking", "846182c", "configs/task_configs")],
    "hil-cap/harness": [("VLA_benchmarking", "1ea375b", ":(exclude)configs/task_configs")],
    "opendubs/bringup": [("rosbag_recorder", "efb44ad")],
    "opendubs/optical-flow": [("M5_stack_sensor_transfer", "cdbf364"), ("open_dubs_mocap", "f8cd5d2")],
    "opendubs/impedance-control": [("openarm_cartesian_control", "176f011"), ("openarm_impedance_control", "bea0dfa")],
    "opendubs/ik-fix": [("ssik", "d153492fc..38eb99809")],
    "opendubs/teleop": [("openarm", "a69881c")],
    "opendubs/arm-group": [("mj_manipulator", "fb55d3652..0858fef99")],
    "opendubs/parallel-arms": [("mj_manipulator_ros", "c7bedb6")],
}

# A bare sha means "everything up to it" unless it's one of the one-commit links.
ONE = {"0dc8cfb", "2c91aac", "74307df", "c68ad1b", "98b23d5", "9caef5c", "feb1611", "c7bedb6",
       "57dd3eb62f9330f57eea4b856fb0c3f8f6fe5a7d", "32612de587558ed10e7d0453618395ba06c242d3"}

if __name__ == "__main__":
    show = "-v" in sys.argv
    result = {}
    import glob
    site = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../src/projects")
    date = {f"{p.split('/')[-3]}/{p.split('/')[-1][11:-3]}": p.split('/')[-1][:10] for p in glob.glob(f"{site}/*/log/*.md")}
    for key, parts in sorted(ENTRIES.items(), key=lambda kv: date[kv[0]]):
        n = 0
        for repo, spec, *path in parts:
            if ".." not in spec and spec not in ONE:
                spec = git(repo, "rev-list", "--no-merges", spec).split()
            m = count(repo, spec, path[0] if path else None, show)
            if show:
                print(f"   {repo} {spec if isinstance(spec, str) else f'{len(spec)} commits'}: {m}")
            n += m
        for repo, *_ in parts:
            settle(repo)
        result[key] = n
        print(f"{n:7}  {key}")
    json.dump(result, open(os.path.join(os.path.dirname(__file__), "loc.json"), "w"), indent=1)
