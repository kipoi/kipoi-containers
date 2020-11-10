from time import sleep
import kipoi


models = ['FactorNet/FOXA2/onePeak_Unique35_DGF', 'FactorNet/FOXA2/multiTask_DGF', 'FactorNet/GABPA/meta_RNAseq_Unique35_DGF', 'FactorNet/GABPA/metaGENCODE_RNAseq_Unique35_DGF', 'FactorNet/TAF1/onePeak_Unique35_DGF', 'FactorNet/TAF1/GENCODE_Unique35_DGF', 'FactorNet/NANOG/onePeak_Unique35_DGF', 'FactorNet/NANOG/GENCODE_Unique35_DGF', 'FactorNet/JUND/meta_Unique35_DGF', 'FactorNet/JUND/meta_Unique35_DGF_2', 'FactorNet/MAX/onePeak_Unique35_DGF', 'FactorNet/MAX/onePeak_Unique35_DGF_2', 'FactorNet/HNF4A/onePeak_Unique35_DGF', 'FactorNet/HNF4A/multiTask_DGF', 'FactorNet/E2F1/onePeak_Unique35_DGF', 'FactorNet/E2F1/GENCODE_Unique35_DGF', 'FactorNet/FOXA1/onePeak_DGF', 'FactorNet/FOXA1/multiTask_DGF', 'FactorNet/CEBPB/onePeak_2_Unique35_DGF', 'FactorNet/CEBPB/meta_Unique35_DGF', 'FactorNet/CEBPB/onePeak_1_DGF', 'FactorNet/MAFK/onePeak_2_Unique35_DGF', 'FactorNet/MAFK/onePeak_1_DGF', 'FactorNet/MAFK/meta_1_Unique35_DGF', 'FactorNet/EGR1/onePeak_DGF', 'FactorNet/EGR1/meta_RNAseq_Unique35_DGF', 'FactorNet/CTCF/meta_RNAseq_Unique35_DGF', 'FactorNet/CTCF/metaGENCODE_RNAseq_Unique35_DGF', 'FactorNet/REST/GENCODE_Unique35_DGF_2', 'FactorNet/REST/GENCODE_Unique35_DGF']

for index, model in enumerate(models):
	model_obj = kipoi.get_model(model)
	pred = model_obj.pipeline.predict_example()
	print(pred)
	if index%10 == 0:
		sleep(5)