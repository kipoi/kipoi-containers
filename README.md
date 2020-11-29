# kipoi-docker
This is an attempt to reduce  and eventully eliminate complexities related to creating and invoking model specific conda environments 

# Building the docker images

First, we need to build the base image which activates a conda environment made with python 3.6 with kipoi installed in it.
```
cd dockerfiles
docker build -f Dockerfile.base -t haimasree/kipoi-docker:kipoi-base-env ..
```
Note: The model specific Dockefiles are sensitive to the name and tag of the base image right now. 
After the base image is built, build any other image using the following template
```
docker build -f Dockerfile.<model-group-name-in-lowercase> -t haimasree/kipoi-docker:<image-name> ..
```
For more information on which model group (or model) can be run with which docker image, see ```test-containers/image-name-to-models.json``` where each  image in docker hub repository haimasree/kipoi-docker is mapped to models they can run. 

# Running the images
For an interactive experience, run the following -
```
docker run -it haimasree
```
This will give you an interactive shell with the relevant conda environment kipoi-KipoiSplice.
To run your custom kipoi cli calls directly,
```
docker run haimasree/kipoi-docker:kipoisplice kipoi test KipoiSplice/4 --source=kipoi
```
The users can also map their own directory using -v option. Assuming the host directory contains a file named test-kipoisplice.py, the following command will enable the user to run their own script directly inside the docker image.
```
docker run -v <aboslute_path_on_host_directory>:<host_directory> haimasree/kipoi-docker:kipoisplice python ./tests/test-kipoisplice.py
```

## Model groups not working

### BPNet-OSKN

Cannot create the environment with the docker base container. 

### SeqVec

Some files are missing. I have notfied the lab.

### rbp_eclip

#### TODO: Check if the same error happens with shared-py3-keras2
With environment created with ```kipoi env create rbp_eclip``` the following tests failed. I will investigate this nd figure out which specific models.

```
2020-11-08 22:54:28,469 [INFO] Downloading dataloader default arguments position_transformer_file from https://sandbox.zenodo.org/record/248594/files/U2AF1.dataloader.pkl?download=1
Downloading https://sandbox.zenodo.org/record/248594/files/U2AF1.dataloader.pkl?download=1 to /Users/b260/.kipoi/models/rbp_eclip/downloaded/dataloader_files/U2AF1/ac1ee344033794b8006277cab7cde94b
0.00B [00:00, ?B/s]Failed download. Trying https -> http instead. Downloading http://sandbox.zenodo.org/record/248594/files/U2AF1.dataloader.pkl?download=1 to /Users/b260/.kipoi/models/rbp_eclip/downloaded/dataloader_files/U2AF1/ac1ee344033794b8006277cab7cde94b
                   Traceback (most recent call last):
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi_utils/external/torchvision/dataset_utils.py", line 67, in download_url
    reporthook=gen_bar_updater(tqdm(unit='B', unit_scale=True))
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 248, in urlretrieve
    with contextlib.closing(urlopen(url, data)) as fp:
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 223, in urlopen
    return opener.open(url, data, timeout)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 532, in open
    response = meth(req, response)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 642, in http_response
    'http', request, response, code, msg, hdrs)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 570, in error
    return self._call_chain(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 504, in _call_chain
    result = func(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 650, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 404: NOT FOUND

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "test-rbp_eclip.py", line 8, in <module>
    model_obj = kipoi.get_model(model)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi/model.py", line 136, in get_model
    dl_source)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi/data.py", line 645, in get_dataloader
    override = download_default_args(descr.args, source.get_dataloader_download_dir(dataloader))
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi/specs.py", line 963, in download_default_args
    args[k].default = args[k].default.get_file(os.path.join(output_dir, fname))
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi/specs.py", line 531, in get_file
    download_url(self.url, root, filename, file_hash)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/site-packages/kipoi_utils/external/torchvision/dataset_utils.py", line 76, in download_url
    reporthook=gen_bar_updater(tqdm(unit='B', unit_scale=True))
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 248, in urlretrieve
    with contextlib.closing(urlopen(url, data)) as fp:
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 223, in urlopen
    return opener.open(url, data, timeout)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 532, in open
    response = meth(req, response)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 642, in http_response
    'http', request, response, code, msg, hdrs)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 564, in error
    result = self._call_chain(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 504, in _call_chain
    result = func(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 756, in http_error_302
    return self.parent.open(new, timeout=req.timeout)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 532, in open
    response = meth(req, response)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 642, in http_response
    'http', request, response, code, msg, hdrs)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 570, in error
    return self._call_chain(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 504, in _call_chain
    result = func(*args)
  File "/Users/b260/anaconda3/envs/kipoi-rbp_eclip/lib/python3.6/urllib/request.py", line 650, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 404: NOT FOUND
```

## Inconsistencies between the website and reality

### Deepbind 

It works if one tests the models in the shared-envs-py3-keras2 as specified here - https://github.com/kipoi/models/blob/master/shared/envs/models.yaml
However, If tested in the environment created by ```kipoi env create DeepBind``` the errors are, 
```
Traceback (most recent call last):
  File "/tmp/test-deepbind.py", line 6, in <module>
    model_obj = kipoi.get_model(model)
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/kipoi/model.py", line 174, in get_model
    mod = AVAILABLE_MODELS[md.type](**md.args)
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/kipoi/model.py", line 365, in __init__
    self.model = model_from_json(arch.read(),
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/saving/model_config.py", line 122, in model_from_json
    return deserialize(config, custom_objects=custom_objects)
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/layers/serialization.py", line 171, in deserialize
    return generic_utils.deserialize_keras_object(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/utils/generic_utils.py", line 354, in deserialize_keras_object
    return cls.from_config(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/engine/training.py", line 2238, in from_config
    return functional.Functional.from_config(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/engine/functional.py", line 616, in from_config
    input_tensors, output_tensors, created_layers = reconstruct_from_config(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/engine/functional.py", line 1204, in reconstruct_from_config
    process_layer(layer_data)
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/engine/functional.py", line 1186, in process_layer
    layer = deserialize_layer(layer_data, custom_objects=custom_objects)
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/layers/serialization.py", line 171, in deserialize
    return generic_utils.deserialize_keras_object(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/utils/generic_utils.py", line 354, in deserialize_keras_object
    return cls.from_config(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/layers/core.py", line 1005, in from_config
    function = cls._parse_function_from_config(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/layers/core.py", line 1057, in _parse_function_from_config
    function = generic_utils.func_load(
  File "/opt/conda/envs/kipoi-DeepBind/lib/python3.8/site-packages/tensorflow/python/keras/utils/generic_utils.py", line 457, in func_load
    code = marshal.loads(raw_code)
ValueError: bad marshal data (unknown type code)
```
Seems eerily similar to https://github.com/kipoi/models/issues/65


### KipoiSplice

Does not work with shared-py3-keras2 environment as specified here - https://github.com/kipoi/models/blob/master/shared/envs/models.yaml. Only works with environment created by ```kipoi env create KipoiSplice```

### CleTimer

Does not work with shared-py3-keras2 environment as specified here - https://github.com/kipoi/models/blob/master/shared/envs/models.yaml. Only works with environment created by ```kipoi env create CleTimer``` plus additional changes. Please take a look at Dockerfile.CleTimer.
