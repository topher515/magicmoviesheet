#!/usr/bin/env python3
import json
import os
import random
import string
import subprocess
import sys
from asyncore import write
from base64 import b64decode
from pathlib import Path
from subprocess import CalledProcessError, check_call, check_output
from tempfile import NamedTemporaryFile, TemporaryFile
from typing import Dict

import click
import click.exceptions
import yaml
from dotenv import dotenv_values
from pyparsing import Optional


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DEMPH = '\033[1m'
    UNDERLINE = '\033[4m'

# HELM_CHART_DIR = "./helm"

ENV_NAMES = ["dev", "prod"]
DEFAULT_ENV = "dev"


APP_NAME = os.getenv('DEPLOYER_APP_PREFIX')
NAMESPACE = os.getenv('DEPLOYER_K8S_NAMESPACE')

# DOCKER_REG_SECRET_NAME = f"deployer-docker-reg-creds-{APP_NAME}"


GENERIC_SECRET_FIELD_NAME = "value"

def exec(*args):
    print(f"{bcolors.DEMPH}Running command: {args}{bcolors.ENDC}")
    return check_call(args)


def exec_io(*args, **kwargs):
    print(f"{bcolors.DEMPH}Running io command: {args}{bcolors.ENDC}")
    proc = subprocess.run(args, capture_output=True, timeout=30, **kwargs)
    try:
        proc.check_returncode()
    except CalledProcessError:
        print(proc.stderr, file=sys.stderr)

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


def _set_docker_registry_secret(secret_name, email, username, password):
    exec(
      "kubectl", 
      f"--namespace={NAMESPACE}",
      "create", 
      "secret",
      "docker-registry",
      secret_name, 
      "--docker-server=ghcr.io", 
      f"--docker-username={username}",
      f"--docker-password={password}", 
      f"--docker-email={email}"
    )


@setup_cli.command("registry")
@click.argument("secret_name")
@click.argument("email")
@click.argument("username")
@click.argument("password")
def registry_cmd(secret_name, email, username, password):
    _set_docker_registry_secret(secret_name, email, username, password)

# @cli.group("release")
# def release_cli():
#     ...


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

def make_mntsecret_name(env: str, filepath: str):
    filepath_slug = filepath.lower().replace('/', '-')
    return f"mntsecret-{env}-{filepath_slug}"


def make_mntsecret_volume_data(env: str, filepath: str):
    name = make_mntsecret_name(env, filepath)
    vol = {
        "name": name,
        "secret": {
            "secretName": name
        }
    }
    vol_mnt = {
        "mountPath": filepath,
        "name": name,
        "readOnly": True
    }
    return vol, vol_mnt


# @release_cli.command('create')
# @click.option("--env", default=DEFAULT_ENV)
# @click.argument("image_pull_secret_name")
# @click.argument("tag")
# def release_new_cmd(env, image_pull_secret_name, tag):

#     release_values_file=f"{HELM_CHART_DIR}/{env}/values.yaml"

#     env_names_file=f"{HELM_CHART_DIR}/{env}/env_names.yaml"
#     with open(env_names_file, 'r') as fp:
#         env_names = yaml.safe_load(fp)

#     envs_json = json.dumps([make_envsecret(env, env_name) for env_name in env_names])
#     img_p_secrets_json = json.dumps([{"name": f"{image_pull_secret_name}"}])


#     print(f'{bcolors.OKCYAN}Deploying tag="{tag}" to env="{env}"...\n{bcolors.ENDC}')
#     exec(
#         "helm", "dependency", "update", HELM_CHART_DIR
#     )
#     exec(
#         "helm", 
#         "upgrade",  # Perform install or upgrade
#         "--create-namespace",  # Create namespace if it doesnt exist
#         f"--namespace={NAMESPACE}",
#         "--install", make_release_name(env),
#         HELM_CHART_DIR,
#         "--set", f"image.tag={tag}",
#         "--set-json", f'imagePullSecrets={img_p_secrets_json}',
#         "--set-json", f'env={envs_json}',
#         f"--values={release_values_file}",
#     )


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


