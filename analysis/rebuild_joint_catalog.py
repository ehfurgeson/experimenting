"""Rebuild the current catalog, joint evidence screen and notebook diagnostics."""

import argparse
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import requests

import catalog_bulk_screen
import catalog_screen_inventory
import evidence_models
import joint_catalog_diagnostics
import joint_catalog_screen
import nice_endpoint_models
import npass_label_model
import plant_catalog_screen
import public_toxicity
from collect_data_sprint import SOURCES
from data_sprint import sha256
from sprint_natural import run_npass
from sprint_report import verify_bundle

RESOURCES = Path(__file__).resolve().with_name('resources') / 'joint-reproduction'
PUBLIC = {
    'catalog/raw/coconut-lite': (SOURCES['coconut-lite'][0],
        '81f3edc1731f01da289fe6b84d162667863e331d52041a781565e1af2eb79939'),
    'raw/OPERA_Data.zip': (('https://raw.githubusercontent.com/kmansouri/OPERA/'
        '01b07c769dd86eadb71843e057783a64a364c885/OPERA_Data.zip'),
        '9dc5d6387201df0f66e9472b034aeaa09ef7a47f705b9b5f50d7c9af8a1aadc3'),
    'raw/lotus-v11.csv.gz': ('https://zenodo.org/records/19360665/files/260413_frozen.csv.gz?download=1',
        'c0744fb4d4395a638739078601836d9472612c1ed6db6c8e4f0b5e8a972ced70'),
    'raw/lotus-v11-metadata.csv.gz': (('https://zenodo.org/records/19360665/files/'
        '260413_frozen_metadata.csv.gz?download=1'),
        '09885dcfb3bc0e6d700fefcd5778e91446a1f9d5d2fbbcbf00eb5d2e83b68844'),
    'raw/lotus-wikidata-smiles-20261019.tar.gz': (('https://zenodo.org/records/23478723/files/'
        'lotus-wikidata-smiles-20261019T154222Z.tar.gz?download=1'),
        '9fd48d9fb34cef18edd999e903f5bcb57c82adcdf61c08808ac71354ae8ffe90'),
}


def public_snapshot(target, url, digest, cache=None):
    if target.exists():
        if sha256(target) != digest:
            raise ValueError(f'Cached public snapshot checksum mismatch: {target}')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent) as temporary:
        staged = Path(temporary) / target.name
        if cache is not None:
            shutil.copyfile(cache, staged)
        else:
            with requests.get(url, stream=True, timeout=(20, 180)) as response:
                response.raise_for_status()
                with staged.open('wb') as stream:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        stream.write(chunk)
        if sha256(staged) != digest:
            raise ValueError(f'Public snapshot checksum mismatch: {url}')
        staged.replace(target)


def stage(output, operation, *args, **kwargs):
    if not output.exists():
        print(f'Building {output.name}', flush=True)
        return operation(*args, output=output, **kwargs)
    if operation is evidence_models.run:
        manifest = json.loads((output / 'manifest.json').read_text())
        if sha256(args[0] / 'manifest.json') != manifest['release_manifest_sha256']:
            raise ValueError(f'{output} was built from different oral cohorts')
        for path, digest in manifest['outputs'].items():
            if sha256(output / path) != digest:
                raise ValueError(f'{output / path} failed verification')
        return manifest
    return verify_bundle(output)


def run(root, imports, public_cache=None, workers=6, threads=8):
    nice = imports / 'NICE'
    training = imports / 'plant-v5/plant_training_observations.csv'
    npass_input = imports / 'NPASS'
    npass_files = {'npass-structure': npass_input / 'NPASS3.0_naturalproducts_structure.txt',
                   'npass-toxicity': npass_input / 'NPASS3.0_toxicity.txt'}
    required = [training, training.with_name('manifest.json'), *npass_files.values()]
    required += [nice / f'{name}.xlsx' for name in ('acute_oral', *sorted({r[0] for r in
                                                                        nice_endpoint_models.NICE_ENDPOINTS.values()}))]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError('Missing local source files: ' + ', '.join(missing))
    for relative, (url, digest) in PUBLIC.items():
        public_snapshot(root / relative, url, digest, public_cache / relative if public_cache else None)

    oral, models, npass, augmented, endpoints, toxicity, plant, joint, diagnostics = (root / name for name in (
        'public-cohorts-v2', 'public-models-v2', 'npass', 'npass-label-trusted-v2', 'other-toxicity-endpoints-v2',
        'catalog-bulk-public-v1', 'catalog-plant-activity-v3', 'catalog-joint-screen-v2', 'catalog-joint-diagnostics-v2'))
    raw = root / 'raw'
    stage(oral, public_toxicity.run, nice / 'acute_oral.xlsx', raw / 'OPERA_Data.zip')
    registry = root / 'npass-local-sources.json'
    registry.write_text(json.dumps([{'source_id': key, 'file': str(path.resolve()), 'status': 'downloaded',
                                     'sha256': sha256(path)} for key, path in npass_files.items()], indent=2) + '\n')
    stage(npass, run_npass, registry, registry, oral / 'cohort_membership.csv')
    stage(models, evidence_models.run, oral)
    stage(augmented, npass_label_model.run, release=oral, models=models, npass=npass,
          toxval=(), review=None, trust_provider=True)
    stage(endpoints, nice_endpoint_models.run, nice, oral, None,
          dermal_evidence=RESOURCES / 'toxval-dermal-observations.csv')

    coconut, lotus, october, npass_features = (root / name for name in (
        'coconut-full-features-v1', 'lotus-v11-features-v1', 'lotus-october-features-v1', 'npass-full-features-v1'))
    for source, path, directory in (
        ('coconut', root / 'catalog/raw/coconut-lite', coconut), ('lotus', raw / 'lotus-v11-metadata.csv.gz', lotus),
        ('lotus-wikidata', raw / 'lotus-wikidata-smiles-20261019.tar.gz', october),
        ('npass', npass / 'npass_identity.csv.gz', npass_features),
    ):
        stage(directory, catalog_screen_inventory.run, source, path, workers=workers)
    stage(toxicity, catalog_bulk_screen.run, root, nice, coconut, raw / 'lotus-v11.csv.gz',
          lotus=(lotus, october), npass_catalog=npass_features, threads=threads)
    stage(plant, plant_catalog_screen.run, toxicity / 'catalog_scores.parquet',
          RESOURCES / 'de-martino-2012-tables.xml', RESOURCES / 'flavonoid-pubchem.json', pooled=training)
    stage(joint, joint_catalog_screen.run, root, training)
    stage(diagnostics, joint_catalog_diagnostics.run, root, training, nice)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--imports', type=Path, default=Path('data_imports'))
    parser.add_argument('--public-cache', type=Path, help='Reuse already downloaded, checksum-matching public files')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--threads', type=int, default=8)
    run(**vars(parser.parse_args()))
