"""User-accepted experimental toxicity cohorts; preserve raw context and frozen A targets."""

import argparse
import csv
import gzip
import json
import math
import shutil
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median

from data_sprint import read_csv, sha256, write_csv
from evidence_release import FEATURES, ld50_bin, structure
from sprint_report import verify_bundle

ACCEPTANCE = ('Continue working on this, assuming that all data is good. Work with full freedom '
              'assuming that all data has been accepted. Make sure that you continue to make '
              'local commits, but work with full experimental freedom.')
SCENARIOS = ('source_asserted', 'all_accepted')
# An exact 100-fold pair uses the log10 median (10 and 1,000 mg/kg → 100).
# Wider spans are not collapsed to one target. The 17 November wide spans all exceed this.
WIDE_DOSE_SPAN = 100
# A lone undetermined secondary point this far below the 1,080 mg/kg tertile is not an exact target.
LONE_IMPLAUSIBLE_MG_KG = 0.05


def rows(path):
    csv.field_size_limit(16 * 1024 * 1024)  # Retained ToxValDB reference JSON can exceed 128 KiB.
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', newline = '') as stream:
        yield from csv.DictReader(stream)


def mass_dose(value, unit):
    """Convert explicit mass/body-mass units only; volume and daily dose stay separate."""
    factors = {'mg/kg': 1, 'mg.kg-1': 1, 'g/kg': 1000, 'ug/kg': .001}
    factor = factors.get((unit or '').strip().lower())
    try:
        result = float(value) * factor if factor is not None else None
        return result if result is not None and math.isfinite(result) and result > 0 else None
    except (TypeError, ValueError):
        return None


def bound_class(value, qualifier):
    """Use a bound only when its complete interval lies within a fixed class."""
    if qualifier == '=':
        return ld50_bin(math.log10(value))
    if qualifier == '<' and value <= 1080 or qualifier == '<=' and value <= 1080:
        return 0
    if qualifier == '>' and value >= 3400 or qualifier == '>=' and value > 3400:
        return 2
    return None


def observation(raw, source, identities):
    dose = mass_dose(raw['value'], raw['unit'])
    rat = raw['test_species'].lower() in {'rat', 'rattus norvegicus'}
    common = rat and raw['endpoint'] == 'LD50' and dose is not None
    assumptions = []
    if source == 'NPASS':
        context = True  # Explicit user-authorized all-accepted sensitivity only.
        source_asserted = False
        assumptions += ['oral_route_assumed', 'acute_context_assumed', 'experimental_status_assumed']
    else:
        payload = json.loads(raw['source_record_json'])['toxval']
        context = raw['test_route'] == 'oral' and payload['STUDY_TYPE'] == 'acute'
        source_asserted = raw['is_experimental'] == 'experimental'
        if not source_asserted:
            assumptions.append('experimental_status_assumed')
    key = raw['full_inchikey']
    identity = identities.get(key)
    reasons = []
    if not common or not context:
        reasons.append('endpoint_species_route_or_mass_dose_incompatible')
    if raw['qualifier'] not in {'=', '<', '>', '<=', '>='}:
        reasons.append('unsupported_qualifier')
    if identity is None or identity['identity_status'] != 'valid':
        reasons.append('no_parsable_single_component_identity')
    return {'source': source, 'source_record_id': raw['source_record_id'],
            'full_key': key, 'value_mg_kg': dose, 'qualifier': raw['qualifier'],
            'reference': raw['citation'], 'source_asserted': source_asserted,
            'assumptions': ';'.join(assumptions), 'eligible': not reasons,
            'exclusion_reason': ';'.join(reasons),
            'class_from_interval': bound_class(dose, raw['qualifier']) if not reasons else None,
            'prior_holds': raw.get('admission_holds', raw.get('exclusion_reason', '')),
            'source_record_json': json.dumps(raw, sort_keys = True)}


def linear_bin_disagreements(observations, new_exact):
    """How many retained new structures change tertile versus the arithmetic-dose median."""
    wanted = {r['full_key'] for r in new_exact}
    bykey = defaultdict(set)
    for row in observations:
        if row['eligible'] and row['qualifier'] == '=' and row['full_key'] in wanted:
            bykey[row['full_key']].add(row['value_mg_kg'])
    flips = 0
    for doses in bykey.values():
        doses = sorted(doses)
        if len(doses) < 2:
            continue
        if ld50_bin(math.log10(median(doses))) != ld50_bin(log_median(doses)):
            flips += 1
    return flips


def log_median(doses):
    """Median on the log10(mg/kg) scale. An even count is not the mean of the linear doses."""
    return median([math.log10(dose) for dose in doses])


def lone_implausible_assumed_dose(obs, doses):
    """One assumed source and a dose below 0.05 mg/kg is not an exact oral LD50 target."""
    exact = [r for r in obs if r['qualifier'] == '=']
    if len(doses) != 1 or doses[0] >= LONE_IMPLAUSIBLE_MG_KG:
        return False
    if any(r.get('source_asserted') in (True, 'True') for r in exact):
        return False
    return len({r.get('reference', '') for r in exact}) == 1


