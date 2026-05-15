from tools.confighelper import DectWIPConfig
from os import environ

_config = DectWIPConfig(config_path=environ.get('CONFIG_PATH', '/etc/dect-wip.ini'))

# starting gunicorn config here

bind = f'{_config.mitelphonebook_listen_ip}:{_config.mitelphonebook_port}'
accesslog = _config.gunicorn_accesslogfile
errorlog = _config.gunicorn_errorlogfile
