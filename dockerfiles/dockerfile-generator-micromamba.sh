#!/bin/bash

newmodelname=$1
imagename="$(tr [A-Z] [a-z] <<< "$newmodelname")"
dir=$(pwd)
sed "s/modelname/$newmodelname/g" ${dir}/dockerfiles/Dockerfile-micromamba.template > ${dir}/dockerfiles/Dockerfile.${imagename}-micromamba
