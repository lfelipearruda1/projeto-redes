import socket, json

HOST = "0.0.0.0"
PORT = 12000
MAX_FRAME_BYTES = 4096
MAX_PAYLOAD = 4
MIN_MESSAGE_LEN = 30

def recv_json_line(fobj):
    line = fobj.readline()
    if not line:
        return None
    if len(line.encode("utf-8")) > MAX_FRAME_BYTES:
        return None
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
    conn, addr = srv.accept()
    f = conn.makefile(mode="r", encoding="utf-8", newline="\n")

    hello = recv_json_line(f)
    if not hello or hello.get("type") != "HELLO":
        conn.close(); srv.close(); return

    mode = str(hello.get("mode", "individual")).lower()
    max_len = int(hello.get("max_len", 120))
    window = int(hello.get("window", 5))
    if max_len < 30:
        max_len = 30

    send_json(conn, {"type": "HELLO_ACK", "ok": True, "window": window, "max_len": max_len})

    current_id = None
    partes = {}
    total_esperado = 0

    while True:
        pkt = recv_json_line(f)
        if pkt is None:
            break

        if pkt.get("type") == "SEND_START":
            msg_id = int(pkt["msg_id"])
            text_len = int(pkt["text_len"])
            if text_len < MIN_MESSAGE_LEN:
                send_json(conn, {"type": "REJECT", "msg_id": msg_id, "reason": "min_len", "min": MIN_MESSAGE_LEN})
                continue
            if text_len > max_len:
                send_json(conn, {"type": "REJECT", "msg_id": msg_id, "reason": "max_len", "max": max_len})
                continue
            current_id = msg_id
            partes = {}
            total_esperado = 0
            send_json(conn, {"type": "START_OK", "msg_id": msg_id})

        elif pkt.get("type") == "DATA":
            if current_id is None:
                continue
            msg_id = int(pkt["msg_id"])
            if msg_id != current_id:
                continue
            seq = int(pkt["seq"])
            total = int(pkt["total"])
            payload = str(pkt["payload"])
            if len(payload) > MAX_PAYLOAD:
                continue
            partes[seq] = payload
            total_esperado = max(total_esperado, total)
            if mode == "individual":
                send_json(conn, {"type": "ACK", "msg_id": msg_id, "seq": seq, "status": "ok"})
            if len(partes) == total:
                texto = "".join(partes[i] for i in range(total))
                if mode == "grupo":
                    send_json(conn, {"type": "ACK", "msg_id": msg_id, "seq": "all", "status": "ok", "total": total})
                current_id = None
                partes = {}
                total_esperado = 0

    conn.close()
    srv.close()

if __name__ == "__main__":
    main()
