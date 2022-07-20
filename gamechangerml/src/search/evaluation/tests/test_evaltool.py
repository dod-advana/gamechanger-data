import os
import json
import logging

logger = logging.getLogger(__name__)

def test_evaltool(evaltool, expected_values):
    metrics_at_k = evaltool.evaluate()
    score, _ = expected_values

    all_pass = True
    for k in metrics_at_k.keys():
        for metric in ["precision", "recall"]:
            predicted_val = round(metrics_at_k[k][metric], 6)
            expected_val = round(score[str(k)][metric], 6)
            if predicted_val != expected_val:
                logger.error(f"{k} {metric}")
                logger.error(f"Expectected: {predicted_val}")
                logger.error(f"Actual:      {expected_val}")
                logger.error("-" * 20)
                all_pass = False

    assert all_pass
