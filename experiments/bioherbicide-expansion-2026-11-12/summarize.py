"""Verify experimental bundles and build a compact offline results checkpoint."""
import sys,json,csv,statistics
from pathlib import Path
sys.path.insert(0,'analysis')
import altair as alt
from screen import hashes,write_csv
from weekly_report import verify_manifest
root=Path('experiments/bioherbicide-expansion-2026-11-12')
outputs=Path('analysis/outputs')
out=outputs/'experimental-research-checkpoint-2026-11-12'
if out.exists():raise ValueError('Use a fresh checkpoint')
paths=[outputs/p/'manifest.json' for p in [
 'experimental-heterogeneous-activity-2026-11-12','experimental-heterogeneous-diagnostics-2026-11-12',
 'experimental-heterogeneous-controls-2026-11-12','experimental-publication-transfer-2026-11-12-final',
 'experimental-ecotox-decisions-2026-11-12']]
paths += [root/'transcription-v1/manifest.json',root/'transcription-additional-v1/manifest.json',root/'source-policies-v1/manifest.json',root/'pooled-v2-corrected-doi/pooled_preflight/manifest.json']
paths += list((root/'baseline_preflight').glob('*/manifest.json'))
paths += list((root/'source-policies-v1').glob('*_preflight/manifest.json'))
for p in paths:verify_manifest(p)
print('verified bundles',len(paths))
def read(p):return list(csv.DictReader(p.open()))
r=read(outputs/'experimental-heterogeneous-diagnostics-2026-11-12/reports.csv')
t=read(outputs/'experimental-publication-transfer-2026-11-12-final/reports.csv')
c=read(outputs/'experimental-heterogeneous-controls-2026-11-12/stress_models.csv')
coeff=read(outputs/'experimental-heterogeneous-diagnostics-2026-11-12/coefficients.csv')
oob=read(outputs/'experimental-heterogeneous-diagnostics-2026-11-12/oob_importance.csv')
weights={}
for row in coeff:weights.setdefault(row['feature'],[]).append(float(row['coefficient']))
weight_rows=sorted([{'feature':k,'mean_coefficient':statistics.mean(v),'fold_sd':statistics.stdev(v),'positive_folds':sum(x>0 for x in v),'scale':'training-fold standard deviation; positive targets source-specific high response'} for k,v in weights.items()],key=lambda r:-abs(r['mean_coefficient']))
null=[]
for representation in ['formula','descriptors','morgan','combined']:
 actual=next(row for row in c if row['scenario']=='common' and row['representation']==representation)
 vals=[float(row['f1']) for row in c if row['scenario']=='shuffled_labels' and row['representation']==representation and row['f1']]
 null.append({'representation':representation,'actual_f1':float(actual['f1']),'null_mean_f1':statistics.mean(vals),'null_min_f1':min(vals),'null_max_f1':max(vals),'repetitions':len(vals),'null_at_least_actual':sum(v>=float(actual['f1']) for v in vals),'scope':'descriptive fixed 20 shuffles; not model selection or a formal multiplicity-adjusted significance claim'})
out.mkdir(parents=True)
write_csv(out/'scaffold_models.csv',r,list(r[0]));write_csv(out/'publication_transfer.csv',t,list(t[0]))
write_csv(out/'formula_weights.csv',weight_rows,list(weight_rows[0]));write_csv(out/'null_controls.csv',null,list(null[0]))
plot=[]
for row in t:
 if row['scenario']!='publication_only':continue
 plot.append({'publication':row['publication'],'model':row['profile'],'f1':float(row['f1']),'balanced_accuracy':float(row['balanced_accuracy']),'baseline_f1':float(row['baseline_f1'])})
fig=alt.Chart(alt.Data(values=plot)).mark_bar().encode(x=alt.X('f1:Q',scale=alt.Scale(domain=[0,1]),title='Publication-held-out F1'),y=alt.Y('model:N',title=None),color=alt.Color('model:N',legend=None),row=alt.Row('publication:N',title=None),tooltip=['publication:N','model:N','f1:Q','baseline_f1:Q','balanced_accuracy:Q']).properties(width=500,height=100,title='Permissive heterogeneous assay pool; source-specific labels')
fig.save(out/'publication_transfer.svg')
scaffold=alt.Chart(alt.Data(values=[{**x,'f1':float(x['f1'])} for x in r])).mark_bar().encode(x=alt.X('f1:Q',scale=alt.Scale(domain=[0,1]),title='Scaffold-held-out F1'),y=alt.Y('profile:N',title=None),tooltip=['profile:N','f1:Q']).properties(width=500,height=250,title='Exploratory heterogeneous pool; n=73; no common efficacy estimand')
scaffold.save(out/'scaffold_models.svg')
summary={'date':'2026-11-12','n':73,'high_response':41,'low_response':32,'class_bearing_scaffolds':{'high_response':6,'low_response':5},'screened_primary_studies':16,'cached_primary_fulltexts':8,'transcribed_plant_observations':304,'transcribed_other_endpoint_observations':59,'new_human_approved_labels':0,'forest_oob_f1':float(oob[0]['baseline_oob_f1']),'verified_bundles':len(paths),'interpretation':'Pooling made five-fold fitting possible but failed publication transfer; no accepted activity model or safer candidate. All original human datasets and source exports unchanged.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'walkthrough.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><title>Experimental research checkpoint</title><style>body{font:17px/1.5 system-ui;max-width:1000px;margin:40px auto;padding:0 20px}img{max-width:100%}</style><h1>Experimental research checkpoint — 12 November 2026</h1><p>Local-only experiment. 73 structures with intentionally heterogeneous source-specific response labels. Passing the scaffold gate did not establish transferable herbicidal activity. No safer candidate is established.</p><img src="scaffold_models.svg" alt="Scaffold-held-out F1 for eight fixed profiles"><img src="publication_transfer.svg" alt="Publication-held-out F1; large performance losses on Li and He sources"><p>See publication_transfer.csv for precision, recall, balanced accuracy, AUROC, confusion counts and majority baselines. Source-only and scaffold-purged splits coincide here because publications have no shared scaffold groups. Ambrosia has only two test compounds.</p><p>304 provisional plant observations and59 other endpoint observations were transcribed from seven primary papers; one additional fulltext is cached with unresolved supplement access. Controls, extracts, repeated doses and species are observations rather than independent training structures. All new decisions are AI experimental proposals.</p><p>Forest OOB F1 is0.7436. OOB does not hold out scaffold families; importance repeat SD is not a p-value. Formula coefficients describe standardized associations with the experimental target, not causal activity or safety effects.</p><ul><li><a href="summary.json">Summary</a></li><li><a href="scaffold_models.csv">Scaffold models</a></li><li><a href="publication_transfer.csv">Publication transfer and baselines</a></li><li><a href="formula_weights.csv">Formula coefficients</a></li><li><a href="null_controls.csv">Shuffled-label controls</a></li></ul></html>''')
inputs=paths+[root/'literature_screen.csv',root/'EXPERIMENT_PROTOCOL.json',root/'pooled-v2-corrected-doi/pooled_lineage.csv',Path(__file__)]
manifest={'input_hashes':hashes(inputs),'output_hashes':hashes(list(out.iterdir())),'scope':'Local experimental checkpoint; not approved biological activity or safety model','summary':summary}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
verify_manifest(out/'manifest.json')
print(json.dumps(summary,indent=2))
