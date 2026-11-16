"""Offline exploratory summaries and two source-specific preflights; no fitting."""
import csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'analysis')
import altair as alt
import vl_convert as vlc
from activity_preflight import run
from labels import LABEL_FIELDS
from screen import write_csv
from structure import structure_features
root=Path(__file__).parent
out=root/'analysis-v2'
if out.exists():raise ValueError('Use fresh output')
out.mkdir()
obs=list(csv.DictReader((root/'transcription-v1/observations.csv').open()))
log=json.loads((root/'sources/identity_retrieval.json').read_text())
compounds=[];identities=[];features=[]
for item in log:
 assert item['status']==200 and item['hits']==1
 p=root/'sources'/item['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 prop=json.loads(p.read_text())['PropertyTable']['Properties'][0]
 feat=structure_features(prop['SMILES']);assert feat['structure_status']=='valid' and feat['structure_inchikey']==prop['InChIKey']
 cid=f"FLAV2012:{item['row']:02}"
 compounds.append(dict(compound_id=cid,smiles=prop['SMILES']))
 identities.append(dict(compound_id=cid,source_name=next(r['source_name'] for r in obs if r['compound_id']==cid),query=item['name'],pubchem_cid=prop['CID'],inchikey=prop['InChIKey'],mapping='AI experimental name mapping; source stereochemistry and sample identity not independently verified',natural_origin='unknown'))
 features.append(dict(compound_id=cid,**{k:feat[k] for k in ['logp','tpsa','hbd','hba','mw','scaffold']}))
assert len({r['smiles'] for r in compounds})==27
write_csv(out/'compounds.csv',compounds,list(compounds[0]));write_csv(out/'identities.csv',identities,list(identities[0]));write_csv(out/'descriptors.csv',features,list(features[0]))
policies=json.loads((root/'transcription-v1/policies.json').read_text())
labelrows=list(csv.DictReader((root/'transcription-v1/labels_by_assay.csv').open()))
reports=[]
for policy in policies:
 if policy['endpoint']!='radicle_length' or policy['dose_uM']!=100:continue
 selected=[r for r in labelrows if r['policy']==policy['policy']]
 labels=[dict(compound_id=r['compound_id'],natural_origin='unknown',origin_reference='',herbicidal_activity=r['activity'],activity_reference='10.3390/ijms13055406 Table2; '+r['observation_id'],activity_context=f"AI experimental; {policy['species']};radicle length;100uM;120h;ratio of means inhibition={float(r['inhibition_percent']):.8g}%;active>=50%;low inhibition<=20% (includes stimulation);stereochemistry provisional;sample vehicle unspecified",activity_policy=policy['policy']) for r in selected]
 path=out/(policy['species'].split()[0].lower()+'_labels.csv');write_csv(path,labels,['compound_id']+sorted(LABEL_FIELDS-{'compound_id'}))
 report=run(out/'compounds.csv',path,[Path('experiments/bioherbicide-expansion-2026-11-12/identity_holds.csv')],out/(policy['species'].split()[0].lower()+'_preflight'))
 reports.append(dict(policy=policy['policy'],**report['reports'][0]))
(out/'support.json').write_text(json.dumps(reports,indent=2)+'\n')
# Six retrospectively selected O-methylation pairs from named compounds in this source.
# Descriptive differences of group means, never new experimental replicates.
pairs=[(2,3,'7-hydroxyflavone'),(4,5,'chrysin'),(7,8,'luteolin'),(9,10,'3-hydroxyflavone'),(17,18,'7-hydroxyflavanone'),(19,20,'pinocembrin')]
paired=[]
for parent,methyl,name in pairs:
 for species in ['Raphanus sativus','Lepidium sativum']:
  for dose in [1,10,100]:
   def pick(i):return next(r for r in obs if r['compound_id']==f'FLAV2012:{i:02}' and r['species']==species and float(r['concentration_uM'])==dose and r['endpoint']=='radicle_length')
   a,b=pick(parent),pick(methyl)
   paired.append(dict(parent=name,parent_id=a['compound_id'],methylated_id=b['compound_id'],species=species,dose_uM=dose,parent_inhibition_percent=float(a['derived_inhibition_percent']),methylated_inhibition_percent=float(b['derived_inhibition_percent']),difference_percentage_points=float(b['derived_inhibition_percent'])-float(a['derived_inhibition_percent']),parent_observation_id=a['observation_id'],methylated_observation_id=b['observation_id'],interpretation='Descriptive difference of rounded group means; no causal attribution or derived uncertainty'))
write_csv(out/'methylation_pairs.csv',paired,list(paired[0]))
chartdata=[]
for r in paired:
 if r['dose_uM']==100:
  for form,key in [('Parent','parent_inhibition_percent'),('O-methylated','methylated_inhibition_percent')]:chartdata.append(dict(parent=r['parent'],species=r['species'].split()[0],form=form,inhibition=r[key]))
chart=alt.Chart(alt.Data(values=chartdata)).mark_point(filled=True,size=70).encode(x=alt.X('inhibition:Q',title='Mean radicle inhibition relative to control (%)',scale=alt.Scale(domain=[-40,100])),y=alt.Y('parent:N',title=None,sort=[p[2] for p in pairs]),color=alt.Color('form:N',title='Form',scale=alt.Scale(domain=['Parent','O-methylated'],range=['#176b87','#c75b12'])),tooltip=['parent:N','species:N','form:N',alt.Tooltip('inhibition:Q',format='.1f')]).properties(width=330,height=220).facet(column=alt.Column('species:N',title=None)).properties(title=alt.TitleParams(text='O-methylation pairs at 100 µM, 120 h',subtitle=['Same-paper means; 3 dishes × 10 seeds per condition; no derived uncertainty.', 'Negative inhibition denotes stimulation. Provisional identities; no efficacy or safety prediction.']))
spec=chart.to_dict();(out/'methylation_pairs.vl.json').write_text(json.dumps(spec,indent=2)+'\n');(out/'methylation_pairs.svg').write_text(vlc.vegalite_to_svg(spec));(out/'methylation_pairs.png').write_bytes(vlc.vegalite_to_png(spec,scale=1.5))
inputs=[Path(__file__),root/'transcription-v1/observations.csv',root/'transcription-v1/policies.json',root/'transcription-v1/labels_by_assay.csv',root/'sources/identity_retrieval.json',*list((root/'sources').glob('*.pubchem.json'))]
(out/'manifest.json').write_text(json.dumps(dict(input_hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},output_hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()},models_fitted=0,natural_origin_labels_added=0,assumptions='Single-hit name mappings provisional; frozen sources/labels unmodified; graph/assay support is not scientific review'),indent=2)+'\n')
print(json.dumps(reports,indent=2))
