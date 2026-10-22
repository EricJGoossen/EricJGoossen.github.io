import numpy as np, json
v2 = np.genfromtxt("v2.csv", delimiter=",", names=True)
mj = np.genfromtxt("mj.csv", delimiter=",", names=True)
v3 = np.genfromtxt("v3.csv", delimiter=",", names=True)
ang = lambda j: 2*np.arctan2(v3[f"j{j}_qx"], v3[f"j{j}_qw"])
out = {"t": mj["t"].tolist()}
for name, s, e in (("v2", v2["q_shoulder"], v2["q_elbow"]), ("mujoco", mj["q_shoulder"], mj["q_elbow"]), ("v3", ang(0), ang(1))):
    s, e = np.unwrap(s), np.unwrap(e)
    out[name] = {"shoulder": s.tolist(), "elbow": e.tolist()}
    print(name, "shoulder@1,2,4s", [round(s[i],3) for i in (1000,2000,4000)], "elbow@1,2,4s", [round(e[i],3) for i in (1000,2000,4000)])
err = lambda a,b: max(np.max(np.abs(np.array(out[a][k])-np.array(out[b][k]))) for k in ("shoulder","elbow"))
print("max |v3-mj| rad", err("v3","mujoco"), " max |v2-mj|", err("v2","mujoco"))
json.dump(out, open("dyn_compare.json","w"))
