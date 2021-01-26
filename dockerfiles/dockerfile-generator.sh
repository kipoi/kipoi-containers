#!/bin/sh

newmodelname=$1
imagename="$(tr [A-Z] [a-z] <<< "$newmodelname")"
sed "s/modelname/$newmodelname/g" ./dockerfiles/Dockerfile.template > ./dockerfiles/Dockerfile.${imagename}
