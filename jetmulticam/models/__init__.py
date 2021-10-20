import os

MODELS_PATH = os.path.dirname(os.path.realpath(__file__))

from .dashcamnet import DashCamNet
from .peoplenet import PeopleNet
