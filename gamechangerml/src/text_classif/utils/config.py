# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging
import os

import yaml


logger = logging.getLogger(__name__)

type_none = type(None)
path_items = ("checkpoint path", "tensorboard path")
cfg_schema = {
    "log_id": str,
    "model_name": str,
    "epochs": int,
    "batch_size": int,
    "random_state": int,
    "load_saved_model_dir": (str, type_none),
    "checkpoint_path": (str, type_none),
    "tensorboard_path": (str, type_none),
    "num_labels": int,
    "split": float,
    "warmup_steps": (int, type_none),
    "lr": float,
    "weight_decay": float,
    "eps": float,
    "clip_grad_norm": (float, type_none),
    "drop_last": bool,
    "truncate": bool,
    "max_seq_len": (int, type_none),
}

supported_types = {
    "roberta-base": "roberta",
    "bert-base-uncased": "bert",
    "distilbert-base-uncased": "distilbert",
}


class Config(object):
    def __init__(self, cfg_dict):
        """
        Simple attributes for configuration

        Examples:
            .. code-block:: python
            cfg = Config("my_config.yml")

            # retrieve the learning rate `lr`
            lr = cfg.lr

        Args:
            cfg_dict (dict): key-value pairs
        """
        for k, v in cfg_dict.items():
            self.__setattr__(k, v)


def read_verify_config(config_file):
    try:
        _, cfg_name = os.path.split(config_file)
        logger.info("verifying config : {}".format(cfg_name))

        with open(config_file, "r") as yaml_file:
            cfg_dict = yaml.load(yaml_file, Loader=yaml.FullLoader)

        _check_cfg(cfg_dict)
        cfg_dict["config"] = cfg_name
        cfg_dict["model_type"] = supported_types[cfg_dict["model_name"]]

        logger.info("config is not unreasonable...")
        return Config(cfg_dict), cfg_dict
    except (FileNotFoundError, ValueError) as e:
        logger.fatal("\n\n\tThat was a fatal error my friend.\n")
        raise e


def _check_cfg(cfg_dict):
    bail = False
    nones = dict()

    req = set(cfg_schema.keys())
    cfg_in = set(cfg_dict.keys())
    diff = req.symmetric_difference(cfg_in)
    if len(diff) != 0:
        msg = "missing or unknown config items: {}".format(diff)
        raise ValueError(msg)

    for k, v in cfg_dict.items():
        if k not in cfg_schema:
            bail = True
            logger.error("missing/unknown config item : {}".format(k))
        else:
            type_ = type(cfg_dict[k])
            req = cfg_schema[k]
            if isinstance(cfg_schema[k], tuple):
                if type_ not in req:
                    logger.error(
                        "{}: expecting type in {}; got {}".format(
                            k, req, type_
                        )
                    )
                    bail = True
            else:
                if type_ != req:
                    logger.error(
                        "{}: expecting type {}; got {}".format(k, req, type_)
                    )
                    bail = True
            if v is None:
                nones[k] = None
    if bail:
        raise ValueError("missing / type errors in the config file")

    cfg_dict.update(nones)

    # check specific values
    bail = not _is_verified(cfg_dict)
    if bail:
        raise ValueError("value errors in the config file")
    if cfg_dict["max_seq_len"] is not None:
        cfg_dict["truncate"] = True
        logger.info("max seq len : {}".format(cfg_dict["max_seq_len"]))
        logger.info("   truncate : {}".format(cfg_dict["truncate"]))


def _is_verified(cfg_data):
    verified = True
    if cfg_data["num_labels"] < 2:
        verified = False
        logger.error(
            "must have at least 2 labels, got {}".format(
                cfg_data["num_labels"]
            )
        )
    if cfg_data["clip_grad_norm"] is not None:
        if cfg_data["clip_grad_norm"] <= 0.0:
            verified = False
            logger.error("invalid `clip_grad_norm")
    if cfg_data["tensorboard_path"] is not None:
        if not os.path.isdir(cfg_data["tensorboard_path"]):
            verified = False
            logger.error("dir does not exist for 'tensorboard_path'")
    if not 0.80 < cfg_data["split"] <= 1.0:
        verified = False
        logger.error(
            "invalid train / val split; got {:0.3f}".format(cfg_data["split"])
        )
    if cfg_data["model_name"] not in supported_types:
        verified = False
        logger.error(
            "model type not supported : {}".format(cfg_data["model_name"])
        )
    if cfg_data["max_seq_len"] is None:
        return verified
    if not 0 < int(cfg_data["max_seq_len"]) <= 512:
        verified = False
        logger.error("incorrect max_seq_len")
    return verified


def _max_len(runtime_dict):
    max_len = 0
    for k, v in runtime_dict.items():
        if k in path_items:
            if isinstance(v, type(None)):
                continue
            _, f_name = os.path.split(v)
            len_v = len(f_name)
        else:
            len_v = len(str(v))
        max_len = max(max_len, len_v)
    return max_len


def log_config(runtime_dict):
    str_cfg = list()
    width = 23 + _max_len(runtime_dict)
    logger.info("-" * width)
    str_cfg.append("-" * width)
    for k, v in runtime_dict.items():
        if k in path_items:
            if type(v) == type_none:
                file_name = str(None)
            else:
                _, file_name = os.path.split(v)
            str_cfg.append("{:>20s} : {:^8s}".format(k, file_name))
            logger.info("{:>20s} : {:^8s}".format(k, file_name))
        elif isinstance(v, int):
            str_cfg.append("{:>20s} : {:>7,d}".format(k, v))
            logger.info("{:>20s} : {:>7,d}".format(k, v))
        elif isinstance(v, str):
            str_cfg.append("{:>20s} : {:^8s}".format(k, v))
            logger.info("{:>20s} : {:^8s}".format(k, v))
        elif isinstance(v, float):
            str_cfg.append("{:>20s} :   {:>0.1E}".format(k, v))
            logger.info("{:>20s} :   {:>0.1E}".format(k, v))
        elif v is None:
            str_cfg.append("{:>20s} : {:^8s}".format(k, str(v)))
            logger.info("{:>20s} : {:^8s}".format(k, str(v)))
        else:
            str_cfg.append("{:>20s} : {}".format(k, v))
            logger.info("{:>20s} : {}".format(k, v))
    logger.info("-" * width)
    str_cfg.append("-" * width)
    fmt_config = "\n".join(str_cfg)
    return fmt_config
