import os
import json
import logging

logger = logging.getLogger(__name__)

def test_ablation(ablation_model,
                  expected_values):
    answer = ablation_model.model_scores
    _, expected_ranks = expected_values

    assert answer == expected_ranks