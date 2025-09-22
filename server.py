import json
import socket

HOST = "127.0.0.1"
PORT = 5000
MAX_FRAME_BYTES = 4096

def checksum_bytes(data: bytes) -> int:
    return sum(data) & 0xFF

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

def main() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[SERVIDOR] Aguardando em {HOST}:{PORT} ...")

    conn, addr = srv.accept()
    fs = FramedSocket(conn)
    print(f"[SERVIDOR] Conectado a {addr}")

    hs = fs.recv_json()
    if not hs:
        conn.close(); srv.close(); return

    modo = str(hs.get("modo_operacao", "")).lower()
    tamanho_max = int(hs.get("tamanho_max", 2048))
    payload_size = int(hs.get("payload_size", 3))

    if modo not in ("individual", "grupo"):
        fs.send_json({"status": "ERRO", "motivo": "modo_operacao inválido. Use 'individual' ou 'grupo'."})
        conn.close(); srv.close(); return

    fs.send_json(
        {
            "status": "OK",
            "modo_operacao": modo,
            "tamanho_max": tamanho_max,
            "payload_size": payload_size,
            "window_size": 5,
        }
    )

    current_id = None
    total_esperado = None
    partes = {}

    while True:
        pkt = fs.recv_json(tamanho_max)
        if pkt is None:
            print("[SERVIDOR] Conexão encerrada pelo cliente.")
            break

        required = ("id_msg", "seq", "total", "payload", "checksum")
        if any(k not in pkt for k in required):
            continue

        msg_id = int(pkt["id_msg"])
        seq = int(pkt["seq"])
        total = int(pkt["total"])
        payload = str(pkt["payload"])
        recv_csum = int(pkt["checksum"])

        if current_id is None or msg_id != current_id:
            current_id = msg_id
            total_esperado = total
            partes = {}

        ok = (checksum_bytes(payload.encode("utf-8")) == recv_csum)
        sufixo = "" if ok else " (FALHA de integridade)"
        print(f"[{modo.upper()}] Pacote {seq + 1}: {payload}{sufixo}")

        partes[seq] = payload
        if len(partes) == total_esperado:
            mensagem = "".join(partes[i] for i in range(total_esperado))
            print(f"\nMensagem reconstruída: {mensagem}\n")
            fs.send_json({"tipo": "eco", "id_msg": msg_id, "texto": mensagem})
            current_id = None
            total_esperado = None
            partes = {}

    conn.close()
    srv.close()
    print("[SERVIDOR] Conexão encerrada.")

if __name__ == "__main__":
    main()
