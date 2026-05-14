from tools.confighelper import DectWIPConfig
from os import environ

_config = DectWIPConfig(config_path=environ.get('CONFIG_PATH', '/etc/dect-wip.ini'))

# starting gunicorn config here

bind = f'{_config.dect_wip_listen_ip}:{_config.dect_wip_port}'
accesslog = _config.gunicorn_accesslogfile
errorlog = _config.gunicorn_errorlogfile
