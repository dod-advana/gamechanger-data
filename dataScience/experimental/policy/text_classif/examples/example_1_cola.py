import logging
import os

from dataScience.experimental.policy.text_classif.classsifier import TextClf
from dataScience.experimental.policy.text_classif.examples.clf_cola_data import (  # noqa
    exc_cola,
)
from dataScience.experimental.policy.text_classif.utils.config import Config
from dataScience.experimental.policy.text_classif.utils.path_to_config_dir import (  # noqa
    to_config_dir,
)
from dataScience.experimental.policy.text_classif.utils.log_init import (
    initialize_logger,
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    # The main show

    initialize_logger(data_name="COLA-data-set")

    path_to_config = os.path.join(to_config_dir(), "cola_config.json")
    assert os.path.isfile(path_to_config)

    cfg = Config(config_file=path_to_config)

    text_clf = TextClf()
    text_clf.fit(fit_func=exc_cola, data_name="COLA data set", cfg=cfg)
