import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time
import pandas as pd


# Função para conectar ao banco de dados e verificar as credenciais do usuário
def login(usuario, senha):
    conexao = None
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        if conexao.is_connected():
            cursor = conexao.cursor()
            query = "SELECT login, senha, tipo FROM solicitantes WHERE login = %s AND senha = %s"
            cursor.execute(query, (usuario, senha))
            result = cursor.fetchone()

            if result:
                return True, result[2]
            else:
                return False, ""
    except Error as e:
        print("Erro ao conectar ao MySQL", e)
        return False, ""
    finally:
        if conexao and conexao.is_connected():
            conexao.close()

# Função para pegar usuários únicos
def pegar_valores_unicos():
    conexao = None 
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        if conexao.is_connected():
            cursor = conexao.cursor()
            query = "SELECT DISTINCT nome FROM dados"
            cursor.execute(query)
            valores_unicos = cursor.fetchall()
            return [valor[0] for valor in valores_unicos] 
    except Error as e:
        print("Erro ao conectar ao MySQL", e)
        return []
    finally:
        if conexao and conexao.is_connected():
            cursor.close()  
            conexao.close()

# Função para inserir solicitação
def inserir_solicitacao(solicitante, data, colaborador, cc, data_inicio, data_termino, diarias, observacao, data_pag, banco_pag):
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        if conexao.is_connected():
            cursor = conexao.cursor()
            # Obter o valor_diaria do colaborador da tabela dados
            query_valor = "SELECT valor_diaria FROM dados WHERE nome = %s"
            cursor.execute(query_valor, (colaborador,))
            resultado = cursor.fetchone()

            # Se o valor_diaria foi encontrado, use-o; senão, use 0 como valor padrão
            valor_diaria = resultado[0] if resultado else 0

            # Calcular o valor_total
            valor_total = diarias * valor_diaria
            
            # Inserir os dados na tabela adiantamento
            query_inserir = """INSERT INTO adiantamento (solicitante, data, colaborador, cc, data_inicio, data_termino, diarias, valor_diaria, valor_total, observacao, data_pagamento, banco_pagamento)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query_inserir, (solicitante, data, colaborador, cc, data_inicio, data_termino, diarias, valor_diaria, valor_total, observacao, data_pag, banco_pag))
            conexao.commit()
            
            # Captura o ID da última inserção para usar no histórico
            id_adiantamento = cursor.lastrowid

            # Registrar no histórico
            detalhes_alteracao = "Solicitação"
            tipo_operacao = "Inserção"
            usuario = st.session_state['usuario']  # Asumindo que o usuário logado é acessível através de st.session_state['usuario']
            registrar_historico(id_adiantamento, usuario, tipo_operacao, detalhes_alteracao)

            return True
    except Error as e:
        print("Erro ao conectar ao MySQL", e)
        return False
    finally:
        if conexao.is_connected():
            cursor.close()
            conexao.close()

# Buscar solicitações
def buscar_solicitacoes(solicitante=None, colaborador=None):
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        query = "SELECT * FROM adiantamento"
        conditions = []
        if solicitante:
            conditions.append(f"solicitante = '{solicitante}'")
        if colaborador:
            conditions.append(f"colaborador = '{colaborador}'")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        df_solicitacoes = pd.read_sql(query, conexao)
        return df_solicitacoes
    except Error as e:
        print("Erro ao buscar as solicitações:", e)
        return pd.DataFrame()  # Retorna um dataframe vazio em caso de erro
    finally:
        if conexao.is_connected():
            conexao.close()

# Buscar solicitantes
def buscar_solicitantes():
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway'
        )
        cursor = conexao.cursor()
        cursor.execute("SELECT DISTINCT solicitante FROM adiantamento")
        solicitantes = cursor.fetchall()
        return [s[0] for s in solicitantes]
    finally:
        conexao.close()

# Buscar colaboradores
def buscar_colaboradores():
    try:
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway'
        )
        cursor = conexao.cursor()
        cursor.execute("SELECT DISTINCT colaborador FROM adiantamento")
        colaboradores = cursor.fetchall()
        return [c[0] for c in colaboradores]
    finally:
        conexao.close()

# Regitra histórico
def registrar_historico(id_adiantamento, usuario, tipo_operacao, detalhes_alteracao):
    try:
        # Criando uma nova conexão dentro da função
        conexao = mysql.connector.connect(
            host='viaduct.proxy.rlwy.net',
            user='root',
            port=58278,
            password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
            database='railway',
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = conexao.cursor()
        query = """
        INSERT INTO historico (id_adiantamento, usuario, tipo_operacao, detalhes_alteracao, data_hora)
        VALUES (%s, %s, %s, %s, %s)
        """
        # A data e hora são definidas no momento da inserção pelo MySQL
        data_hora = datetime.now()
        cursor.execute(query, (id_adiantamento, usuario, tipo_operacao, detalhes_alteracao, data_hora))
        conexao.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao registrar histórico: {e}")
    finally:
        if conexao.is_connected():
            cursor.close()
            conexao.close()

# Busca historico
def buscar_historico():
    conexao = mysql.connector.connect(
        host='viaduct.proxy.rlwy.net',
        user='root',
        port=58278,
        password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
        database='railway',
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )
    query = "SELECT * FROM historico ORDER BY data_hora DESC"
    df_historico = pd.read_sql(query, conexao)
    conexao.close()
    return df_historico

# DEFINIÇÃO DE LISTAS #
centro_custos = ['Bahia FSA', 'Ipubi', 'Paraíba', 'Russas', 'Sul']
tipo_adiantamento = ['Diária']
usuarios_unicos = pegar_valores_unicos()
periodos_adian = ['3/3 (100%)','2/3 (66%)','1/3 (33%)']
bancos_pagamento = ['','Itaú OP Matriz','Itaú OPEX','Itaú Prestadora']

# Inicialização de variáveis de sessão
if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
    st.session_state['usuario'] = ""
    st.session_state['tipo_usuario'] = ""

# Tela de login
if not st.session_state['login_status']:

    st.title(':blue[Sistema de Gestão de Viagem]')
    st.markdown('Sistema criado para gerir solicitações de adiantamento para viagens')

    st.sidebar.title("Login 🔐")
    usuario = st.sidebar.text_input("Usuário")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Login"):
        status, tipo_usuario = login(usuario, senha)
        if status:
            st.session_state['login_status'] = True
            st.session_state['usuario'] = usuario
            st.session_state['tipo_usuario'] = tipo_usuario
            st.experimental_rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos")

# Exibir conteúdo com base no tipo de usuário
if st.session_state['login_status']:

# ============= TELA DO ADMIN =============== #    
    if st.session_state['tipo_usuario'] == 'admin':
        
        # ==== Radio itens das opções ===== #
        st.sidebar.title("Administrador")
        admin_opcao = st.sidebar.radio(
            "Escolha uma opção:",
            ('Inserir Solicitação', 'Ajustar Solicitação', 'Ver Histórico de Ajustes')
        )
        
        # ====== Inserir Solicitação ======= #
        if admin_opcao == 'Inserir Solicitação':
            st.header("Inserir Solicitação de Adiantamento 💵")

            colaborador_sol = st.selectbox('Escolha o Colaborador', usuarios_unicos)

            col1, col2, col3 = st.columns(3)
            centro_custo_sol = col1.selectbox('Escolha o Centro de Custo', centro_custos)
            tipo_sol = col2.selectbox('Escolha o tipo', tipo_adiantamento)
            banco_pag = col3.selectbox('Escolha o Banco de Pagamento', bancos_pagamento)

            col1, col2 = st.columns(2)
            data_ini_sol = col1.date_input('Data inicial')
            data_fim_sol = col2.date_input('Data término')

            # Verificação se a data final é menor que a data inicial
            if data_fim_sol < data_ini_sol:
                st.error("Erro: A data final não pode ser menor que a data inicial.")
            else:
                # Continua com o restante do seu código apenas se a data final for maior ou igual à data inicial
                dif_dias = (data_fim_sol - data_ini_sol).days-1

                col1, col2 = st.columns(2)
                periodo_ini_sol = col1.selectbox('Período de Início', periodos_adian)
                periodo_fim_sol = col2.selectbox('Período de Término', periodos_adian)

                # Cálculo das diárias
                if periodo_ini_sol == '3/3 (100%)':
                    valor_per_ini = 1
                elif periodo_ini_sol == '2/3 (66%)':
                    valor_per_ini = .67
                else:
                    valor_per_ini = .33

                if periodo_fim_sol == '3/3 (100%)':
                    valor_per_fim = 1
                elif periodo_fim_sol == '2/3 (66%)':
                    valor_per_fim = .67
                else:
                    valor_per_fim = .33
                
                diferenca_dias = dif_dias + valor_per_ini + valor_per_fim

                # Adiciona o checkbox na interface
                definir_data_pagamento = st.checkbox("Pagamento Realizado?")
                # Inicializa data_pag como None
                data_pag = None
                # Se o checkbox estiver marcado, mostra o campo de entrada para data_pag
                if definir_data_pagamento:
                    data_pag = st.date_input('Data do Pagamento')

                desc_sol = st.text_input('Observações')

                # Extrato da Solicitação #
                st.markdown('---')
                st.subheader('Extrato da Solicitação')

                
                st.write(f"**Colaborador:** {colaborador_sol}")
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Data Início:** {data_ini_sol.strftime('%d-%m-%y')}")
                col2.write(f"**Data Término:** {data_fim_sol.strftime('%d-%m-%y')}")
                col3.write(f"**Qtde de Diárias:** {diferenca_dias}")

                # Conecta ao banco de dados para obter valor_diaria
                conexao = mysql.connector.connect(
                    host='viaduct.proxy.rlwy.net',
                    user='root',
                    port=58278,
                    password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
                    database='railway',
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci'
                )
                cursor = conexao.cursor()
                query_valor = "SELECT valor_diaria FROM dados WHERE nome = %s"
                cursor.execute(query_valor, (colaborador_sol,))
                resultado = cursor.fetchone()
                conexao.close()

                # Se o valor_diaria foi encontrado, use-o; senão, use 0 como valor padrão
                valor_diaria = resultado[0] if resultado else 0

                # Calcula o valor_total
                valor_total = diferenca_dias * valor_diaria

                # Exibe o valor total antes do botão de inserir solicitação
                st.write(f"**Valor do Adiantamento:** R$ {valor_total:.2f}")

                # Botão para inserir a solicitação vem aqui
                if st.button("Inserir Solicitação"):
                    data_atual = datetime.now()

                    # Chama a função de inserção
                    sucesso = inserir_solicitacao(st.session_state['usuario'], data_atual, colaborador_sol, centro_custo_sol, data_ini_sol, data_fim_sol, diferenca_dias, desc_sol, data_pag, banco_pag)
                    
                    if sucesso:
                        st.session_state['mensagem'] = "Solicitação inserida com sucesso!"
                        st.session_state['tipo_mensagem'] = "sucesso"
                    else:
                        st.session_state['mensagem'] = "Falha ao inserir a solicitação."
                        st.session_state['tipo_mensagem'] = "falha"

                    st.experimental_rerun()

                # Exibir a mensagem com base no tipo e usar sleep para aguardar 2 segundos antes de fazer a mensagem desaparecer
                if 'mensagem' in st.session_state and 'tipo_mensagem' in st.session_state:
                    if st.session_state['tipo_mensagem'] == "sucesso":
                        st.success(st.session_state['mensagem'])
                    elif st.session_state['tipo_mensagem'] == "falha":
                        st.error(st.session_state['mensagem'])
        
                    # Espera 2 segundos
                    time.sleep(2)

                    # Faz a mensagem desaparecer
                    del st.session_state['mensagem']
                    del st.session_state['tipo_mensagem']
                    
                    # Recarrega a página para atualizar o estado e remover a mensagem
                    st.experimental_rerun()

        # ====== Ajustar Solicitação ======= #    
        elif admin_opcao == 'Ajustar Solicitação':
            st.header("Ajustar Solicitação")
            st.markdown('**:blue[Filtros de seleção para alteração de uma solicitação]**')
            solicitantes = buscar_solicitantes()
            colaboradores = buscar_colaboradores()

            solicitante_selecionado = st.selectbox('Escolha o Solicitante', solicitantes)
            colaborador_selecionado = st.selectbox('Escolha o Colaborador', colaboradores)

            df_solicitacoes = buscar_solicitacoes(solicitante_selecionado, colaborador_selecionado)
            df_solicitacoes = df_solicitacoes.set_index('idadiantamento')
            st.dataframe(df_solicitacoes)
            st.markdown('---')
            st.markdown('**:blue[Área para ajustes nas informações]**')
            # Função para buscar IDs de solicitações
            def buscar_ids_solicitacoes(solicitante=None, colaborador=None):
                with mysql.connector.connect(
                    host='viaduct.proxy.rlwy.net',
                    user='root',
                    port=58278,
                    password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
                    database='railway',
                ) as conexao:
                    with conexao.cursor() as cursor:
                        # Construir a consulta com base nos filtros aplicados
                        query = "SELECT DISTINCT idadiantamento FROM adiantamento"
                        conditions = []
                        if solicitante:
                            conditions.append(f"solicitante = '{solicitante}'")
                        if colaborador:
                            conditions.append(f"colaborador = '{colaborador}'")
                        if conditions:
                            query += " WHERE " + " AND ".join(conditions)
                        
                        # Executar a consulta
                        cursor.execute(query)
                        ids = cursor.fetchall()
                        return [id[0] for id in ids]

            # Função para buscar dados da solicitação por ID
            def buscar_dados_solicitacao_por_id(id_solicitacao):
                with mysql.connector.connect(
                    host='viaduct.proxy.rlwy.net',
                    user='root',
                    port=58278,
                    password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
                    database='railway',
                ) as conexao:
                    df_solicitacao = pd.read_sql(f"SELECT * FROM adiantamento WHERE idadiantamento = {id_solicitacao}", conexao)  # Corrigido para o nome correto da coluna
                    return df_solicitacao

            # Ajuste na página de ajuste de solicitação
            if st.session_state['login_status'] and st.session_state['tipo_usuario'] == 'admin':
                ids_solicitacoes = buscar_ids_solicitacoes()
                id_selecionado = st.selectbox('Escolha o ID da Solicitação para alterar', ids_solicitacoes)
                
                # Definindo as variáveis data_inicio e data_fim fora do escopo condicional
                data_inicio = None
                data_fim = None
                if id_selecionado:
                    df_solicitacao = buscar_dados_solicitacao_por_id(id_selecionado)
                    if not df_solicitacao.empty:
                        # Defina aqui os widgets de input, assegurando que eles apareçam antes do botão
                        novo_solicitante = st.session_state['usuario']  # O solicitante é o usuário logado
                        nova_data = datetime.now()  # A data é agora
                        novo_colaborador = st.selectbox('Novo Colaborador', usuarios_unicos, index=usuarios_unicos.index(df_solicitacao.iloc[0]['colaborador']))
                        novo_cc = st.selectbox('Novo Centro de Custo', centro_custos, index=centro_custos.index(df_solicitacao.iloc[0]['cc']))
                        nova_observacao = st.text_area('Observações', value=df_solicitacao.iloc[0]['observacao'])
                        novo_data_pagamento = st.date_input('Nova Data de Pagamento', value=df_solicitacao.iloc[0]['data_pagamento'])
                        novo_banco_pagamento = st.selectbox('Novo Banco de Pagamento', bancos_pagamento, index=bancos_pagamento.index(df_solicitacao.iloc[0]['banco_pagamento']))
                        col1, col2 = st.columns(2)
                        data_inicio = col1.date_input("Data Inicial", value=df_solicitacao.iloc[0]['data_inicio'])
                        data_fim = col2.date_input("Data Final", value=df_solicitacao.iloc[0]['data_termino'])

                        # Calcular diárias e valor_total conforme a lógica de inserção
                        # Verificação se a data final é menor que a data inicial
                        if data_fim < data_inicio:
                            st.error("Erro: A data final não pode ser menor que a data inicial.")
                        else:
                            # Continua com o restante do seu código apenas se a data final for maior ou igual à data inicial
                            dif_dias = (data_fim - data_inicio).days-1

                            col1, col2 = st.columns(2)
                            periodo_ini_sol = col1.selectbox('Período de Início', periodos_adian)
                            periodo_fim_sol = col2.selectbox('Período de Término', periodos_adian)

                            # Cálculo das diárias
                            if periodo_ini_sol == '3/3 (100%)':
                                valor_per_ini = 1
                            elif periodo_ini_sol == '2/3 (66%)':
                                valor_per_ini = .67
                            else:
                                valor_per_ini = .33

                            if periodo_fim_sol == '3/3 (100%)':
                                valor_per_fim = 1
                            elif periodo_fim_sol == '2/3 (66%)':
                                valor_per_fim = .67
                            else:
                                valor_per_fim = .33
                            
                            diferenca_dias = dif_dias + valor_per_ini + valor_per_fim

                            # Conecta ao banco de dados para obter valor_diaria
                            conexao = mysql.connector.connect(
                                host='viaduct.proxy.rlwy.net',
                                user='root',
                                port=58278,
                                password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
                                database='railway',
                                charset='utf8mb4',
                                collation='utf8mb4_unicode_ci'
                            )
                            cursor = conexao.cursor()
                            query_valor = "SELECT valor_diaria FROM dados WHERE nome = %s"
                            cursor.execute(query_valor, (novo_colaborador,))
                            resultado = cursor.fetchone()
                            conexao.close()

                            # Se o valor_diaria foi encontrado, use-o; senão, use 0 como valor padrão
                            valor_diaria = resultado[0] if resultado else 0

                            # Calcula o valor_total
                            valor_total_calculado = diferenca_dias * valor_diaria
                        
                        if st.button("Salvar Alterações"):
                            try:
                                conexao = mysql.connector.connect(
                                    host='viaduct.proxy.rlwy.net',
                                    user='root',
                                    port=58278,
                                    password='tcDWrsUDzZFiREsUBpOUivzDVzpvSfFJ',
                                    database='railway'
                                )
                                cursor = conexao.cursor()
                                query = """UPDATE adiantamento SET solicitante = %s, data = %s, colaborador = %s, cc = %s, 
                                        data_inicio = %s, data_termino = %s, diarias = %s, valor_total = %s, 
                                        observacao = %s, data_pagamento = %s, banco_pagamento = %s WHERE idadiantamento = %s"""
                                cursor.execute(query, (novo_solicitante, nova_data, novo_colaborador, novo_cc, 
                                                        data_inicio, data_fim, diferenca_dias, valor_total_calculado, 
                                                        nova_observacao, novo_data_pagamento, novo_banco_pagamento, id_selecionado))
                                conexao.commit()
                                
                                # Prepara os detalhes para registro no histórico
                                detalhes_alteracao = f"Solicitação {id_selecionado} alterada. Novos valores: [Colaborador: {novo_colaborador}, CC: {novo_cc}, Data de Inicio:{data_inicio}, Data Término:{data_fim}, Diarias:{diferenca_dias}, Valor total:{valor_total_calculado}, Nova observação:{nova_observacao}, Data Pagamento:{novo_data_pagamento}, Banco de Pagamento:{novo_banco_pagamento}]"
                                tipo_operacao = "Atualização"
                                usuario = st.session_state['usuario']  # Supondo acesso ao usuário logado
                                
                                # Registrar no histórico
                                registrar_historico(id_selecionado, usuario, tipo_operacao, detalhes_alteracao)
                                
                                st.success("Solicitação atualizada com sucesso!")
                                st.experimental_rerun()

                            except Error as e:
                                st.error(f"Erro ao atualizar a solicitação: {e}")
                            finally:
                                if conexao:
                                    cursor.close()
                                    conexao.close()

        # ====== Ver Histórico de Ajustes ======= #   
        elif admin_opcao == 'Ver Histórico de Ajustes':
            st.header("Histórico de Ajustes")
            df_historico = buscar_historico()
            st.dataframe(df_historico)

# ============= TELA USUARIO ================= #
    elif st.session_state['tipo_usuario'] == 'normal':
        st.write("Tela do Usuário")
        # Aqui você pode adicionar o conteúdo específico para o usuário normal

        # Inserir solicitação

        # Acompanhar solicitação

        # Ajustar solicitação
    
    st.sidebar.success(f"Logado como: {st.session_state['usuario']}")

    if st.sidebar.button("Logout"):
        st.session_state['login_status'] = False
        st.session_state['usuario'] = ""
        st.session_state['role'] = ""
        st.session_state['ver_historico'] = False
        st.experimental_rerun()