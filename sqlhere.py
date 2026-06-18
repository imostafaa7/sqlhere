#!/usr/bin/env python3
"""
sqlhere v3.0 — Advanced SQLi Discovery & Exploitation Engine
Author: @mb7 | Red Team Style
"""

import os, sys, subprocess, time, json, shutil, re, signal, random, threading
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"; M = "\033[95m"; C = "\033[96m"
W = "\033[97m"; D = "\033[90m"; N = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"

HOME = os.path.expanduser("~")
OUTPUT = os.getcwd()
TARGET = None
THREADS = 20
CRAWL_DEPTH = 3
GF_PATTERN = "sqli"
PROXY = ""
SQLMAP_ARGS = "--batch --random-agent --tamper=space2comment --level 3 --risk 2 --smart"
VERBOSE = False
QUIET = False
RESUME = False
SKIP_SQLMAP = False
NO_KATANA = False
NO_HAKRAWLER = False
NO_WAYMORE = False
NO_GF = False
NO_URO = False
NO_HTTPX = False
TIMEOUT = 600

COMPLETED = set()
START_TIME = None
TOTAL_URLS = 0

def sec():
    return datetime.now().strftime("%H:%M:%S")

def log(msg, level="info"):
    if QUIET and level in ("info","cmd"): return
    icons = {"info": f"{R}[{W}*{R}]{N}", "ok": f"{R}[{G}+{R}]{N}", "warn": f"{R}[{Y}!{R}]{N}", "err": f"{R}[{R}x{R}]{N}", "cmd": f"{R}[{C}~{R}]{N}"}
    print(f"{DIM}[{sec()}]{N} {icons.get(level, icons['info'])} {msg}")

def run(cmd, timeout=None, capture=False):
    if VERBOSE: log(f"$ {cmd}", "cmd")
    t = timeout or TIMEOUT
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture, text=True, timeout=t)
        return (r.stdout.strip(), r.stderr.strip(), r.returncode) if capture else ("", "", r.returncode)
    except subprocess.TimeoutExpired:
        log(f"Timed out ({t}s): {cmd[:60]}", "err")
        return "", "", -1
    except Exception as e:
        log(f"Error: {e}", "err")
        return "", "", -1

def banner():
    os.system("clear" if os.name == "posix" else "cls")
    print(f"""{R}
  ╔═══╗╦═══╗╦  ╦╦═══╗╦═══╗╦═╗╔═╗
  ║╔═╗║║╔═╗║╚╗╔╝║╔═╗║║╔═╗║║╔╗║║║
  ║╚═╝║║╚═╝║ ║║ ║╚═╝║║╚═╝║║║║║║║╚╗
  ║╔══╣║╔═╗║ ║║ ║╔══╣║╔═╗║║║║║║║ ║
  ║║  ║║╚═╝║ ║║ ║║  ║║╚═╝║║╚╝║║╚═╝║
  ╚╝  ╚╩═══╩ ╚╝ ╚╝  ╚╩═══╩╩══╝╩═══╝
{N}{DIM}  ╔══════════════════════════════════════════╗
  ║  {W}SQLi Automation Engine v3.0{D}          ║
  ║  {W}Author: @mb7 | Red Team{D}              ║
  ╚══════════════════════════════════════════╝{N}
""")

def spin(msg):
    chars = ["< ^ > v", "/ - \\ |", ". o O o"]
    e = threading.Event()
    def _spin():
        cs = random.choice(chars).split()
        while not e.is_set():
            for c in cs:
                if e.is_set(): break
                sys.stdout.write(f"\r  {R}[{N} {msg} {R}{c}{N} ]")
                sys.stdout.flush()
                time.sleep(0.1)
        sys.stdout.write(f"\r  {G}[{N} {msg} {' ' * 20}\n")
    t = threading.Thread(target=_spin, daemon=True)
    t.start()
    return e

def check_tools():
    global SKIP_SQLMAP, NO_URO
    tools = {"katana": "go install ...",
             "hakrawler": "go install ...",
             "waymore": "pip3 install waymore",
             "gf": "go install ...",
             "httpx": "go install ...",
             "sqlmap": "apt install sqlmap"}
    missing = []
    for t, inst in tools.items():
        if not shutil.which(t):
            if t == "sqlmap": SKIP_SQLMAP = True
            missing.append(f"{t}")
    if missing:
        log(f"Missing: {', '.join(missing)}", "err")
        log("Install with: go install/apt install/pip3", "warn")
        return False
    if not shutil.which("uro"):
        NO_URO = True
        log("uro not found - using built-in dedup", "warn")
    return True

def dedup_urls(urls):
    seen = set()
    result = []
    for u in urls:
        u = u.split("#")[0].rstrip("/")
        if u and u not in seen:
            seen.add(u)
            result.append(u)
    return result

def run_tool_parallel(target, name, cmd, timeout):
    e = spin(f"{name}...")
    _, _, rc = run(cmd, timeout)
    e.set()
    return name, rc

def collect_urls(target):
    global TOTAL_URLS
    all_urls = set()
    jobs = []
    executor = ThreadPoolExecutor(max_workers=3)

    if not NO_KATANA and "collect" not in COMPLETED:
        o = f"{OUTPUT}/.sqlhere_katana.txt"
        p = f"-p {PROXY}" if PROXY else ""
        cmd = f"katana -u {target} -d {CRAWL_DEPTH} -jc -silent -o {o} -rate-limit 50 -concurrency {THREADS} {p} 2>/dev/null"
        jobs.append(executor.submit(run_tool_parallel, target, "katana", cmd, 300))

    if not NO_HAKRAWLER and "collect" not in COMPLETED:
        o = f"{OUTPUT}/.sqlhere_hakrawler.txt"
        p = f"-p {PROXY}" if PROXY else ""
        cmd = f"echo '{target}' | hakrawler -d {CRAWL_DEPTH} -subs -u {THREADS} -t 10 {p} 2>/dev/null > {o}"
        jobs.append(executor.submit(run_tool_parallel, target, "hakrawler", cmd, 300))

    if not NO_WAYMORE and "collect" not in COMPLETED:
        o = f"{OUTPUT}/.sqlhere_waymore"
        p = f"--proxy {PROXY}" if PROXY else ""
        cmd = f"waymore -i {target} -mode U -o {o} -x 5000 {p} 2>/dev/null"
        jobs.append(executor.submit(run_tool_parallel, target, "waymore", cmd, 600))

    for f in as_completed(jobs):
        pass

    for fname in [".sqlhere_katana.txt", ".sqlhere_hakrawler.txt"]:
        fp = f"{OUTPUT}/{fname}"
        if os.path.exists(fp) and os.path.getsize(fp) > 0:
            with open(fp) as f:
                all_urls.update(f.read().splitlines())
            log(f"{fname.split('.')[1]}: OK", "ok")

    wd = f"{OUTPUT}/.sqlhere_waymore"
    if os.path.exists(wd):
        wayfile = f"{wd}/{target}.txt"
        if not os.path.exists(wayfile):
            wayfile = f"{wd}/{target}/{target}.txt"
        if not os.path.exists(wayfile):
            found = list(Path(wd).rglob("*.txt"))
            if found: wayfile = str(found[0])
        if os.path.exists(wayfile):
            with open(wayfile) as f:
                all_urls.update(f.read().splitlines())
            log(f"waymore: OK", "ok")

    if not all_urls:
        log("No URLs collected!", "err")
        return False

    COMPLETED.add("collect")
    all_urls = dedup_urls(sorted(all_urls))
    TOTAL_URLS = len(all_urls)
    with open(f"{OUTPUT}/.sqlhere_urls_raw.txt", "w") as f:
        f.write("\n".join(all_urls))
    log(f"Total unique: {TOTAL_URLS} URLs", "ok")
    return True

def gf_filter():
    rf = f"{OUTPUT}/.sqlhere_urls_raw.txt"
    gf = f"{OUTPUT}/.sqlhere_gf.txt"
    if "gf" in COMPLETED:
        return os.path.exists(gf) and os.path.getsize(gf) > 0
    if not os.path.exists(rf) or os.path.getsize(rf) == 0:
        return False
    if NO_GF:
        shutil.copy(rf, gf); COMPLETED.add("gf"); return True
    e = spin(f"gf {GF_PATTERN}...")
    cmd = f"cat {rf} | gf {GF_PATTERN} 2>/dev/null > {gf}"
    _, _, rc = run(cmd, 120)
    e.set()
    if os.path.exists(gf) and os.path.getsize(gf) > 0:
        cnt = len(open(gf).read().splitlines())
        log(f"gf {GF_PATTERN}: {cnt} URLs", "ok")
        COMPLETED.add("gf")
        return cnt > 0
    log("No gf matches", "warn")
    return False

def dedup_stage():
    gf = f"{OUTPUT}/.sqlhere_gf.txt"
    ur = f"{OUTPUT}/.sqlhere_uro.txt"
    if "uro" in COMPLETED:
        return os.path.exists(ur) and os.path.getsize(ur) > 0
    if not os.path.exists(gf) or os.path.getsize(gf) == 0:
        return False
    if NO_URO:
        urls = dedup_urls(open(gf).read().splitlines())
        with open(ur, "w") as f: f.write("\n".join(urls))
        log(f"built-in dedup: {len(urls)} URLs", "ok")
        COMPLETED.add("uro")
        return len(urls) > 0
    e = spin("uro dedup...")
    _, _, rc = run(f"cat {gf} | uro 2>/dev/null > {ur}", 120)
    e.set()
    if os.path.exists(ur) and os.path.getsize(ur) > 0:
        cnt = len(open(ur).read().splitlines())
        log(f"uro dedup: {cnt} URLs", "ok")
        COMPLETED.add("uro")
        return cnt > 0
    return False

def httpx_stage():
    ur = f"{OUTPUT}/.sqlhere_uro.txt"
    fn = f"{OUTPUT}/.sqlhere_final.txt"
    if "httpx" in COMPLETED:
        return os.path.exists(fn) and os.path.getsize(fn) > 0
    if not os.path.exists(ur) or os.path.getsize(ur) == 0:
        return False
    if NO_HTTPX:
        shutil.copy(ur, fn); COMPLETED.add("httpx"); return True
    p = f"-proxy {PROXY}" if PROXY else ""
    e = spin("httpx probing...")
    _, _, rc = run(f"cat {ur} | httpx -silent -mc 200,301,302,403,500 -timeout 10 {p} -o {fn} 2>/dev/null", 300)
    e.set()
    if os.path.exists(fn) and os.path.getsize(fn) > 0:
        cnt = len(open(fn).read().splitlines())
        log(f"httpx: {cnt} live", "ok")
        COMPLETED.add("httpx")
        return cnt > 0
    return False

def sqlmap_stage():
    fn = f"{OUTPUT}/.sqlhere_final.txt"
    sd = f"{OUTPUT}/sqlmap_results"
    sl = f"{OUTPUT}/sqlmap_attack.log"
    if "sqlmap" in COMPLETED:
        log("sqlmap already done", "info"); return
    if not os.path.exists(fn) or os.path.getsize(fn) == 0:
        log("No targets", "warn"); return
    cnt = len(open(fn).read().splitlines())
    log(f"sqlmap: {cnt} targets", "info")
    os.makedirs(sd, exist_ok=True)
    p = f"--proxy={PROXY}" if PROXY else ""
    cmd = f"sqlmap -m {fn} {SQLMAP_ARGS} {p} --output-dir={sd} --batch --flush-session 2>&1 | tee -a {sl}"
    if not QUIET:
        for i in range(3,0,-1):
            sys.stdout.write(f"\r  {R}[{N} Starting in {R}{i}{N} ]")
            sys.stdout.flush(); time.sleep(1)
        sys.stdout.write("\r"+" "*30+"\r")
    t0 = time.time()
    log("sqlmap running...", "info")
    _, _, rc = run(cmd, 86400)
    el = time.time()-t0
    log(f"sqlmap done ({el:.0f}s exit:{rc})", "ok")
    if rc == 0: COMPLETED.add("sqlmap")

def show_summary():
    fn = f"{OUTPUT}/.sqlhere_final.txt"
    sd = f"{OUTPUT}/sqlmap_results"
    print(f"\n  {R}{'='*50}{N}")
    print(f"  {R}+{'='*48}+{N}")
    print(f"  {R}|{N}  {BOLD}SUMMARY{R}  {' '*37}{R}|{N}")
    print(f"  {R}+{'='*48}+{N}")
    stages = [
        ("Raw collection", ".sqlhere_urls_raw.txt"),
        ("GF filter", ".sqlhere_gf.txt"),
        ("Dedup", ".sqlhere_uro.txt"),
        ("Live (httpx)", ".sqlhere_final.txt"),
    ]
    for name, sf in stages:
        p = f"{OUTPUT}/{sf}"
        if os.path.exists(p):
            c = len(open(p).read().splitlines())
            print(f"  {R}|{N}  {name:20s} -> {G}{c:>6}{N} URLs  {R}|{N}")
        else:
            print(f"  {R}|{N}  {name:20s} -> {R}{'N/A':>6}{N}       {R}|{N}")
    if os.path.exists(sd):
        logs = list(Path(sd).rglob("log"))
        vulns = 0
        for lf in logs:
            if "parameter" in open(lf).read(): vulns += 1
        print(f"  {R}|{N}  {'SQLi found':20s} -> {G}{vulns:>6}{N} issues {R}|{N}")
        print(f"  {R}|{N}  {'sqlmap output':20s} -> {D}{sd}{N} {R}|{N}")
    print(f"  {R}+{'='*48}+{N}")
    if os.path.exists(fn):
        urls = open(fn).read().splitlines()
        print(f"  {R}>{N} Targets ({len(urls)}):")
        for u in urls[:8]: print(f"    {DIM}*{N} {C}{u}{N}")
        if len(urls) > 8: print(f"    {DIM}... +{len(urls)-8}{N}")
    print()

def save_state():
    if RESUME:
        with open(f"{OUTPUT}/.sqlhere_resume", "w") as f:
            json.dump(list(COMPLETED), f)

def load_state():
    if RESUME and os.path.exists(f"{OUTPUT}/.sqlhere_resume"):
        with open(f"{OUTPUT}/.sqlhere_resume") as f:
            COMPLETED.update(json.load(f))
        log(f"Resume: {len(COMPLETED)} stages done", "info")

def cleanup():
    for f in [".sqlhere_urls_raw.txt", ".sqlhere_katana.txt", ".sqlhere_hakrawler.txt",
              ".sqlhere_waymore", ".sqlhere_wayback.txt", ".sqlhere_gf.txt", ".sqlhere_uro.txt"]:
        p = os.path.join(OUTPUT, f)
        if os.path.isfile(p): os.remove(p)
        elif os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)