def aggregate(base, observations, identities, scenario):
    """Never relabel frozen A. New exact targets use log10-dose medians; bounds stay bounds."""
    selected = [r for r in observations if r['eligible'] and
                (scenario == 'all_accepted' or r['source_asserted'])]
    bykey = defaultdict(list)
    for row in selected:
        bykey[row['full_key']].append(row)
    exact_rows, class_rows, conflicts = [], [], []
    for key in sorted(set(base) | set(bykey)):
        obs = bykey[key]
        doses = sorted({r['value_mg_kg'] for r in obs if r['qualifier'] == '='})
        bounds_only = False
        if key in base:
            row = dict(base[key])
            row.update(membership = 'frozen_A', assumptions = '',
                       new_source_records = len(obs), source_cohort = 'ICE_frozen_A')
        elif doses and max(doses) / min(doses) > WIDE_DOSE_SPAN:
            conflicts.append({'full_key': key, 'status': 'wide_exact_dose_span',
                              'retained_class': '',
                              'reported_classes': f'{min(doses):g}:{max(doses):g}'})
            row = None
            bounds_only = True
        elif doses and lone_implausible_assumed_dose(obs, doses):
            conflicts.append({'full_key': key, 'status': 'single_implausible_assumed_dose',
                              'retained_class': '', 'reported_classes': f'{doses[0]:g}'})
            row = None
            bounds_only = True
        elif doses:
            target_log = log_median(doses)
            identity = identities[key]
            row = {k: identity[k] for k in ['full_key', 'connectivity', 'smiles', 'scaffold', *FEATURES]}
            row.update(target_log10_mg_kg = target_log, ld50_bin = ld50_bin(target_log),
                       membership = 'new_external_exact', source_cohort = ';'.join(sorted({
                           r['source'] for r in obs})), new_source_records = len(obs),
                       assumptions = ';'.join(sorted({a for r in obs for a in r['assumptions'].split(';')
                                                       if a})))
        else:
            row = None
        if bounds_only:
            interval_classes = {r['class_from_interval'] for r in obs
                                if r['qualifier'] != '=' and r['class_from_interval'] is not None}
        else:
            interval_classes = {r['class_from_interval'] for r in obs
                                if r['class_from_interval'] is not None}
        if row is not None:
            exact_rows.append(row)
            class_rows.append({**row, 'target_kind': 'exact_compound_median'})
            if interval_classes - {int(row['ld50_bin'])}:
                conflicts.append({'full_key': key, 'status': 'exact_vs_source_class_disagreement',
                                  'retained_class': row['ld50_bin'],
                                  'reported_classes': ';'.join(map(str, sorted(interval_classes)))})
        elif len(interval_classes) == 1:
            identity = identities[key]
            cls = next(iter(interval_classes))
            class_rows.append({**{k: identity[k] for k in ['full_key', 'connectivity', 'smiles',
                                                           'scaffold', *FEATURES]},
                               'target_log10_mg_kg': None, 'ld50_bin': cls,
                               'membership': 'new_external_censored',
                               'source_cohort': ';'.join(sorted({r['source'] for r in obs})),
                               'new_source_records': len(obs),
                               'assumptions': ';'.join(sorted({a for r in obs
                                   for a in r['assumptions'].split(';') if a})),
                               'target_kind': 'unambiguous_censored_interval'})
        elif len(interval_classes) > 1:
            conflicts.append({'full_key': key, 'status': 'conflicting_censored_classes',
                              'retained_class': '',
                              'reported_classes': ';'.join(map(str, sorted(interval_classes)))})
    return exact_rows, class_rows, conflicts


