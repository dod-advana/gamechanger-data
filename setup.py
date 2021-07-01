from setuptools import setup, find_packages
from pathlib import Path
from typing import List
import sys
import re
import os

ROOT_PATH = Path(os.path.dirname(os.path.abspath(__file__))).resolve()

REQUIREMENTS_PATH = Path(
    ROOT_PATH,
    os.path.join(
        "dev_tools",
        "requirements",
        "gc-venv-current.txt"
    )
)

DEV_REQUIREMENTS_PATH = Path(
    ROOT_PATH,
    os.path.join(
        "dev_tools",
        "requirements",
        "dev-requirements.txt",
    )
)

CI_REQUIREMENTS_PATH = Path(
    ROOT_PATH,
    os.path.join(
        "dev_tools",
        "requirements",
        "ci-requirements.txt",
    )
)

CDVID19_REQUIREMENTS_PATH = Path(
    ROOT_PATH,
    os.path.join(
        "dev_tools",
        "requirements",
        "covid-19-dev-requirements.txt",
    )
)


def parse_requirements(requirements: Path) -> List[str]:
    with requirements.open(mode="r") as fd:

        rlist_sans_comments = [
            line.strip()
            for line in fd.read().split("\n")
            if (line.strip() or line.strip().startswith("#"))
        ]

        final_rlist = [
            line
            if not re.match(
                pattern=r"^https?://.*$",
                string=line)
            else re.sub(
                pattern=r"(.*(?:https?://.*/)([a-zA-Z0-9_].*)[-]([a-zA-Z0-9.]*)([.]tar[.]gz|[.]tgz).*)",
                repl=r"\2 @ \1",
                string=line
            )
            for line in rlist_sans_comments
        ]

    return final_rlist

setup(
    name='gamechanger',
    version='evergreen',
    packages=find_packages(),
    url='https://bitbucket.di2e.net/projects/UOT/repos/gamechanger',
    author='gamechanger@advana',
    install_requires=list(filter(
        lambda p: not (p.lower().startswith('faiss-gpu') and sys.platform != 'linux'),
        parse_requirements(REQUIREMENTS_PATH)
    )),
    extras_require={
        "dev": parse_requirements(DEV_REQUIREMENTS_PATH),
        "ci": parse_requirements(CI_REQUIREMENTS_PATH),
        "covid-dev": parse_requirements(CDVID19_REQUIREMENTS_PATH),
    },
    python_requires="==3.6.*",
    entry_points = {
        'console_scripts': [
            'composectl=dev.composectl.__main__:main',
            'configuration=configuration.__main__:main',
            'gci=dataPipelines.gc_ingest.__main__:cli',
            'uni=dev.universal_test_harness.__main__:cli'
        ]
    }
)
