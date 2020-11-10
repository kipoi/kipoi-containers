newmodelname=$1
sed "s/modelname/$newmodelname/g" Dockerfile.template > Dockerfile.${newmodelname}
