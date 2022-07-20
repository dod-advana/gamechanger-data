import logging
import pandas as pd

from gamechangerml.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def linkage_report(
    df, no_entity_id="Unable to connect Responsibility to Entity"
):
    """
    Creates primary entity linking report for processed RE documents.

    Args:
        df: dataframe of post-processed RE docs
        no_entity_id: text of non-linked entity option

    Returns:
        dataframe of 
    """
    grouped_data = df.groupby(['Source Document', 'Organization / Personnel']).count().reset_index()
    doc_list = list(grouped_data['Source Document'].unique())
    
    output_data = {}
    for i in doc_list:
        output_data[i] = [0, 0]

    for i, row in grouped_data.iterrows():
        if row['Organization / Personnel'] == no_entity_id:
            output_data[row['Source Document']][1] += row["Responsibility Text"]
        else:
            output_data[row['Source Document']][0] += row["Responsibility Text"]

    output_df = pd.DataFrame.from_dict(output_data, orient='index').reset_index()
    output_df.rename(columns={'index':'Source Document', 0:'linked', 1:'unlinked'}, inplace=True)
    output_df['link_percent'] = round((output_df['linked']) / (output_df['linked'] + output_df['unlinked']) * 100, 2)
    return output_df

if __name__ == "__main__":
    from argparse import ArgumentParser

    initialize_logger(to_file=False, log_name="none")

    parser = ArgumentParser(prog="python agg_stats.py")
    parser.add_argument(
        "-c",
        "--csv-path",
        dest="csv_path",
        type=str,
        required=True,
        help="finalized RE to have stats conducted on it",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        dest="output_path",
        type=str,
        required=True,
        help="location for linkage report",
    )
    args = parser.parse_args()
    final_df = pd.read_csv(args.csv_path)

    # unclear as to what to do with this output
    output_df = linkage_report(
        final_df
    )

    output_df.to_csv(args.out_path, header=False)