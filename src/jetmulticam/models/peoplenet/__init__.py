# Here we do lazy loading of the model weights

import os

from .peoplenet import PeopleNet

FILEPATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(FILEPATH)

if not os.path.isfile(
    DIRPATH + "/tlt_peoplenet_pruned_v2.0/resnet18_peoplenet_int8_dla.txt"
):
    PeopleNet._download()
