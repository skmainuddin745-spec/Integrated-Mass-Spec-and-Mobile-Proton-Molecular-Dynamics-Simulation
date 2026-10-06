# Cytochrome c & Myoglobin  -  Mobile Proton Molecular Dynamics Simulation Study
### *An Integrated Mass Spectrometry and MD Simulation Approach to Elucidate Protein-Herbicide Interactions*

> **GROMACS input files, selected outputs and analysis scripts from gas-phase mobile-proton MD of Cytochrome c (cyt9+, cyt10+) and Myoglobin (myo9+), alone and with the herbicide glyphosate, supporting a combined mass-spectrometry and simulation study of protein-herbicide binding.**

---

## Scientific Background

### Mobile Proton Model in Mass Spectrometry

Native electrospray ionisation mass spectrometry (ESI-MS) can eject intact protein ions into the gas phase with specific charge states. The **mobile proton model** explains how protons migrate along the protein backbone during collision-induced dissociation (CID). Critically, the charge state controls:

- **Gas-phase protein structure**  -  higher charge states (more protons) lead to Coulomb-driven unfolding
- **Herbicide binding affinity**  -  the protein-ligand interaction energy changes with protonation state
- **Fragmentation pathways**  -  mobile protons determine which backbone bonds cleave first

This study uses **GROMACS MD in vacuo, heated from 298 K to 623 K over 100 ns**, to sample gas-phase conformations of the three charge-state/protein combinations with and without the herbicide.

---

## Systems Studied

| System ID | Protein | Charge State | Herbicide | Simulation Type |
|-----------|---------|-------------|-----------|----------------|
| `cyt9+` | Cytochrome c | 9+ | None | Protein only  -  gas phase |
| `cyt10+` | Cytochrome c | 10+ | None | Protein only  -  gas phase |
| `myo9+` | Myoglobin | 9+ | None | Protein only  -  gas phase |
| `lig-cyt9+` | Cytochrome c | 9+ | Glyphosate | Protein + ligand  -  gas phase |
| `lig-cyt10+` | Cytochrome c | 10+ | Glyphosate | Protein + ligand  -  gas phase |
| `lig-myo9+` | Myoglobin | 9+ | Glyphosate | Protein + ligand  -  gas phase |

---

## Repository Structure

```
08_CytMyo-Mobile-Proton-MD-Pesticides/
│
├── 01_protein_only/
│   ├── cyt9plus/       ← Cyt c 9+ gas-phase MD (topology + MDP files)
│   ├── cyt10plus/      ← Cyt c 10+ gas-phase MD
│   └── myo9plus/       ← Myoglobin 9+ gas-phase MD (full production run)
│       ├── md.mdp           ← 10-ns run, 590.5→623 K annealing, 0.5 fs step, pull code (see Protocol note)
│       ├── nvt.mdp          ← NVT equilibration at 590.5 K
│       ├── em.mdp           ← Energy minimisation (conjugate gradient)
│       ├── topol.top        ← Master topology
│       ├── topol_Protein.itp    ← Protein bonded parameters
│       ├── topol_Other2.itp     ← Heme group / cofactor ITP
│       ├── posre_Protein.itp    ← Position restraints (equilibration)
│       ├── glp.itp / glp.prm   ← Glyphosate (molecule type `glp`), CGenFF-typed parameters
│       ├── pos.itp / pos.prm   ← Phosphate ion (molecule type `pos`, PO₄, net charge −3)
│       ├── index.ndx            ← GROMACS index (pull groups)
│       ├── protein.pdb          ← Cleaned input structure
│       └── energy_terms_myo9+.xvg ← Production energy output
│
├── 02_with_herbicide_ligand/
│   ├── cyt9plus_lig/   ← Cyt c 9+ + herbicide complex
│   │   └── initial.pdb  ← Starting structure (9+ charge state)
│   ├── cyt10plus_lig/  ← Cyt c 10+ + herbicide complex
│   └── myo9plus_lig/   ← Myo 9+ + herbicide complex
│
├── 03_analysis_scripts/
│   ├── resinteractionanalysis.py   ← Residue-wise non-covalent interaction analysis
│   ├── README_interaction_analysis.md
│   ├── int_example.xlsx            ← Example Biovia Discovery Studio input
│   ├── sasa.tcl                    ← VMD: Solvent Accessible Surface Area
│   ├── gyr_radius.tcl              ← VMD: Radius of gyration
│   ├── rog_loop_dcd.tcl            ← VMD: Rg for loop regions
│   └── RMSF.txt                    ← RMSF output data
│
└── 04_pca_ms_analysis/
    ├── cyt-9/          ← PCA+MS data for cyt 9+ protein only
    ├── cyt-10/         ← PCA+MS data for cyt 10+ protein only
    ├── myo/            ← PCA+MS data for myo 9+ protein only
    ├── lig-cyt-9/      ← PCA+MS data for cyt 9+ + herbicide
    ├── lig-cyt-10/     ← PCA+MS data for cyt 10+ + herbicide
    └── lig-myo/        ← PCA+MS data for myo 9+ + herbicide
```

