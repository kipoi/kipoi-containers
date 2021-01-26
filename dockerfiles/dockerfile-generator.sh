#!/bin/sh

newmodelname=$1
imagename="$(tr [A-Z] [a-z] <<< "$newmodelname")"
dir=$(pwd)
sed "s/modelname/$newmodelname/g" ${dir}/dockerfiles/Dockerfile.template > ${dir}/dockerfiles/Dockerfile.${imagename}
