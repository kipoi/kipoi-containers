#!/bin/bash

envNames=(kipoi-base-env sharedpy3keras1.2 sharedpy3keras2 mpra-dragonn extended_coda mmsplice mmsplice-mtsplice deepmel framepool kipoisplice deeptarget attentivechrome bpnet-oskn seqvec)
docker build -f dockerfiles/Dockerfile.kipoi-base-env -t haimasree/kipoi-docker:kipoi-base-env . || exit 1
docker push haimasree:kipoi-base-env || exit 1

for env in ${envNames[@]}; do
    docker build -f dockerfiles/Dockerfile.${env} -t haimasree/kipoi-docker:${env} . || exit 1
    pytest -s test-containers/test_containers_from_command_line.py --image=haimasree/kipoi-docker:${env} || exit 1
    docker push haimasree/kipoi-docker:${env} || exit 1
    docker system prune -a -f
done

docker system prune -a -f



