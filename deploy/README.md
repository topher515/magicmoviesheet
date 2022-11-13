
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

- Create a PAT https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token
- Get deployk8s: https://github.com/topher515/deployk8s
- Setup docker registry secrets with `deployk8s wiz config`
- Push secrets from helm env: e.g,: `deployk8s wiz push helm/dev`
 
 - Use `deployk8s 

# Run Wiz Deployer

Setup wiz env dir to looks like:

- `helm`
  - `{envname}`
    - `wiz.yml`
    - `.env`, looks like:
      ---
      RAPID_API_KEY=c43e633c6...rapidapi_apikey...37d2d572
      GOOGLE_APPLICATION_CREDENTIALS=/var/google_credential.json
      MOVIE_SPREADSHEET_ID=1KLIddsN...spreadsheetid...0fifd2RlRMo
      ---
    - `secretfiles`
      - `var`
        - `google_credential.json`  # Service robot account creds

- See deployk8s docs: https://github.com/topher515/deployk8s