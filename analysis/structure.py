"""Offline structural descriptors, with explicit unavailable states."""
import math

from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Contrib.SA_Score import sascorer

from formula import formula_features

DESCRIPTORS = ["mw", "logp", "tpsa", "hbd", "hba", "rotatable_bonds", "rings",
               "fraction_csp3", "sa_score", "lipinski_violations", "tice_proxy_violations"]
FINGERPRINT_SIZE = 2048


def screening_rules(mw, logp, hbd, hba, rotatable_bonds):
    """Count violations using RDKit descriptors; these are screening proxies."""
    result = {"lipinski_violations": None, "tice_proxy_violations": None}
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
               for v in (mw, logp, hbd, hba, rotatable_bonds)):
        return result
    result["lipinski_violations"] = sum((mw > 500, logp > 5, hbd > 5, hba > 10))
    result["tice_proxy_violations"] = sum((
        not 150 <= mw <= 500, logp > 3.5, hbd > 3, not 2 <= hba <= 12, rotatable_bonds > 12,
    ))
    return result


def structure_features(smiles):
    """Compute features for single-component, nonradical carbon compounds."""
    empty = {**dict.fromkeys(DESCRIPTORS), **formula_features(None),
             **dict.fromkeys(["derived_formula", "canonical_structure", "structure_inchikey",
                              "fingerprint", "scaffold"])}
    if smiles is None or isinstance(smiles, str) and not smiles.strip():
        return {**empty, "structure_status": "missing"}
    # RDKit can otherwise accept a trailing name after whitespace.
    if not isinstance(smiles, str) or any(c.isspace() for c in smiles.strip()):
        return {**empty, "structure_status": "invalid_smiles"}
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None or not mol.GetNumAtoms():
        return {**empty, "structure_status": "invalid_smiles"}
    if len(Chem.GetMolFrags(mol)) != 1:
        return {**empty, "structure_status": "multicomponent"}
    if not any(atom.GetAtomicNum() == 6 for atom in mol.GetAtoms()) or any(
        atom.GetNumRadicalElectrons() or atom.GetAtomicNum() == 0 for atom in mol.GetAtoms()
    ):
        return {**empty, "structure_status": "unsupported_chemistry"}
    formula = rdMolDescriptors.CalcMolFormula(mol)
    result = {
        "structure_status": "valid", "derived_formula": formula,
        "canonical_structure": Chem.MolToSmiles(mol),
        "structure_inchikey": Chem.MolToInchiKey(mol),
        "scaffold": MurckoScaffold.MurckoScaffoldSmiles(mol = mol) or "ACYCLIC",
        "mw": Descriptors.MolWt(mol), "logp": Crippen.MolLogP(mol),
        "tpsa": rdMolDescriptors.CalcTPSA(mol), "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol), "rotatable_bonds": Lipinski.NumRotatableBonds(mol),
        "rings": rdMolDescriptors.CalcNumRings(mol),
        "fraction_csp3": rdMolDescriptors.CalcFractionCSP3(mol),
        "sa_score": sascorer.calculateScore(mol), **formula_features(formula),
    }
    result.update(screening_rules(*(result[key] for key in
                                  ("mw", "logp", "hbd", "hba", "rotatable_bonds"))))
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius = 2, fpSize = FINGERPRINT_SIZE, includeChirality = True,
    )
    result["fingerprint"] = list(generator.GetFingerprint(mol))
    return result
