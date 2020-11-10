from time import sleep
import kipoi


models = ['MaxEntScan/5prime', 'MaxEntScan/3prime']

for index, model in enumerate(models):
	model_obj = kipoi.get_model(model)
	pred = model_obj.pipeline.predict_example()
	print(pred)
	if index%10 == 0:
		sleep(5)