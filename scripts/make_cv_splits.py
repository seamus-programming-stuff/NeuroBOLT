#!/usr/bin/env python3
"""Write a 5-fold, subject-grouped cross-validation workbook (scan_split_cv5.xlsx).

Fold 1 is the authors' split exactly (test: subjects 07, 11, 16, 18, 21; validation: 06, 13, 15, 22).
The authors' 13 training subjects are cut into three more groups, and the folds rotate: fold k
tests group k and validates on group k+1 (wrapping), so every subject is a test subject exactly
once and both scans of a subject always stay in the same set. Same columns as the authors'
workbook, so main.py and the baselines read any fold with --split_fold.

    python scripts/make_cv_splits.py --source scan_split_example.xlsx --out scan_split_cv5.xlsx
"""
import argparse
import re

import pandas as pd

GROUPS = [
    [7, 11, 16, 18, 21],      # the authors' test subjects
    [6, 13, 15, 22],          # the authors' validation subjects
    [1, 2, 3, 4],             # the authors' training subjects, in three groups
    [5, 8, 9, 10],
    [12, 14, 17, 19, 20],
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default="scan_split_example.xlsx")
    parser.add_argument("--out", default="scan_split_cv5.xlsx")
    args = parser.parse_args()

    scans = pd.read_excel(args.source, sheet_name="fold1")["scan_name"].tolist()
    subject = {scan: int(re.match(r"sub(\d+)", scan).group(1)) for scan in scans}
    assert sorted(s for g in GROUPS for s in g) == sorted(set(subject.values())), "groups must cover every subject once"

    with pd.ExcelWriter(args.out) as writer:
        for k in range(len(GROUPS)):
            test, val = set(GROUPS[k]), set(GROUPS[(k + 1) % len(GROUPS)])
            sheet = pd.DataFrame({"scan_name": scans})
            sheet["train"] = [1.0 if subject[s] not in test | val else None for s in scans]
            sheet["val"] = [1.0 if subject[s] in val else None for s in scans]
            sheet["test"] = [1.0 if subject[s] in test else None for s in scans]
            sheet.insert(0, "Unnamed: 0", range(1, len(scans) + 1))
            sheet.to_excel(writer, sheet_name=f"fold{k + 1}", index=False)
            print(f"fold{k + 1}: {int(sheet['train'].sum())} train / {int(sheet['val'].sum())} val / "
                  f"{int(sheet['test'].sum())} test scans; test subjects {sorted(test)}")

    original = pd.read_excel(args.source, sheet_name="fold1")
    ours = pd.read_excel(args.out, sheet_name="fold1")
    for column in ("train", "val", "test"):
        assert original[column].fillna(0).tolist() == ours[column].fillna(0).tolist(), f"fold1 {column} differs"
    print("fold1 matches the authors' split")


if __name__ == "__main__":
    main()
