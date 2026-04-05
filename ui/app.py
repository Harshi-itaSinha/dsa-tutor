#!/usr/bin/env python3
"""
DSA Tutor — Flask Web UI
Run: cd ui && flask run  (or python3 app.py)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "dsa-tutor-local"

ROOT = Path(__file__).parent.parent
SESSIONS_DIR = ROOT / "sessions"
SCRIPTS_DIR = ROOT / "scripts"


# ── ANSI stripping ─────────────────────────────────────────────────────────────

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mABCDEFGHJKSTfu]")


def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# ── .cpp file parser ──────────────────────────────────────────────────────────

def parse_cpp(filepath: Path) -> dict:
    """Parse a .cpp problem file into a structured dict."""
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

    # problem statement: between "PROBLEM STATEMENT:" ... "// [TIER 1"
    stmt_m = re.search(
        r"PROBLEM STATEMENT:\s*\n// -{5,}\n(.*?)// \[TIER 1",
        text, re.DOTALL
    )
    statement = ""
    if stmt_m:
        raw = stmt_m.group(1)
        lines = []
        for line in raw.splitlines():
            # strip leading "// " or "//"
            lines.append(re.sub(r"^// ?", "", line))
        statement = "\n".join(lines).strip()

    # tier1 hint: between "[TIER 1 HINT" ... "// [TIER 2"
    tier1_m = re.search(
        r"\[TIER 1 HINT[^\n]*\]\s*:\s*\n// -{5,}\n(.*?)// \[TIER 2",
        text, re.DOTALL
    )
    tier1 = ""
    if tier1_m:
        raw = tier1_m.group(1)
        lines = [re.sub(r"^// ?", "", l) for l in raw.splitlines()]
        tier1 = "\n".join(lines).strip()

    # tier2 hint: between "[TIER 2 HINT" ... "YOUR NOTES" or "// ===="
    tier2_m = re.search(
        r"\[TIER 2 HINT[^\n]*\]\s*:\s*\n// -{5,}\n(.*?)(?:// YOUR NOTES|// ={4,})",
        text, re.DOTALL
    )
    tier2 = ""
    if tier2_m:
        raw = tier2_m.group(1)
        lines = [re.sub(r"^// ?", "", l) for l in raw.splitlines()]
        tier2 = "\n".join(lines).strip()

    # notes block: between "YOUR NOTES" ... "// ===="
    notes_m = re.search(
        r"YOUR NOTES.*?\n// -{5,}\n(.*?)// ={4,}",
        text, re.DOTALL
    )
    notes = {
        "approach": "",
        "time_complexity": "",
        "space_complexity": "",
        "edge_cases": "",
        "confidence": "",
    }
    if notes_m:
        notes_block = notes_m.group(1)
        def note_field(label):
            m = re.search(rf"{re.escape(label)}\s*(.*)", notes_block)
            return m.group(1).strip() if m else ""

        notes["approach"] = note_field("Approach tried:")
        notes["time_complexity"] = note_field("Time complexity:")
        notes["space_complexity"] = note_field("Space complexity:")
        notes["edge_cases"] = note_field("Edge cases missed:")
        notes["confidence"] = note_field("Confidence (1-5):")

    # code section: from first #include onwards
    code_m = re.search(r"(#include.*)", text, re.DOTALL)
    code = code_m.group(1).strip() if code_m else ""

    is_stub = "_tbd" in filepath.name

    return {
        "title": title,
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
        "is_stub": is_stub,
        "filename": filepath.name,
        "filepath": str(filepath),
    }


def save_cpp(filepath: Path, new_code: str, notes: dict = None):
    """Save code and optionally update notes fields in the .cpp file."""
    if not filepath.exists():
        return False, "File not found"

    text = filepath.read_text(errors="replace")

    # Update notes fields if provided
    if notes:
        def replace_field(label, value):
            nonlocal text
            # Match "   label <old_value>" and replace with "   label <new_value>"
            pattern = rf"(//\s+{re.escape(label)}\s*)([^\n]*)"
            repl = rf"\g<1>{value}"
            text, n = re.subn(pattern, repl, text)
            return n > 0

        replace_field("Approach tried:", notes.get("approach", ""))
        replace_field("Time complexity:", notes.get("time_complexity", ""))
        replace_field("Space complexity:", notes.get("space_complexity", ""))
        replace_field("Edge cases missed:", notes.get("edge_cases", ""))
        replace_field("Confidence (1-5):", notes.get("confidence", ""))

    # Replace code section: keep everything before first #include, then append new code
    code_m = re.search(r"#include", text)
    if code_m:
        header = text[:code_m.start()]
        text = header + new_code.strip() + "\n"

    filepath.write_text(text)
    return True, "Saved"


# ── patterns parser ────────────────────────────────────────────────────────────

def parse_patterns() -> list:
    """Parse coding_patterns.md SUMMARY DASHBOARD table."""
    patterns_file = ROOT / "coding_patterns.md"
    if not patterns_file.exists():
        return []

    text = patterns_file.read_text()
    # Find the table
    table_m = re.search(
        r"\| Pattern \| Comfort.*?\n\|[-| ]+\|\n(.*?)(?:\n\n|\Z)",
        text, re.DOTALL
    )
    if not table_m:
        return []

    rows = []
    for line in table_m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 6:
            continue

        pattern_name = parts[0].strip()
        comfort_raw = parts[1].strip()
        attempted = parts[2].strip()
        solved = parts[3].strip()
        avg_time = parts[4].strip()
        priority = parts[5].strip()

        # Parse comfort to number
        try:
            comfort = float(comfort_raw)
        except ValueError:
            comfort = 0.0

        comfort_pct = int((comfort / 5.0) * 100)

        rows.append({
            "pattern": pattern_name,
            "comfort": comfort_raw,
            "comfort_pct": comfort_pct,
            "attempted": attempted,
            "solved": solved,
            "avg_time": avg_time,
            "priority": priority,
        })

    return rows


# ── session lister ─────────────────────────────────────────────────────────────

def list_sessions() -> list:
    """List all session directories, newest first."""
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for d in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue

        name = d.name
        # date is first 10 chars (YYYY-MM-DD)
        date_str = name[:10] if len(name) >= 10 else name

        # determine type
        if "_contest_" in name or (len(name) > 11 and name[11:] and not name[11:].startswith("practice") and not name[11:].startswith("doubt")):
            stype = "contest"
        elif "practice" in name:
            stype = "practice"
        elif "doubt" in name:
            stype = "doubt"
        else:
            stype = "contest"

        # list problem files
        problems = []
        for slot in ["p1", "p2", "p3", "p4", "p5", "p5_repeat"]:
            cpp_files = list(d.glob(f"{slot}*.cpp"))
            for cpp in cpp_files:
                parsed = parse_cpp(cpp)
                problems.append({
                    "slot": slot,
                    "filename": cpp.name,
                    "title": parsed.get("title") or "Problem TBD",
                    "is_stub": parsed.get("is_stub", False),
                })

        sessions.append({
            "name": name,
            "date": date_str,
            "type": stype,
            "problems": problems,
            "problem_count": len(problems),
        })

    return sessions


# ── session log parser ─────────────────────────────────────────────────────────

def parse_session_log() -> list:
    """Parse session_log.md, return last 10 rows."""
    log_file = ROOT / "session_log.md"
    if not log_file.exists():
        return []

    text = log_file.read_text()
    rows = []
    in_table = False
    header_skipped = False

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "Date" in line and "Type" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            header_skipped = True
            continue
        if in_table and header_skipped:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 5:
                rows.append({
                    "date": parts[0],
                    "type": parts[1],
                    "topic": parts[2],
                    "attempted": parts[3],
                    "solved": parts[4],
                    "hints": parts[5] if len(parts) > 5 else "",
                    "duration": parts[6] if len(parts) > 6 else "",
                    "notes": parts[7] if len(parts) > 7 else "",
                })

    return rows[-10:]


# ── stats helpers ──────────────────────────────────────────────────────────────

def get_stats() -> dict:
    sessions = list_sessions()
    patterns = parse_patterns()
    high_priority = sum(1 for p in patterns if p["priority"].upper() == "HIGH")
    total_problems = sum(s["problem_count"] for s in sessions)

    return {
        "session_count": len(sessions),
        "problems_attempted": total_problems,
        "high_priority": high_priority,
    }


# ── run output parser ──────────────────────────────────────────────────────────

def parse_run_output(output: str) -> dict:
    """Parse run_tests.py output into structured test results."""
    tests = []
    summary = {"passed": 0, "total": 0}
    current_fail = None

    for line in output.splitlines():
        raw = line

        # Check for summary line like "  3/5 passed" or "  2/2 passed ✓ All"
        sum_m = re.search(r"(\d+)/(\d+) passed", line)
        if sum_m and not line.strip().startswith("✓") and not line.strip().startswith("✗"):
            summary["passed"] = int(sum_m.group(1))
            summary["total"] = int(sum_m.group(2))
            tests.append({"status": "summary", "line": line.strip()})
            current_fail = None
            continue

        stripped = line.strip()

        if stripped.startswith("✓"):
            tests.append({"status": "pass", "line": stripped})
            current_fail = None
        elif stripped.startswith("✗"):
            fail_entry = {"status": "fail", "line": stripped, "details": []}
            tests.append(fail_entry)
            current_fail = fail_entry
        elif stripped.startswith("⏱") or "TLE" in stripped and stripped.startswith("⏱"):
            tests.append({"status": "tle", "line": stripped})
            current_fail = None
        elif re.match(r"COMPILE ERROR", stripped, re.IGNORECASE):
            tests.append({"status": "error", "line": stripped})
            current_fail = None
        elif stripped.startswith("Input:") or stripped.startswith("Expected:") or stripped.startswith("Got:"):
            if current_fail is not None:
                current_fail["details"].append(stripped)
            else:
                tests.append({"status": "detail", "line": stripped})
        elif stripped and current_fail is not None and (
            "Input" in stripped or "Expected" in stripped or "Got" in stripped
        ):
            current_fail["details"].append(stripped)
        elif stripped.startswith("Compiling:") or stripped.startswith("Compiled OK"):
            tests.append({"status": "info", "line": stripped})
        elif stripped:
            tests.append({"status": "info", "line": stripped})

    return {"tests": tests, "summary": summary}


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    sessions = list_sessions()
    patterns = parse_patterns()
    stats = get_stats()
    return render_template(
        "dashboard.html",
        sessions=sessions[:20],
        patterns=patterns,
        stats=stats,
    )


@app.route("/start", methods=["POST"])
def start_session():
    stype = request.form.get("type", "practice")
    company = request.form.get("company_topic", "").strip()
    duration = request.form.get("duration", "60").strip()
    num_problems = request.form.get("num_problems", "4").strip()

    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "new_session.py"),
        "--type", stype,
        "--no-timer",
        "--duration", duration,
    ]

    if stype == "contest" and company:
        cmd += ["--company", company]
    elif stype in ("practice", "doubt") and company:
        cmd += ["--topic", company]

    if stype == "practice":
        cmd += ["--num-problems", num_problems]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=30,
        )
        output = result.stdout + result.stderr

        # Parse "Session ready: sessions/XXXX" from stdout
        m = re.search(r"Session ready:\s+sessions/(\S+)", output)
        if m:
            session_name = m.group(1).strip()
            return redirect(url_for("session_view", name=session_name))

        # Fallback: look for the directory that was just created
        # Try to figure out from output
        dir_m = re.search(r"Directory:\s+.+/sessions/(\S+)", output)
        if dir_m:
            session_name = dir_m.group(1).strip()
            return redirect(url_for("session_view", name=session_name))

        # Return error page
        return render_template("dashboard.html",
                               sessions=list_sessions()[:20],
                               patterns=parse_patterns(),
                               stats=get_stats(),
                               error=f"Could not parse session name from output:\n{output}"), 500

    except subprocess.TimeoutExpired:
        return render_template("dashboard.html",
                               sessions=list_sessions()[:20],
                               patterns=parse_patterns(),
                               stats=get_stats(),
                               error="Timed out creating session"), 500
    except Exception as e:
        return render_template("dashboard.html",
                               sessions=list_sessions()[:20],
                               patterns=parse_patterns(),
                               stats=get_stats(),
                               error=str(e)), 500


@app.route("/session/<name>")
def session_view(name):
    session_dir = SESSIONS_DIR / name
    if not session_dir.exists():
        return "Session not found", 404

    problems = []
    # Check all slots p1–p5, including p5_REPEAT
    for slot in ["p1", "p2", "p3", "p4", "p5_REPEAT", "p5"]:
        cpp_files = sorted(session_dir.glob(f"{slot}*.cpp"))
        for cpp in cpp_files:
            parsed = parse_cpp(cpp)
            parsed["slot"] = slot.lower()
            # normalize slot for URL: p5_REPEAT → p5_repeat
            parsed["slot_url"] = slot.lower()
            problems.append(parsed)

    # Deduplicate by filename (in case p5 and p5_REPEAT both match)
    seen = set()
    unique_problems = []
    for p in problems:
        if p["filename"] not in seen:
            seen.add(p["filename"])
            unique_problems.append(p)

    return render_template("session.html", session_name=name, problems=unique_problems)


@app.route("/session/<name>/<slot>")
def editor_view(name, slot):
    session_dir = SESSIONS_DIR / name
    if not session_dir.exists():
        return "Session not found", 404

    # Find the cpp file for this slot
    cpp_files = sorted(session_dir.glob(f"{slot}*.cpp"))
    if not cpp_files:
        # Try case-insensitive for p5_REPEAT
        cpp_files = sorted(session_dir.glob(f"{slot.upper()}*.cpp"))
    if not cpp_files:
        return f"No .cpp file found for slot {slot}", 404

    filepath = cpp_files[0]
    problem = parse_cpp(filepath)
    problem["slot"] = slot

    # Build list of all problems for sidebar
    all_problems = []
    for s in ["p1", "p2", "p3", "p4", "p5_REPEAT", "p5"]:
        files = sorted(session_dir.glob(f"{s}*.cpp"))
        for f in files:
            p = parse_cpp(f)
            p["slot"] = s.lower()
            all_problems.append(p)

    # Deduplicate
    seen = set()
    unique_all = []
    for p in all_problems:
        if p["filename"] not in seen:
            seen.add(p["filename"])
            unique_all.append(p)

    return render_template(
        "editor.html",
        session_name=name,
        slot=slot,
        problem=problem,
        all_problems=unique_all,
        filepath=str(filepath),
    )


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    filepath = Path(data.get("filepath", ""))
    new_code = data.get("code", "")
    notes = data.get("notes")

    if not filepath.exists():
        return jsonify({"ok": False, "error": f"File not found: {filepath}"}), 404

    ok, msg = save_cpp(filepath, new_code, notes)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No JSON data"}), 400

    filepath = Path(data.get("filepath", ""))
    new_code = data.get("code", "")
    notes = data.get("notes")

    if not filepath.exists():
        return jsonify({"ok": False, "error": f"File not found: {filepath}"}), 404

    # Save first
    ok, msg = save_cpp(filepath, new_code, notes)
    if not ok:
        return jsonify({"ok": False, "error": f"Save failed: {msg}"}), 500

    # Run tests
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_tests.py"), str(filepath)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=60,
        )
        raw_output = result.stdout + result.stderr
        output = strip_ansi(raw_output)
        parsed = parse_run_output(output)

        return jsonify({
            "ok": True,
            "output": output,
            "tests": parsed["tests"],
            "summary": parsed["summary"],
        })

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
        return jsonify({"ok": False, "error": f"File not found: {filepath}"}), 404

    # Determine session dir and slot from filepath
    session_dir = filepath.parent
    # slot is the part before the first underscore after p prefix e.g. p1_tbd.cpp → p1
    slot_m = re.match(r"(p\d+(?:_REPEAT)?)", filepath.stem, re.IGNORECASE)
    slot = slot_m.group(1) if slot_m else "p1"

    # Remove old stub files for this slot
    # We'll let fetch_problem.py handle the new filename

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS_DIR / "fetch_problem.py"),
                "--url", url,
                "--session", str(session_dir),
                "--slot", slot,
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=30,
            input="N\n",  # answer "N" to overwrite prompt if file exists
        )
        output = result.stdout + result.stderr

        if result.returncode != 0:
            return jsonify({"ok": False, "error": output}), 500

        # Find the new file that was created
        new_files = [f for f in session_dir.glob(f"{slot}*.cpp") if "_tbd" not in f.name]
        new_filepath = str(new_files[0]) if new_files else None

        return jsonify({
            "ok": True,
            "output": output,
            "new_filepath": new_filepath,
        })

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Fetch timed out (30s)"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
