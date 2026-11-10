# Integracao_sistemas
🏭 Integração Industrial: Elipse SCADA $\leftrightarrow$ CODESYS $\leftrightarrow$ Open MESEste repositório contém a documentação e os scripts de integração para automatizar o bloqueio de linhas de produção no Open MES a partir de alarmes de emergência oriundos do CODESYS (CLP) e supervisionados pelo Elipse SCADA / E3.📐 Fluxo da Arquitetura  ┌─────────────────┐       ┌─────────────────┐       ┌──────────────────────┐       ┌─────────────────┐
  │  Elipse SCADA   │ <───> │  CODESYS (CLP)  │ ───>  │  Python Integration  │ ───>  │    Open MES     │
  │  (Supervisório) │       │ (SoftPLC / V3)  │ OPC UA│      Middleware      │ REST │  (Docker / MES) │
  └─────────────────┘       └─────────────────┘       └──────────────────────┘       └─────────────────┘
Elipse SCADA / E3: Atua como IHM/Supervisório de operação da planta.CODESYS (Control Win V3): Executa a lógica do CLP e expõe as variáveis globais (GVL) via servidor OPC UA.Middleware Python: Escuta a tag de alarme OPC UA e dispara requisições HTTP REST com autenticação Bearer Token para a API do Open MES.Open MES: Recebe a requisição, gera um Issue bloqueante e altera o estado da Ordem de Produção ativa para BLOCKED.🛠️ Pré-requisitos e DependênciasSoftwares NecessáriosDocker e Docker ComposeCODESYS Development System V3.5 (com CODESYS Control Win V3 instalado)Elipse SCADA ou Elipse E3Python 3.9+Bibliotecas PythonInstale as dependências executando no terminal:pip install requests opcua python-dotenv
🐳 1. Instalação e Execução do Open MES via DockerDe acordo com a documentação oficial do Open MES, siga os passos abaixo para subir a aplicação em ambiente local:Passo 1.1: Criar a pasta do projeto e o docker-compose.ymlCrie um diretório para o Open MES e adicione o arquivo docker-compose.yml:version: '3.8'

services:
  openmes-app:
    image: openmes/openmes:latest
    container_name: openmes_app
    restart: always
    ports:
      - "8081:80"
    environment:
      - APP_ENV=production
      - APP_KEY=base64:Xv9N7xKzQ2W4M8pP0lR5tY1uV3wX6yZ7aB8c9d0e1f2=
      - DB_CONNECTION=sqlite
    volumes:
      - openmes_data:/var/www/html/storage

volumes:
  openmes_data:
Passo 1.2: Subir o containerNo terminal da pasta onde criou o arquivo, execute:docker compose up -d
Passo 1.3: Acessar o sistemaApós alguns segundos, acesse o painel no navegador:URL: http://localhost:8081Usuário padrão: admin@example.comSenha padrão: admin🔑 2. Como Obter o Token de API no Open MESO middleware Python utiliza um Bearer Token para autenticar as chamadas REST.Acesse o painel do Open MES (http://localhost:8081).No menu lateral esquerdo, vá em Settings (Configurações) $\rightarrow$ API Tokens (ou acesse diretamente http://localhost:8081/admin/tokens).Clique no botão Create Token / Novo Token.Defina um nome para o token (ex: Integracao_Python) e confirme.Copie o token gerado (exemplo: 2|OJ9RSpp0jfFoQjMBE6riBfWcf2X493v6QxiL8Q2pbd31fff9).⚠️ Atenção: Guarde esta chave, pois ela não será exibida novamente no painel.⚙️ 3. Configuração do CODESYS e Elipse SCADAConfiguração no CODESYS (Servidor OPC UA)Crie uma Global Variable List (GVL) chamada GVL no seu projeto CODESYS:VAR_GLOBAL
    bAlarmeEmergencia : BOOL := FALSE; (* TRUE = Parada ativada *)
    nPeçasProduzidas  : DINT := 0;     (* Contador de peças *)
END_VAR
Clique com o botão direito na aplicação $\rightarrow$ Add Object $\rightarrow$ Symbol Configuration.Clique em Build para compilar e carregar os símbolos.Na árvore do Symbol Configuration, selecione a GVL e marque a variável bAlarmeEmergencia garantindo permissão de Read/Write (Leitura e Escrita).Inicie o CODESYS Control Win V3 e faça o Download/Online do programa. O servidor OPC UA ficará ativo no endereço:
opc.tcp://localhost:4840Configuração no Elipse SCADA / E3Adicione o Driver OPC UA ou Driver Modbus/CODESYS na aplicação Elipse.Mapeie o botão de emergência da IHM para alterar o valor da variável física ou lógica associada à GVL.bAlarmeEmergencia no CODESYS.Quando o operador acionar o botão no Elipse, ele definirá GVL.bAlarmeEmergencia = TRUE no CLP.💻 4. Estrutura do Módulo de Integração em PythonCrie os arquivos abaixo na sua pasta de desenvolvimento:📄 .env (Configurações de Ambiente)OPENMES_URL=http://localhost:8081/api/v1
OPENMES_TOKEN=2|OJ9RSpp0jfFoQjMBE6riBfWcf2X493v6QxiL8Q2pbd31fff9
OPC_SERVER_URL=opc.tcp://localhost:4840
OPC_TAG_ALARME=ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL.bAlarmeEmergencia
WORK_ORDER_ID=1
LINE_ID=1
📄 main.py (Script Principal)import os
import time
import requests
from dotenv import load_dotenv
from opcua import Client

