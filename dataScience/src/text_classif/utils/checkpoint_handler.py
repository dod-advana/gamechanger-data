# The MIT License (MIT)
# Subject to the terms and conditions in LICENSE
import datetime
import json
import logging
import os

from packaging import version

logger = logging.getLogger(__name__)


def write_checkpoint(output_dir, model, tokenizer, loss, stats):
    """
    Checkpoints the model if the loss has improved.

    Args:
        output_dir (str): where to write the checkpoint file

        model (Classifier): the model

        tokenizer (Classifier): the optimizer

        loss (float): validation metric

        stats (dict): performance metrics for this checkpoint

    """
    logger.info("saving model with loss : {:0.3f}".format(loss))
    model_to_save = model.module if hasattr(model, "module") else model
    model_to_save.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    stats_enc = json.dumps(stats)
    with open(os.path.join(output_dir, "run_stats.json"), "w") as f:
        f.write(stats_enc)


def checkpoint_meta(chkpt_path, version_in):
    stats_path = os.path.join(chkpt_path, "run_stats.json")
    if not os.path.isfile(stats_path):
        logger.warning("no 'run_stats.json' in the checkpoint directory")
        return
    else:
        # default: stat the config.json and that file must be present
        ts = os.path.getmtime(os.path.join(chkpt_path, "config.json"))
        with open(stats_path) as f:
            chkpt_stats = json.load(f)
        if "timestamp" in chkpt_stats:
            ts = chkpt_stats["timestamp"]

        c_version = chkpt_stats["config"]["version"]
        log_v = False
        if version_in is not None:
            if version.parse(c_version) < version.parse(version_in):
                msg = (
                    "Checkpoint was created with v{}, you're using v{}".format(
                        c_version, version_in
                    )
                )  # noqa
                msg1 = "...your mileage may vary."
                logger.warning(msg)
                logger.warning(msg1)
                log_v = True
        ts_ = datetime.datetime.fromtimestamp(ts)
        val_loss = chkpt_stats["avg_val_loss"]
        logger.info(
            "  checkpoint time : {}".format(ts_.strftime("%Y-%m-%d %H:%M:%S"))
        )
        logger.info("  package version : {}".format(c_version))
        if log_v:
            logger.info("  current version : {}".format(version_in))
        logger.info("            epoch : {}".format(chkpt_stats["epoch"]))
        logger.info("     avg val loss : {:0.3f}".format(val_loss))
        logger.info("              mcc : {:0.3f}".format(chkpt_stats["mcc"]))
