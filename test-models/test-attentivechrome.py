import kipoi

models = ['AttentiveChrome/E003', 'AttentiveChrome/E004', 'AttentiveChrome/E005',
          'AttentiveChrome/E006', 'AttentiveChrome/E007', 'AttentiveChrome/E011', 
          'AttentiveChrome/E012', 'AttentiveChrome/E013', 'AttentiveChrome/E016', 
          'AttentiveChrome/E024', 'AttentiveChrome/E027', 'AttentiveChrome/E028', 
          'AttentiveChrome/E037', 'AttentiveChrome/E038', 'AttentiveChrome/E047', 
          'AttentiveChrome/E050', 'AttentiveChrome/E053', 'AttentiveChrome/E054', 
          'AttentiveChrome/E055', 'AttentiveChrome/E056', 'AttentiveChrome/E057', 
          'AttentiveChrome/E058', 'AttentiveChrome/E061', 'AttentiveChrome/E062', 
          'AttentiveChrome/E065', 'AttentiveChrome/E066', 'AttentiveChrome/E070', 
          'AttentiveChrome/E071', 'AttentiveChrome/E079', 'AttentiveChrome/E082', 
          'AttentiveChrome/E084', 'AttentiveChrome/E085', 'AttentiveChrome/E087', 
          'AttentiveChrome/E094', 'AttentiveChrome/E095', 'AttentiveChrome/E096', 
          'AttentiveChrome/E097', 'AttentiveChrome/E098', 'AttentiveChrome/E100', 
          'AttentiveChrome/E104', 'AttentiveChrome/E105', 'AttentiveChrome/E106', 
          'AttentiveChrome/E109', 'AttentiveChrome/E112', 'AttentiveChrome/E113', 
          'AttentiveChrome/E114', 'AttentiveChrome/E116', 'AttentiveChrome/E117', 
          'AttentiveChrome/E118', 'AttentiveChrome/E119', 'AttentiveChrome/E120', 
          'AttentiveChrome/E122', 'AttentiveChrome/E123', 'AttentiveChrome/E127', 
          'AttentiveChrome/E128']

for model in models:
    model_obj = kipoi.get_model(model)
    pred = model_obj.pipeline.predict_example()
    print(f"model = {model}, pred = {pred}")
