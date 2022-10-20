from common.document_parser.lib.responsibility_parse import ResponsibilityParser
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CLI tool for the Responsibility Section Parser")

    parser.add_argument(
        "--json-files-input-directory", "-i",
        dest="json_files_input_directory",
        required=True,
        help="Directory to the input directory for Gamechanger JSONs"
    )

    parser.add_argument(
        "--excel-save-filepath", "-s",
        dest="excel_save_filepath",
        required=False,
        default=None,
        help="Filepath (including diectory and filename) of the excel file that the responsibility explorer results should"
             "be saved to"
    )
    args = parser.parse_args()

    responsibility_parser = ResponsibilityParser()
    responsibility_parser.main(files_input_directory=args.json_files_input_directory,
                               excel_save_filepath=args.excel_save_filepath)
