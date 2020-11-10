import kipoi

models = ['CpGenie/A549_ENCSR000DDI', 'DeepCpG_DNA/Hou2016_HCC_dna', 'Divergent421']
for model in models:
    model_obj = kipoi.get_model(model)
    pred = model_obj.pipeline.predict_example()
    print(pred)