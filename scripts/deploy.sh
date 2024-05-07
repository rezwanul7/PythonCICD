#!/bin/bash
if [[ $1 = "prod" || $1 = "dev" ]] && [[ $2 = "down" || $2 = "up" ]]; then
  cd ..
  export COMPOSE_PATH_SEPARATOR=:
  #    fileEnv="compose.${1}.yaml"
  export COMPOSE_FILE=compose.yaml:compose.${1}.yaml
  downOrUp=$2
  echo "Running docker compose $downOrUp for profile $COMPOSE_FILE"
  docker compose $downOrUp
else
  echo 'Need to follow format ./deploy prod|dev down|up'
fi

#export COMPOSE_PATH_SEPARATOR=:
#
#echo hello $COMPOSE_FILE
#docker compose config
#docker compose up
#docker compose -f common.yaml -f compose.stag.yaml config
#docker compose -f common.yaml -f compose.stag.yaml pull
#docker compose -f common.yaml -f compose.stag.yaml up -d
#echo "Deployment completed successfully."
