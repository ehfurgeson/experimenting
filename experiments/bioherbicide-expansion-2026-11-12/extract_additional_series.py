"""Offline second transcription batch: intact/punctured ophiobolins and marine fungi."""
import csv, hashlib, json, re
from pathlib import Path

root=Path('experiments/bioherbicide-expansion-2026-11-12')
sources=root/'sources';out=root/'transcription-additional-v1'
if out.exists():raise ValueError('Use a fresh output version')
rows=[]
def add(study,compound,species,endpoint,hours,dose,unit,raw,response_unit,application,sample_type='isolated_compound',gaps=''):
    filename={'OPHIOBOLINS2021':'ophiobolins2021.html','MARINEFUNGI2018':'marinefungi2018.html'}[study]
    doi={'OPHIOBOLINS2021':'10.47371/mycosci.2020.11.002','MARINEFUNGI2018':'10.1039/c8ra08047j'}[study]
    key='|'.join(map(str,[study,compound,species,endpoint,hours,dose,application]))
    values={'value':None,'qualifier':'','lower':None,'upper':None,'dispersion':None,'parse_status':'qualitative'}
    match=re.fullmatch(r'([<>]=?)?(\d+(?:\.\d+)?)(?:[–-](\d+(?:\.\d+)?))?(?:\s*±\s*(\d+(?:\.\d+)?))?',raw)
    if match:
        if match[3]:values.update(qualifier='range',lower=float(match[2]),upper=float(match[3]),parse_status='interval')
        else:values.update(value=float(match[2]),qualifier=match[1] or '=',dispersion=float(match[4]) if match[4] else None,parse_status='numeric')
    rows.append({'observation_id':study+':'+hashlib.sha256(key.encode()).hexdigest()[:20],
        'study_id':study,'compound_id':study+':'+compound,'source_compound':compound,
        'species':species,'endpoint':endpoint,'assessment_hours':hours,'dose':dose,'dose_unit':unit,
        'raw_response':raw,'response_unit':response_unit,**values,'application':application,'sample_type':sample_type,
        'source_doi':doi,'source_file':str(sources/filename),'source_sha256':hashlib.sha256((sources/filename).read_bytes()).hexdigest(),
        'source_locator':'Table 1; section 2.6' if study=='OPHIOBOLINS2021' else 'Tables 3/4 and section 2.3; sections 3.2.1/3.4',
        'quality_gaps':gaps,'extractor':'Codex AI','checker':'not_independently_checked','date':'2026-11-12',
        'status':'AI_experimental_provisional_transcription'})

tables=json.loads((sources/'ophiobolins2021.tables.json').read_text())
names=['3-anhydro-ophiobolin A','6-epi-ophiobolin A','6-epi-ophiobolin B','3-anhydro-6-epi-ophiobolin B','ophiobolin I']
assert len(tables[0])==6
for rawrow in tables[0][2:]:
    row=[v for v in rawrow if v!=''];assert len(row)==11
    for i,name in enumerate(names):
        for j,treatment in enumerate(['punctured','intact']):
            add('OPHIOBOLINS2021',name,'Setaria viridis','necrotic_lesion_diameter',48,float(row[0]),'mg/mL; 5 microliters per droplet',row[1+2*i+j],'mm',
                'detached '+treatment+' leaf; 3 droplets/segment; 3 segments/treatment; repeated 3 times; control 0.1% Tween-80 and 1% acetone',
                gaps='Exact source-to-database stereo mapping provisional. OPH I punctured table 1 mm at 2 d versus text delayed sporadic spots at 4 d; retain contradiction. Puncture wound 0.5 mm not subtracted.')
# Same-paper human cancer cell cytotoxicity is separate from rat LD50 and ecological endpoints.
for row in tables[1][2:]:
    assert len(row)==6
    for species,raw in zip(['HCT-8','Bel-7402','BGC-823','A549','A2780'],row[1:],strict=True):
        add('OPHIOBOLINS2021',row[0],species,'cancer_cell_cytotoxicity_IC50',None,None,'dose_response',raw,'micromolar','MTT assay; section 2.7 cites prior method',gaps='Assay duration not recovered; not organism toxicity or safety evidence.')
assert len(rows)==60

tables=json.loads((sources/'marinefungi2018.tables.json').read_text())
for table_index,dose in [(2,200),(3,50)]:
    table=tables[table_index]
    assert len(table)==(9 if table_index==2 else 7)
    for row in table[2:]:
        assert len(row)==5
        for i,species,endpoint in [(1,'Amaranthus retroflexus','root_length'),(2,'Lactuca sativa','root_length'),(3,'Amaranthus retroflexus','hypocotyl_length'),(4,'Lactuca sativa','hypocotyl_length')]:
            add('MARINEFUNGI2018',row[0],species,endpoint,96,dose,'ppm as reported',row[i],'mm',
                '24-well plate; 5 seeds/well; methanol evaporated; 200 microliters sterile water; 28 C; 12h light/dark',
                sample_type='water_control' if row[0]=='H 2 O' else 'glyphosate_control' if row[0]=='gp' else 'isolated_compound',
                gaps='ppm retained as reported; replicate count not explicit in inspected pure-compound subsection. Means/SD do not give paired uncertainty for derived inhibition.')
for compound in ['3','4','5']:
    add('MARINEFUNGI2018',compound,'Amaranthus retroflexus and Lactuca sativa','qualitative_seedling_phytotoxicity',96,200,'ppm as reported','no phytotoxicity observed','author_category',
        'seed assay as section 3.4; narrative section 2.3; no exact table lengths',gaps='Do not manufacture endpoint-specific zero inhibition, error bars or equivalence margin from qualitative narrative.')
assert len(rows)==111,len(rows)
assert len({r['observation_id'] for r in rows})==len(rows)
out.mkdir()
with (out/'observations.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
manifest={'input_hashes':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),sources/'ophiobolins2021.html',sources/'ophiobolins2021.tables.json',sources/'marinefungi2018.html',sources/'marinefungi2018.tables.json']},
    'output_hashes':{str((out/'observations.csv').resolve()):hashlib.sha256((out/'observations.csv').read_bytes()).hexdigest()},
    'plant_observations':91,'cancer_cell_observations':20,'new_human_approved_labels':0,
    'scope':'Provisional AI transcription; all source compounds/conditions in the selected tables. Raw intervals retained without midpoints; qualitative negatives remain qualitative; no model fitting.'}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in {'input_hashes','output_hashes'}},indent=2))
