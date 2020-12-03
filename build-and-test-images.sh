#!/bin/bash

envNames=(kipoi-base-env sharedpy3keras1.2 sharedpy3keras2 mpra-dragonn extended_coda mmsplice mmsplice-mtsplice deepmel framepool kipoisplice deeptarget attentivechrome bpnet-oskn)
docker build -f dockerfiles/Dockerfile.kipoi-base-env -t haimasree/kipoi-docker:kipoi-base-env .

for env in ${envNames[@]}; do
    docker build -f dockerfiles/Dockerfile.${env} -t haimasree/kipoi-docker:${env} .
    pytest -s test-containers/test_containers_from_command_line.py --image=haimasree/kipoi-docker:${env}
    docker system prune -a -f
done

docker system prune -a -f



