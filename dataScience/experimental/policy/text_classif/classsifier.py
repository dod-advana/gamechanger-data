import logging

import dataScience.experimental.policy.text_classif.version as v
from sklearn import metrics

logger = logging.getLogger(__name__)


class TextClf(object):
    __version__ = v.__version__

    def __init__(self):
        """
        A user-driven class to run classification models. The intent is
        continue adding metrics as the diversity of model types increases.
        Subclassing this for special cases is encouraged.

        More properties are planned.

        """

        self.label_names = None
        self.results = None
        self.cfg = None

        logger.info(
            "{} version {}".format(self.__class__.__name__, self.__version__)
        )

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)

    def _y_values(self):
        y_test, y_pred = self.results[-2:]
        return y_test, y_pred

    def _check_attr(self, attr_name):
        if not hasattr(self.cfg, attr_name):
            self.cfg.add(attr_name, None)

    @property
    def confusion_matrix(self):
        """
        Confusion matrix

        Returns:
            str

        """
        self._check_attr("target_names")
        cm = metrics.confusion_matrix(
            self._y_values()[0], self._y_values()[1],
        )
        return cm

    @property
    def classification_report(self):
        """
        Detailed classification report

        Returns:
            str

        """
        self._check_attr("target_names")
        cr = metrics.classification_report(
            self._y_values()[0],
            self._y_values()[1],
            target_names=self.cfg.target_names,
        )
        return cr

    def fit(
        self, fit_func=None, label_names=None, data_name="no name", cfg=None
    ):
        """
        Fits a user defined function. `fit_func` runs whatever model or models
        defined in that function, taking `*args` as the list of its arguments.

        This function is responsible for reading, massaging, and creating
        the training and test data.


        Args:
            fit_func (callable): user defined function for executing the
              model

            label_names (list|tuple): strings designating the label names

            data_name (str): user defined name for the data set

            cfg (Configuration): config class

        Returns:
            iterable

        """
        if cfg is None:
            raise ValueError("'cfg' cannot be None")

        self.cfg = cfg

        logger.info("fit function : {}()".format(fit_func.__name__))
        self.label_names = label_names
        try:
            self.results = fit_func(data_name=data_name, cfg=cfg)
            return self.results
        except (RuntimeError, ValueError) as e:
            logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
            raise e
