import socket, json
from itertools import count

HOST = "127.0.0.1"
PORT = 12000
MAX_FRAME_BYTES = 4096
MAX_PAYLOAD = 4
NEGOTIATED_MAX = 120
MIN_MESSAGE_LEN = 30

def send_json(conn, obj):
    data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
    if len(data) > MAX_FRAME_BYTES:
        return
    conn.sendall(data)

def recv_json_line(fobj):
    line = fobj.readline()
    if not line:
        return None
    if len(line.encode("utf-8")) > MAX_FRAME_BYTES:
        return None
    return json.loads(line)

def chunk_text(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i+size]

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    f = sock.makefile(mode="r", encoding="utf-8", newline="\n")

    desired_mode = "individual"

    send_json(sock, {"type": "HELLO", "mode": desired_mode, "max_len": NEGOTIATED_MAX, "window": 5})
    hello_ack = recv_json_line(f)
    if not hello_ack or not hello_ack.get("ok"):
        sock.close(); return

    window = int(hello_ack.get("window"))
    max_len = max(30, int(hello_ack.get("max_len")))
    mode = desired_mode

    msg_ids = count(start=1)

    while True:
        msg = input("\nMensagem (ou sair): ").strip()
        if msg.lower() in ("sair", "encerrar", "exit", "quit"):
            break
        if len(msg) < MIN_MESSAGE_LEN:
            print(f"Mínimo {MIN_MESSAGE_LEN} caracteres.")
            continue
        if len(msg) > max_len:
            msg = msg[:max_len]

        parts = list(chunk_text(msg, MAX_PAYLOAD))
        total = len(parts)
        msg_id = next(msg_ids)

        send_json(sock, {"type": "SEND_START", "msg_id": msg_id, "text_len": len(msg)})
        resp = recv_json_line(f)
        if not resp or resp.get("type") != "START_OK":
            print(f"Recusado pelo servidor: {resp}")
            continue

        if mode == "individual":
            for seq, payload in enumerate(parts):
                send_json(sock, {"type": "DATA", "msg_id": msg_id, "seq": seq, "total": total, "payload": payload})
                ack = recv_json_line(f)
                if ack:
                    print(f"ACK seq={ack.get('seq')}")
        else:
            for seq, payload in enumerate(parts):
                send_json(sock, {"type": "DATA", "msg_id": msg_id, "seq": seq, "total": total, "payload": payload})
            ack = recv_json_line(f)
            print(f"ACK final: {ack}")

    sock.close()

if __name__ == "__main__":
    main()
