"""Accepted plant-response experiments with explicit context, numerical and identity audits."""

import argparse
import csv
import gzip
import json
import math
import re
import shutil
from collections import Counter
from pathlib import Path

from accepted_sprint import rows
from data_sprint import read_csv, sha256, write_csv
from evidence_release import FEATURES, structure
from sprint_report import verify_bundle
from sprint_toxval import identifier_crosswalk


def finite(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def inhibition_label(value, qualifier = '=', high = 40, low = 20):
    """A retrospective response-band policy. Unknown/intermediate outcomes stay unknown."""
    value = finite(value)
    if value is None:
        return None
    if qualifier in {'', '=', '~'}:
        return 1 if value >= high else 0 if value <= low else None
    if qualifier in {'>', '>='} and value >= high:
        return 1
    if qualifier in {'<', '<='} and value <= low:
        return 0
    return None


def ecotox_basis(native):
    text = (native.get('effect_pct_comments', '') + ' ' +
            native.get('additional_comments', '')).lower().replace('%', 'percent')
    if re.search(r'percent (?:reduction|inhibition|decrease|increase|change)', text):
        return 'percent_change'
    if re.search(r'\bof controls?\b|percent(?:age)? controls?\b', text):
        return 'percent_control'
    return 'unknown'


def native_comment(row):
    return ' '.join(str(row.get(name) or '') for name in (
        'effect_pct_comments', 'additional_comments')).lower()


def documents_decrease(row):
    """True when the native comment itself records a decrease, reduction, or inhibition."""
    return re.search(r'\b(?:decrease|reduction|inhibition)\b', native_comment(row)) is not None


def documents_increase(row):
    """True when the native comment itself records an increase or stimulation."""
    return re.search(r'\b(?:increase|stimulation|stimulated)\b', native_comment(row)) is not None


_CONTROL_SCALE = re.compile(
    r'\b(?:percent(?:age)?(?:\s+of)?\s+controls?|of\s+controls?)\b')


def percent_control_scale_only(row):
    """True when the effect comment only names a percent-of-control scale."""
    text = str(row.get('effect_pct_comments') or '').lower().replace('%', 'percent')
    if _CONTROL_SCALE.search(text) is None:
        return False
    return re.sub(r'[^a-z]+', '', _CONTROL_SCALE.sub(' ', text)) == ''


def percent_control_direction_unresolved(row, value):
    """INC at or below 100% of control, with a comment that does not resolve the scale."""
    return (row.get('effect_direction') == 'INC' and value <= 100
            and not documents_decrease(row) and not percent_control_scale_only(row)
            and not documents_increase(row))


def percent_control_increase_contradiction(row, value):
    """Stimulation override: INC at or below 100 only when the comment says increase.

    A comment that only names percent of control does not match, so inhibition
    stays 100 − value. Decrease language keeps that reading too.
    """
    return (row.get('effect_direction') == 'INC' and value <= 100
            and documents_increase(row) and not documents_decrease(row))


def ecotox_response(row):
    value = finite(row['observed_response'])
    if value is None:
        return None, None
    basis = row.get('response_basis', 'unknown')
    if basis == 'percent_control' and value >= 0:
        # Above 100% of control is stimulation (120% of control → inhibition −20).
        # At or below 100, direction INC is stimulation only when the comment
        # documents an increase or stimulation. A bare percent-of-control comment
        # keeps inhibition = 100 − value. Decrease language does too. If the
        # comment does not resolve the contradiction, withhold the label.
        if percent_control_increase_contradiction(row, value):
            return -value, 0
        if percent_control_direction_unresolved(row, value):
            return None, None
        inhibition = 100 - value
        reverse = {'<': '>', '<=': '>=', '>': '<', '>=': '<='}
        qualifier = reverse.get(row['qualifier'], row['qualifier'])
        return inhibition, inhibition_label(inhibition, qualifier)
    if basis != 'percent_change':
        return None, None
    direction = row['effect_direction']
    if direction == 'INC' and value >= 0:
        return -value, 0  # Low inhibition includes measured stimulation, not universal inactivity.
    if direction == 'DEC' and 0 <= value <= 100:
        return value, inhibition_label(value, row['qualifier'])
    if direction == 'NEF' and value == 0:
        return 0., 0
    return None, None


def run(sprint, frozen, adoption, flavonoids, output):
    sprint, frozen, adoption, flavonoids, output = map(Path, [sprint, frozen, adoption, flavonoids, output])
    for name in ['plant-inventory-v2', 'chembl-review-v1']:
        verify_bundle(sprint / name)
    inputs = [sprint / 'plant-inventory-v2/plant_activity_observations.csv.gz',
              sprint / 'chembl-review-v1/plant_activity_observations.csv',
              adoption / 'accepted_activity_features.csv',
              flavonoids / 'transcription-v1/observations.csv',
              flavonoids / 'analysis-v2/compounds.csv', frozen / 'chemical_identity.csv',
              frozen / 'A_observations.csv', frozen / 'B_predictions.csv']
    before = {str(p): sha256(p) for p in inputs}
    mapping = identifier_crosswalk(frozen)
    identities = {r['full_key']: r for r in rows(frozen / 'chemical_identity.csv')
                  if r['identity_status'] == 'valid'}
    flav_identity = {r['compound_id']: structure(r['smiles'])
                     for r in read_csv(flavonoids / 'analysis-v2/compounds.csv')}
    matrix, audit, registry = [], [], Counter()

    def retain(item, identity, label, status):
        item.setdefault('response_basis', 'source_category' if item['label_kind'] == 'categorical'
                        else 'percent_change')
        item.setdefault('normalized_qualifier', item['qualifier'])
        audit.append({k: item.get(k, '') for k in ['observation_id', 'source', 'source_assay_id',
                                                   'full_key', 'reference_id', 'response_basis',
                                                   'normalized_qualifier']} |
                     {'label': label, 'status': status})
        registry[(item['source'], status)] += 1
        if label is not None and identity and identity['identity_status'] == 'valid':
            matrix.append({**item, 'label': label,
                           **{k: identity[k] for k in ['full_key', 'connectivity', 'smiles',
                                                       'scaffold', *FEATURES]}})

    for row in rows(inputs[0]):
        keys = mapping.get(row['dtxsid'], set())
        key = next(iter(keys)) if len(keys) == 1 else ''
        identity = identities.get(key)
        raw = json.loads(row['source_record_json'])
        result = raw['result']
        row['response_basis'] = ecotox_basis(result)
        row['effect_pct_comments'] = result.get('effect_pct_comments', '')
        row['additional_comments'] = result.get('additional_comments', '')
        reference = row['doi'] or 'ECOTOX_REF:' + raw['test']['reference_number']
        value, label = ecotox_response(row)
        observed = finite(row['observed_response'])
        contradicts = (row['response_basis'] == 'percent_control' and observed is not None
                       and percent_control_increase_contradiction(row, observed))
        item = {'observation_id': 'ECOTOX:' + row['source_record_id'], 'source': 'ECOTOX',
                'source_assay_id': row['source_assay_id'], 'reference_id': reference.lower(),
                'full_key': key, 'plant_species': row['plant_species'],
                'endpoint': row['measurement'], 'response_endpoint': row['endpoint'],
                'dose': row['concentration'], 'dose_unit': row['concentration_unit'],
                'duration': row['duration'], 'duration_unit': row['duration_unit'],
                'signed_inhibition_percent': value, 'qualifier': row['qualifier'],
                'response_basis': row['response_basis'],
                'normalized_qualifier': (row['qualifier'] if contradicts or
                    row['response_basis'] != 'percent_control' else
                    {'<': '>', '<=': '>=', '>': '<', '>=': '<='}.get(
                        row['qualifier'], row['qualifier'])),
                'label_kind': 'quantitative', 'control_context': row['control_context'],
                'assumptions': 'response_basis=' + row['response_basis'],
                'source_locator': row['source_locator']}
        status = ('missing_or_ambiguous_structure' if not identity else
                  'missing_intermediate_or_ambiguous_response' if label is None else 'accepted_label')
        retain(item, identity, label, status)
    for row in read_csv(inputs[1]):
        raw = json.loads(row['source_record_json'])
        identity = structure(row['original_structure'])
        val = finite(row['observed_response'])
        label = inhibition_label(val, row['qualifier']) if row['response_unit'] == '%' else None
        # For this fixed source package, descriptions explicitly identify inhibition/reduction.
        if row['endpoint'] not in {'Inhibition', 'GI', 'Activity'}:
            label = None
        item = {'observation_id': 'ChEMBL:' + row['source_record_id'], 'source': 'ChEMBL',
                'source_assay_id': row['source_assay_id'], 'reference_id': row['doi'].lower(),
                'full_key': identity.get('full_key', ''), 'plant_species': row['plant_species'],
                'endpoint': row['endpoint'], 'response_endpoint': row['endpoint'],
                'dose': '', 'dose_unit': '', 'duration': '', 'duration_unit': '',
                'signed_inhibition_percent': val, 'qualifier': row['qualifier'],
                'label_kind': 'quantitative', 'control_context': row['assay_description'],
                'assumptions': 'source_dose_and_identity_mapping_user_accepted',
                'source_locator': row['source_locator'] + ':activity:' + str(raw['activity_id'])}
        retain(item, identity, label, 'accepted_label' if label is not None else 'missing_intermediate_response')
    for row in read_csv(inputs[3]):
        identity = flav_identity[row['compound_id']]
        val = finite(row['derived_inhibition_percent'])
        item = {'observation_id': row['observation_id'], 'source': 'Flavonoids2012',
                'source_assay_id': '|'.join(row[k] for k in ['species', 'endpoint', 'concentration_uM']),
                'reference_id': row['source_doi'].lower(), 'full_key': identity.get('full_key', ''),
                'plant_species': row['species'], 'endpoint': row['endpoint'],
                'response_endpoint': row['endpoint'], 'dose': row['concentration_uM'], 'dose_unit': 'uM',
                'duration': row['observation_hours'], 'duration_unit': 'h',
                'signed_inhibition_percent': val, 'qualifier': '=', 'label_kind': 'quantitative',
                'control_context': row['control_raw'], 'assumptions': 'reported_mean_ratio_accepted',
                'source_locator': row['source_locator']}
        label = inhibition_label(val)
        retain(item, identity, label, 'accepted_label' if label is not None else 'intermediate_response')
    for ordinal, row in enumerate(read_csv(inputs[2])):
        if row['activity_target'] not in {'0', '1', '0.0', '1.0'}:
            continue
        identity = structure(row['canonical_structure'])
        doi = re.search(r'10\.\d{4,9}/[^;\s]+', row['activity_reference'])
        item = {'observation_id': f'AcceptedCategory:{ordinal}', 'source': 'AcceptedCategory',
                'source_assay_id': row['policy'], 'reference_id': doi[0].lower() if doi else row['policy'],
                'full_key': identity.get('full_key', ''), 'plant_species': '',
                'endpoint': row['policy'], 'response_endpoint': 'original_policy_high_low',
                'dose': '', 'dose_unit': '', 'duration': '', 'duration_unit': '',
                'signed_inhibition_percent': None, 'qualifier': '', 'label_kind': 'categorical',
                'control_context': row['activity_context'], 'assumptions': 'original_policy_labels_accepted',
                'source_locator': row['activity_reference']}
        retain(item, identity, int(float(row['activity_target'])), 'accepted_label')
    if len({r['observation_id'] for r in matrix}) != len(matrix):
        raise ValueError('Duplicate native plant observation IDs')
    matrix.sort(key = lambda r: r['observation_id'])
    output.mkdir(parents = True, exist_ok = False)
    write_csv(output / 'plant_training_observations.csv', matrix, list(matrix[0]))
    with gzip.open(output / 'plant_observation_audit.csv.gz', 'wt', newline = '') as stream:
        writer = csv.DictWriter(stream, fieldnames = list(audit[0]))
        writer.writeheader()
        writer.writerows(audit)
    summary_rows = [{'source': source, 'status': status, 'observations': count}
                    for (source, status), count in sorted(registry.items())]
    write_csv(output / 'plant_source_yield.csv', summary_rows, list(summary_rows[0]))
    summary = {'inputs': before, 'observations': len(matrix),
               'full_structures': len({r['full_key'] for r in matrix}),
               'references': len({r['reference_id'] for r in matrix}),
               'source_counts': dict(Counter(r['source'] for r in matrix)),
               'class_counts': dict(Counter(r['label'] for r in matrix)),
               'mixed_response_structures': sum(len({r['label'] for r in matrix if r['full_key'] == key}) > 1
                                               for key in {r['full_key'] for r in matrix}),
               'policy': 'User-accepted experimental pool: numeric inhibition >=40 high, <=20 low; '
                         'compatible bound intervals; stimulation is low inhibition. Categorical '
                         'accepted policies retain their original thresholds. Missing numerical '
                         'responses and undocumented response scales remain unknown. Explicit '
                         'percent-of-control above 100 is transformed as 100 minus response, with '
                         'reversed bound qualifiers. A percent-of-control value at or below 100 '
                         'keeps inhibition = 100 − response when the comment only names that scale, '
                         'even if direction is INC, and when the comment records a decrease. '
                         'Stimulation (−response, low) applies only when the comment documents an '
                         'increase or stimulation. An unresolved INC contradiction is unlabeled. '
                         'Individual assay/dose/time/endpoint are retained.',
               'limits': 'Heterogeneous observed response, not universal herbicidal activity. '
                         'Same chemical can have different outcomes in different contexts; these '
                         'are retained as separate observations. Unit/context differences are '
                         'not made comparable by acceptance.'}
    if before != {str(p): sha256(p) for p in inputs}:
        raise ValueError('Plant inputs changed')
    rep = output / 'reproduction'
    rep.mkdir()
    shutil.copyfile(__file__, rep / Path(__file__).name)
    summary['products'] = {str(p.relative_to(output)): sha256(p)
                           for p in output.rglob('*') if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(summary, indent = 2) + '\n')
    return {k: v for k, v in summary.items() if k not in {'inputs', 'products'}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = __doc__)
    for name in ['sprint', 'frozen', 'adoption', 'flavonoids', 'output']:
        parser.add_argument('--' + name, type = Path, required = True)
    args = parser.parse_args()
    print(json.dumps(run(args.sprint, args.frozen, args.adoption, args.flavonoids, args.output), indent = 2))
