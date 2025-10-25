# client.py
import socket, json
from itertools import count

HOST = "127.0.0.1"  
PORT = 12000
MAX_FRAME_BYTES = 4096
MAX_PAYLOAD = 4
NEGOTIATED_MAX = 120

def send_json(conn, obj):
    data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
    conn.sendall(data)

def recv_json_line(fobj):
    line = fobj.readline()
    if not line:
        return None
    return json.loads(line)

def chunk_text(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i:i+size]

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    f = sock.makefile(mode="r", encoding="utf-8", newline="\n")

    send_json(sock, {"type":"HELLO","mode":"individual","max_len":NEGOTIATED_MAX,"window":5})
    hello_ack = recv_json_line(f)
    if not hello_ack or not hello_ack.get("ok"):
        print("Handshake falhou:", hello_ack)
        sock.close(); return

    window = hello_ack.get("window")
    max_len = hello_ack.get("max_len")
    print(f"[CLIENT] Handshake OK | window={window} max_len={max_len}")

    msg_ids = count(start=1)

    while True:
        msg = input("\nDigite a mensagem (ou 'sair'): ").strip()
        if not msg:
            continue
        if msg.lower() in ("sair","encerrar","exit","quit"):
            break

        if len(msg) > max_len:
            print(f"[CLIENT] A mensagem excede max_len ({max_len}). Será truncada nesta etapa.")
            msg = msg[:max_len]

        parts = list(chunk_text(msg, MAX_PAYLOAD))
        total = len(parts)
        msg_id = next(msg_ids)

        send_json(sock, {"type":"SEND_START","msg_id":msg_id,"text_len":len(msg)})

        for seq, payload in enumerate(parts):
            send_json(sock, {
                "type":"DATA",
                "msg_id":msg_id,
                "seq":seq,
                "total":total,
                "payload":payload
            })
            ack = recv_json_line(f)
            if not ack or ack.get("type") != "ACK":
                print(f"[CLIENT] ACK ausente/inesperado para seq={seq}: {ack}")
                break
            print(f"[ACK] msg_id={ack['msg_id']} seq={ack['seq']} status={ack['status']}")

    sock.close()
    print("[CLIENT] Encerrado.")

if __name__ == "__main__":
    main()
