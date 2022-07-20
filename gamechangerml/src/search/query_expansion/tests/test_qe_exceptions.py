import logging

import pytest

from gamechangerml.src.search.query_expansion.build_ann_cli.build_qe_model import (  # noqa
    main,
)

logger = logging.getLogger(__name__)


def test_qe_except_build():
    fake_path = "foo"
    with pytest.raises(FileNotFoundError):
        main(fake_path, fake_path)
