"""
Residue-Wise Non-Covalent Interaction Analysis
===============================================
Parses interaction data exported from Biovia Discovery Studio
(after MD trajectory â†’ PDB â†’ interaction analysis) and produces
a per-residue interaction summary with an Excel heatmap output.

Authors : Md Jaish Uddin, Sk. Mainuddin
Contact : [available upon request]
License : All rights reserved  -  Authors

Workflow
--------
1. Run MD simulation in GROMACS â†’ export trajectory frames as PDB
2. Open each PDB frame in Biovia Discovery Studio
3. Run: Analyze â†’ Calculate Interactions
4. Copy the interaction table into ``int.xlsx`` (see README for format)
5. Execute:

   .. code-block:: bash

       pip install openpyxl pandas matplotlib seaborn
       python resinteractionanalysis.py -i int.xlsx [-o output.xlsx]

Output
------
``output.xlsx``  â€” per-residue interaction frequency table + colour heatmap

Interaction types detected (from Biovia DS output columns)
----------------------------------------------------------
- Conventional Hydrogen Bonds
- Carbon Hydrogen Bonds
- Pi-Pi Stacking
- Pi-Cation
- Halogen Bonds
- Hydrophobic Contacts
- Salt Bridges
- van der Waals contacts
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Residue-wise non-covalent interaction analysis from Biovia DS export.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "-i", "--input", required=True,
        help="Input Excel file (.xlsx) exported from Biovia Discovery Studio."
    )
    p.add_argument(
        "-o", "--output", default="output.xlsx",
        help="Output Excel file (default: output.xlsx)."
    )
    p.add_argument(
        "--sheet", default=0,
        help="Sheet name or 0-based index to read from input (default: 0)."
    )
    p.add_argument(
        "--top", type=int, default=20,
        help="Number of top interacting residues to include in heatmap (default: 20)."
    )
    return p


# ---------------------------------------------------------------------------
# Interaction type normalisation
# ---------------------------------------------------------------------------

#: Map raw Biovia DS column names â†’ short display labels
INTERACTION_LABELS: Dict[str, str] = {
    "conventional hydrogen bond": "H-Bond",
    "carbon hydrogen bond":       "Câ€“H Bond",
    "pi-pi stacking":             "Ï€â€“Ï€ Stack",
    "pi-cation":                  "Ï€â€“Cation",
    "pi-sigma":                   "Ï€â€“Sigma",
    "halogen":                    "Halogen",
    "hydrophobic":                "Hydrophobic",
    "salt bridge":                "Salt Bridge",
    "van der waals":              "vdW",
    "unfavourable bump":          "Clash",
}

INTERACTION_COLOURS: Dict[str, str] = {
    "H-Bond":      "#2563EB",
    "Câ€“H Bond":    "#7C3AED",
    "Ï€â€“Ï€ Stack":   "#059669",
    "Ï€â€“Cation":    "#D97706",
    "Ï€â€“Sigma":     "#0891B2",
    "Halogen":     "#DC2626",
    "Hydrophobic": "#F59E0B",
    "Salt Bridge": "#9333EA",
    "vdW":         "#6B7280",
    "Clash":       "#EF4444",
}


def normalise_interaction_type(raw: str) -> str:
    """Return a short display label for a raw Biovia DS interaction type string."""
    key = str(raw).strip().lower()
    for pattern, label in INTERACTION_LABELS.items():
        if pattern in key:
            return label
    return str(raw).strip()


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def load_interactions(path: Path, sheet) -> pd.DataFrame:
    """
    Load the Biovia DS interaction table from Excel.

    Expected columns (case-insensitive):
        RESNM | RESID | CHAIN | INTERACTION | FRAME (optional)

    Returns a cleaned DataFrame with standardised column names.
    """
    try:
        df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    except FileNotFoundError:
        sys.exit(f"[ERROR] Input file not found: {path}")
    except Exception as exc:
        sys.exit(f"[ERROR] Cannot read {path}: {exc}")

    # Normalise column names
    df.columns = [c.strip().upper() for c in df.columns]
    required = {"RESNM", "RESID", "INTERACTION"}
    missing = required - set(df.columns)
    if missing:
        # Try common alternative column names
        alt_map = {
            "RESIDUE NAME": "RESNM",
            "RESIDUE NUMBER": "RESID",
            "RESIDUE": "RESNM",
            "INTERACTION TYPE": "INTERACTION",
            "TYPE": "INTERACTION",
        }
        df.rename(columns=alt_map, inplace=True)
        missing = required - set(df.columns)
        if missing:
            sys.exit(
                f"[ERROR] Cannot find required columns {missing}.\n"
                f"Found: {list(df.columns)}\n"
                "See README for the expected input format."
            )

    # Build a unified residue label: e.g.  "LYS_23"
    df["RESIDUE_LABEL"] = (
        df["RESNM"].astype(str).str.strip().str.upper()
        + "_"
        + df["RESID"].astype(str).str.strip()
    )

    # Normalise interaction type
    df["INT_TYPE"] = df["INTERACTION"].apply(normalise_interaction_type)

    return df[["RESIDUE_LABEL", "INT_TYPE"] + (["FRAME"] if "FRAME" in df.columns else [])]


def build_frequency_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a residue Ã -  interaction_type frequency table.

    Each cell = number of frames (or occurrences) in which that
    residue forms that interaction type with the ligand.
    """
    pivot = (
        df.groupby(["RESIDUE_LABEL", "INT_TYPE"])
        .size()
        .unstack(fill_value=0)
        .astype(int)
    )
    pivot["TOTAL"] = pivot.sum(axis=1)
    pivot.sort_values("TOTAL", ascending=False, inplace=True)
    return pivot