def run(sprint, release, output):
    sprint, release, output = Path(sprint), Path(release), Path(output)
    for name in ['npass-v3', 'toxval-v2', 'reports-v3']:
        verify_bundle(sprint / name)
    frozen = json.loads((release / 'manifest.json').read_text())
    for name in ['A_compounds.csv', 'B_compounds.csv', 'chemical_identity.csv']:
        if sha256(release / name) != frozen['outputs'][name]:
            raise ValueError('Frozen A/B input changed')
    inputs = [release / p for p in ['A_compounds.csv', 'B_compounds.csv', 'chemical_identity.csv']]
    inputs += [sprint / 'npass-v3/npass_identity.csv.gz',
               sprint / 'npass-v3/npass_toxicity_all.csv.gz',
               sprint / 'toxval-v2/toxval_observations_all.csv.gz',
               sprint / 'reports-v3/cohort_overlap.csv.gz']
    before = {str(p): sha256(p) for p in inputs}
    base = {r['full_key']: r for r in read_csv(release / 'A_compounds.csv')}
    identities = {r['full_key']: r for r in rows(release / 'chemical_identity.csv')
                  if r['identity_status'] == 'valid'}
    for r in base.values():
        identities[r['full_key']] = dict(r) | {'identity_status': 'valid'}
    toxval = [r for r in rows(inputs[-2]) if r['test_species'] == 'Rat' and r['endpoint'] == 'LD50']
    npass = [r for r in rows(inputs[-3]) if r['test_species'].lower() in {'rat', 'rattus norvegicus'}
             and r['endpoint'] == 'LD50']
    wanted = {r['full_inchikey'] for r in npass}
    for r in rows(sprint / 'npass-v3/npass_identity.csv.gz'):
        if r['full_inchikey'] in wanted and r['full_inchikey'] not in identities:
            parsed = structure(r['original_structure'])
            if parsed['identity_status'] == 'valid' and parsed['full_key'] == r['full_inchikey']:
                identities[r['full_inchikey']] = parsed
    observations = [observation(r, source, identities)
                    for source, collection in [('ToxValDB', toxval), ('NPASS', npass)]
                    for r in collection]
    output.mkdir(parents = True, exist_ok = False)
    declaration = {'accepted_at': datetime.now(UTC).isoformat(), 'instruction': ACCEPTANCE,
                   'scope': 'all acquired sprint data accepted for experimental analysis',
                   'status': 'user_declared_acceptance',
                   'assumptions_are_not_new_source_metadata': True,
                   'frozen_releases_unchanged': True}
    (output / 'acceptance.json').write_text(json.dumps(declaration, indent = 2) + '\n')
    with gzip.open(output / 'toxicity_observations.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(observations[0]))
        writer.writeheader()
        writer.writerows(observations)
    counts = {}
    for scenario in SCENARIOS:
        exact, classes, conflicts = aggregate(base, observations, identities, scenario)
        for name, data in [('exact_compounds', exact), ('classification_compounds', classes)]:
            fields = list(dict.fromkeys(k for r in data for k in r))
            write_csv(output / f'{scenario}_{name}.csv', data, fields)
        write_csv(output / f'{scenario}_source_conflicts.csv', conflicts,
                  ['full_key', 'status', 'retained_class', 'reported_classes'])
        new_exact = [r for r in exact if r.get('membership') == 'new_external_exact']
        counts[scenario] = {'exact_structures': len(exact), 'new_exact_structures': len(exact) - len(base),
                            'classification_structures': len(classes),
                            'censored_only_class_additions': len(classes) - len(exact),
                            'class_counts': dict(Counter(int(r['ld50_bin']) for r in classes)),
                            'source_conflicts': len(conflicts),
                            'new_exact_with_context_assumption': sum(
                                1 for r in new_exact if r.get('assumptions')),
                            'wide_exact_dose_spans': sum(c['status'] == 'wide_exact_dose_span' for c in conflicts),
                            'single_implausible_assumed_doses': sum(
                                c['status'] == 'single_implausible_assumed_dose' for c in conflicts),
                            'log_median_bin_disagreements': linear_bin_disagreements(observations, new_exact)}
    write_csv(output / 'frozen_A_compounds.csv', list(base.values()), list(next(iter(base.values()))))
    overlaps = list(rows(sprint / 'reports-v3/cohort_overlap.csv.gz'))
    natural = {r['full_inchikey']: r for r in overlaps if r['either_catalog_exact'] == 'True'}
    write_csv(output / 'accepted_natural_catalog.csv', list(natural.values()), list(overlaps[0]))
    summary = {'acceptance': declaration, 'scenarios': counts,
               'source_observations': len(observations),
               'eligible_observations': sum(r['eligible'] for r in observations),
               'exclusions': dict(Counter(r['exclusion_reason'] for r in observations if not r['eligible'])),
               'policy': 'Frozen A targets unchanged. New exact targets use the median of distinct '
                         'reported doses on the log10 scale, so an even count is not the arithmetic '
                         'mean of mg/kg. Spans greater than 100-fold are conflicts and do not become '
                         'one exact target. A lone assumed dose below 0.05 mg/kg is the same kind of '
                         'withheld point. Censored bounds never become point targets; when the exact '
                         'target is withheld they can still assign a class. Source-asserted and '
                         'user-assumed context stay distinguishable. Repeated copies of one value are '
                         'one reported dose, not multiple studies. B structures can resolve identities; '
                         'B teacher predictions are not labels. Project bins at 1,080 and 3,400 mg/kg '
                         'are tertiles, not EPA or GHS categories.',
               'inputs': before}
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Inputs changed during accepted release')
    reproduction = output / 'reproduction'
    reproduction.mkdir()
    for p in [Path(__file__), Path('analysis/evidence_release.py')]:
        shutil.copyfile(p, reproduction / p.name)
    summary['products'] = {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return counts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['sprint', 'release', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.sprint, args.release, args.output), indent = 2))
