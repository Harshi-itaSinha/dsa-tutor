#!/usr/bin/env python3
"""
DSA Tutor — Flask API Server
Serves JSON APIs for the React frontend.

Dev:  python3 app.py  (port 5000, React dev server proxies to this)
Prod: python3 app.py  (also serves built React from frontend/dist/)
"""

import re
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
app.secret_key = "dsa-tutor-local"

ROOT = Path(__file__).parent.parent
SESSIONS_DIR = ROOT / "sessions"
SCRIPTS_DIR = ROOT / "scripts"


# ── CORS for dev mode ─────────────────────────────────────────────────────────

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ── ANSI stripping ─────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mABCDEFGHJKSTfu]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# ── .cpp file parser ──────────────────────────────────────────────────────────

def parse_cpp(filepath: Path) -> dict:
    if not filepath.exists():
        return {}

    text = filepath.read_text(errors="replace")

    def first_match(pattern, default=""):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else default

    title = first_match(r"// PROBLEM:\s*(.+)")
    platform = first_match(r"Platform:\s*(\S+)")
    tags = first_match(r"\bTAGS:\s*(.+)")
    difficulty = first_match(r"DIFFICULTY:\s*([^|]+)")
    company = first_match(r"COMPANY:\s*(.+)")
    url = first_match(r"SOURCE:\s*(https?://\S+)")

    # problem statement
    stmt_m = re.search(r"PROBLEM STATEMENT:\s*\n// -{5,}\n(.*?)// \[TIER 1", text, re.DOTALL)
    statement = ""
    if stmt_m:
        lines = [re.sub(r"^// ?", "", l) for l in stmt_m.group(1).splitlines()]
        statement = "\n".join(lines).strip()

    # tier1 hint
    t1_m = re.search(r"\[TIER 1 HINT[^\n]*\]\s*:\s*\n// -{5,}\n(.*?)// \[TIER 2", text, re.DOTALL)
    tier1 = ""
    if t1_m:
        lines = [re.sub(r"^// ?", "", l) for l in t1_m.group(1).splitlines()]
        tier1 = "\n".join(lines).strip()

    # tier2 hint
    t2_m = re.search(r"\[TIER 2 HINT[^\n]*\]\s*:\s*\n// -{5,}\n(.*?)(?:// YOUR NOTES|// ={4,})", text, re.DOTALL)
    tier2 = ""
    if t2_m:
        lines = [re.sub(r"^// ?", "", l) for l in t2_m.group(1).splitlines()]
        tier2 = "\n".join(lines).strip()

    # notes
    notes = {"approach": "", "time_complexity": "", "space_complexity": "", "edge_cases": "", "confidence": ""}
    for field, label in [
        ("approach", "Approach tried:"),
        ("time_complexity", "Time complexity:"),
        ("space_complexity", "Space complexity:"),
        ("edge_cases", "Edge cases missed:"),
        ("confidence", "Confidence (1-5):"),
    ]:
        m = re.search(rf"{re.escape(label)}\s*([^\n]*)", text)
        if m and m.group(1).strip() not in ("", "?"):
            notes[field] = m.group(1).strip()

    # code section
    code_m = re.search(r"(#include.*)", text, re.DOTALL)
    code = code_m.group(1).strip() if code_m else ""

    return {
        "title": title or filepath.stem,
        "platform": platform,
        "tags": tags,
        "difficulty": difficulty.strip(),
        "company": company,
        "url": url,
        "statement": statement,
        "tier1": tier1,
        "tier2": tier2,
        "notes": notes,
        "code": code,
        "is_stub": "_tbd" in filepath.name,
        "filename": filepath.name,
        "filepath": str(filepath),
    }


def save_cpp(filepath: Path, new_code: str, notes: dict = None):
    if not filepath.exists():
        return False, "File not found"

    text = filepath.read_text(errors="replace")

    if notes:
        for label, key in [
            ("Approach tried:", "approach"),
            ("Time complexity:", "time_complexity"),
            ("Space complexity:", "space_complexity"),
            ("Edge cases missed:", "edge_cases"),
            ("Confidence (1-5):", "confidence"),
        ]:
            if key in notes:
                pattern = rf"(//\s+{re.escape(label)}\s*)([^\n]*)"
                text = re.sub(pattern, rf"\g<1>{notes[key]}", text)

    code_m = re.search(r"#include", text)
    if code_m:
        text = text[:code_m.start()] + new_code.strip() + "\n"

    filepath.write_text(text)
    return True, "Saved"


# ── patterns parser ───────────────────────────────────────────────────────────

