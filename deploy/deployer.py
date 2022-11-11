#!/usr/bin/env python3
import os
import subprocess
from base64 import b64decode
from subprocess import check_call, check_output

import click

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

HELM_CHART_DIR = "./helm"

ENV_NAMES = ["dev", "prod"]
DEFAULT_ENV = "dev"


APP_NAME = os.getenv('DEPLOYER_APP_PREFIX')
NAMESPACE = os.getenv('DEPLOYER_K8S_NAMESPACE')


def exec(*args):
    print(f"Running command: {args}")
    return check_call(args)


def exec_io(*args, **kwargs):
    print(f"Running io command: {args}")
    proc = subprocess.run(args, capture_output=True, timeout=30, check=True, **kwargs)
    return proc.stdout


def make_release_name(env: str):
    return f"{APP_NAME}-{env}"


@click.group()
def cli():
    if not NAMESPACE:
        raise RuntimeError("You must configure deployer NAMESPACE")
    if not APP_NAME:
        raise RuntimeError("You must configure deployer APP_NAME")


@cli.command("sync")
def sync_cmd():
    exec("kubectl", "create", "namespace", NAMESPACE)

@cli.command("info")
def sync_cmd():
    print(exec_io('kubectl','config','current-context').decode('utf8'))
    print(f"NAMESPACE={NAMESPACE}")
    print(f"APP_NAME={APP_NAME}")

@cli.group("release")
def release_cli():
    ...


@release_cli.command('create')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("tag")
def new_cmd(env, tag):

    release_values_file=f"{HELM_CHART_DIR}/{env}/values.yaml"

    print(f'{bcolors.OKCYAN}Deploying tag="{tag}" to env="{env}"...\n{bcolors.ENDC}')
    exec(
        "helm", "dependency", "update", HELM_CHART_DIR
    )
    exec(
        "helm", 
        "upgrade",  # Perform install or upgrade
        "--create-namespace",  # Create namespace if it doesnt exist
        f"--namespace={NAMESPACE}",
        "--install", make_release_name(env),
        HELM_CHART_DIR,
        "--set", f"image.tag={tag}",
        f"--values={release_values_file}",
    )


@release_cli.command('nuke')
@click.option("--env", default=DEFAULT_ENV)
def nuke_cmd(env):
    exec(
        "helm",
        "uninstall",
        f"--namespace={NAMESPACE}",
        make_release_name(env)
    )


@release_cli.command('list')
@click.option("--env", default=DEFAULT_ENV)
def list_cmd(env):
    exec(
        "helm",
        "history",
        f"--namespace={NAMESPACE}",
        make_release_name(env)
    )


@release_cli.command('rollback')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("revision")
def rollback_cmd(env, revision):
    exec(
        "helm",
        "rollback",
        f"--namespace={NAMESPACE}",
        make_release_name(env),
        revision
    )


@cli.group("secret")
def secret_cli():
    ...
 

@secret_cli.command('list')
def list_cmd():
    exec(
        'kubectl',
        'get',
        'secret',
        f'--namespace={NAMESPACE}'
    )

@secret_cli.command('set')
@click.argument("secret_name")
@click.argument("secret_value")
def set_cmd(secret_name, secret_value):

    out = exec_io(
        'kubectl',
        'create',
        'secret',
        f'--namespace={NAMESPACE}',
        '--dry-run=client',
        'generic',
        '-o',
        'yaml',
        secret_name,
        f'--from-literal=value={secret_value}',
    )
    exec_io(
        'kubectl', 
        'apply',
        '-f',
        '-',
        input=out
    )

@secret_cli.command('get')
@click.argument("secret_name")
def get_cmd(secret_name):
    output = check_output([
        "kubectl",
        "get",
        "secret",
        f'--namespace={NAMESPACE}',
        secret_name,
        "-o=jsonpath='{.data.value}'",
    ])
    print(b64decode(output).decode('utf8'))


cli.add_command(release_cli)
cli.add_command(secret_cli)


if __name__ == "__main__":
   cli() 