def _set_secret_multi_cmd(secret_name: str, secrets: Dict[str,str]):

    print(f"{bcolors.OKBLUE}Will save secret '{secret_name}'{bcolors.ENDC}")
    from_literals = [
        f'--from-literal={secret_key}={secret_value}'
        for secret_key, secret_value in secrets.items()
    ]

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
        *from_literals,
    )
    exec_io(
        'kubectl', 
        'apply',
        '-f',
        '-',
        input=out
    )


def _set_secret_cmd(secret_name: str, secret_value: str):
    return _set_secret_multi_cmd(secret_name, {"value": secret_value})


def _is_extant_secret(secret_name) -> bool:

    proc = subprocess.run([
        'kubectl', 'get', 'secret', secret_name
    ], capture_output=True, timeout=30)
    if proc.returncode == 0:
        return True
    if 'Error from server (NotFound)' in proc.stderr.decode('utf8'):
        return False
    proc.check_returncode() # Something else broke


@secret_cli.command('set')
@click.argument("secret_name")
@click.argument("secret_value")
def set_secret_cmd(secret_name, secret_value):
    _set_secret_cmd(secret_name, secret_value)


@secret_cli.command('get')
@click.option('--no-parse')
@click.argument("secret_name")
def get_secret_cmd(no_parse, secret_name):
    extras = [] if no_parse else ["-o=jsonpath='{.data.value}'"]
    output = exec_io(
        "kubectl",
        "get",
        "secret",
        f'--namespace={NAMESPACE}',
        secret_name,
          # This also comes from GENERIC_SECRET_FIELD_NAME
        *extras)
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


def _push_envfile(env, dotenv_file):

    dotenv_vals: Dict[str,str] = dotenv_values(dotenv_file)

    for envvar_name, envvar_value in dotenv_vals.items():
        secret_name = make_envsecret_name(env, envvar_name)
        _set_secret_cmd(secret_name, envvar_value)


@envsecret_cli.command('pushfile')
@click.option("--env", default=DEFAULT_ENV)
@click.argument("dotenv_file")
def set_envvar_cmd(env, dotenv_file):
    return _push_envfile(env, dotenv_file)


@cli.group("mntsecret")
def mntsecret_cli():
    ...
 

def _set_file_as_secret(env, remote_filepath, local_filepath):
    print(f"{bcolors.OKBLUE}Will make local file '{local_filepath}' available at '{remote_filepath}' {bcolors.ENDC}")
    dirname = os.path.dirname(remote_filepath)
    if not dirname:
        raise RuntimeError("You must specify a full remote path, not just a filename")
    basename = os.path.basename(remote_filepath)

    with open(local_filepath, 'r') as fp:
        contents = fp.read()

    name = make_mntsecret_name(env, dirname)
    _set_secret_multi_cmd(name, { basename: contents})

@mntsecret_cli.command("set")
@click.option("--env", default=DEFAULT_ENV)
@click.argument("remote_filepath")
@click.argument("local_filepath")
def set_mntsecret_cli(env, remote_filepath, local_filepath):
    _set_file_as_secret(env, remote_filepath, local_filepath)

 
@cli.group("wiz")
def wiz_cli():
    ...

def _iter_filepaths(dirpath: Path):

    for local_path in dirpath.rglob('*'):
        if local_path.is_dir():
            continue
        remote_path = str(local_path).split(str(dirpath))[1]
        yield local_path, remote_path


def load_wiz_config(dirpath: Path, key: Optional[str] = None):
    wizdir = dirpath / 'wiz'
    config_yml = wizdir / 'wiz.yml'

    try:
        with open(config_yml, 'r') as fp:
            config = yaml.safe_load(fp)
    except FileNotFoundError:
        config = {}

    if not key:
        return config

    if config.get(key) is None:
        raise click.exceptions.UsageError(f"{config_yml} does not have {key} set")

    return config[key]


