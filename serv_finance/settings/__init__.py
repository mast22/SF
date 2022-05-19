from pathlib import Path
import environ, os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))

if env('ENV', str, default='dev') == 'dev':
    from .dev import *
else:
    from .prod import *
