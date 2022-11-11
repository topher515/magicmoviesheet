#!/usr/bin/env python3
import os
import subprocess
from typing import Dict
from base64 import b64decode
from subprocess import check_call, check_output
from dotenv import dotenv_values

import yaml
import json

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

DOCKER_REG_SECRET_NAME = f"deployer-docker-reg-creds-{APP_NAME}"


GENERIC_SECRET_FIELD_NAME = "value"

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


@cli.command("info")
def sync_cmd():
    print(exec_io('kubectl','config','current-context').decode('utf8'))
    print(f"NAMESPACE={NAMESPACE}")
    print(f"APP_NAME={APP_NAME}")


@cli.group("setup")
def setup_cli():
    ...


@setup_cli.command("sync")
def sync_cmd():
    exec("kubectl", "create", "namespace", NAMESPACE)


@setup_cli.command("registry")
@click.argument("username")
@click.argument("email")
@click.argument("password")
def registry_cmd(username, email, password):

    exec(
      "kubectl", 
      f"--namespace={NAMESPACE}",
      "create", 
      "secret",
      "docker-registry",
      DOCKER_REG_SECRET_NAME, 
      "--docker-server=ghcr.io", 
      f"--docker-username={username}",
      f"--docker-password={password}", 
      f"--docker-email={email}"
    )


@cli.group("release")
def release_cli():
    ...


def make_envsecret_name(env: str, env_var_name: str):
    env_var_slug = env_var_name.lower().replace('_', '-')
    return f"envsecret-{env}-{env_var_slug}"


def make_envsecret(env: str, env_var_name: str):
    return {
        "name": env_var_name,
        "valueFrom": {
            "secretKeyRef": {
                "key": GENERIC_SECRET_FIELD_NAME,
                "name": make_envsecret_name(env, env_var_name)
            }
        }
    }


@release_cli.command('create')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("tag")
def new_cmd(env, tag):

    release_values_file=f"{HELM_CHART_DIR}/{env}/values.yaml"

    env_names_file=f"{HELM_CHART_DIR}/{env}/env_names.yaml"
    with open(env_names_file, 'r') as fp:
        env_names = yaml.safe_load(fp)

    envs_json = json.dumps([make_envsecret(env, env_name) for env_name in env_names])
    img_p_secrets_json = json.dumps([{"name": f"{DOCKER_REG_SECRET_NAME}"}])


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
        "--set-json", f'imagePullSecrets={img_p_secrets_json}',
        "--set-json", f'envs={envs_json}',
        f"--values={release_values_file}",
    )

    # imagePullSecrets:
    # - name: k8s-docker-registry-secret-name

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


def _set_secret_cmd(secret_name: str, secret_value: str):
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

@secret_cli.command('set')
@click.argument("secret_name")
@click.argument("secret_value")
def set_secret_cmd(secret_name, secret_value):
    _set_secret_cmd(secret_name, secret_value)

@secret_cli.command('get')
@click.argument("secret_name")
def get_secret_cmd(secret_name):
    output = check_output([
        "kubectl",
        "get",
        "secret",
        f'--namespace={NAMESPACE}',
        secret_name,
        "-o=jsonpath='{.data.value}'",  # This also comes from GENERIC_SECRET_FIELD_NAME
    ])
    print(b64decode(output).decode('utf8'))

@secret_cli.command('rm')
@click.argument("secret_name")
def rm_secret_cmd(secret_name):
    exec(
        "kubectl",
        "remove",
        "secret",
        f'--namespace={NAMESPACE}',
        secret_name
    )


@cli.group("envsecret")
def envsecret_cli():
    ...
 

@envsecret_cli.command('set')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("envvar_name")
@click.argument("envvar_value")
def set_envvar_cmd(env, envvar_name, envvar_value):

    secret_name = make_envsecret_name(env, envvar_name)
    _set_secret_cmd(secret_name, envvar_value)


@envsecret_cli.command('pushfile')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("dotenv_file")
def set_envvar_cmd(env, dotenv_file):

    dotenv_vals: Dict[str,str] = dotenv_values(dotenv_file)

    for envvar_name, envvar_value in dotenv_vals.items():
        secret_name = make_envsecret_name(env, envvar_name)
        _set_secret_cmd(secret_name, envvar_value)


from dotenv import dotenv_values

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}

cli.add_command(release_cli)
cli.add_command(secret_cli)
cli.add_command(envsecret_cli)


if __name__ == "__main__":
   cli() 