def parse_patterns() -> list:
    patterns_file = ROOT / "coding_patterns.md"
    if not patterns_file.exists():
        return []

    text = patterns_file.read_text()
    table_m = re.search(r"\| Pattern \| Comfort.*?\n\|[-| ]+\|\n(.*?)(?:\n\n|\Z)", text, re.DOTALL)
    if not table_m:
        return []

    rows = []
    for line in table_m.group(1).splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 6:
            continue

        try:
            comfort = float(parts[1])
        except ValueError:
            comfort = 0.0

        rows.append({
            "pattern": parts[0],
            "comfort": parts[1],
            "comfort_pct": int((comfort / 5.0) * 100),
            "attempted": parts[2],
            "solved": parts[3],
            "avg_time": parts[4],
            "priority": parts[5],
        })
    return rows


# ── session helpers ───────────────────────────────────────────────────────────

def list_sessions() -> list:
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for d in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        name = d.name
        date_str = name[:10] if len(name) >= 10 else name

        if "practice" in name:
            stype = "practice"
        elif "doubt" in name:
            stype = "doubt"
        else:
            stype = "contest"

        problems = []
        seen = set()
        for slot in ["p1", "p2", "p3", "p4", "p5_REPEAT", "p5"]:
            for cpp in sorted(d.glob(f"{slot}*.cpp")):
                if cpp.name in seen:
                    continue
                seen.add(cpp.name)
                parsed = parse_cpp(cpp)
                problems.append({
                    "slot": slot.lower(),
                    "filename": cpp.name,
                    "title": parsed.get("title") or "Problem TBD",
                    "difficulty": parsed.get("difficulty", ""),
                    "tags": parsed.get("tags", ""),
                    "is_stub": parsed.get("is_stub", False),
                    "confidence": parsed.get("notes", {}).get("confidence", ""),
                })

        sessions.append({
            "name": name, "date": date_str, "type": stype,
            "problems": problems, "problem_count": len(problems),
        })
    return sessions


