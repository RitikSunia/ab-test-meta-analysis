"""
Run all 5 analysis stages in sequence and regenerate export files.
"""

import subprocess
import sys
import os

SCRIPTS = [
    '01_false_discovery.py',
    '02_power_audit.py',
    '03_peeking_detection.py',
    '04_revenue_impact.py',
    '05_category_analysis.py',
]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("Running all analysis stages...\n")

    for script in SCRIPTS:
        path = os.path.join(script_dir, script)
        print(f"{'=' * 60}")
        print(f"Running {script}")
        print(f"{'=' * 60}")
        result = subprocess.run([sys.executable, path], cwd=script_dir)
        if result.returncode != 0:
            print(f"\nFailed: {script}")
            sys.exit(result.returncode)
        print()

    print("All stages complete. Export files are in ../exports/")


if __name__ == '__main__':
    main()
