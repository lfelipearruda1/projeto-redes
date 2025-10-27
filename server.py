# server.py
import socket, json

HOST = "0.0.0.0"
PORT = 12000
MAX_FRAME_BYTES = 4096
MAX_PAYLOAD = 4

def recv_json_line(fobj):
    line = fobj.readline()
    if not line:
        return None
    
    if len(line.encode("utf-8")) > MAX_FRAME_BYTES:
        raise ValueError("Frame maior que MAX_FRAME_BYTES")
    return json.loads(line)

def send_json(conn, obj):
    data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
    conn.sendall(data)

def checksum8(text: str) -> int:
    return sum(text.encode("utf-8")) & 0xFF

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(1)
    print(f"[SERVIDOR] Aguardando em {HOST}:{PORT} ...")

    conn, addr = srv.accept()
    print(f"[SERVIDOR] Conectado a {addr}")
    f = conn.makefile(mode="r", encoding="utf-8", newline="\n")

    try:
        hello = recv_json_line(f)
    except ValueError as e:
        print(f"[SERVIDOR] Erro no frame de handshake: {e}")
        conn.close(); srv.close(); return

    if not hello or hello.get("type") != "HELLO":
        print("[SERVIDOR] Handshake inválido ou ausente.")
        conn.close(); srv.close(); return

    mode = str(hello.get("mode", "individual")).lower()
    max_len = int(hello.get("max_len", 120))
    window = int(hello.get("window", 5))

    if max_len < 30:
        max_len = 30

    send_json(conn, {"type": "HELLO_ACK", "ok": True, "window": window, "max_len": max_len})
    print(f"[SERVIDOR] Handshake OK | mode={mode} max_len={max_len} window={window}")

    current_id = None
    partes = {}
    total_esperado = 0

    while True:
        try:
            pkt = recv_json_line(f)
        except ValueError as e:
            print(f"[SERVIDOR] Erro de frame: {e}")
            break

        if pkt is None:
            print("[SERVIDOR] Conexão encerrada pelo cliente.")
            break

        ptype = pkt.get("type")

        if ptype == "SEND_START":
            current_id = int(pkt["msg_id"])
            text_len = int(pkt["text_len"])
            partes = {}
            total_esperado = 0
            print(f"\n[RECV] SEND_START msg_id={current_id} text_len={text_len}")

        elif ptype == "DATA":
            msg_id = int(pkt["msg_id"])
            seq = int(pkt["seq"])
            total = int(pkt["total"])
            payload = str(pkt["payload"])

            if len(payload) > MAX_PAYLOAD:
                print(f"[WARN] payload > {MAX_PAYLOAD} ignorado (seq={seq})")
                continue

            if current_id != msg_id:
                current_id = msg_id
                partes = {}
                total_esperado = 0

            partes[seq] = payload
            total_esperado = max(total_esperado, total)

            csum = checksum8(payload)
            print(f"[PKT] msg_id={msg_id} seq={seq}/{total-1} "
                  f"payload_len={len(payload)} checksum={csum} payload='{payload}'")

            if mode == "individual":
                send_json(conn, {"type": "ACK", "msg_id": msg_id, "seq": seq, "status": "ok"})

            if len(partes) == total:
                texto = "".join(partes[i] for i in range(total))
                print(f"[MSG] reconstruída (msg_id={msg_id}): '{texto}'\n")

                if mode == "grupo":
                    send_json(conn, {"type": "ACK", "msg_id": msg_id, "seq": "all", "status": "ok", "total": total})

                current_id = None
                partes = {}
                total_esperado = 0

        else:
            pass

    conn.close()
    srv.close()
    print("[SERVIDOR] Encerrado.")

if __name__ == "__main__":
    main()
