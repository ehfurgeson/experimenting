"""Audit displayed footnote-c arithmetic without correcting primary values."""
import csv,json
from pathlib import Path
root=Path(__file__).parent
out=root/'conversion-audit-v1'
if out.exists():raise ValueError('Use fresh output')
rows=[]
for r in csv.DictReader((root/'curation-v1/table1.csv').open()):
 if not r['material_ld50_mg_kg']:
  rows.append(dict(paper_record_id=r['paper_record_id'],reported_acid_equivalent_mg_kg=None,computed_from_displayed_inputs_mg_kg=None,reported_minus_computed_mg_kg=None,status='not_calculable_source_cell',limits='No scalar or conversion fabricated'))
  continue
 ratio=float(r['molecular_weight_ratio_percent'] or 100)
 expected=ratio*float(r['active_ingredient_percent'])*float(r['material_ld50_mg_kg'])/10000
 reported=float(r['reported_acid_equivalent_mg_kg']);delta=reported-expected
 rows.append(dict(paper_record_id=r['paper_record_id'],reported_acid_equivalent_mg_kg=reported,computed_from_displayed_inputs_mg_kg=expected,reported_minus_computed_mg_kg=delta,status='agrees_within_1mg_rounding' if abs(delta)<=1 else 'does_not_reproduce_displayed_formula',limits='Arithmetic check of rounded printed inputs, not a correction or uncertainty estimate; acid MWratio blank interpreted as100% for acid only; primary values unchanged'))
flags=[r for r in rows if r['status']=='does_not_reproduce_displayed_formula']
assert {r['paper_record_id'] for r in flags}=={'GORZ1987:T1:Butoxyethanol ester:female','GORZ1987:T1:Butyl ester:female'}
out.mkdir()
with (out/'conversion_audit.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
import sys
sys.path.insert(0,'analysis')
from screen import hashes
(out/'manifest.json').write_text(json.dumps(dict(input_hashes=hashes([Path(__file__),root/'curation-v1/table1.csv',root/'sources/gorzinski1987.pdf']),output_hashes=hashes(list(out.iterdir())),flagged_cells=2,reported_values_changed=0,source_locator='printedp426 Table1/footnotec;visually rechecked enlarged source table;no asserted cause of discrepancy'),indent=2)+'\n')
print(json.dumps(flags,indent=2))
