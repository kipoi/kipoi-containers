import kipoi

model = kipoi.get_model('Basset')
pred = model.pipeline.predict_example()
print(pred)