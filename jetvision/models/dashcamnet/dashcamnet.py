import os

FILEPATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(FILEPATH)


class DashCamNet:
    DLA0 = DIRPATH + "/dashcamnet_dla0.txt"
    DLA1 = DIRPATH + "/dashcamnet_dla1.txt"
    GPU = DIRPATH + "/dashcamnet_gpu.txt"

    @staticmethod
    def _download():
        # Lazy loading of dashcamnet model
        MODEL_URL = "https://api.ngc.nvidia.com/v2/models/nvidia/tao/dashcamnet/versions/pruned_v1.0/zip"

        import urllib.request
        from zipfile import PyZipFile

        print(
            "Downloading pretrained weights for DashCamNet model. This may take a while..."
        )
        urllib.request.urlretrieve(
            MODEL_URL, filename="/tmp/dashcamnet_pruned_v1.0.zip"
        )
        # TODO: progressbar here would be nice. Keras has something like that:
        # https://github.com/keras-team/keras/blob/5550cb0c96c508211b1f0af4aa5af6caff7385a2/keras/utils/data_utils.py#L276

        extract_to = DIRPATH + "/dashcamnet_pruned_v1.0"
        pzf = PyZipFile("/tmp/dashcamnet_pruned_v1.0.zip")
        pzf.extractall(path=extract_to)
        print(f"Dowloaded pre-trained DashCamNet model to: {extract_to}")
