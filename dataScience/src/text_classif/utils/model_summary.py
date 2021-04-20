import logging

logger = logging.getLogger(__name__)


def model_summary(model):
    params = list(model.named_parameters())
    logger.info("==== Embedding Layer ====\n")
    for p in params[0:5]:
        logger.info("{:<55} {:>12}".format(p[0], str(tuple(p[1].size()))))
        logger.info("\n==== First Transformer ====\n")
        for p in params[5:21]:
            logger.info("{:<55} {:>12}".format(p[0], str(tuple(p[1].size()))))
            logger.info("\n==== Output Layer ====\n")
            for p in params[-4:]:
                logger.info(
                    "{:<55} {:>12}".format(p[0], str(tuple(p[1].size())))
                )
