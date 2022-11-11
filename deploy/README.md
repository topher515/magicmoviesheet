
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
    - `export PAT_TOKEN=<here>`
    - `kubectl -n default create secret docker-registry k8s-docker-registry-secret-name --docker-server=ghcr.io --docker-username=topher515 --docker-password=$PAT_TOKEN  --docker-email=ckwilcox@gmail.com`

- Set app secret key (can be any value):
    - `./set-simple-secret.sh puzzliveio-{envname}-auth-secret-key '{some value}'`
- Set DB secret:
    - `./set-simple-secret.sh puzzliveio-{envname}-db-uri 'postgresql://doadmin:h...uo5k@dbdomain.com:25060/helloflask-prod-db'`
- Set email API secret key:
    - `./set-simple-secret.sh puzzliveio-{evname}-sendinblue-api-key '{api key}'`

# FAQ

- Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress
  - View currently deployed releases: `./list-deploys.sh dev`
  - Rollback the broken one: `./rollback.sh dev 18`