import os
import re
from time import sleep
import sqlite3
from datetime import datetime
from sys import exit


# Conexão com o banco de dados
conn = sqlite3.connect("banco.db")
cursor = conn.cursor()

# Usuários
cursor.execute ("")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT UNIQUE NOT NULL,
    nome TEXT,
    saldo REAL DEFAULT 0,
    senha TEXT NOT NULL,
    investimentos REAL DEFAULT 0
);
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS investimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf_investidor TEXT NOT NULL,
        tipo_investimento TEXT NOT NULL,
        valor_final REAL NOT NULL,
        valor_investido REAL NOT NULL,
        data_hora TEXT NOT NULL,
        FOREIGN KEY (cpf_investidor) REFERENCES usuarios(cpf)
    );
""")

# Transações
cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf_origem TEXT,
    cpf_destino TEXT,
    valor REAL,
    tipo TEXT,
    data_hora TEXT,
    FOREIGN KEY (cpf_origem) REFERENCES usuarios(cpf),
    FOREIGN KEY (cpf_destino) REFERENCES usuarios(cpf)
);
""")

conn.commit()

# 
def limpar_tela():
    os.system("cls")

def menu():
    limpar_tela()
    print("1 - Entrar")
    print("2 - Criar conta")
    print("4 - Sair")
    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        entrar()
    elif opcao == "2":
        criar_conta()
    elif opcao == "4":
        print("Encerrando o programa...")
        conn.close()
        exit()
    else:
        print("Opção inválida. Tente novamente.")
        menu()

def criar_conta():
    limpar_tela()
    print("--- Criar Conta ---")

    cpf = input("Digite o CPF (somente números): ").strip()
    cursor.execute("SELECT * FROM usuarios WHERE cpf = ?", (cpf,))

    if cursor.fetchone():
        print("CPF já cadastrado.")
        return

    nome = input("Digite seu nome: ").strip()
    senha = input("Crie uma senha (mínimo 8 caracteres, 1 número, 1 maiúscula): ").strip()

    if not re.fullmatch(r'^(?=.*[A-Z])(?=.*\d).{8,}$', senha):
        print("Senha inválida.")
        return

    cursor.execute("INSERT INTO usuarios (cpf, nome, senha) VALUES (?, ?, ?)", (cpf, nome, senha))
    conn.commit()

    print("Conta criada com sucesso!")
    sleep(2)
    menu()

def entrar():
    limpar_tela()
    print("--- Entrar ---")

    cpf = input("Digite seu CPF: ").strip()
    senha = input("Digite sua senha: ").strip()

    cursor.execute("SELECT * FROM usuarios WHERE cpf = ? AND senha = ?", (cpf, senha))
    usuario = cursor.fetchone()

    if usuario:
        print(f"Bem-vindo(a), {usuario[2]}!")
        menu_usuario(cpf)
    else:
        print("CPF ou senha inválidos.")
        sleep(2)
        menu()

