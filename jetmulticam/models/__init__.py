import sys
import os

MODELS_PATH = os.path.dirname(os.path.realpath(__file__))


class PeopleNet:
    DLA0 = MODELS_PATH + "/peoplenet/peoplenet_dla0.txt"
    DLA1 = MODELS_PATH + "/peoplenet/peoplenet_dla1.txt"
    GPU = MODELS_PATH + "/peoplenet/peoplenet_gpu.txt"


class DashCamNet:
    DLA0 = MODELS_PATH + "/peoplenet_dla0.txt"
    DLA1 = MODELS_PATH + "/peoplenet_dla1.txt"
    GPU = MODELS_PATH + "/peoplenet_gpu.txt"
