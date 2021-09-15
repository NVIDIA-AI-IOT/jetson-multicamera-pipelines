import os
from .dashcamnet import DashCamNet

FILEPATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(FILEPATH)

if not os.path.isfile(DashCamNet.DLA0):
    DashCamNet._download()
