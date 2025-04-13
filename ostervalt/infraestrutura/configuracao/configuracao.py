import yaml

class Configuracao:
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Log ou raise exception apropriada
            print(f"Erro: Arquivo de configuração '{self.config_path}' não encontrado.")
            return {}
        except yaml.YAMLError as e:
            # Log ou raise exception apropriada
            print(f"Erro ao carregar o arquivo YAML '{self.config_path}': {e}")
            return {}

    def obter(self, chave, default=None):
        """
        Obtém um valor de configuração usando uma chave.
        Permite chaves aninhadas separadas por ponto (ex: 'limites.intervalo_trabalhar').
        """
        keys = chave.split('.')
        value = self.config
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    # Se tentarmos acessar uma chave em algo que não é um dicionário
                    return default
            return value
        except KeyError:
            return default
        except TypeError:
             # Caso 'value' se torne None ou outro tipo não indexável
            return default

    def recarregar(self):
        """Recarrega as configurações do arquivo."""
        self.config = self._load_config()

# Exemplo de como poderia ser usado (opcional, apenas para ilustração)
# if __name__ == '__main__':
#     config_loader = Configuracao()
#     intervalo = config_loader.obter('limites.intervalo_trabalhar', 3600)
#     print(f"Intervalo de trabalho: {intervalo}")