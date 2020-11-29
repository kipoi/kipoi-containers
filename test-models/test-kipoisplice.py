from time import sleep
import kipoi


models = ['KipoiSplice/4cons', 'KipoiSplice/4']

for index, model in enumerate(models):
	model_obj = kipoi.get_model(model)
	pred = model_obj.pipeline.predict_example()
	print(pred)
	if index%10 == 0:
		sleep(5)