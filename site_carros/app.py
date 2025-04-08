from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import pandas as pd
import plotly.graph_objs as go

app = Flask(__name__)

# Login padrão
LOGIN_PADRAO = 'funcionario'
SENHA_PADRAO = '123'

# Rota de login


@app.route('/')
def login():
    return render_template('login.html')

# Autenticação


@app.route('/autenticar', methods=['POST'])
def autenticar():
    usuario = request.form['usuario']
    senha = request.form['senha']
    if usuario == LOGIN_PADRAO and senha == SENHA_PADRAO:
        return redirect(url_for('painel'))
    else:
        return render_template('login.html', erro=True)

# Painel


@app.route('/painel')
def painel():
    return render_template('painel.html')

# Cadastro


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        carro = request.form['carro']
        cpf = request.form['cpf']
        placa = request.form['placa']
        estado = "Na fila de espera"

        try:
            conexao = mysql.connector.connect(
                host='localhost',
                port=8889,
                user='root',
                password='root',
                database='teste'
            )
            cursor = conexao.cursor()
            sql = "INSERT INTO clientes (nome, carro, cpf, placa, estado) VALUES (%s, %s, %s, %s, %s)"
            valores = (nome, carro, cpf, placa, estado)
            cursor.execute(sql, valores)
            conexao.commit()
            cursor.close()
            conexao.close()
        except mysql.connector.Error as erro:
            return f"Erro ao cadastrar cliente: {erro}"

        return redirect(url_for('painel'))

    return render_template('cadastrar.html')

# Verificação


@app.route('/verificar', methods=['GET', 'POST'])
def verificar_cliente():
    resultado = None
    if request.method == 'POST':
        cpf = request.form['cpf']

        try:
            conexao = mysql.connector.connect(
                host='localhost',
                port=8889,
                user='root',
                password='root',
                database='teste'
            )
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                "SELECT nome, carro, estado FROM clientes WHERE cpf = %s", (cpf,))
            resultado = cursor.fetchone()
            cursor.close()
            conexao.close()
        except mysql.connector.Error as erro:
            return f"Erro ao consultar cliente: {erro}"

    return render_template('verificar.html', resultado=resultado)

# Atualização


@app.route('/atualizar', methods=['GET', 'POST'])
def atualizar_cliente():
    cliente = None
    mensagem = None

    if request.method == 'POST':
        if 'cpf' in request.form and 'estado' not in request.form:
            cpf = request.form['cpf']
            try:
                conexao = mysql.connector.connect(
                    host='localhost',
                    port=8889,
                    user='root',
                    password='root',
                    database='teste'
                )
                cursor = conexao.cursor(dictionary=True)
                cursor.execute("SELECT * FROM clientes WHERE cpf = %s", (cpf,))
                cliente = cursor.fetchone()
                cursor.close()
                conexao.close()
            except mysql.connector.Error as erro:
                mensagem = f"Erro ao buscar cliente: {erro}"

        elif 'cpf' in request.form and 'estado' in request.form:
            cpf = request.form['cpf']
            novo_estado = request.form['estado']
            try:
                conexao = mysql.connector.connect(
                    host='localhost',
                    port=8889,
                    user='root',
                    password='root',
                    database='teste'
                )
                cursor = conexao.cursor()
                cursor.execute(
                    "UPDATE clientes SET estado = %s WHERE cpf = %s", (novo_estado, cpf))
                conexao.commit()
                cursor.close()
                conexao.close()
                mensagem = "Situação atualizada com sucesso!"
            except mysql.connector.Error as erro:
                mensagem = f"Erro ao atualizar cliente: {erro}"

    return render_template('atualizar.html', cliente=cliente, mensagem=mensagem)

# Análise com gráficos


@app.route('/analise')
def analise():
    try:
        conexao = mysql.connector.connect(
            host='localhost',
            port=8889,
            user='root',
            password='root',
            database='teste'
        )

        df = pd.read_sql("SELECT carro, estado FROM clientes", conexao)
        conexao.close()

        # Gráfico de linha - top 3 carros
        top_carros = df['carro'].value_counts().nlargest(10)
        fig_linha = go.Figure()
        fig_linha.add_trace(go.Scatter(
            x=top_carros.index,
            y=top_carros.values,
            mode='lines+markers',
            line=dict(color='black')
        ))
        fig_linha.update_layout(title="10 Carros Mais Atendidos",
                                xaxis_title="Modelo", yaxis_title="Quantidade")
        grafico_linha = fig_linha.to_html(full_html=False)

        # Gráfico de barras - estados em espera/manutenção
        estados_filtrados = df[df['estado'].isin(
            ["Na fila de espera", "Em manutenção"])]
        contagem_estados = estados_filtrados['estado'].value_counts()

        fig_barras = go.Figure([go.Bar(
            x=contagem_estados.index,
            y=contagem_estados.values,
            marker_color=['yellow', 'black']
        )])
        fig_barras.update_layout(
            title="Veículos por Situação", xaxis_title="Situação", yaxis_title="Quantidade")
        grafico_barras = fig_barras.to_html(full_html=False)

        return render_template('analise.html', grafico_linha=grafico_linha, grafico_barras=grafico_barras)

    except Exception as e:
        return f"Erro ao gerar gráficos: {e}"


# Rodar o app
if __name__ == '__main__':
    app.run(debug=True)
