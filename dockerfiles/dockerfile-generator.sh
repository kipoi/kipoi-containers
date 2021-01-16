newmodelname=$1
sed "s/modelname/$newmodelname/g" ./dockerfiles/Dockerfile.template > ./dockerfiles/Dockerfile.${newmodelname}
