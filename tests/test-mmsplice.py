from time import sleep
import kipoi


models = ['MMSplice/pathogenicity', 'MMSplice/splicingEfficiency', 'MMSplice/deltaLogitPSI', 'MMSplice/modularPredictions']

for index, model in enumerate(models):
	model_obj = kipoi.get_model(model)
	pred = model_obj.pipeline.predict_example()
	print(pred)
	if index%10 == 0:
		sleep(5)