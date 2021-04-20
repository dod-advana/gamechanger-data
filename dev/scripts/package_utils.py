"""
Various utils to make it easier to resolve/scan/report on changes to package lists
"""

import functools as ft
import itertools as it
import typing as t
import pydantic as pyd
from pathlib import Path
import re
import subprocess as sub
import pkg_resources
import shutil

EXTENDED_PKG_SPEC_REGEX = re.compile(r'^\s*(?P<package_name>[\w\-_.]+)\s*@\s*(?P<package_url>\S+)\s*$')
REGULAR_PKG_SPEC_REGEX = re.compile(r'^\s*(?P<package_name>[\w\-_.]+)==(?P<package_version>\S+)\s*$')

NonBlankStr = t.NewType('NonBlankStr', pyd.constr(strip_whitespace=True, min_length=1))


class HashableMixin:
    def __hash__(self) -> int:
        return hash(
            (type(self),) + tuple(getattr(self, f) for f in self.__fields__.keys())
        )


class Package(HashableMixin, pyd.BaseModel):
    name: NonBlankStr
    pkg_spec: NonBlankStr


class DownloadedPackage(Package):
    dldir: pyd.DirectoryPath


class PackageReplacement(pyd.BaseModel):
    old_pkg: Package
    new_pkg: Package


class SonarScanner(pyd.BaseModel):

    sonar_login: NonBlankStr = 'admin'
    sonar_password: NonBlankStr = 'admin'
    sonar_host_url: pyd.stricturl(allowed_schemes={'http', 'https'}) = "http://localhost:9000"
    sonar_scm_disabled: bool = True
    sonar_exclusions: t.Optional[str] = '**/writers/latex2e/__init__.py, **/test/**/*, **/tests/**/*'

    def get_base_scan_args(self) -> t.List[str]:
        return [f'-D{k.replace("_", ".")}={v!s}' for k, v in self.__fields__.items() if v]

    def scan(self,
             name: str,
             src_dir: t.Union[str, Path],
             key: t.Optional[str] = None,
             raise_error: bool = True,
             scanner_cmd: str = 'sonar-scanner',
             docker_cmd: str = 'docker',
             docker_container_id: t.Optional[str] = None) -> sub.CompletedProcess:

        name = name.strip()
        key = (key.strip() if key else None) or name
        src_dir = Path(src_dir).resolve()

        scanner_args = [
            scanner_cmd,
            f'-Dsonar.projectBaseDir={src_dir!s}',
            f'-Dsonar.projectKey={key}',
            f'-Dsonar.projectName={name}',
            *self.get_base_scan_args()
        ]

        if docker_container_id:
            scanner_args = [docker_cmd, 'exec', docker_container_id] + scanner_args

        return sub.run(scanner_args, check=raise_error)


def upgrade_all_packages(python_cmd: str = shutil.which('python')) -> None:
    packages = [dist.project_name for dist in pkg_resources.working_set]
    if packages:
        sub.run([
            python_cmd,
            '-m',
            'pip',
            'install',
            '--upgrade',
            *packages
        ])


def is_regular_pkg_spec(_s: str) -> bool:
    return bool(REGULAR_PKG_SPEC_REGEX.match(_s))


def is_ext_pkg_spec(_s: str) -> bool:
    return bool(EXTENDED_PKG_SPEC_REGEX.match(_s))


def normalize_package_name(_s: str) -> str:
    """All comparisons of distribution names MUST be case insensitive,
        and MUST consider hyphens and underscores to be equivalent.
        ref: https://www.python.org/dev/peps/pep-0426/#name"""
    return _s.replace('_', '-').lower()


def parse_regular_pkg(_s: str) -> Package:
    m = REGULAR_PKG_SPEC_REGEX.match(_s)
    pkg_name = normalize_package_name(m.group('package_name'))
    pkg_version = m.group('package_version')
    return Package(
        name=pkg_name,
        pkg_spec='{}=={}'.format(pkg_name, pkg_version)
    )


def parse_ext_pkg(_s: str) -> Package:
    m = EXTENDED_PKG_SPEC_REGEX.match(_s)
    pkg_name = normalize_package_name(m.group('package_name'))
    pkg_url = m.group('package_url')
    return Package(
        name=pkg_name,
        pkg_spec="{}@{}".format(pkg_name, pkg_url)
    )


def get_package_list(file: t.Union[str, Path]) -> t.List[Package]:
    file = Path(file).resolve()
    pkg_specs = [ l.strip() for l in file.read_text().split('\n') if l.strip() and not l.strip().startswith('#') ]
    pypi_packages = [ parse_regular_pkg(l) for l in pkg_specs if is_regular_pkg_spec(l) ]
    ext_packages = [ parse_ext_pkg(l) for l in pkg_specs if is_ext_pkg_spec(l) ]
    return pypi_packages + ext_packages


def get_packages_to_replace(old: t.List[Package], new: t.List[Package]) -> t.List[PackageReplacement]:
    results = []
    for old_pkg in old:
        for new_pkg in new:
            if old_pkg.name.lower() == new_pkg.name.lower() and old_pkg.pkg_spec.lower() != new_pkg.pkg_spec.lower():
                results.append(PackageReplacement(old_pkg=old_pkg.copy(deep=True), new_pkg=new_pkg.copy(deep=True)))
    return results


def fmt_package_replacements(replacements: t.Iterable[PackageReplacement]) -> str:
    _s = "### Package replacements:\n"
    for r in replacements:
        _s += f'- {r.old_pkg.name}\n'
        _s += f'  - old: {r.old_pkg.pkg_spec}\n'
        _s += f'  - new: {r.new_pkg.pkg_spec}\n'
    return _s


def fmt_new_packages(pkgs: t.Iterable[Package]) -> str:
    _s = "### New packages:\n"
    for p in pkgs:
        _s += f'- {p.pkg_spec}\n'
    return _s


def get_packages_to_install(old: t.Iterable[Package], new: t.Iterable[Package]) -> t.List[Package]:
    return list(set(new) - set(old))


def get_packages_to_remove(old: t.Iterable[Package], new: t.Iterable[Package]) -> t.List[Package]:
    new_names = [n for n in map(lambda i: i.name, new)]
    return list((p for p in old if p.name in new_names))


def install_pkg_to_base_dir(pkg: Package, base_dir: t.Union[str, Path], python_cmd="/resolver/bin/python") -> DownloadedPackage:

    base_dir = Path(base_dir).resolve()
    download_dir = Path(base_dir, pkg.name)
    download_dir.mkdir(exist_ok=True)

    sub.run([python_cmd, '-m', 'pip', 'install', '--no-deps', '-t', str(download_dir), pkg.pkg_spec], check=True)

    return DownloadedPackage(name=pkg.name, version=pkg.version, pkg_spec=pkg.pkg_spec, dldir=download_dir)


def scan_pkg(
        pkg: DownloadedPackage,
        scanner_kwargs: t.Optional[t.Dict[str, t.Any]] = None,
        scan_kwargs: t.Optional[t.Dict[str, t.Any]] = None) -> None:

    s = SonarScanner(**(scanner_kwargs or {}))
    s.scan(name=pkg.name, src_dir=pkg.dldir, **(scan_kwargs or {}))
