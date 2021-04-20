import requests
from click.testing import CliRunner
from dataPipelines.gc_crawler.jcs_pubs.cli import cli
from dataPipelines.gc_crawler.jcs_pubs import get_json_output_sample, BASE_SOURCE_URL


def test_run():

    runner = CliRunner()
    result = runner.invoke(cli, ['run', '--fake-run'])

    print(result.output)

    # TODO: add more detailed output vs sample checks
    sample_output_len = len(get_json_output_sample().strip().split("\n"))
    result_output_len = len(result.output.strip().split("\n"))

    assert result.exit_code == 0
    assert sample_output_len == result_output_len
    assert requests.get(BASE_SOURCE_URL).ok is True
