#pip install requests opcua2
#pip install requests
import requests
import requests

BASE_URL = "http://localhost:8081/api/v1"
API_TOKEN = "2|OJ9RSpp0jfFoQjMBE6riBfWcf2X493v6QxiL8Q2pbd31fff9"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

WORK_ORDER_ID = 1
LINE_ID = 1

def obter_tipo_issue_bloqueante():
    """Busca o ID de um tipo de Issue cadastrado no Open MES."""
    try:
        res = requests.get(f"{BASE_URL}/issue-types", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            tipos = res.json().get("data", [])
            for t in tipos:
                # Procura preferencialmente um tipo marcado como bloqueante
                if t.get("is_blocking") or t.get("blocks_production"):
                    return t.get("id")
            if tipos:
                return tipos[0].get("id")
    except Exception:
        pass
    return 1

def executar_bloqueio_linha():
    print("=== 1. PASSANDO A ORDEM PARA EM EXECUÇÃO (in_progress) ===")
    
    # 1. Altera o status da ordem de 'Accepted' para 'in_progress'
    res_status = requests.put(
        f"{BASE_URL}/work-orders/{WORK_ORDER_ID}",
        json={"status": "in_progress"},
        headers=HEADERS
    )
    print(f"Status em Execução: HTTP {res_status.status_code}")

    print("\n=== 2. DISPARANDO ISSUE BLOQUEANTE DE EMERGÊNCIA ===")
    issue_type_id = obter_tipo_issue_bloqueante()

    payload_blocking_issue = {
        "work_order_id": WORK_ORDER_ID,
        "line_id": LINE_ID,
        "issue_type_id": issue_type_id,
        "title": "Alarme Crítico de Emergência - CODESYS",
        "description": "Linha paralisada via interrupção do CLP/Elipse SCADA",
        "severity": "critical",
        "is_blocking": True,  # Força a ida para 'Blocking issues'
        "status": "open"
    }

    res_issue = requests.post(f"{BASE_URL}/issues", json=payload_blocking_issue, headers=HEADERS)
    print(f"POST /issues -> HTTP {res_issue.status_code}")
    print(f"Resposta: {res_issue.text}")

    print("\n=== 3. APLICANDO PAUSA NA ORDEM ===")
    res_pause = requests.put(
        f"{BASE_URL}/work-orders/{WORK_ORDER_ID}",
        json={"status": "paused"},
        headers=HEADERS
    )
    if res_pause.status_code == 405:
        res_pause = requests.patch(
            f"{BASE_URL}/work-orders/{WORK_ORDER_ID}",
            json={"status": "paused"},
            headers=HEADERS
        )
    print(f"Status Pausado: HTTP {res_pause.status_code}")

if __name__ == "__main__":
    executar_bloqueio_linha()