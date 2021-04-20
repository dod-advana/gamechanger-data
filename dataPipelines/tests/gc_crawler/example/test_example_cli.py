from click.testing import CliRunner
from dataPipelines.gc_crawler.example.cli import cli
from dataPipelines.gc_crawler.example import get_json_output_sample


def test_run():
    runner = CliRunner()
    result = runner.invoke(cli, ['run', '--fake-run'])

    # TODO: add more detailed output vs sample checks
    sample_output_len = len(get_json_output_sample().strip().split("\n"))
    result_output_len = len(result.output.strip().split("\n"))

    assert result.exit_code == 0
    assert sample_output_len == result_output_len
