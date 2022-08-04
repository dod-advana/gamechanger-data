import logging
import os
import json
from pathlib import Path

from gamechangerml.src.search.evaluation.ablation import AblationStudy
from gamechangerml.src.search.evaluation.evaltool import EvalTool

import pytest

log_fmt = (
    "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
    + "%(funcName)s()], %(message)s"
)
logging.basicConfig(level=logging.DEBUG, format=log_fmt)
logger = logging.getLogger(__name__)

here = os.path.dirname(os.path.realpath(__file__))
p = Path(here)

test_data_dir = os.path.join(p.parents[0], "tests", "test_data")
model_a_pred_path = os.path.join(test_data_dir, "model_a_predictions.json")
model_b_pred_path = os.path.join(test_data_dir, "model_b_predictions.json")
ground_truth_path = os.path.join(test_data_dir, "ground_truth.json")


eval_tool_pred = os.path.join(test_data_dir, "predictions.json")
eval_tool_true = os.path.join(test_data_dir, "relations.json")

expected_scores_path = os.path.join(test_data_dir, "expected_score.json")
expected_ranks_path = os.path.join(test_data_dir, "expected_ranks.json")

assert os.path.isdir(test_data_dir), test_data_dir

def load_json(fpath):
    with open(fpath, "r") as fp:
        data = json.load(fp)
    return data

@pytest.fixture(scope="session")
def ablation_model():
    ablation = AblationStudy(
        model_a_answer_path = model_a_pred_path,
        model_b_answer_path = model_b_pred_path,
        ground_truth_path = ground_truth_path,
    )
    return ablation

@pytest.fixture(scope="session")
def evaltool():
    test_k_values = [5, 10, 20, 50, 100]
    ev = EvalTool(
        eval_tool_pred,
        eval_tool_true,
        test_k_values
    )
    return ev

@pytest.fixture(scope="session")
def expected_values():
    expected_scores = load_json(expected_scores_path)
    expected_ranks = load_json(expected_ranks_path)

    return expected_scores, expected_ranks