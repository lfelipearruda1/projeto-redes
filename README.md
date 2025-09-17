# Projeto Cliente-Servidor com Transporte Confiável na Camada de Aplicação

## 📌 Descrição
Este projeto implementa uma aplicação cliente-servidor que simula um transporte confiável de dados **na camada de aplicação**, considerando a possibilidade de perdas e erros no canal de comunicação.  
A comunicação é realizada via **sockets TCP**, mas os mecanismos de confiabilidade (checksum, número de sequência, janela, etc.) são implementados manualmente pelo protocolo da aplicação.

---

## 🎯 Objetivos
- Desenvolver um **protocolo de aplicação confiável** independente da camada de transporte.  
- Implementar envio de **mensagens segmentadas** (máx. 4 caracteres por pacote).  
- Garantir confiabilidade por meio de:
  - ✅ Soma de verificação (checksum)  
  - ✅ Temporizador e retransmissão  
  - ✅ Números de sequência  
  - ✅ Reconhecimento positivo (ACK) e negativo (NAK)  
  - ✅ Controle de janela (1 a 5 pacotes simultâneos)  
- Suportar **Go-Back-N** e **Repetição Seletiva**, configurados pelo cliente.  
- Permitir a **simulação de perdas e erros** de pacotes.  
- Exibir **metadados das mensagens e confirmações** no cliente e no servidor.  

---

## ⚙️ Funcionalidades

### 🖥️ Cliente
- Conecta-se ao servidor via **localhost** ou **IP**.  
- Realiza o **handshake inicial** trocando:
  - Modo de operação (Go-Back-N ou Selective Repeat)  
  - Tamanho máximo da mensagem  
  - Tamanho da janela inicial (até 5)  
- Divide mensagens em pacotes de até **4 caracteres** cada.  
- Envia pacotes de forma **isolada** ou em **lotes**.  
- Exibe os **metadados dos ACKs/NAKs** recebidos.  
- Pode inserir **erros determinísticos** nos pacotes.  

### 🖥️ Servidor
- Aceita conexões de clientes.  
- Recebe pacotes e valida:
  - Número de sequência  
  - Checksum  
- Pode operar em modo:
  - **Confirmação individual** (ACK/NAK por pacote)  
  - **Confirmação em grupo** (ACK por janela inteira)  
- Reconstrói a **mensagem final** a partir dos pacotes recebidos.  
- Exibe **metadados de cada pacote**.  

---

## 👨‍💻 Autores

- Bruno Mayer  
- Caio Buonora  
- Caio Melo  
- George Pessoa  
- Lucas Ramon  
- Luis Felipe Furlaneto  
- Luiz Felipe Arruda

