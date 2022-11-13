
# Setup local

## Install helm
- `brew instal helm`
- `helm repo add bitnami https://charts.bitnami.com/bitnami`

## Setup digital ocean cli
- `brew install doctl`
- `doctl auth init`
- Create a cluster if you dont have one already
- Authenticate doctl to cluster / add kube config
    - `doctl kubernetes cluster kubeconfig save {CLUSTER_ID}`
    - Probably want to add this to `.envrc`

# Setup cluster

## Create secrets

- Setup docker registry secrets with `./deployer wiz config`
- Push secrets from helm env: e.g,: `./deployer wiz push helm/dev`

### DEPRECATED
- Set docker registry secret so k8s can pull from ghrc.io
    -  Create a PAT https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token
 
 - Use the `secret` and `envsecret` command in `./deployer.py`

# Run Deploy

Use the `./deployer.py wiz` subcommand to do deploy stuff

- To see what helm values with be deployed for an env dir `./deployer.py wiz genvalues helm/dev`

- Something like `./deployer.py wiz release helm/dev ghcr.io/topher515/magicmoviesheet:latest-main`