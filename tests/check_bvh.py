"""
check_bvh.py — Validates a BVH file for structural correctness and data integrity.
Can be run as a module: python tests/check_bvh.py <path_to.bvh>
"""

import os
import sys
import math


def check_bvh(filepath: str) -> bool:
    """
    Run a series of validation checks on a BVH file.

    Checks:
        1. File exists and is non-empty.
        2. HIERARCHY block is present.
        3. MOTION block is present, after HIERARCHY.
        4. 'Frames:' line is present and the count matches the actual data lines.
        5. 'Frame Time:' line is present and the value is a positive float.
        6. No NaN or Inf values in any motion data frame.

    Args:
        filepath: Absolute or relative path to the .bvh file.

    Returns:
        True if all checks pass, False otherwise (prints each failure).
    """
    problems = []

    # ── 1. File exists ──────────────────────────────────────────────────
    if not os.path.exists(filepath):
        print(f"FAIL: File not found — {filepath}")
        return False

    if os.path.getsize(filepath) == 0:
        print("FAIL: File is empty.")
        return False

    with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()

    lines = raw.splitlines()

    # ── 2. HIERARCHY block ───────────────────────────────────────────────
    hier_idx = next((i for i, l in enumerate(lines) if l.strip() == "HIERARCHY"), None)
    if hier_idx is None:
        problems.append("Missing HIERARCHY block.")
    
    # ── 3. MOTION block ──────────────────────────────────────────────────
    motion_idx = next((i for i, l in enumerate(lines) if l.strip() == "MOTION"), None)
    if motion_idx is None:
        problems.append("Missing MOTION block.")
    elif hier_idx is not None and motion_idx < hier_idx:
        problems.append("MOTION block appears before HIERARCHY block.")

    # ── 4. Frames count consistency ──────────────────────────────────────
    declared_frames = None
    frame_time_idx = None

    if motion_idx is not None:
        for i, line in enumerate(lines[motion_idx:], start=motion_idx):
            stripped = line.strip()
            if stripped.startswith("Frames:"):
                try:
                    declared_frames = int(stripped.split(":")[1].strip())
                except ValueError:
                    problems.append(f"Could not parse 'Frames:' value on line {i+1}.")
            elif stripped.startswith("Frame Time:"):
                frame_time_idx = i
                try:
                    ft = float(stripped.split(":")[1].strip())
                    if ft <= 0:
                        problems.append(f"Frame Time is non-positive ({ft}) on line {i+1}.")
                except ValueError:
                    problems.append(f"Could not parse 'Frame Time:' value on line {i+1}.")
                break  # Data starts after this line

    if declared_frames is None and motion_idx is not None:
        problems.append("'Frames:' line not found in MOTION block.")

    # Actual data lines are everything after Frame Time line
    if frame_time_idx is not None and declared_frames is not None:
        data_lines = [l for l in lines[frame_time_idx + 1:] if l.strip()]
        actual_frames = len(data_lines)
        if actual_frames != declared_frames:
            problems.append(
                f"Frame count mismatch: declared {declared_frames}, found {actual_frames} data lines."
            )

        # ── 6. NaN / Inf check ───────────────────────────────────────
        nan_frames = []
        for idx, dl in enumerate(data_lines):
            for token in dl.split():
                try:
                    val = float(token)
                    if math.isnan(val) or math.isinf(val):
                        nan_frames.append(idx)
                        break
                except ValueError:
                    nan_frames.append(idx)
                    break
        if nan_frames:
            sample = nan_frames[:5]
            problems.append(
                f"NaN/Inf/invalid values in {len(nan_frames)} frame(s). "
                f"First occurrences: frames {sample}."
            )

    # ── Report ───────────────────────────────────────────────────────────
    if problems:
        print(f"BVH check FAILED ({len(problems)} issue(s)):")
        for p in problems:
            print(f"  ✗ {p}")
        return False

    print(
        f"BVH check PASSED — "
        f"{declared_frames} frames, "
        f"frame time {1.0/ft:.1f} fps."
    )
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/check_bvh.py <path_to.bvh>")
        sys.exit(1)
    ok = check_bvh(sys.argv[1])
    sys.exit(0 if ok else 1)
