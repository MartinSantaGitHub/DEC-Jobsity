#!/bin/bash
bash stop.sh
docker rm -f db_c dec_c
docker rmi -f postgres:14.2 dec:1.0