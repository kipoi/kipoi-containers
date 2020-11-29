from time import sleep
import kipoi


models = ['DeepCpG_DNA/Hou2016_HepG2_dna', 'DeepCpG_DNA/Hou2016_HCC_dna', 'DeepCpG_DNA/Smallwood2014_2i_dna', 'DeepCpG_DNA/Smallwood2014_serum_dna', 'DeepCpG_DNA/Hou2016_mESC_dna']

for index, model in enumerate(models):
	model_obj = kipoi.get_model(model)
	pred = model_obj.pipeline.predict_example()
	print(pred)
	if index%10 == 0:
		sleep(5)