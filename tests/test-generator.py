import json
import sys
 
def get_list_of_models(model_group):
    with open("model_groups_and_names.json", "r") as infile:
        cached_model_dict = json.load(infile)

    return cached_model_dict.get(model_group, [])


if __name__=="__main__":
    model_group = sys.argv[1]
    list_of_models = get_list_of_models(model_group=model_group)
    with open(f"test-{model_group.lower()}.py", 'w') as output_file:
        output_file.write(f"from time import sleep\nimport kipoi\n\n\nmodels = {list_of_models}\n\nfor index, model in enumerate(models):\n\tmodel_obj = kipoi.get_model(model)\n\tpred = model_obj.pipeline.predict_example()\n\tprint(pred)\n\tif index%10 == 0:\n\t\tsleep(5)")

# sleep is introduced to avoid HTTP error 429 (Too Many Requests) from python    