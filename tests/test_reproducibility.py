import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_simulator_is_independent_of_hash_seed():
    script = (
        "import json\n"
        "from oblivionx.corpus.generate import _expected_failure\n"
        "from oblivionx.common import FAMILIES\n"
        "from oblivionx.simulate.simulator import simulate_sample\n"
        "spec = FAMILIES['donoff_downloader']\n"
        "gt = {'stages': spec.stages, 'behaviors': spec.behaviors,"
        " 'expected_failure': _expected_failure(spec)}\n"
        "sa = simulate_sample('s', gt, spec.family, 'plain', 'docm')\n"
        "print(json.dumps(sa.to_dict(), sort_keys=True))\n"
    )
    outputs = []
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT))
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                capture_output=True, text=True, check=True)
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]


def test_e2_tie_ordering_is_independent_of_hash_seed(tiny_corpus,
                                                      tiny_analysis, tmp_path):
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from oblivionx.eval.experiments import experiment_E2\n"
        "r = experiment_E2(Path(sys.argv[1]), Path(sys.argv[2]),"
        " Path(sys.argv[3]))\n"
        "keys = ('static_only', 'dynamic_only', 'most_static_missed',"
        " 'most_dynamic_missed')\n"
        "print(json.dumps({k: r[k] for k in keys}, sort_keys=True))\n"
    )
    outputs = []
    for seed in ("1", "2"):
        out = tmp_path / f"eval-{seed}"
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT))
        result = subprocess.run(
            [sys.executable, "-c", script, str(tiny_corpus),
             str(tiny_analysis), str(out)],
            env=env, capture_output=True, text=True, check=True)
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]
