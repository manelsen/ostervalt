from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from .models import ConfiguracaoServidorModel

class RepositorioConfiguracaoServidor:
    def __init__(self, session: Session):
        self.session = session

    def adicionar_ou_atualizar(self, servidor_id: int, chave: str, valor: Any) -> ConfiguracaoServidorModel:
        """Adiciona ou atualiza uma configuração. Converte o valor para JSON string."""
        config = self.obter(servidor_id, chave)
        valor_str = json.dumps(valor) # Armazena como JSON string

        if config:
            config.valor = valor_str
        else:
            config = ConfiguracaoServidorModel(
                servidor_id=servidor_id,
                chave=chave,
                valor=valor_str
            )
            self.session.add(config)

        self.session.commit()
        self.session.refresh(config)
        return config

    def obter(self, servidor_id: int, chave: str) -> Optional[ConfiguracaoServidorModel]:
        """Obtém uma configuração específica."""
        return self.session.query(ConfiguracaoServidorModel).filter_by(servidor_id=servidor_id, chave=chave).first()

    def obter_valor(self, servidor_id: int, chave: str, default: Optional[Any] = None) -> Any:
        """Obtém o valor de uma configuração, desserializando o JSON."""
        config = self.obter(servidor_id, chave)
        if config:
            try:
                return json.loads(config.valor)
            except json.JSONDecodeError:
                # Retorna o valor bruto se não for JSON válido (fallback)
                return config.valor
        return default

    def listar_por_servidor(self, servidor_id: int) -> List[ConfiguracaoServidorModel]:
        """Lista todas as configurações de um servidor."""
        return self.session.query(ConfiguracaoServidorModel).filter_by(servidor_id=servidor_id).all()

    def listar_por_servidor_como_dict(self, servidor_id: int) -> Dict[str, Any]:
        """Lista todas as configurações de um servidor como um dicionário chave/valor."""
        configs = self.listar_por_servidor(servidor_id)
        config_dict = {}
        for config in configs:
             try:
                config_dict[config.chave] = json.loads(config.valor)
             except json.JSONDecodeError:
                 config_dict[config.chave] = config.valor # Fallback
        return config_dict

    def remover(self, servidor_id: int, chave: str) -> bool:
        """Remove uma configuração específica."""
        config = self.obter(servidor_id, chave)
        if config:
            self.session.delete(config)
            self.session.commit()
            return True
        return False