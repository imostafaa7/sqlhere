
<p align="center">
  <img src="https://img.shields.io/badge/sqlhere-v3.0-red?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/license-MIT-red?style=for-the-badge">
  <img src="https://img.shields.io/badge/purpose-pentesting-red?style=for-the-badge">
</p>

```
  ╔═══╗╦═══╗╦  ╦╦═══╗╦═══╗╦═╗╔═╗
  ║╔═╗║║╔═╗║╚╗╔╝║╔═╗║║╔═╗║║╔╗║║║
  ║╚═╝║║╚═╝║ ║║ ║╚═╝║║╚═╝║║║║║║║╚╗
  ║╔══╣║╔═╗║ ║║ ║╔══╣║╔═╗║║║║║║║ ║
  ║║  ║║╚═╝║ ║║ ║║  ║║╚═╝║║╚╝║║╚═╝║
  ╚╝  ╚╩═══╩ ╚╝ ╚╝  ╚╩═══╩╩══╝╩═══╝
```

# sqlhere 🔴

**Automated SQLi Discovery & Exploitation Engine**  
A powerful, multi-threaded reconnaissance pipeline that automatically discovers SQL injection vulnerabilities — without touching the target directly.

---

## 📖 Overview

`sqlhere` automates the full SQLi workflow in 5 stages, using passive archive sources and headless crawlers so **you never make a direct request to the target** during discovery:

```
katana + hakrawler + waymore   →   gf sqli   →   uro   →   httpx   →   sqlmap
        URL collection             filtering       dedup    probing     exploitation
```

## ✨ Features

| Feature | Description |
|---|---|
| 🚀 **Parallel execution** | katana, hakrawler, waymore run concurrently via ThreadPoolExecutor |
| 🔍 **Passive collection** | No direct target requests — uses archives + headless crawlers |
| 🎯 **Multi-pattern GF** | Supports `sqli`, `xss`, `lfi`, `rce`, `ssrf`, `ssti` and more |
| 🧹 **Built-in dedup** | Falls back to internal dedup if `uro` is not installed |
| 📡 **Live probing** | `httpx` filters only live endpoints before sqlmap |
| 💉 **Auto sqlmap** | Feeds cleaned URLs directly into sqlmap with custom flags |
| 🔄 **Resume support** | `--resume` saves progress after each stage — resume from where you left off |
| 🔌 **Proxy support** | Route all traffic through Burp/ZAP with `--proxy` |
| 🎭 **Quiet / Verbose** | `-q` for minimal output, `-v` for full command tracing |
| 📊 **Summary table** | Clear breakdown of URLs at each stage + sqlmap findings |
| 🧵 **Thread control** | Adjust concurrency with `--threads` (default: 20) |
| 📁 **Multi-target** | Scan multiple domains from a file with `-l` |

## 🛠️ Requirements

