"""Extract the data the findings page charts, from the archived raw records only.

    python extract_site_data.py <evidence_root> <verified_numbers.json> <out.json>
"""
import json
import sys
import tarfile

import numpy as np

EV, VN, OUT = sys.argv[1:4]
v = json.load(open(VN))
ORD = ["hot_first", "cool_first", "alternating", "random"]


def jl(t, n):
    return [json.loads(l) for l in t.extractfile(n) if l.strip()]


# Exp 1: (temperature step, clock level) -> count
t1 = tarfile.open(f"{EV}/a3/run_exp1-4core-a3-20261016-01.tar")
tel1 = jl(t1, "results/exp1-4core-a3-20261016-01/exp1.telemetry.jsonl")
cnt = {}
for x in tel1:
    if x.get("temp_c") is None or x.get("arm_clock_mhz") is None:
        continue
    k = (round(x["temp_c"], 3), round(x["arm_clock_mhz"]))
    cnt[k] = cnt.get(k, 0) + 1
exp1 = [[t, c, n] for (t, c), n in sorted(cnt.items())]

# Exp 2 run -03 bins
t2 = tarfile.open(f"{EV}/a4/run_exp2-a4-20261018-03.tar")
m2 = json.load(t2.extractfile("results/exp2-a4-20261018-03/exp2.meta.json"))
exp2 = [[b["ramp"], round(b["temp_median_c"], 3), round(b["latency_median_ms"], 3), b["n"]] for b in m2["bins"]]

# Exp 3
t3 = tarfile.open(f"{EV}/a7/run_exp3-a7-20261018-01.tar")
P = "results/exp3-a7-20261018-01/"
m3 = json.load(t3.extractfile(P + "exp3.meta.json"))
tel3 = jl(t3, P + "exp3.telemetry.jsonl")
jobs3 = jl(t3, P + "exp3.jobs.jsonl")
by, start = {}, {}
for s in tel3:
    start[s["run_index"]] = min(start.get(s["run_index"], s["t_wall"]), s["t_wall"])
    if s.get("temp_c") is not None:
        by.setdefault(s["run_index"], []).append((s["t_wall"], s["temp_c"]))
t_first = min(start.values())
grid = np.arange(0, 119, 1.0)
traj = {}
for m in ORD:
    C = []
    for r in m3["runs"]:
        if r["mode"] == m and r["valid"]:
            pts = sorted(by[r["run_index"]])
            C.append(np.interp(grid, [p[0] - pts[0][0] for p in pts], [p[1] for p in pts]))
    C = np.array(C)
    traj[m] = {"med": np.round(np.median(C, 0), 2).tolist(), "q1": np.round(np.percentile(C, 25, 0), 2).tolist(),
               "q3": np.round(np.percentile(C, 75, 0), 2).tolist()}
seqs = [{"i": r["run_index"], "rep": r["rep"], "mode": r["mode"], "tak": round(r["time_above_knee_s"], 2),
         "p99": round(r["p99_ms"], 3), "mean": round(r["mean_ms"], 3), "thr": round(r["throughput_jobs_s"], 4),
         "cool": round(r["cooldown_s"], 1), "start_min": round((start[r["run_index"]] - t_first) / 60, 2)}
        for r in m3["runs"]]
# one example random ordering (first random sequence), as HOT=1 / COOL=0
rnd = min((r for r in m3["runs"] if r["mode"] == "random"), key=lambda r: r["run_index"])["run_index"]
pattern = "".join("1" if j["class"] == "HOT" else "0"
                  for j in sorted((j for j in jobs3 if j["run_index"] == rnd), key=lambda j: j["idx"]))
X = v["exploratory"]
data = {
    "exp1": exp1, "knee": v["G1"]["knee_c"], "g1": {k: v["G1"][k] for k in ("f_max_mhz", "f_min_mhz", "depth", "throttled_samples", "samples_with_temp")},
    "exp2": exp2, "g2": {"slope": v["G2"]["slope_ms_per_c"], "ci": v["G2"]["ci"], "jobs": v["G2"]["jobs"], "bins": v["G2"]["kept_bins"]},
    "g3": {"gap": v["G3"]["gap"]["g_hat"], "lo": v["G3"]["gap"]["ci_lo"], "hi": v["G3"]["gap"]["ci_hi"],
           "hot": v["G3"]["values"]["hot_median_ms"], "cool": v["G3"]["values"]["cool_median_ms"]},
    "g4": v["G4"]["ours"],
    "g5": [{k: p[k] for k in ("a", "b", "diff", "ci_lo", "ci_hi", "p_value", "survives_holm", "cliffs_delta")} for p in v["G5"]["p99_ms"]],
    "per_ordering": {f: {m: v["exp3_per_ordering"][f][m] for m in ORD}
                     for f in ("time_above_knee_s", "p99_ms", "mean_ms", "throughput_jobs_s", "peak_temp_c")},
    "traj": traj, "seqs": seqs, "random_pattern": pattern,
    "explore": {"jobs_over_205": X["jobs_over_205ms"], "hot_by_knee": X["hot_latency_by_knee"],
                "pooled_p99": X["pooled_p99_ms"], "mde": {k: d["sd_based"] for k, d in X["approx_mde_ms_80pct_power_holm_first_step"].items()}},
    "session": {k: v["exp3_session"][k] for k in ("n_sequences", "valid", "reruns", "jobs_total", "start_temp_range", "idle_temp_c")},
}
json.dump(data, open(OUT, "w"), separators=(",", ":"))
print("wrote", OUT, "exp1 cells", len(exp1), "pattern len", len(pattern), "HOT", pattern.count("1"))
