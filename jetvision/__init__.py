# For logging
import logging
import sys

# Expose top-level API for the package
from .pipelines.singlecam import CameraPipeline
from .pipelines.multicam import CameraPipelineDNN

# Setup logging
log = logging.getLogger("jetvision")
log.setLevel(logging.INFO)

# By default stream to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)