| Tool | Purpose | Install |
|---|---|---|
| [katana](https://github.com/projectdiscovery/katana) | Headless crawling | `go install ...` |
| [hakrawler](https://github.com/hakluke/hakrawler) | URL harvesting | `go install ...` |
| [waymore](https://github.com/xnl-h4ck3r/waymore) | Archive URL collection | `pip3 install waymore` |
| [gf](https://github.com/tomnomnom/gf) | Pattern-based filtering | `go install ...` + [patterns](https://github.com/1ndianlone/gf-patterns) |
| [uro](https://github.com/six2dez/uro) *(optional)* | URL deduplication | `pip3 install uro` |
| [httpx](https://github.com/projectdiscovery/httpx) | Live host probing | `go install ...` |
| [sqlmap](https://github.com/sqlmapproject/sqlmap) | SQL injection exploitation | `apt install sqlmap` |

```bash
# Quick install
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/hakluke/hakrawler@latest
go install github.com/tomnomnom/gf@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
pip3 install uro waymore
apt install sqlmap -y

# GF patterns (required)
git clone https://github.com/1ndianlone/gf-patterns /tmp/gf
mkdir -p ~/.gf && cp /tmp/gf/*.json ~/.gf/ && rm -rf /tmp/gf
```

## 📦 Installation

```bash
# Download
wget -O ~/Tools/sqlhere https://raw.githubusercontent.com/your/sqlhere/main/sqlhere
chmod +x ~/Tools/sqlhere
sudo ln -sf ~/Tools/sqlhere /usr/local/bin/sqlhere

# Or create manually
nano ~/Tools/sqlhere   # paste script content
chmod +x ~/Tools/sqlhere
sudo ln -sf ~/Tools/sqlhere /usr/local/bin/sqlhere
```

## 🚀 Usage

```
sqlhere [-d DOMAIN | -l LIST | --sqlmap-only FILE] [options]
```

### Basic

```bash
# Full scan
sqlhere -d target.com

# Quiet mode
sqlhere -d target.com -q

# Multi-target
sqlhere -l domains.txt
```

### Advanced

```bash
# Custom GF pattern (xss)
sqlhere -d target.com --gf xss

# With proxy (Burp/ZAP)
sqlhere -d target.com --proxy http://127.0.0.1:8080

# Resume interrupted scan
sqlhere -d target.com --resume

# Higher concurrency + depth
sqlhere -d target.com --threads 50 --depth 5

# Skip specific tools
sqlhere -d target.com --no-katana --no-waymore

# Only run sqlmap on existing URL file
sqlhere --sqlmap-only urls.txt

# Custom sqlmap args
sqlhere -d target.com --sqlmap-args "--batch --random-agent --level 5 --risk 3"
```

### Options

```
Required (choose one):
  -d, --domain               Target domain (e.g., target.com)
  -l, --list                 File with list of domains (one per line)
  --sqlmap-only URLS_FILE    Skip collection, run sqlmap on existing URLs

Collection:
  --threads N                Concurrency threads (default: 20)
  --depth N                  Crawl depth for katana/hakrawler (default: 3)
  --proxy URL                HTTP proxy (e.g., http://127.0.0.1:8080)
  --timeout N                Per-tool timeout in seconds (default: 600)

Filtering:
  --gf PATTERN               GF pattern filter (default: sqli)
                                Options: sqli, xss, lfi, rce, ssrf, ssti

SQLMap:
  --sqlmap-args ARGS         Custom sqlmap arguments
  --sqlmap-skip              Skip sqlmap phase entirely

Output:
  -o, --output DIR           Output directory (default: current dir)
  -v, --verbose              Show every command being executed
  -q, --quiet                Minimal output (errors + summary only)

Resume:
  --resume                   Resume from last completed stage

Skip tools:
  --no-katana                Skip katana
  --no-hakrawler             Skip hakrawler
  --no-waymore               Skip waymore
  --no-gf                    Skip GF filter
  --no-httpx                 Skip httpx probing
```

## 📁 Output Structure

```
/path/to/output/
├── .sqlhere_urls_raw.txt      # All collected URLs (raw)
├── .sqlhere_gf.txt            # GF-filtered URLs
├── .sqlhere_uro.txt           # De-duplicated URLs
├── .sqlhere_final.txt         # Live, probed targets → sent to sqlmap
├── .sqlhere_resume            # Resume state (when --resume used)
├── sqlmap_results/            # sqlmap output directory
│   └── ...                    # Per-target sqlmap logs
└── sqlmap_attack.log          # Full sqlmap execution log
```

## 📊 Sample Output

```
[12:34:56] [*] Target: target.com
[12:34:56] [*] Threads: 20 | Depth: 3 | GF: sqli
[12:34:56] [*] Output: /home/user/Recon/target
[12:34:57] [+] katana: 1,234 URLs
[12:34:58] [+] hakrawler: 567 URLs
[12:35:10] [+] waymore: 8,901 URLs
[12:35:10] [+] Total unique: 9,876 URLs
[12:35:12] [+] gf sqli: 89 URLs
[12:35:13] [+] uro dedup: 76 URLs
[12:35:15] [+] httpx: 42 live

  >>>>>>>>>>  TARGETS READY  >>>>>>>>>>

    * https://target.com/page?id=1
    * https://target.com/search?q=test
    * ...

  +==================================================+
  |  SUMMARY                                          |
  +==================================================+
  |  Raw collection       ->  9,876 URLs              |
  |  GF filter            ->     89 URLs              |
  |  Dedup                ->     76 URLs              |
  |  Live (httpx)         ->     42 URLs              |
  |  SQLi found           ->      3 issues            |
  |  sqlmap output        ->  /out/sqlmap_results     |
  +==================================================+
```

## 🧠 Pipeline Explained

```
┌─────────────────────────────────────────────────────────┐
│  1. URL COLLECTION (parallel)                           │
│                                                          │
│  ┌─────────┐  ┌───────────┐  ┌─────────┐               │
│  │ katana  │  │ hakrawler │  │ waymore │               │
│  │ crawl   │  │ harvest   │  │ archive │               │
│  └────┬────┘  └─────┬─────┘  └────┬────┘               │
│       └──────────────┼─────────────┘                     │
│                      ▼                                   │
│              .sqlhere_urls_raw.txt                       │
│                                                          │
│  2. GF FILTER                                            │
│     cat raw | gf sqli > gf.txt                          │
│                                                          │
│  3. DEDUP                                                │
│     cat gf | uro > uro.txt    (or built-in dedup)       │
│                                                          │
│  4. HTTPX PROBE                                          │
│     cat uro | httpx -mc 200,301,302,403,500 > final.txt │
│                                                          │
│  5. SQLMAP EXPLOITATION                                  │
│     sqlmap -m final.txt --batch [flags]                  │
└─────────────────────────────────────────────────────────┘
```

## 🎯 GF Patterns

Install patterns:
```bash
git clone https://github.com/1ndianlone/gf-patterns
mkdir -p ~/.gf && cp gf-patterns/*.json ~/.gf/
```

Use with `--gf`:
```bash
sqlhere -d target.com --gf xss       # Find XSS candidates
sqlhere -d target.com --gf lfi       # Find LFI candidates
sqlhere -d target.com --gf rce       # Find RCE candidates
sqlhere -d target.com --gf ssrf      # Find SSRF candidates
sqlhere -d target.com --gf ssti      # Find SSTI candidates
sqlhere -d target.com --gf sqli      # Find SQLi candidates (default)
sqlhere -d target.com --gf idor      # Find IDOR candidates
sqlhere -d target.com --gf redirect  # Find Open Redirect candidates
sqlhere -d target.com --gf debug     # Find Debug pages
sqlhere -d target.com --gf all       # Find ALL patterns at once
```

## 🔄 Resume & Interrupt

Press `Ctrl+C` at any time — sqlhere saves progress and exits cleanly:
```bash
# Start scan
sqlhere -d target.com --resume

# Interrupt with Ctrl+C...
# State saved to .sqlhere_resume

# Resume later — skips completed stages
sqlhere -d target.com --resume
```

## ⚡ Performance Tips

| Scenario | Recommended Flags |
|---|---|
| **Small target** | `sqlhere -d target.com` |
| **Large target** | `sqlhere -d target.com --threads 50 --depth 5` |
| **Many targets** | `sqlhere -l targets.txt --threads 30` |
| **Slow network** | `sqlhere -d target.com --timeout 300` |
| **Burp/ZAP** | `sqlhere -d target.com --proxy http://127.0.0.1:8080` |
| **Quick check** | `sqlhere -d target.com --no-waymore --no-httpx --sqlmap-skip` |
| **Stealth** | `sqlhere -d target.com --threads 5 --depth 2` |
| **Deep scan** | `sqlhere -d target.com --threads 100 --depth 7 --gf all` |

## ⚠️ Disclaimer

This tool is for **authorized security testing only**.  
Unauthorized use against targets you do not own or have explicit permission to test is **illegal**.  
The author assumes no liability for misuse.

---

<p align="center">
  <b>sqlhere</b> — <i>find the needle, pull the trigger</i>
</p>
