#!/bin/bash
SECRET_NAME="$1"
kubectl get secret "$SECRET_NAME" -o=jsonpath='{.data.value}' "$@" | base64 --decode