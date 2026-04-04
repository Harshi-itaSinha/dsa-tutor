#!/usr/bin/env python3
"""
timer.py — Countdown timer for DSA contest sessions.

Usage:
  python3 scripts/timer.py 90          # 90-minute countdown
  python3 scripts/timer.py 90 --quiet  # no per-minute alerts, only final warning
"""

import argparse
import sys
import time
import threading

USE_COLOR = sys.stdout.isatty()

def green(s):  return f"\033[32m{s}\033[0m" if USE_COLOR else s
def yellow(s): return f"\033[33m{s}\033[0m" if USE_COLOR else s
def red(s):    return f"\033[31m{s}\033[0m" if USE_COLOR else s
def bold(s):   return f"\033[1m{s}\033[0m" if USE_COLOR else s
def clear_line(): print("\r" + " " * 60 + "\r", end="", flush=True)


def fmt_time(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def beep():
    """Try to emit a terminal bell."""
    print("\a", end="", flush=True)


def run_timer(total_minutes: int, quiet: bool):
    total_seconds = total_minutes * 60
    remaining = total_seconds

    # milestone alerts (minutes remaining)
    milestones = {30, 15, 10, 5, 2, 1}
    fired = set()

    print(bold(f"\n⏱  Contest timer started: {total_minutes} minutes"))
    print("   Press Ctrl+C to stop.\n")

    try:
        while remaining >= 0:
            # display
            elapsed = total_seconds - remaining
            bar_len = 40
            filled = int(bar_len * elapsed / total_seconds) if total_seconds else bar_len
            bar = "█" * filled + "░" * (bar_len - filled)

            if remaining > 10 * 60:
                color = green
            elif remaining > 5 * 60:
                color = yellow
            else:
                color = red

            line = color(f"  [{bar}]  {fmt_time(remaining)} remaining")
            print(f"\r{line}", end="", flush=True)

            # milestone alerts
            mins_left = remaining // 60
            if not quiet and mins_left in milestones and mins_left not in fired:
                fired.add(mins_left)
                beep()
                clear_line()
                if mins_left > 5:
                    print(yellow(f"\n  ⚡ {mins_left} minutes remaining!\n"))
                elif mins_left > 1:
                    print(red(bold(f"\n  ⚠️  {mins_left} minutes left! Wrap up!\n")))
                else:
                    print(red(bold(f"\n  🚨 LAST MINUTE!\n")))

            if remaining == 0:
                break

            time.sleep(1)
            remaining -= 1

    except KeyboardInterrupt:
        clear_line()
        print(yellow("\n  Timer stopped early."))
        sys.exit(0)

    clear_line()
    beep()
    beep()
    print(red(bold("\n  🔴 TIME'S UP! Contest over.\n")))
    print("  Post-session checklist:")
    print("    1. Fill YOUR NOTES in each problem file")
    print("    2. Fill session_summary.md")
    print("    3. python3 scripts/update_patterns.py --session <dir>")
    print("    4. git add . && git commit -m 'Session: ...' && git push\n")


def main():
    parser = argparse.ArgumentParser(description="Countdown timer for DSA sessions.")
    parser.add_argument("minutes", type=int, help="Duration in minutes")
    parser.add_argument("--quiet", action="store_true", help="Suppress mid-session alerts")
    args = parser.parse_args()

    if args.minutes <= 0:
        print("Minutes must be > 0")
        sys.exit(1)

    run_timer(args.minutes, args.quiet)


if __name__ == "__main__":
    main()
