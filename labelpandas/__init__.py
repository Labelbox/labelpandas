from .client import Client
from .load_local_files import load_local_files
from labelpandas import connector
from labelpandas import uploader
import warnings

warnings.warn(f'The module {__name__} is deprecated.', DeprecationWarning, stacklevel=2)