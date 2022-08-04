import logging
import os
import fnmatch
import pandas as pd
import gamechangerml.src.text_classif.utils.log_init as li

logger = logging.getLogger(__name__)

# TODO Turn this into a proper CLI if it's still useful
if __name__ == "__main__":
    li.initialize_logger(to_file=False, log_name="none")
    failed_data_path = ""
    train_data_path = ""
    output_csv = ""
    if not failed_data_path or not train_data_path or output_csv:
        msg = "Please update `failed_data_path`, `train_data_path` "
        msg += "or `output_csv` with appropriate file names."
        raise NotImplementedError(msg)

    file_list = [
        f for f in os.listdir(failed_data_path) if fnmatch.fnmatch(f, "*.csv")
    ]
    new_df = pd.DataFrame(columns=["src", "label", "sentence"])

    for f in sorted(file_list):
        df = pd.read_csv(os.path.join(failed_data_path, f))
        df = df.drop(["prob", "label"], axis=1)
        df.rename(columns={"top_class": "label"}, inplace=True)
        new_df = new_df.append(df, ignore_index=True)
        logger.info("adding {:>5,d} : {:>5,d}".format(len(df), len(new_df)))

    df = pd.read_csv(train_data_path)
    logger.info("training data size : {:>6,d}".format(len(df)))
    combined = df.append(new_df, ignore_index=True)
    logger.info(" new training size : {:>6,d}".format(len(combined)))

    # update this name as required!
    df.to_csv(output_csv, header=False)
