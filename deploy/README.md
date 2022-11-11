
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

- Set docker registry secret so k8s can pull from ghrc.io
    -  Create a PAT https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token
 
 - Use the `secret` and `envsecret` command in `./deployer.py`