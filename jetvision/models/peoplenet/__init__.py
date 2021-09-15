# Here we do lazy loading of the model weights

import os
from .peoplenet import PeopleNet

FILEPATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(FILEPATH)

if not os.path.isfile(PeopleNet.DLA0):
    PeopleNet._download()