@wiz_cli.command("setup")
@click.argument("dirpath")
def wiz_setup(env, dirpath):

    dirpath = Path(dirpath)
    wizdir = dirpath / 'wiz'
    config_yml = wizdir / 'wiz.yml'

    config = load_wiz_config(dirpath)

    def write_config(config):
        with open(config_yml, 'w') as fp:
            yaml.dump(config, fp)

    # Handle env name
    env = config.get("envName")
    if not env:
        print("The wiz dir does not have an envName configured.")
        env = click.prompt("- env name? (e.g., dev, prod): ")
        config["envName"] = env
        write_config(config)

    # Handle image pull secret config
    image_pull_secret_name = config.get('imagePullSecret')

    if not image_pull_secret_name:
        randstr = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        image_pull_secret_name = f'wiz-setup-imagepullsecret-{env}-{randstr}'
        config['imagePullSecret'] = image_pull_secret_name
        write_config(config)

    if not _is_extant_secret(image_pull_secret_name):
        print(f"Docker Registry Secret '{image_pull_secret_name}' does not exist. Creating it...")
        email = click.prompt("- Email?: ")
        username = click.prompt("- Username?: ")
        password = click.prompt("- Password?: ")
        _set_docker_registry_secret(image_pull_secret_name, email, username, password)

    # # Handle image pull secret

    # # Handle push .env file
    # dirpath = Path(dirpath)
    # wizdir = dirpath / "wiz"
    # dotenv_file = wizdir / '.env'
    # _push_envfile(env, str(dotenv_file))

    # # Handle secret files for mnting
    # for local_path, remote_path in _iter_filepaths(wizdir / 'secretfiles'):
    #     _set_file_as_secret(env, remote_path, local_path)




@wiz_cli.command("push")
@click.argument("dirpath")
def wiz_push(dirpath):
    '''
    Push the secrets data generated from this wiz env directory
    '''

    env = load_wiz_config(dirpath, "envName")

    # Handle push .env file
    dirpath = Path(dirpath)
    wizdir = dirpath / "wiz"
    dotenv_file = wizdir / '.env'
    _push_envfile(env, str(dotenv_file))

    # Handle secret files for mnting
    for local_path, remote_path in _iter_filepaths(wizdir / 'secretfiles'):
        _set_file_as_secret(env, remote_path, local_path)


def _wiz_genvalues(dirpath):
    '''
    Print the `values.yaml` file generated from this wiz env directory
    '''

    dirpath = Path(dirpath)
    wizpath = dirpath / 'wiz'

    env = load_wiz_config(dirpath, "envName")
    image_pull_secret_name = load_wiz_config(dirpath, "imagePullSecret")

    dotenv_file = wizpath / '.env'
    dotenv_vals: Dict[str,str] = dotenv_values(dotenv_file)

    values = {}
    envs = [make_envsecret(env, env_name) for env_name in dotenv_vals.keys()]

    vols = []
    vol_mnts = []
    for local_path, remote_path in _iter_filepaths(wizpath / 'secretfiles'):
        vol, vol_mnt = make_mntsecret_volume_data(env, remote_path)
        vols.append(vol)
        vol_mnts.append(vol_mnt)

    values = {
        "env": envs,
        "volumes": vols,
        "volumeMounts": vol_mnts,
        "imagePullSecrets": [{ "name":image_pull_secret_name }]
    }

    return values


@wiz_cli.command("genvalues")
@click.argument("dirpath")
def wiz_genvalues(dirpath):
    values = _wiz_genvalues(dirpath)
    yaml.dump(values, sys.stdout)


@wiz_cli.command("release")
@click.argument("dirpath")
@click.argument("image")
def wiz_release(dirpath, image):
    values = _wiz_genvalues(dirpath)

    dirpath = Path(dirpath)

    env = load_wiz_config(dirpath, "envName")

    helm_chart_dir = str((dirpath / '..').resolve())

    print(f'{bcolors.OKCYAN}Deploying image="{image}" to env="{env}"...\n{bcolors.ENDC}')
    exec(
        "helm", "dependency", "update", helm_chart_dir
    )

    with NamedTemporaryFile('w') as values_file:

        exec(
            "helm", 
            "upgrade",  # Perform install or upgrade
            "--create-namespace",  # Create namespace if it doesnt exist
            f"--namespace={NAMESPACE}",
            "--install", make_release_name(env),
            helm_chart_dir,
            "--set", f"image={image}",
            f"--values={values_file.name}",
        )


cli.add_command(wiz_cli)
# cli.add_command(release_cli)
cli.add_command(secret_cli)
cli.add_command(envsecret_cli)


if __name__ == "__main__":
   cli() 

