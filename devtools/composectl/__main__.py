from .checks import check_unique_service_names, check_env_file_exists
from .cli import cli


def main() -> None:
    try:
        check_unique_service_names()
        check_env_file_exists()
    except RuntimeError as e:
        print(e)
        exit(1)
    cli()


main()
