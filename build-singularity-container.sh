#!/bin/bash

imageName=""
modelName=""

while getopts 'i:m:' flag; do
  case "${flag}" in
    i) imageName="${OPTARG}" ;;
    m) modelName="${OPTARG}" ;;
  esac
done

if [[ ($imageName = "" && $modelName != "") || ($imageName != "" && $modelName = "") ]]
then
    echo "Please enter both image and model name"
    exit 1
fi

if [$imageName = ""] && [$modelName = ""]
then
    imageNames=(sharedpy3keras1.2 sharedpy3keras2 mpra-dragonn extended_coda mmsplice mmsplice-mtsplice deepmel framepool kipoisplice deeptarget attentivechrome bpnet-oskn)
    modelNames=(DeepCpG_DNA/Hou2016_HepG2_dna Basset MPRA-DragoNN/DeepFactorizedModel extended_coda MMSplice/deltaLogitPSI MMSplice/mtsplice DeepMEL Framepool KipoiSplice/4 deepTarget AttentiveChrome/E003 BPNet-OSKN)
    for i in ${!imageNames[@]}; do
        singularity pull docker://kipoi/kipoi-docker:${imageNames[$i]}
        singularity exec kipoi-docker_${imageNames[$i]}.sif kipoi test ${modelNames[$i]} --source=kipoi
        rm -rf ~/.singularity
        rm -rf ~/.kipoi/models/${modelNames[$i]/downloaded}
    done
else
    echo $imageName
    echo $modelName
    singularity pull docker://kipoi/kipoi-docker:${imageName}
    singularity exec kipoi-docker_${imageName}.sif kipoi test ${modelName} --source=kipoi
    rm -rf ~/.singularity
    rm -rf ~/.kipoi/models/${modelName/downloaded}
fi


