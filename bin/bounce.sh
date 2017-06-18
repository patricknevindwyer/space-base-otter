#!/usr/bin/env bash

if [ "$#" -eq 0 ]; then
    echo "You must specify a service to bounce (a container name in the docker-compose file)"
    exit 1
fi

if [ "$1" == "db" ]; then
    echo "Nope. Not gonna do that."
    exit 1
fi

echo "Bouncing $1"

docker-compose stop $1
docker-compose rm -f $1
docker-compose build $1
docker-compose create $1
docker-compose start $1