def write_output(freq_table: pd.DataFrame, out_path: Path, top_n: int) -> None:
    """
    Write the frequency table and a colour-coded heatmap to Excel.

    Sheet 1 â€” Full interaction frequency table
    Sheet 2 â€” Heatmap (top N residues, conditional formatting)
    """
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()

    # â”€â”€ Sheet 1: Full frequency table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ws_full = wb.active
    ws_full.title = "Interaction Frequencies"

    header_font   = Font(bold=True, color="FFFFFF")
    header_fill   = PatternFill("solid", fgColor="1E3A5F")
    center_align  = Alignment(horizontal="center", vertical="center")
    thin_border   = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    cols = ["Residue"] + list(freq_table.columns)
    for col_idx, col_name in enumerate(cols, start=1):
        cell = ws_full.cell(row=1, column=col_idx, value=col_name)
        cell.font      = header_font
        cell.fill      = header_fill
        cell.alignment = center_align
        cell.border    = thin_border

    for row_idx, (residue, row) in enumerate(freq_table.iterrows(), start=2):
        ws_full.cell(row=row_idx, column=1, value=residue).border = thin_border
        for col_idx, val in enumerate(row, start=2):
            c = ws_full.cell(row=row_idx, column=col_idx, value=int(val))
            c.alignment = center_align
            c.border    = thin_border
            # Colour scale: white â†’ blue based on value
            if isinstance(val, (int, float)) and val > 0:
                intensity = min(int(val / max(freq_table.values.max(), 1) * 200), 200)
                hex_val   = f"{255 - intensity:02X}{255 - intensity:02X}FF"
                c.fill    = PatternFill("solid", fgColor=hex_val)

    # Auto-width
    for col in ws_full.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=8)
        ws_full.column_dimensions[get_column_letter(col[0].column)].width = max_len + 2

    # â”€â”€ Sheet 2: Top-N heatmap â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ws_heat = wb.create_sheet("Top Residues Heatmap")
    top_df  = freq_table.head(top_n)

    ws_heat.cell(row=1, column=1, value=f"Top {top_n} Interacting Residues â€” Interaction Heatmap")
    ws_heat.cell(row=1, column=1).font = Font(bold=True, size=12)
    ws_heat.merge_cells(start_row=1, start_column=1,
                         end_row=1, end_column=len(top_df.columns) + 1)

    # Header row
    ws_heat.cell(row=2, column=1, value="Residue").font = header_font
    ws_heat.cell(row=2, column=1).fill = header_fill
    for col_idx, col_name in enumerate(top_df.columns, start=2):
        c = ws_heat.cell(row=2, column=col_idx, value=col_name)
        c.font = header_font
        c.fill = header_fill
        c.alignment = center_align

    # Data rows
    for row_idx, (residue, row) in enumerate(top_df.iterrows(), start=3):
        ws_heat.cell(row=row_idx, column=1, value=residue)
        for col_idx, (col_name, val) in enumerate(row.items(), start=2):
            c = ws_heat.cell(row=row_idx, column=col_idx, value=int(val))
            c.alignment = center_align
            if val > 0:
                # Per-interaction-type colour
                colour = INTERACTION_COLOURS.get(col_name, "AAAAAA")
                hex_colour = colour.lstrip("#")
                intensity  = min(int(val / max(top_df.max().max(), 1) * 180), 180)
                r = max(0, int(hex_colour[0:2], 16) - intensity // 3)
                g = max(0, int(hex_colour[2:4], 16) - intensity // 3)
                b = max(0, int(hex_colour[4:6], 16) - intensity // 3)
                c.fill = PatternFill("solid", fgColor=f"{r:02X}{g:02X}{b:02X}")
                c.font = Font(color="FFFFFF", bold=True)

    for col in ws_heat.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=8)
        ws_heat.column_dimensions[get_column_letter(col[0].column)].width = max_len + 2

    wb.save(out_path)
    print(f"[OK] Output written to: {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args   = _build_parser().parse_args()
    in_path  = Path(args.input)
    out_path = Path(args.output)

    print(f"[INFO] Reading interactions from: {in_path}")
    df = load_interactions(in_path, args.sheet)
    print(f"[INFO] Loaded {len(df):,} interaction records")

    freq_table = build_frequency_table(df)
    print(f"[INFO] Found {len(freq_table)} unique residues interacting with the ligand")

    # Print top 10 to console
    print(f"\n{'Residue':<20} {'Total Interactions':>18}")
    print("-" * 40)
    for res, row in freq_table.head(10).iterrows():
        print(f"{res:<20} {row['TOTAL']:>18}")

    write_output(freq_table, out_path, top_n=args.top)
    print(f"\n[DONE] Analysis complete. Open {out_path} to view the heatmap.")


if __name__ == "__main__":
    main()

