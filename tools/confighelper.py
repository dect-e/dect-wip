import os

def str_to_bool(input):
    if input.lower() in ["true", "yes", "y", "1"]:
        return True
    elif input.lower() in ["false", "no", "n", "0"]:
        return False
    else:
        raise ValueError(f'"{input}" can no be converted to boolean')

class DectWIPConfig():
    import configparser
    config = configparser.ConfigParser()

    def __get_config_with_env_override(self, section: str, key: str):
        env_var = f'{section}_{key}'.upper()

        if f'FROM_FILE_{env_var}' in os.environ:
            print(f'USING OVERRIDE FROM ENV: FROM_FILE_{env_var}')

            secret_file = os.environ[f'FROM_FILE_{env_var}']
            print(f'reading variable content from file: {secret_file}')
            with open(secret_file, 'r') as secret_file_handle:
                return secret_file_handle.read()

        if env_var in os.environ:
            print(f'USING OVERRIDE FROM ENV: {env_var}')
            return os.environ[env_var]

        return self.config.get(section, key)

    def __init__(self, config_path = '/etc/dect-wip.ini'):
        print(f'Using config: {config_path}')

        if not os.path.isfile(config_path):
            raise Exception(f'config file {config_path} does not exist')

        self.config.read(config_path)

        # [gunicorn]
        self.gunicorn_accesslogfile = self.__get_config_with_env_override('gunicorn', 'accesslogfile')
        self.gunicorn_errorlogfile = self.__get_config_with_env_override('gunicorn', 'errorlogfile')

        # [Asterisk]
        self.asterisk_pjsip_wizard_user_conf = self.__get_config_with_env_override('asterisk', 'pjsip_wizard_user_conf')
        self.asterisk_pjsip_wizard_temp_conf = self.__get_config_with_env_override('asterisk', 'pjsip_wizard_temp_conf')
        self.asterisk_ami_host = self.__get_config_with_env_override('asterisk', 'ami_host')
        self.asterisk_ami_port = int(self.__get_config_with_env_override('asterisk', 'ami_port'))
        self.asterisk_ami_user = self.__get_config_with_env_override('asterisk', 'ami_user')
        self.asterisk_ami_password = self.__get_config_with_env_override('asterisk', 'ami_password')

        # [Flask]
        self.flask_swagger_enable = self.__get_config_with_env_override('flask', 'swagger_enabled')
        self.flask_secret_key = self.__get_config_with_env_override('flask', 'secret_key')

        # [Event]
        self.event_name = self.__get_config_with_env_override('event', 'name')
        self.event_token_prefix = self.__get_config_with_env_override('event', 'token_prefix')
        self.event_token_random_count = int(self.__get_config_with_env_override('event', 'token_random_count'))
        self.event_show_voucher = self.__get_config_with_env_override('event', 'show_voucher')

        # [dect_wip] --- MicroService
        self.dect_wip_listen_ip = self.__get_config_with_env_override('dect-wip', 'listen_ip')
        self.dect_wip_internal_ip = self.__get_config_with_env_override('dect-wip', 'internal_ip')
        self.dect_wip_port = int(self.__get_config_with_env_override('dect-wip', 'port'))

        # [mitelphonebook] --- MicroService
        self.mitelphonebook_always_search_with_contains = self.__get_config_with_env_override('mitelphonebook', 'always_search_with_contains')
        self.mitelphonebook_listen_ip = self.__get_config_with_env_override('mitelphonebook', 'listen_ip')
        self.mitelphonebook_port = int(self.__get_config_with_env_override('mitelphonebook', 'port'))

        # [ommsync] --- MicroService
        self.ommsync_listen_ip = self.__get_config_with_env_override('ommsync', 'listen_ip')
        self.ommsync_port = int(self.__get_config_with_env_override('ommsync', 'port'))
        self.ommsync_enable_subscription = str_to_bool(self.__get_config_with_env_override('ommsync', 'enable_subscription'))
        self.ommsync_auth_code = self.__get_config_with_env_override('ommsync', 'auth_code')

        # [omm]
        self.omm_ip = self.__get_config_with_env_override('omm', 'ip')
        self.omm_port = int(self.__get_config_with_env_override('omm', 'port'))
        self.omm_use_ssl = str_to_bool(self.__get_config_with_env_override('omm', 'use_ssl'))
        self.omm_username = self.__get_config_with_env_override('omm', 'username')
        self.omm_password = self.__get_config_with_env_override('omm', 'password')