---

## Simulation Protocol  -  Mobile Proton Gas-Phase MD

### Key Design Choices (critically different from standard aqueous MD)

| Parameter | Standard Aqueous MD | Mobile Proton Gas-Phase MD |
|-----------|--------------------|-----------------------------|
| Solvent | Explicit water (SPC/E, TIP3P) | **None (vacuum)** |
| PBC | Yes (periodic box) | Yes (large box, effectively non-PBC) |
| Temperature | 300 K | **298 K → 623 K over 100 ns (manuscript protocol)** |
| Electrostatics | PME (long-range) | **Cut-off only** (ε_r = 1, gas phase) |
| Barostat | Parrinello-Rahman | **None (NVT)** |
| Charge handling | Neutralised with counterions | **Explicit protonation (+9 or +10)** |
| Duration | 100-1000 ns | **100 ns per run, two replicates (manuscript); each `md.mdp` here is a 10-ns run** |

### MDP  -  Production Run Parameters (`md.mdp`, myo9+)

```ini
; Gas-phase mobile proton simulation
integrator      = md
nsteps          = 20000000   ; 10 ns total
dt              = 0.0005     ; 0.5 fs timestep (tighter for gas phase)

; Non-bonded: simple cut-off, NO PME (gas phase has no periodic charge distribution)
coulombtype     = cut-off
rcoulomb        = 300        ; Effectively infinite  -  all pairs seen
rvdw            = 300
epsilon_r       = 1          ; Vacuum permittivity
vdwtype         = cut-off
periodic-molecules = no

; Temperature: Nose-Hoover thermostat
tcoupl          = Nose-Hoover
ref_t           = 590.5
annealing       = single
annealing-time  = 0 10000    ; 0 → 10000 ps
annealing-temp  = 590.5 623  ; Linear ramp: 590.5 K → 623 K

; No pressure coupling (gas phase  -  NVT only)
pcoupl          = no

; Pull code: distance restraint between specific atoms
; (mimics mass-spectrometer ejection geometry)
pull            = yes
pull-coord1-type     = umbrella
pull-coord1-geometry = distance
pull-coord1-k        = 5000    ; kJ mol⁻¹ nm⁻²
pull-coord1-init     = 0.180   ; 1.8 Å reference distance
```

### Charge State Preparation

The 9+ and 10+ charge states follow the mass-spectrometry data. In the production simulations reported in the manuscript, protons were redistributed among titratable residues at regular intervals by the **Charge Placer** algorithm and an in-house bash script, which chooses the protonation pattern that minimises the total energy, balancing Coulomb repulsion against proton affinity.

### Protocol note

The manuscript describes heating from 298 K to 623 K over 100 ns with a Nose-Hoover thermostat (coupling constant 0.1 ps), a 1 fs time step with LINCS constraints, two replicate runs per system, CHARMM36, and snapshots every 100 ps. The `md.mdp` files in this repository are 10-ns runs that anneal from 590.5 K to 623 K with a 0.5 fs step and write coordinates every 100 ps (200,000 steps). 590.5 K is the temperature reached after 90 ns of a linear 298 → 623 K ramp over 100 ns, so these files appear to correspond to the final 10-ns segment of that ramp. The time-step difference (0.5 fs here, 1 fs in the manuscript) has not been reconciled. Some inline comments in the `.mdp` files predate the final protocol; the parameter values, not the comments, are what GROMACS reads.

---

## Analysis Pipeline

