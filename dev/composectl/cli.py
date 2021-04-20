import subprocess as sub
import click
from itertools import chain
from typing import Iterable, List
from .config import Config
from .utils import (
    run_or_die,
    get_command_names,
    get_main_service_names
)


def run_sup_compose_commands(commands_to_run: Iterable[str], in_order: bool = False, verbose: bool = False):
    available_commands = get_command_names()
    unmatched_commands = [c for c in commands_to_run if c not in available_commands]
    if unmatched_commands:
        raise ValueError(f"Attempted to run non-existing commands: {commands_to_run!s}")

    if not in_order:
        run_or_die([
            *Config.BASE_DOCKER_COMPOSE_ARGS,
            *(['--verbose'] if verbose else []),
            *[
                '-f', str(Config.COMMAND_COMPOSE_FILE_PATH),
                'up',
                '--force-recreate',
            ],
            *commands_to_run
        ])
    else:
        for cmd in commands_to_run:
            run_or_die([
                *Config.BASE_DOCKER_COMPOSE_ARGS,
                *(['--verbose'] if verbose else []),
                *[
                    '-f', str(Config.COMMAND_COMPOSE_FILE_PATH),
                    'up',
                    '--force-recreate',
                    cmd
                ]
            ])


def up(force_recreate: bool = False,  other_service_sets: Iterable[str] = []):
    compose_cmd_base = [
        *Config.BASE_DOCKER_COMPOSE_ARGS,
        *list(chain(
            *[('-f', str(p)) for n, p in Config.COMPOSE_SUPPLEMENTS.items() if n in other_service_sets]
        ))
    ]

    full_cmd = compose_cmd_base + [
        'up',
        '-d',
        * ([
               '--force-recreate'
           ] if force_recreate else [])
    ]

    run_or_die(full_cmd)


def down(clean: bool = False):
    compose_cmd_base = [
        *Config.BASE_DOCKER_COMPOSE_ARGS,
        *list(chain(
            *[('-f', str(p)) for p in Config.COMPOSE_SUPPLEMENTS.values()]
        ))
    ]

    full_cmd = compose_cmd_base + [
        'down',
        *([
              '--volumes',
              '--remove-orphans',
          ] if clean else [])
    ]

    run_or_die(full_cmd)


@click.group()
def cli():
    """Compose-CTL, docker-compose convenience wrapper for dev_env"""
    pass


@cli.command(name='up')
@click.option(
    '-c',
    '--clean',
    is_flag=True,
    help='Run clean-up before '
)
@click.option(
    '-f',
    '--force-recreate',
    is_flag=True,
    help='Force recreate any existing containers'
)
@click.option(
    '-b',
    '--initialize-buckets',
    is_flag=True,
    help='Initialize buckets once up'
)
@click.option(
    '-a',
    '--also',
    'other_service_sets',
    help='One or many service sets associated with supplementary compose files',
    type=click.Choice([v for v in Config.COMPOSE_SUPPLEMENTS if v != 'commands']),
    multiple=True,
    required=False
)
def up_cmd(clean: bool, force_recreate: bool, initialize_buckets: bool, other_service_sets: List[str]):
    """Start up common services"""
    if clean:
        down(clean=clean)
    up(force_recreate=force_recreate, other_service_sets=other_service_sets)
    if initialize_buckets:
        run_sup_compose_commands(['cmd-recreate-buckets'])


@cli.command(name='down')
@click.option(
    '-c',
    '--clean',
    is_flag=True,
    help='Delete all containers/volumes as well'
)
def down_cmd(clean: bool):
    """Shut down common services"""
    down(clean=clean)


@cli.command(name='cmd')
@click.option(
    '--in-order',
    help='Run commands in order specified - no parallelization',
    is_flag=True
)
@click.argument(
    'commands',
    type=click.Choice(get_command_names()),
    nargs=-1,
    required=True
)
def sup_cmd(commands: List[str], in_order: bool,) -> None:
    """Run supplementary commands defined in commands compose file"""
    run_sup_compose_commands(commands_to_run=commands, in_order=in_order)


@cli.command(name='raw')
@click.argument(
    'docker-compose-args',
    type=str,
    nargs=-1
)
@click.option(
    '-h',
    '--help',
    'help_flag',
    is_flag = True
)
def raw_cmd(docker_compose_args: List[str], help_flag: bool) -> None:
    "Passes args through to raw docker-compose cli command"

    compose_cmd_base = [
        *Config.BASE_DOCKER_COMPOSE_ARGS,
        *list(chain(
            *[('-f', str(p)) for p in Config.COMPOSE_SUPPLEMENTS.values()]
        ))
    ]

    final_cmd = (
        compose_cmd_base
        + ( list(docker_compose_args) if docker_compose_args else [] )
        + ( ['--help'] if help_flag else [])
    )

    r: sub.CompletedProcess = sub.run(final_cmd, **dict(check=False, cwd=Config.PROJECT_DIR))

    if r.returncode != 0:
        exit(r.returncode)


@cli.command(name='ps')
@click.pass_context
def ps_cmd(ctx: click.Context):
    """View status of running containers"""
    ctx.invoke(raw_cmd, docker_compose_args=['ps'])


@cli.command(name='build')
@click.option(
    '-f',
    '--force',
    is_flag=True,
    help="Force rebuild. - Remove custom images, pull newest base images, rebuild all."
)
@click.pass_context
def build_cmd(ctx: click.Context, force: bool):
    """Rebuild main service images"""

    if force:
        ctx.invoke(raw_cmd, docker_compose_args=[
            'down',
            '--rmi=local',
            '--volumes',
            '--remove-orphans'
        ])

    # first pull main svc images that don't need building
    run_or_die([
        *Config.BASE_DOCKER_COMPOSE_ARGS,
        *['pull']
    ])

    # then build baseline image
    run_sup_compose_commands(
        commands_to_run=['cmd-ensure-baseline-image'],
        in_order=True,
        verbose=True
    )

    # then build everything else
    ctx.invoke(raw_cmd, docker_compose_args=[
        *[
            'build',
            *(['--pull'] if force else []),
            '--',
        ],
        *get_main_service_names()
    ])
