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
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print("Conectado ao servidor.")

    handshake = {"modo_operacao": "texto", "tamanho_max": 1024}
    client_socket.send(json.dumps(handshake).encode())

    data = client_socket.recv(1024).decode()
    handshake_confirmado = json.loads(data)
    modo = handshake_confirmado.get("modo_operacao", "texto")
    tamanho_max = handshake_confirmado.get("tamanho_max", 1024)
    print("Handshake confirmado pelo servidor:", handshake_confirmado)


    while True:
        msg = input("Digite a mensagem (ou 'sair' para encerrar): ")
        if msg.lower() == "sair":
            break
        enviar_mensagem(client_socket, msg, modo)
        response = receber_mensagem(client_socket, tamanho_max, modo)
        if response is None:
            break
        print(f"Servidor: {response}")

    client_socket.close()
    print("Conexão encerrada.")

if __name__ == "__main__":
    main()
