import enum


class PerfilUsuario(str, enum.Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"


class TipoConsentimento(str, enum.Enum):
    CADASTRO_LGPD = "CADASTRO_LGPD"
    FIDELIDADE = "FIDELIDADE"


class TipoOperacaoUnidade(str, enum.Enum):
    COMPLETA = "COMPLETA"
    REDUZIDA = "REDUZIDA"