# Carrega as variáveis de ambiente
load_dotenv()

OPENMES_URL = os.getenv("OPENMES_URL", "http://localhost:8081/api/v1")
OPENMES_TOKEN = os.getenv("OPENMES_TOKEN")
OPC_SERVER_URL = os.getenv("OPC_SERVER_URL", "opc.tcp://localhost:4840")
OPC_TAG_ALARME = os.getenv("OPC_TAG_ALARME")
WORK_ORDER_ID = int(os.getenv("WORK_ORDER_ID", 1))
LINE_ID = int(os.getenv("LINE_ID", 1))

HEADERS = {
    "Authorization": f"Bearer {OPENMES_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class OpenMesEngine:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def bloquear_producao(self, order_id, line_id, titulo, descricao):
        """Dispara um Issue bloqueante no Open MES e altera o status para BLOCKED."""
        print(f"\n🚨 [MES Engine] Enviando parada de emergência da Ordem #{order_id}...")
        
        # Garante que a ordem esteja em execução
        requests.put(
            f"{self.base_url}/work-orders/{order_id}",
            json={"status": "in_progress"},
            headers=self.headers,
            timeout=5
        )

        # Registra o Issue Bloqueante (id 5: PROCESS_CLARIFICATION com is_blocking: True)
        payload = {
            "work_order_id": order_id,
            "line_id": line_id,
            "issue_type_id": 5,
            "title": titulo,
            "description": descricao,
            "severity": "critical",
            "is_blocking": True,
            "status": "open"
        }
        
        res = requests.post(f"{self.base_url}/issues", json=payload, headers=self.headers, timeout=5)
        
        if res.status_code in [200, 201]:
            print(f"--> [SUCESSO] Ordem #{order_id} BLOQUEADA no Open MES!")
            return True
        else:
            print(f"--> [ERRO] Falha ao registrar issue: {res.text}")
            return False

    def desbloquear_producao(self, order_id):
        """Restaura o status da ordem para IN_PROGRESS no Open MES."""
        print(f"\n✅ [MES Engine] Normalizando Ordem #{order_id}...")
        res = requests.put(
            f"{self.base_url}/work-orders/{order_id}",
            json={"status": "in_progress"},
            headers=self.headers,
            timeout=5
        )
        if res.status_code in [200, 201]:
            print(f"--> [SUCESSO] Ordem #{order_id} liberada para IN_PROGRESS!")
            return True
        return False

def monitorar_opc_ua():
    engine = OpenMesEngine(OPENMES_URL, HEADERS)
    client = Client(OPC_SERVER_URL)

    try:
        print(f"Conectando ao Servidor OPC UA ({OPC_SERVER_URL})...")
        client.connect()
        print("✅ Conectado ao OPC UA do CODESYS / Elipse!")

        node_alarme = client.get_node(OPC_TAG_ALARME)
        alarme_anterior = False

        while True:
            # Leitura do valor atual no CLP ($t = 0.5\text{s}$)
            alarme_atual = node_alarme.get_value()

            # Borda de subida: Alarme acionado no CODESYS (False -> True)
            if alarme_atual and not alarme_anterior:
                print("\n⚠️ ALARME DETECTADO NO CLP!")
                engine.bloquear_producao(
                    order_id=WORK_ORDER_ID,
                    line_id=LINE_ID,
                    titulo="Alarme de Emergência - CODESYS",
                    descricao="Botão de Emergência acionado na planta / Elipse SCADA"
                )
                alarme_anterior = True

            # Borda de descida: Alarme resetado no CODESYS (True -> False)
            elif not alarme_atual and alarme_anterior:
                print("\n✅ ALARME RESETADO NO CLP!")
                engine.desbloquear_producao(order_id=WORK_ORDER_ID)
                alarme_anterior = False

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nEncerrando monitoramento.")
    except Exception as e:
        print(f"\n[ERRO OPC UA]: {e}")
    finally:
        try:
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    monitorar_opc_ua()
🚀 5. Execução do Projeto CompletoInicie a pilha Docker:docker compose up -d
Abra o CODESYS Control Win V3 e coloque a aplicação em Run.Abra o Elipse SCADA e inicie o modo de execução (Run).Execute o script de integração em Python:python main.py
Teste de Parada:Simule ou force um alarme no Elipse/CODESYS mudando bAlarmeEmergencia para TRUE.Observe o log no terminal indicando o envio do Issue.Atualize o painel de Work Orders (http://localhost:8081/admin/work-orders) no Open MES para ver a Ordem com o selo vermelho Blocked.
