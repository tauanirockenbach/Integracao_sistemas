# 🏭 Integração Industrial: Elipse SCADA ↔ CODESYS ↔ Open MES

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue?logo=docker&logoColor=white)
![CODESYS](https://img.shields.io/badge/CODESYS-V3.5-orange)
![OPC UA](https://img.shields.io/badge/Protocol-OPC%20UA-green)
![License](https://img.shields.io/badge/License-MIT-green)

## 📌 Sobre o Projeto

Este repositório apresenta a documentação técnica e os scripts de integração entre **Elipse SCADA, CODESYS e Open MES**, com o objetivo de automatizar o gerenciamento de paradas de produção e bloqueios de linha em tempo real.

A solução monitora alarmes de emergência provenientes do CLP (CODESYS), supervisionados pelo Elipse SCADA, e encaminha os eventos ao Open MES por meio de um middleware desenvolvido em Python.

Quando uma condição crítica é identificada, o sistema registra uma ocorrência (*Issue*) e solicita o bloqueio da Ordem de Produção correspondente.

## 🔀 Arquitetura da Integração

```text
┌──────────────────┐
│   Elipse SCADA   │
│   Supervisório   │
└────────┬─────────┘
         │
         ↕
┌──────────────────┐
│  CODESYS (CLP)   │
│  SoftPLC V3      │
└────────┬─────────┘
         │ OPC UA
         ↕
┌──────────────────┐
│ Middleware       │
│ Python           │
│ OPC UA / REST    │
└────────┬─────────┘
         │ HTTP REST
         ↕
┌──────────────────┐
│     Open MES     │
│   Docker / MES   │
└──────────────────┘
```

### 🔧 Responsabilidade de cada componente

- **Elipse SCADA / E3:** Atua como interface de supervisão e operação da planta industrial.
- **CODESYS (Control Win V3):** Executa a lógica de controle do CLP e disponibiliza variáveis globais (GVL) por meio do servidor OPC UA.
- **Middleware Python:** Monitora as variáveis do CLP e envia requisições HTTP REST autenticadas com Bearer Token.
- **Open MES:** Recebe as ocorrências, registra os *Issues* bloqueantes e gerencia o estado das Ordens de Produção.

## 🛠️ Pré-requisitos

### Softwares necessários

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [CODESYS Development System V3.5](https://store.codesys.com/)
- [CODESYS Control Win V3](https://store.codesys.com/)
- [Elipse SCADA / E3](https://www.elipse.com.br/)
- [Python 3.9 ou superior](https://www.python.org/)

### Bibliotecas Python

Instale as dependências:

```bash
pip install requests python-opcua python-dotenv
```

## 🚀 1. Instalação do Open MES com Docker

### 1.1. Criar o arquivo `docker-compose.yml`

Crie uma pasta para o projeto e adicione o arquivo:

```yaml
services:
  openmes-app:
    image: openmes/openmes:latest
    container_name: openmes_app
    restart: always
    ports:
      - "8081:80"
    environment:
      APP_ENV: production
      APP_KEY: ${APP_KEY}
      DB_CONNECTION: sqlite
    volumes:
      - openmes_data:/var/www/html/storage

volumes:
  openmes_data:
```

> **Observação:** Configure uma chave APP_KEY válida conforme a documentação da imagem utilizada. Confirme também a disponibilidade e os requisitos da imagem Open MES antes de iniciar o container.

### 1.2. Iniciar o container

No terminal, dentro da pasta do projeto, execute:

```bash
docker compose up -d
```

Para verificar se o container está funcionando:

```bash
docker ps
```

### 1.3. Acessar o Open MES

Após a inicialização, acesse:

**URL:** http://localhost:8081

Utilize as credenciais iniciais disponibilizadas pela instalação ou pelo administrador do sistema.

## 🔑 2. Configuração do Token de API

O middleware Python utiliza autenticação Bearer Token para realizar as requisições à API do Open MES.

### Etapas

1. Acesse o painel do Open MES.
2. Entre em **Settings → API Tokens**.
3. Selecione **Create Token**.
4. Defina um nome, por exemplo: `Integracao_Python`.
5. Gere e copie o token.

> ⚠️ **Segurança:** O token deve ser armazenado em uma variável de ambiente. Nunca publique tokens reais, senhas ou chaves de API no GitHub.

## ⚙️ 3. Configuração do CODESYS e Elipse SCADA

### 3.1. Configuração do CODESYS

Crie uma lista de variáveis globais (*Global Variable List – GVL*) com o nome `GVL`.

Exemplo:

```iecst
VAR_GLOBAL
    bAlarmeEmergencia : BOOL := FALSE;
    nPecasProduzidas : DINT := 0;
END_VAR
```

**Configuração do servidor OPC UA:**

1. Clique com o botão direito na aplicação.
2. Selecione `Add Object → Symbol Configuration`.
3. Compile o projeto utilizando `Build`.
4. Selecione a GVL na configuração de símbolos.
5. Habilite a variável `bAlarmeEmergencia` para leitura.
6. Habilite a escrita caso o sistema também precise alterar essa variável externamente.
7. Execute o programa no CODESYS Control Win V3.

Endereço do servidor OPC UA:

```text
opc.tcp://localhost:4840
```

O endereço deve ser ajustado conforme a configuração de rede e o servidor utilizado.

### 3.2. Configuração do Elipse SCADA / E3

1. Adicione o driver de comunicação OPC UA compatível com a instalação.
2. Configure a conexão com o servidor OPC UA do CODESYS.
3. Localize a variável `GVL.bAlarmeEmergencia`.
4. Associe o botão de emergência da IHM à variável correspondente.
5. Configure a comunicação para atualizar o estado da variável no CLP.

Quando o operador acionar o botão de emergência, a variável deverá assumir:

```iecst
GVL.bAlarmeEmergencia := TRUE;
```

## 💻 4. Desenvolvimento do Middleware Python

O middleware é responsável pela comunicação entre o CLP e o Open MES.

### 4.1. Estrutura do projeto

```text
Integracao-Industrial/
│
├── main.py
├── .env
├── .gitignore
├── docker-compose.yml
│
└── README.md
```

### 4.2. Arquivo `.env`

Crie o arquivo `.env` para armazenar as configurações:

```env
OPENMES_URL=http://localhost:8081/api/v1
OPENMES_TOKEN=SEU_TOKEN_AQUI

OPC_SERVER_URL=opc.tcp://localhost:4840
OPC_TAG_ALARME=ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.bAlarmeEmergencia

WORK_ORDER_ID=1
LINE_ID=1
```

**Importante:** O Node ID da variável OPC UA deve corresponder ao endereço efetivamente disponibilizado pelo CODESYS.

### 4.3. Arquivo `main.py`

```python
import os
import time
import requests

from dotenv import load_dotenv
from opcua import Client

# Carrega as variáveis de ambiente
load_dotenv()

OPENMES_URL = os.getenv("OPENMES_URL")
OPENMES_TOKEN = os.getenv("OPENMES_TOKEN")

OPC_SERVER_URL = os.getenv("OPC_SERVER_URL")
OPC_TAG_ALARME = os.getenv("OPC_TAG_ALARME")

WORK_ORDER_ID = int(os.getenv("WORK_ORDER_ID", 1))
LINE_ID = int(os.getenv("LINE_ID", 1))

HEADERS = {
    "Authorization": f"Bearer {OPENMES_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def bloquear_producao_no_mes():
    """Registra um Issue bloqueante no Open MES."""

    print(
        f"\n🚨 [INTEGRAÇÃO MES] "
        f"Processando bloqueio na Linha #{LINE_ID}..."
    )

    # Coloca a ordem em execução antes de registrar a ocorrência
    requests.put(
        f"{OPENMES_URL}/work-orders/{WORK_ORDER_ID}",
        json={"status": "in_progress"},
        headers=HEADERS,
        timeout=10
    )

    # Dados da ocorrência
    payload_issue = {
        "work_order_id": WORK_ORDER_ID,
        "line_id": LINE_ID,
        "issue_type_id": 5,
        "title": "Alarme Crítico de Emergência - CODESYS",
        "description": (
            "Linha paralisada via interrupção "
            "do CLP / Elipse SCADA"
        ),
        "severity": "critical",
        "is_blocking": True,
        "status": "open"
    }

    res = requests.post(
        f"{OPENMES_URL}/issues",
        json=payload_issue,
        headers=HEADERS,
        timeout=10
    )

    if res.status_code in [200, 201]:
        print(
            f"--> [SUCESSO] Ocorrência registrada "
            f"para a Ordem #{WORK_ORDER_ID}!"
        )
        return True

    print(f"--> [ERRO] Falha ao registrar bloqueio: {res.text}")
    return False


def desbloquear_producao_no_mes():
    """Solicita a restauração da Ordem de Produção."""

    print(
        f"\n✅ [INTEGRAÇÃO MES] "
        f"Restaurando Ordem #{WORK_ORDER_ID}..."
    )

    res = requests.put(
        f"{OPENMES_URL}/work-orders/{WORK_ORDER_ID}",
        json={"status": "in_progress"},
        headers=HEADERS,
        timeout=10
    )

    if res.status_code in [200, 201]:
        print(
            f"--> [SUCESSO] Ordem #{WORK_ORDER_ID} "
            "restaurada para IN_PROGRESS!"
        )
        return True

    print(f"--> [ERRO] Falha ao restaurar ordem: {res.text}")
    return False


def executar_monitoramento_opc_ua():
    """Monitora a variável de emergência via OPC UA."""

    client = Client(OPC_SERVER_URL)

    conectado = False

    try:
        print(
            f"Conectando ao servidor OPC UA: "
            f"{OPC_SERVER_URL}"
        )

        client.connect()
        conectado = True

        print("✅ Conexão OPC UA estabelecida!")

        node_alarme = client.get_node(OPC_TAG_ALARME)

        estado_alarme_anterior = False

        while True:

            alarme_atual = node_alarme.get_value()

            # Borda de subida: False -> True
            if alarme_atual and not estado_alarme_anterior:

                if bloquear_producao_no_mes():
                    estado_alarme_anterior = True

            # Borda de descida: True -> False
            elif not alarme_atual and estado_alarme_anterior:

                if desbloquear_producao_no_mes():
                    estado_alarme_anterior = False

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nMonitoramento finalizado pelo usuário.")

    except Exception as e:
        print(f"\nErro na integração: {e}")

    finally:
        if conectado:
            client.disconnect()


if __name__ == "__main__":
    executar_monitoramento_opc_ua()
```

> **Nota técnica:** Os endpoints, campos, códigos de status e identificadores utilizados no exemplo devem ser conferidos na documentação da API da versão instalada do Open MES. A criação de um Issue bloqueante não garante, por si só, que a Ordem de Produção será alterada para `BLOCKED`. Essa transição precisa estar implementada e validada no MES.

## 🏃 5. Execução do Projeto

Antes de iniciar, verifique se:

- [ ] Docker está instalado e funcionando.
- [ ] Open MES está acessível.
- [ ] Token de API está configurado no `.env`.
- [ ] CODESYS Control Win V3 está em modo Online / Run.
- [ ] Servidor OPC UA está ativo.
- [ ] Elipse SCADA está conectado ao CLP.
- [ ] Node ID da variável de emergência está correto.
- [ ] Ordem de Produção e linha estão configuradas.

### 5.1. Iniciar o Open MES

```bash
docker compose up -d
```

### 5.2. Instalar as dependências

```bash
pip install -r requirements.txt
```

Caso ainda não exista o arquivo `requirements.txt`, crie-o:

```text
requests
python-opcua
python-dotenv
```

### 5.3. Executar o middleware

No terminal, dentro da pasta do projeto:

```bash
python main.py
```

### 5.4. Testar a integração

1. Inicie o monitoramento Python.
2. Altere `GVL.bAlarmeEmergencia` para `TRUE` no CODESYS ou acione o botão de emergência no Elipse SCADA.
3. O middleware identificará a mudança de estado.
4. Uma requisição será enviada ao Open MES.
5. O sistema deverá registrar o Issue correspondente.
6. Após o reset do alarme, o middleware solicitará a restauração da Ordem de Produção.

## 📊 6. Resultado Esperado no Open MES

Quando um alarme de emergência for acionado, espera-se o seguinte comportamento:

| Componente | Resultado esperado |
|---|---|
| Elipse SCADA | Identificação do acionamento de emergência |
| CODESYS | Alteração da variável para `TRUE` |
| Middleware Python | Detecção do alarme via OPC UA |
| Open MES | Registro de uma ocorrência crítica |
| Blocking Issues | Exibição do Issue bloqueante |
| Work Orders | Atualização do estado da Ordem de Produção para `BLOCKED` |

Quando o alarme for resetado:

| Componente | Resultado esperado |
|---|---|
| CODESYS | Variável retorna para `FALSE` |
| Middleware Python | Identificação do reset |
| Open MES | Solicitação de restauração da Ordem |
| Work Orders | Retorno para `IN_PROGRESS`, conforme as regras do MES |

## 🔒 7. Segurança e Boas Práticas

Para manter a segurança e a confiabilidade da integração:

- Nunca publique tokens de API ou senhas no GitHub.
- Utilize variáveis de ambiente para informações confidenciais.
- Configure autenticação e permissões adequadas no OPC UA.
- Utilize comunicação segura em ambientes de produção.
- Implemente logs para registrar eventos e falhas.
- Valide as respostas da API antes de alterar o estado da integração.
- Implemente mecanismos para evitar o registro duplicado de ocorrências.
- Não utilize o reset de alarme como única condição para liberar uma linha: a liberação deve depender também da confirmação de segurança e das regras operacionais da planta.

### Arquivo `.gitignore`

Para evitar o envio de informações confidenciais ao GitHub:

```gitignore
.env
.venv/
venv/
__pycache__/
*.pyc
.vscode/
```

## 🎯 8. Objetivo da Solução

A integração busca conectar os níveis de automação industrial e gestão da produção, permitindo que eventos críticos identificados no chão de fábrica sejam refletidos diretamente no sistema MES.

Com essa arquitetura, é possível:

- Automatizar o registro de paradas industriais.
- Melhorar a comunicação entre CLP, supervisório e MES.
- Centralizar ocorrências e bloqueios de produção.
- Aumentar a rastreabilidade dos eventos.
- Reduzir a dependência de registros manuais.
- Facilitar o acompanhamento das Ordens de Produção.

## 📄 Licença

Este projeto está disponibilizado sob a licença **MIT**.

---

**Desenvolvido para integração de sistemas industriais, automação e gestão da produção.** 🏭