### 1. Structural Analysis (GROMACS)

```bash
# RMSD  -  backbone structural deviation
gmx rms -f md.xtc -s md.tpr -n index.ndx -o rmsd.xvg

# RMSF  -  per-residue flexibility
gmx rmsf -f md.xtc -s md.tpr -n index.ndx -res -o rmsf.xvg

# Radius of gyration  -  compactness
gmx gyrate -f md.xtc -s md.tpr -n index.ndx -o gyrate.xvg

# Energy terms
gmx energy -f md.edr -o energy_terms.xvg
```

### 2. Solvent Accessible Surface Area (VMD Tcl)

```tcl
# sasa.tcl  -  frame-wise SASA calculation
set sel [atomselect top "protein"]
set nframes [molinfo top get numframes]
for {set i 0} {$i < $nframes} {incr i} {
    $sel frame $i
    set sasa [measure sasa 1.4 $sel]
    puts "$i $sasa"
}
```

### 3. Residue-wise Non-Covalent Interaction Analysis

`resinteractionanalysis.py` reads Biovia Discovery Studio interaction tables (exported from GROMACS trajectory frames → PDB → Discovery Studio) and generates per-residue interaction heatmaps:

```bash
# Workflow:
# 1. Convert MD trajectory to PDB snapshots
gmx trjconv -f md.xtc -s md.tpr -o snapshot.pdb -sep

# 2. Open in Biovia Discovery Studio → Analyse → Calculate Interactions
# 3. Copy interaction table to int.xlsx

# 4. Run analysis
python resinteractionanalysis.py -i int.xlsx
# Output: output.xlsx with per-residue interaction summary + heatmap
```

**Interactions captured:**
- Hydrogen bonds (backbone and side-chain)
- Hydrophobic contacts
- π-π stacking
- Charge-charge (salt bridges)
- van der Waals contacts

### 4. PCA and MS Integration (`04_pca_ms_analysis/`)

Principal Component Analysis (PCA) of the MD trajectory, combined with mass spectrometry fragmentation data to identify herbicide-binding residues:

```python
# PCA of MD trajectory
import MDAnalysis as mda
from MDAnalysis.analysis import pca as PCA

u = mda.Universe("md.tpr", "md.xtc")
pc = PCA.PCA(u, select="backbone").run()
transformed = pc.transform(u.select_atoms("backbone"))
```

---

## Results

The results (structural changes with charge state, glyphosate binding sites and stoichiometry, and agreement with collision cross-sections and mass spectra) are reported in the manuscript, which is under review. They are not restated here.

---

## Manuscript and authorship

Sazmi M. M.⊥, Uddin M. J.⊥, Mainuddin S.⊥, Halim M. A., *An Integrated Mass Spectrometry and Mobile Proton Molecular Dynamics Simulation Approach to Elucidate Protein-Herbicide Interactions* (⊥ equal contribution; under review). In this work S. Mainuddin assisted with the simulations, analysed the computational data and drafted the manuscript.

---

## Technology Stack

| Tool | Version | Role |
|------|---------|------|
| GROMACS | 2022 | Gas-phase MD engine |
| CHARMM36 |  -  | Protein force field (as stated in the manuscript) |
| CGenFF |  -  | Herbicide ligand parametrisation |
| VMD | 1.9.4 | Trajectory analysis (Tcl scripts) |
| Biovia Discovery Studio | 2021 | Interaction analysis |
| Python | 3.9 | `resinteractionanalysis.py`  -  interaction heatmaps |
| MDAnalysis | 2.x | PCA of MD trajectory |
| GROMACS gmx tools |  -  | RMSD, RMSF, Rg, SASA, energy |

---

## References

1. Dongré et al., *J. Am. Chem. Soc.* **1996**  -  Mobile proton model (original)
2. Zubarev et al., *Anal. Chem.* **2003**  -  Mobile proton and charge-directed fragmentation
3. Harvey et al., *J. Am. Soc. Mass Spectrom.* **2012**  -  Gas-phase protein MD validation
4. Huang & MacKerell, *J. Comput. Chem.* **2013**  -  CHARMM36 protein force field
5. GROMACS 2022 reference manual

---

*Molecular Dynamics · Mass Spectrometry · Herbicide Interactions · Mobile Proton · GROMACS · Protein Biophysics*