def sigint(sig, frame):
    log("Interrupted - saving state", "warn")
    save_state(); cleanup(); sys.exit(0)

def main():
    global TARGET, THREADS, CRAWL_DEPTH, GF_PATTERN, PROXY, SQLMAP_ARGS
    global VERBOSE, QUIET, RESUME, SKIP_SQLMAP, NO_KATANA, NO_HAKRAWLER, NO_WAYMORE
    global NO_GF, NO_URO, NO_HTTPX, TIMEOUT, OUTPUT

    import argparse
    p = argparse.ArgumentParser(prog="sqlhere", formatter_class=argparse.RawTextHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("-d", "--domain", help="Target domain")
    g.add_argument("-l", "--list", help="Domains file (one per line)")
    g.add_argument("--sqlmap-only", metavar="URLS_FILE", help="Run sqlmap on existing URLs file")

    p.add_argument("--threads", type=int, default=20, help="Concurrency (default: 20)")
    p.add_argument("--depth", type=int, default=3, help="Crawl depth (default: 3)")
    p.add_argument("--gf", default="sqli", help="GF pattern: sqli, xss, lfi, rce, etc")
    p.add_argument("--proxy", default="", help="HTTP proxy")
    p.add_argument("--sqlmap-args", default=SQLMAP_ARGS, help="sqlmap args")
    p.add_argument("--timeout", type=int, default=600, help="Per-tool timeout (s)")
    p.add_argument("--output", "-o", default=OUTPUT, help="Output directory")
    p.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose (show commands)")
    p.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    p.add_argument("--no-katana", action="store_true", help="Skip katana")
    p.add_argument("--no-hakrawler", action="store_true", help="Skip hakrawler")
    p.add_argument("--no-waymore", action="store_true", help="Skip waymore")
    p.add_argument("--no-gf", action="store_true", help="Skip GF filter")
    p.add_argument("--no-httpx", action="store_true", help="Skip httpx probe")
    p.add_argument("--sqlmap-skip", action="store_true", help="Skip sqlmap")

    args = p.parse_args()
    TARGET = args.domain
    if args.list:
        with open(args.list) as f:
            TARGET = [l.strip() for l in f if l.strip()]
    THREADS = args.threads; CRAWL_DEPTH = args.depth; GF_PATTERN = args.gf
    PROXY = args.proxy; SQLMAP_ARGS = args.sqlmap_args; TIMEOUT = args.timeout
    OUTPUT = args.output; VERBOSE = args.verbose; QUIET = args.quiet; RESUME = args.resume
    NO_KATANA = args.no_katana; NO_HAKRAWLER = args.no_hakrawler; NO_WAYMORE = args.no_waymore
    NO_GF = args.no_gf; NO_HTTPX = args.no_httpx
    if args.sqlmap_skip: SKIP_SQLMAP = True
    if args.sqlmap_only:
        TARGET = args.sqlmap_only; SKIP_SQLMAP = False
        NO_KATANA = NO_HAKRAWLER = NO_WAYMORE = NO_GF = True; NO_HTTPX = True
        NO_URO = True

    signal.signal(signal.SIGINT, sigint)
    banner()
    os.makedirs(OUTPUT, exist_ok=True)

    if not check_tools():
        log("Install missing tools and try again", "err"); sys.exit(1)

    load_state()
    tgt = TARGET if isinstance(TARGET, str) else f"{len(TARGET)} targets"
    log(f"Target: {Y}{tgt}{N}", "info")
    log(f"Threads: {THREADS} | Depth: {CRAWL_DEPTH} | GF: {GF_PATTERN}", "info")
    if PROXY: log(f"Proxy: {M}{PROXY}{N}", "info")
    log(f"Output: {D}{OUTPUT}{N}", "info")
    if RESUME: log(f"Resume: {len(COMPLETED)} stages", "info")
    print()

    if isinstance(TARGET, str) and os.path.isfile(TARGET):
        shutil.copy(TARGET, f"{OUTPUT}/.sqlhere_final.txt")
        COMPLETED.update(["collect","gf","uro","httpx"])
        sqlmap_stage(); show_summary(); save_state(); return

    ok = True
    if isinstance(TARGET, list):
        all_u = set()
        for t in TARGET:
            if not t: continue
            log(f"Target: {C}{t}{N}", "info")
            if collect_urls(t):
                rf = f"{OUTPUT}/.sqlhere_urls_raw.txt"
                if os.path.exists(rf): all_u.update(open(rf).read().splitlines())
        if not all_u: log("No URLs", "err"); return
        with open(f"{OUTPUT}/.sqlhere_urls_raw.txt", "w") as f:
            f.write("\n".join(sorted(all_u)))
        log(f"Merged: {len(all_u)} URLs", "ok")
    else:
        if not collect_urls(TARGET): return
    save_state()

    if not gf_filter(): return
    save_state()
    if not dedup_stage(): return
    save_state()
    if not httpx_stage(): return
    save_state()

    fn = f"{OUTPUT}/.sqlhere_final.txt"
    if os.path.exists(fn) and os.path.getsize(fn) > 0:
        urls = open(fn).read().splitlines()
        log(f"{G}{len(urls)}{N} live targets", "ok")
        for u in urls[:5]: print(f"    {DIM}*{N} {C}{u}{N}")
        if len(urls) > 5: print(f"    {DIM}... +{len(urls)-5}{N}")
        print()

    if not SKIP_SQLMAP: sqlmap_stage()
    save_state()
    show_summary()
    cleanup()
    print(f"  {R}sqlhere{N} done.\n")

if __name__ == "__main__":
    main()