def menu_usuario(cpf):
    while True:
        limpar_tela()
        print("1 - Consultar Saldo")
        print("2 - Adicionar Saldo")
        print("3 - Realizar Transferência")
        print("4 - Histórico de Transações")
        print("5 - Investimentos")
        print("6 - Resumo da Conta")
        print("7 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            consultar_saldo(cpf)
        elif opcao == "2":
            adicionar_saldo(cpf)
        elif opcao == "3":
            realizar_transferencia(cpf)
        elif opcao == "4":
            historico_transacoes(cpf)
        elif opcao == "5":
            investimentos(cpf)
        elif opcao == "6":
            resumo_conta(cpf)
        elif opcao == "7":
            menu()
        else:
            print("Opção inválida.")
            sleep(2)

def consultar_saldo(cpf):
    cursor.execute("SELECT saldo FROM usuarios WHERE cpf = ?", (cpf,))
    saldo = cursor.fetchone()[0]
    print(f"Seu saldo atual é: R${saldo:.2f}")
    input("Pressione Enter para voltar.")

def adicionar_saldo(cpf):
    valor = float(input("Digite o valor para adicionar: "))
    if valor <= 0:
        print("Valor inválido.")
        return

    cursor.execute("UPDATE usuarios SET saldo = saldo + ? WHERE cpf = ?", (valor, cpf))
    conn.commit()
    print(f"R${valor:.2f} adicionados com sucesso.")
    sleep(2)

def realizar_transferencia(cpf_origem):
    cpf_destino = input("Digite o CPF do destinatário: ").strip()
    valor = float(input("Digite o valor a transferir: "))

    if valor <= 0:
        print("Valor inválido.")
        return

    cursor.execute("SELECT saldo FROM usuarios WHERE cpf = ?", (cpf_origem,))
    saldo_origem = cursor.fetchone()[0]

    if saldo_origem < valor:
        print("Saldo insuficiente.")
        return

    cursor.execute("SELECT * FROM usuarios WHERE cpf = ?", (cpf_destino,))
    if not cursor.fetchone():
        print("CPF do destinatário não encontrado.")
        return

    cursor.execute("UPDATE usuarios SET saldo = saldo - ? WHERE cpf = ?", (valor, cpf_origem))
    cursor.execute("UPDATE usuarios SET saldo = saldo + ? WHERE cpf = ?", (valor, cpf_destino))

    cursor.execute("INSERT INTO transacoes (cpf_origem, cpf_destino, valor, tipo, data_hora) VALUES (?, ?, ?, ?, ?)",
                   (cpf_origem, cpf_destino, valor, "Transferência", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

    print("Transferência realizada com sucesso.")
    sleep(2)

def historico_transacoes(cpf):
    cursor.execute("SELECT * FROM transacoes WHERE cpf_origem = ? OR cpf_destino = ?", (cpf, cpf))
    transacoes = cursor.fetchall()

    if not transacoes:
        print("Nenhuma transação encontrada.")
    else:
        for transacao in transacoes:
            tipo = "Enviado" if transacao[1] == cpf else "Recebido"
            print(f"{tipo}: R${transacao[3]:.2f} | {transacao[5]} | Destino: {transacao[2]}")

    input("Pressione Enter para voltar.")

def investimentos(cpf):
    print("--- Investimentos ---")
    print("1 - Realizar investimento")
    print("2 - Cancelar investimento")
    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        valor_investimento = float(input("Digite o valor para investir: "))

        cursor.execute("SELECT saldo FROM usuarios WHERE cpf = ?", (cpf,))
        saldo = cursor.fetchone()[0]

        if valor_investimento <= 0 or valor_investimento > saldo:
            print("Saldo insuficiente ou valor inválido.")
            print("Preciose 'ENTER' para retornar.")
            input()
            return

        print("Escolha uma opção de investimento:")
        print("1 - Curto Prazo\n2 - Médio Prazo\n3 - Longo Prazo")
        opcao_inv = int(input())

        if opcao_inv == 1:
            print("Escolha o prazo:\n1 - 30 Dias\n2 - 60 Dias\n3 - 180 Dias")
            prazo = int(input())
            dias, taxa_cdi, = (30, 0.9) if prazo == 1 else (60, 0.95) if prazo == 2 else (180, 1.0)
            tipo_investimento = "Curto Prazo"
            
        elif opcao_inv == 2:
            print("Escolha o prazo:\n1 - 1 Ano\n2 - 2 Anos")
            prazo = int(input())
            dias, taxa_cdi = (365, 1.1) if prazo == 1 else (730, 1.2)
            tipo_investimento = "Médio Prazo"
        elif opcao_inv == 3:
            print("Escolha o prazo:\n1 - 3 Anos\n2 - 5 Anos")
            prazo = int(input())
            dias, taxa_cdi = (1095, 1.25) if prazo == 1 else (1825, 1.5)
            tipo_investimento = "Longo Prazo"
        else:
            print("Opção inválida.")
            return

        cdi_anual = 13.65 / 100
        rendimento = valor_investimento * ((1 + (cdi_anual * taxa_cdi)) ** (dias / 365) - 1)
        valor_final = valor_investimento + rendimento

        cursor.execute("UPDATE usuarios SET saldo = saldo - ? WHERE cpf = ?", (valor_investimento, cpf))
        cursor.execute("""
            INSERT INTO investimentos (cpf_investidor, tipo_investimento, valor_final, valor_investido, data_hora) 
            VALUES (?, ?, ?, ?, ?)
        """, (cpf, tipo_investimento, valor_final, valor_investimento, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        print(f"Investimento de R${valor_investimento:.2f} realizado com sucesso. Valor ao final do prazo: R${valor_final:.2f}.")
        sleep(2)
    elif opcao == "2":
        print("Cancelamento de investimento ainda não implementado.")
    else:
        print("Opção inválida.")

def resumo_conta(cpf_usuario):
    cursor.execute("SELECT * FROM usuarios WHERE cpf = ?", (cpf_usuario,))
    usuario = cursor.fetchone()

    if not usuario:
        print("Usuário não encontrado.")
        return

    print(f"CPF: {usuario[1]}")
    print(f"Nome: {usuario[2]}")
    print(f"Saldo: R${usuario[3]:.2f}")
    historico_transacoes(cpf_usuario)

    cursor.execute("""
        SELECT tipo_investimento, valor_investido, valor_final, data_hora 
        FROM investimentos 
        WHERE cpf_investidor = ?
    """, (cpf_usuario,))
    investimentos = cursor.fetchall()

    if investimentos:
        print("\n--- Investimentos ---")
        for i, inv in enumerate(investimentos, start=1):
            tipo, valor_investido, valor_final, data_hora = inv
            print(f"\nInvestimento #{i}:")
            print(f"  Tipo: {tipo}")
            print(f"  Valor Investido: R$ {valor_investido:.2f}")
            print(f"  Valor Final (Estimado): R$ {valor_final:.2f}")
            print(f"  Data: {data_hora}")
    else:
        print("\nNenhum investimento encontrado.")

menu()
