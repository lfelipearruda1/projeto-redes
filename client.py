import json
import socket
from itertools import count

HOST = "127.0.0.1"
PORT = 12000
PAYLOAD_SIZE = 3
MAX_FRAME_BYTES = 4096
ECO_TIMEOUT_SEC = 0.7

def checksum_bytes(data: bytes) -> int:
    return sum(data) & 0xFF

def chunk_text(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i : i + size]

def corrupt_checksum(csum: int) -> int:
    return (csum + 1) & 0xFF

class FramedSocket:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self._buffer = b""

    def send_json(self, obj: dict) -> None:
        data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        self.sock.sendall(data)

    def recv_json(self, max_bytes: int = MAX_FRAME_BYTES):
        while b"\n" not in self._buffer:
            chunk = self.sock.recv(max_bytes)
            if not chunk:
                return None
            self._buffer += chunk
        line, _, rest = self._buffer.partition(b"\n")
        self._buffer = rest
        try:
            return json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            return None

def yesno(prompt: str) -> bool:
    print(prompt)
    ans = input("> ").strip().lower()
    return ans in ("s", "sim", "y", "yes")

def escolher_modo() -> str:
    while True:
        print("Escolha o modo de operação: 'individual' ou 'grupo'")
        modo = input("> ").strip().lower()
        if modo in ("individual", "grupo"):
            return modo
        print("Valor inválido. Digite 'individual' ou 'grupo'.")

def escolher_erro() -> str:
    while True:
        print("Escolha o tipo de erro: 'corrompido' ou 'perdido'")
        escolha = input("> ").strip().lower()
        if escolha in ("corrompido", "perdido"):
            return escolha
        print("Valor inválido. Digite 'corrompido' ou 'perdido'.")

def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    fs = FramedSocket(sock)

    modo = escolher_modo()
    fs.send_json({
        "modo_operacao": modo,
        "tamanho_max": 2048,
        "payload_size": PAYLOAD_SIZE,
    })

    hs_resp = fs.recv_json(1024)
    if not hs_resp or hs_resp.get("status") != "OK":
        print("Falha no handshake:", hs_resp)
        sock.close()
        return

    print(f"Handshake OK. Modo: {hs_resp.get('modo_operacao')} | janela: {hs_resp.get('window_size')}")
    id_gen = count(start=1)

    while True:
        print("\nDigite sua mensagem (ou 'sair' para encerrar):")
        msg = input("> ").strip()
        if msg.lower() in ("sair", "encerrar"):
            break
        if not msg:
            continue

        erro_ativo = yesno("Quer que esta mensagem apresente erro/perda? (s/n)")
        tipo_erro = None
        if erro_ativo:
            tipo_erro = escolher_erro()

        parts = list(chunk_text(msg, PAYLOAD_SIZE))
        total = len(parts)
        msg_id = next(id_gen)

        for seq, payload in enumerate(parts):
            # Trata erro específico escolhido pelo usuário
            pacote_perdido = (tipo_erro == "perdido")
            pacote_errado = (tipo_erro == "corrompido")

            if pacote_perdido:
                print(f"[DEBUG] Pacote {seq} perdido.")
                continue  # não envia

            csum = checksum_bytes(payload.encode("utf-8"))
            if pacote_errado:
                payload = payload[::-1]  # corrompe payload
                csum = corrupt_checksum(csum)
                print(f"[DEBUG] Pacote {seq} corrompido.")

            fs.send_json({
                "id_msg": msg_id,
                "seq": seq,
                "total": total,
                "payload": payload,
                "checksum": csum,
            })

        # Espera eco do servidor
        sock.settimeout(ECO_TIMEOUT_SEC)
        try:
            _ = fs.recv_json()
        except socket.timeout:
            pass
        finally:
            sock.settimeout(None)

    sock.close()

if __name__ == "__main__":
    main()