def parse_session_log() -> list:
    log_file = ROOT / "session_log.md"
    if not log_file.exists():
        return []
    rows = []
    in_table = False
    for line in log_file.read_text().splitlines():
        if "Date" in line and "Type" in line and line.startswith("|"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 5:
                rows.append({
                    "date": parts[0], "type": parts[1], "topic": parts[2],
                    "attempted": parts[3], "solved": parts[4],
                    "hints": parts[5] if len(parts) > 5 else "",
                    "duration": parts[6] if len(parts) > 6 else "",
                })
    return rows[-10:]


def parse_run_output(output: str) -> dict:
    tests = []
    summary = {"passed": 0, "total": 0}
    current_fail = None

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        sum_m = re.search(r"(\d+)/(\d+) passed", line)
        if sum_m and not stripped.startswith("✓") and not stripped.startswith("✗"):
            summary["passed"] = int(sum_m.group(1))
            summary["total"] = int(sum_m.group(2))
            tests.append({"status": "summary", "line": stripped})
            current_fail = None
            continue

        if stripped.startswith("✓"):
            tests.append({"status": "pass", "line": stripped})
            current_fail = None
        elif stripped.startswith("✗"):
            entry = {"status": "fail", "line": stripped, "details": []}
            tests.append(entry)
            current_fail = entry
        elif stripped.startswith("⏱") or ("TLE" in stripped and "⏱" in stripped):
            tests.append({"status": "tle", "line": stripped})
            current_fail = None
        elif "COMPILE ERROR" in stripped.upper():
            tests.append({"status": "error", "line": stripped})
            current_fail = None
        elif any(stripped.startswith(k) for k in ("Input:", "Expected:", "Got:")):
            if current_fail is not None:
                current_fail["details"].append(stripped)
        elif stripped.startswith("Compil"):
            tests.append({"status": "info", "line": stripped})

    return {"tests": tests, "summary": summary}


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/api/dashboard")
def api_dashboard():
    sessions = list_sessions()
    patterns = parse_patterns()
    high_priority = sum(1 for p in patterns if p["priority"].strip().upper() == "HIGH")
    total_problems = sum(s["problem_count"] for s in sessions)
    return jsonify({
        "sessions": sessions[:20],
        "patterns": patterns,
        "stats": {
            "session_count": len(sessions),
            "problems_loaded": total_problems,
            "high_priority": high_priority,
        },
        "log": parse_session_log(),
    })


@app.route("/api/session/<name>")
def api_session(name):
    session_dir = SESSIONS_DIR / name
    if not session_dir.exists():
        return jsonify({"ok": False, "error": "Session not found"}), 404

    problems = []
    seen = set()
    for slot in ["p1", "p2", "p3", "p4", "p5_REPEAT", "p5"]:
        for cpp in sorted(session_dir.glob(f"{slot}*.cpp")):
            if cpp.name in seen:
                continue
            seen.add(cpp.name)
            parsed = parse_cpp(cpp)
            parsed["slot"] = slot.lower()
            problems.append(parsed)

    return jsonify({"session_name": name, "problems": problems})


@app.route("/api/problem/<name>/<slot>")
def api_problem(name, slot):
    session_dir = SESSIONS_DIR / name
    if not session_dir.exists():
        return jsonify({"ok": False, "error": "Session not found"}), 404

    cpp_files = sorted(session_dir.glob(f"{slot}*.cpp"))
    if not cpp_files:
        return jsonify({"ok": False, "error": f"No file for slot {slot}"}), 404

    parsed = parse_cpp(cpp_files[0])
    parsed["slot"] = slot

    # all problems for sidebar
    all_problems = []
    seen = set()
    for s in ["p1", "p2", "p3", "p4", "p5_REPEAT", "p5"]:
        for f in sorted(session_dir.glob(f"{s}*.cpp")):
            if f.name in seen:
                continue
            seen.add(f.name)
            p = parse_cpp(f)
            p["slot"] = s.lower()
            all_problems.append({"slot": s.lower(), "title": p["title"], "is_stub": p["is_stub"],
                                 "confidence": p["notes"]["confidence"], "filename": f.name})

    return jsonify({"problem": parsed, "all_problems": all_problems})


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    stype = data.get("type", "practice")
    company_topic = data.get("company_topic", "").strip()
    duration = str(data.get("duration", 60))
    num_problems = str(data.get("num_problems", 4))

    cmd = [sys.executable, str(SCRIPTS_DIR / "new_session.py"),
           "--type", stype, "--no-timer", "--duration", duration]

    if stype == "contest" and company_topic:
        cmd += ["--company", company_topic]
    elif stype in ("practice", "doubt") and company_topic:
        cmd += ["--topic", company_topic]
    if stype == "practice":
        cmd += ["--num-problems", num_problems]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=str(ROOT), timeout=15, stdin=subprocess.DEVNULL)
        output = result.stdout + result.stderr

        m = re.search(r"Session ready:\s+sessions/(\S+)", output)
        if not m:
            m = re.search(r"Directory:\s+\S+/sessions/(\S+)", output)
        if m:
            return jsonify({"ok": True, "session_name": m.group(1).strip()})

        return jsonify({"ok": False, "error": f"Could not create session:\n{output}"}), 500

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Timed out creating session"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    filepath = Path(data.get("filepath", ""))
    if not filepath.exists():
        return jsonify({"ok": False, "error": "File not found"}), 404

    ok, msg = save_cpp(filepath, data.get("code", ""), data.get("notes"))
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    filepath = Path(data.get("filepath", ""))
    if not filepath.exists():
        return jsonify({"ok": False, "error": "File not found"}), 404

    ok, msg = save_cpp(filepath, data.get("code", ""), data.get("notes"))
    if not ok:
        return jsonify({"ok": False, "error": f"Save failed: {msg}"}), 500

    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_tests.py"), str(filepath)],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=60, stdin=subprocess.DEVNULL)
        output = strip_ansi(result.stdout + result.stderr)
        parsed = parse_run_output(output)
        return jsonify({"ok": True, "output": output, "tests": parsed["tests"], "summary": parsed["summary"]})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Test run timed out (60s)"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    url = data.get("url", "").strip()
    filepath = Path(data.get("filepath", ""))
    if not url:
        return jsonify({"ok": False, "error": "No URL provided"}), 400
    if not filepath.exists():
        return jsonify({"ok": False, "error": "File not found"}), 404

    session_dir = filepath.parent
    slot_m = re.match(r"(p\d+(?:_REPEAT)?)", filepath.stem, re.IGNORECASE)
    slot = slot_m.group(1) if slot_m else "p1"

    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "fetch_problem.py"),
             "--url", url, "--session", str(session_dir), "--slot", slot],
            capture_output=True, text=True, cwd=str(ROOT),
            timeout=30, stdin=subprocess.DEVNULL)
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return jsonify({"ok": False, "error": output}), 500

        new_files = [f for f in session_dir.glob(f"{slot}*.cpp") if "_tbd" not in f.name]
        return jsonify({"ok": True, "output": output,
                        "new_filepath": str(new_files[0]) if new_files else None})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Fetch timed out (30s)"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Serve React build (production) ────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    dist = Path(__file__).parent / "frontend" / "dist"
    if path and (dist / path).exists():
        return send_from_directory(str(dist), path)
    if (dist / "index.html").exists():
        return send_from_directory(str(dist), "index.html")
    return "<h1>Run: cd ui/frontend && npm run build</h1>", 404


if __name__ == "__main__":
    print("\n  DSA Tutor API Server")
    print("  API:  http://localhost:5000/api/dashboard")
    print("  UI:   cd frontend && npm run dev  (port 5173)\n")
    app.run(debug=True, port=5000)
