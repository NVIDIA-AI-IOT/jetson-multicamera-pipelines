import os

MODELS_PATH = os.path.dirname(os.path.realpath(__file__))

from .peoplenet import PeopleNet
from .dashcamnet import DashCamNet