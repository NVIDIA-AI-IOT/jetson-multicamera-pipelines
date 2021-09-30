import os

from .dashcamnet import DashCamNet

FILEPATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(FILEPATH)

if not os.path.isfile(
    DIRPATH + "./dashcamnet_pruned_v1.0/resnet18_dashcamnet_pruned.etlt"
):
    DashCamNet._download()
