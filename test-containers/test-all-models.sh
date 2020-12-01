#!/bin/bash

envNames=(sharedpy3keras1.2 sharedpy3keras1.2 sharedpy3keras1.2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 sharedpy3keras2 mpra-dragonn extended_coda mmsplice mmsplice-mtsplice deepmel framepool kipoisplice deeptarget attentivechrome bpnet-oskn)
modelNames=(CpGenie/A549_ENCSR000DDI Divergent421 DeepCpG_DNA/Hou2016_HepG2_dna Basenji Basset HAL DeepSEA/variantEffects Optimus_5Prime labranchor CleTimer/customBP SiSp FactorNet/FOXA2/onePeak_Unique35_DGF MaxEntScan/5prime pwm_HOCOMOCO/human/AHR DeepBind/Arabidopsis_thaliana/RBP/D00283.001_RNAcompete_At_0284 lsgkm-SVM/Chip/OpenChrom/Cmyc/K562 rbp_eclip/AARS MPRA-DragoNN/DeepFactorizedModel extended_coda MMSplice/deltaLogitPSI MMSplice/mtsplice DeepMEL Framepool KipoiSplice/4 deepTarget AttentiveChrome/E003 BPNet-OSKN)

for i in ${!modelNames[@]}; do
        #pytest -s test-containers/test_models_from_command_line.py --model=${modelNames[$i]}
        if (( $i -lt ${#envNames[@]} )) ; then
          if (( ${envNames[$i]} -ne ${envNames[$i+1]} )) ; then
            echo ${envNames[$i]}
            docker system prune -a -f
          fi
        fi
done


