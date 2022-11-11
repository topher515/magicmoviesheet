pipenv requirements > requirements.txt &&
    docker build --tag "$DOCKER_IMAGE_TAG" . &&
    echo $CR_PAT | docker login ghcr.io -u topher515 --password-stdin &&
    docker push "$DOCKER_IMAGE_TAG" &&
    printf "Built and pushed '$DOCKER_IMAGE_TAG'"
    