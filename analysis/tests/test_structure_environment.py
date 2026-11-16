"""The locked analysis environment supports the actual modeling operations."""
import importlib.util


def test_chemistry_and_modeling_dependencies_are_available():
    assert importlib.util.find_spec("rdkit") is not None
    assert importlib.util.find_spec("sklearn") is not None
    from rdkit import Chem
    from rdkit.Contrib.SA_Score import sascorer
    from sklearn.decomposition import PCA

    assert 1 <= sascorer.calculateScore(Chem.MolFromSmiles("CCO")) <= 10
    assert PCA(n_components = 1).fit_transform([[0, 1], [1, 0]]).shape == (2, 1)
