import socket
import json

HOST = '127.0.0.1'
PORT = 5000

def receber_mensagem(conn, tamanho_max, modo):
    data = conn.recv(tamanho_max)
    if not data:
        return None
    if modo == "texto":
        return data.decode()
    elif modo == "binario":
        return data
    else:
        return None

def enviar_mensagem(conn, msg, modo):
    if modo == "texto":
        conn.send(msg.encode())
    elif modo == "binario":
        conn.send(msg)
        
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print("Servidor aguardando conexão...")

    conn, addr = server_socket.accept()
    print(f"Conectado a {addr}")

    data = conn.recv(1024).decode()
    handshake = json.loads(data)
    modo = handshake.get("modo_operacao", "texto")
    tamanho_max = handshake.get("tamanho_max", 1024)
    print("Handshake recebido:", handshake)

    response = {"status": "OK", "modo_operacao": modo, "tamanho_max": tamanho_max}
    conn.send(json.dumps(response).encode())
    print("Handshake confirmado.")

    while True:
        msg = receber_mensagem(conn, tamanho_max, modo)
        if msg is None:
            break
        print(f"Mensagem do cliente ({modo}):", msg)
        enviar_mensagem(conn, f"Servidor recebeu: {msg}", modo)

    conn.close()
    server_socket.close()
    print("Conexão encerrada.")

if __name__ == "__main__":
    main()
