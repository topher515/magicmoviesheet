#!/bin/bash
SECRET_VALUE="$2"
SECRET_NAME="$1"
kubectl create secret generic --dry-run=client -o yaml "$SECRET_NAME" --from-literal=value="$SECRET_VALUE" "$@" | kubectl apply -f -