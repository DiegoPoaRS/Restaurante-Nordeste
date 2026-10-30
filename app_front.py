import flet as ft
import requests

API_URL = "http://127.0.0.1:8000"
token_jwt = None  
tipo_usuario = None
canal_atual = "APP"
unidade_atual = 1
carrinho = []

def main(page: ft.Page):
    global token_jwt, tipo_usuario, canal_atual, unidade_atual, carrinho
    
    page.title = "Raízes do Nordeste"
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT

    conteudo_principal = ft.Container(expand=True, padding=20, alignment=ft.Alignment.CENTER)

    def mudar_tela(novo_conteudo):
        conteudo_principal.content = novo_conteudo
        page.update()

    # ==========================================
    # TELA 0: INICIAL (ROTEAMENTO PRINCIPAL)
    # ==========================================
    def ir_para_tela_inicial(e=None):
        tela_inicial = ft.Column([
            ft.Icon(ft.Icons.RESTAURANT_MENU, size=80, color=ft.Colors.ORANGE),
            ft.Text("Bem-vindo(a)!", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Raízes do Nordeste", size=18, color=ft.Colors.GREY_700),
            ft.Container(height=30),
            ft.Text("Como deseja acessar?", size=16),
            ft.Button("Fazer Login", width=300, height=50, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE, on_click=lambda _: mudar_tela(tela_login)),
            ft.Button("Cadastrar-se (Ganha Pontos!)", width=300, height=50, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE, on_click=lambda _: ir_para_tela_cadastro()),
            ft.TextButton("Não quero me identificar", width=300, height=50, on_click=lambda _: entrar_como_visitante())
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        mudar_tela(tela_inicial)

    def entrar_como_visitante():
        global token_jwt, tipo_usuario
        token_jwt = None
        tipo_usuario = "VISITANTE"
        ir_para_home_cliente()

    # ==========================================
    # TELA 1: LOGIN
    # ==========================================
    email_input = ft.TextField(label="E-mail", width=300)
    senha_input = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
    status_text_login = ft.Text(value="", color=ft.Colors.RED)

    def fazer_login(e):
        global token_jwt, tipo_usuario
        try:
            dados = {"username": email_input.value, "password": senha_input.value}
            response = requests.post(f"{API_URL}/auth/login", data=dados)
            if response.status_code == 200:
                json_resp = response.json()
                token_jwt = json_resp["access_token"]
                tipo_usuario = json_resp["tipo"]
                
                if tipo_usuario in ["ADMIN", "GERENTE", "FUNCIONARIO"]:
                    ir_para_painel_gerente()
                else:
                    ir_para_home_cliente()
            else:
                status_text_login.value = "E-mail ou senha inválidos."
                page.update()
        except Exception as ex:
            status_text_login.value = f"Erro de conexão: {ex}"
            page.update()

    tela_login = ft.Column([
        ft.Icon(ft.Icons.LOCK_PERSON, size=60, color=ft.Colors.BLUE),
        ft.Text("Acesso ao Sistema", size=22, weight=ft.FontWeight.BOLD),
        email_input, senha_input,
        ft.Button(content="Entrar", on_click=fazer_login, width=300, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
        ft.TextButton("Voltar", on_click=ir_para_tela_inicial),
        status_text_login
    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    # ==========================================
    # TELA 2: CADASTRO COM LGPD (MODAL SOBREPOSTO)
    # ==========================================
    def ir_para_tela_cadastro():
        nome_cad = ft.TextField(label="Nome Completo", width=300)
        email_cad = ft.TextField(label="E-mail", width=300)
        senha_cad = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
        cpf_cad = ft.TextField(label="CPF", width=300)
        tel_cad = ft.TextField(label="Telefone", width=300)
        end_cad = ft.TextField(label="Endereço", width=300)
        nasc_cad = ft.TextField(label="Nascimento (YYYY-MM-DD)", width=300)
        
        texto_lgpd_completo = ("""  POLÍTICA DE PRIVACIDADE PARA CLIENTES E USUÁRIOS DO SITE, APP E DEMAIS APLICAÇÕES DE INTERNET -  RAIZES DO NORDESTE \n
    A RAIZES DO NORDESTE COMÉRCIO DE ALIMENTOS S.A. (“RAIZES DO NORDESTE”) está comprometida com a proteção dos dados pessoais de seus clientes (referidos aqui em conjunto como “Clientes”, “Titulares”, “Usuários” ou “vocês”) que adquirem produtos, seja por meio do site https://www.raizesdonordeste.com.br, do aplicativo “RaizesND”, do canal no WhatsApp “RaizesND Zap”, das demais funcionalidades oferecidas , como o delivery McDonald’s (“RaizesDelivery”) e o “Peça e Retire” (referidos, respectivamente, como “Site”, “App”, “RaizesND Zap”, “RaizesDelivery”, “Peça e Retire”) ou diretamente nos restaurantes da RAIZES DO NORDESTE.
    Esta Política de Privacidade tem por objetivo dar transparência sobre como seus dados pessoais são tratados pela RAIZES DO NORDESTE. Caso você não concorde com as práticas aqui apresentadas, não prossiga com o uso de nossos sistemas e plataformas.
    \n
    Quem é o controlador de seus dados pessoais?
    A RAIZES DO NORDESTE COMÉRCIO DE ALIMENTOS S.A., sociedade inscrita no CNPJ/ME sob nº 11.876.666/0001-47, com sede na Alameda Sergipe, nº 123, Alphagama, na Cidade de Bauru/RN, é a empresa controladora dos dados pessoais tratados no âmbito desta Política de Privacidade. Para fins da legislação aplicável, “controlador” é a quem compete as decisões referentes ao tratamento de dados pessoais. Nos termos da Lei Geral de Proteção de Dados Pessoais (Lei n. 13.709/18 ou “LGPD”), a RAIZES DO NORDESTE é responsável apenas pelas atividades de tratamento de dados pessoais dos Titulares que a própria RAIZES DO NORDESTE realizar no contexto das suas operações e estabelecimentos, mas não pelas atividades de processamento das empresas franqueadas da Família Raizes do Nordeste (conforme definido abaixo).
    Conforme será detalhado na presente Política de Privacidade, os seus dados pessoais poderão ser compartilhados com empresas franqueadas, franqueadora e empresas do grupo (em conjunto com o McDonald’s, “Família Raizes do Nordeste”) e/ou empresas parceiras da RAIZES DO NORDESTE para fins estritamente relacionados à gestão e operação do Site, do App, do RaizesND Zap, do RaizesDelivery, do Peça e Retire, do Programa Meu RaizesND e das demais aplicações de Internet da RAIZES DO NORDESTE, bem como para aprimoramento dos produtos, programas e serviços oferecidos pela RAIZES DO NORDESTE, hipóteses em que tais empresas também poderão ser controladoras independentes de seus dados pessoais. Especificamente no que se refere às empresas franqueadas pertencentes à Família Raizes do Nordeste, podemos compartilhar os dados pessoais dos Titulares com tais empresas, com a finalidade estritamente necessária para viabilizar a fabricação e a entrega de produtos e/ou a prestação dos nossos serviços ao Cliente. Exceto pelas atividades descritas acima, existe a possibilidade de seus dados pessoais serem tratados pelas empresas franqueadas pertencentes à Família Raizes do Nordeste para outras finalidades, as quais a RAIZES DO NORDESTE não tem qualquer ingerência e/ou participação em sua realização. NESTAS CIRCUNSTÂNCIAS, A RAIZES DO NORDESTE NÃO É RESPONSÁVEL POR TAIS ATIVIDADES DE TRATAMENTO DE DADOS PESSOAIS NOS TERMOS DA LGPD.
    \n
    Quais dados pessoais tratamos?
    A RAIZES DO NORDESTE trata dados pessoais de Titulares que são coletados e/ou processados: (a) durante o acesso e/ou navegação do Site, do App, do RaizesND Zap, do RaizesDelivery, do Peça e Retire, do Programa Meu RaizesND e demais aplicações de Internet da RAIZES DO NORDESTE; e (b) antes, durante ou após o fornecimento de produtos e/ou prestação dos serviços pela RAIZES DO NORDESTE. Especificamente, a RAIZES DO NORDESTE coleta as seguintes informações dos Titulares e/ou Clientes, conforme o caso:
    • Informações Cadastrais. Ao criar sua conta no Site, no App, no RaizesDelivery, do Peça e Retire e/ou ao utilizar o RaizesND Zap, o Titular fornecerá os seguintes dados pessoais (conforme aplicável): (i) nome completo, (ii) endereço de e-mail; (iii) endereço informado para entrega de produtos; (iv) telefones para contato; (v) CPF; (vi) data de nascimento, entre outros dados de identificação ou necessários para o cadastro junto à RAIZES DO NORDESTE e fornecimento de produtos e serviços, conforme aplicável. Alguns destes dados podem ser voluntariamente fornecidos pelo Cliente ao adquirir um produto e/ou contratar algum serviço nos restaurantes da RAIZES DO NORDESTE.
    • Informações sobre pagamentos. A RAIZES DO NORDESTE poderá coletar dados transacionais para processamento de compras feitas através do App, do RaizesDelivery, do Peça e Retire e nos restaurantes do McDonald’s (por exemplo: dados que constam dos cartões de crédito, cartão de débito etc.);
    • Informações de navegação e uso. A RAIZES DO NORDESTE poderá coletar outros dados, automaticamente, quando o Usuário utiliza o Site, o App, o RaizesND Zap, o RaizesDelivery ou o Peça e Retire, tais como: geolocalização, páginas visitadas ou anúncios visualizados, dados do dispositivo (como fabricante, modelo e versão do aparelho, sistema operacional e ID), comportamento de compra e preferências na escolha de produtos, etc. O Usuário pode optar por não fornecer algumas informações, desde que não sejam necessárias para o fornecimento dos produtos, a prestação dos serviços e/ou utilização do Site, do App, do RaizesND Zap, do RaizesDelivery ou do Peça e Retire, mas é provável que a sua experiência com o Site, o App, o RaizesND Zap, o RaizesDelivery ou o Peça e Retire não conte com todos os recursos oferecidos pela RAIZES DO NORDESTE. Por exemplo, a RAIZES DO NORDESTE poderá precisar coletar informações sobre a sua localização para permitir a retirada de produtos que tenham sido solicitados por meio do Peça e Retire, bem como para lhe enviar notificações de push, que podem variar a depender da sua proximidade de um de nossos restaurantes.
    • Registros de acesso e demais informações automatizadas. A RAIZES DO NORDESTE poderá coletar e armazenar algumas informações que recebe automaticamente toda vez que o Usuário interage com o Site, com o App, com o RaizesND Zap, com o RaizesDelivery, com o Peça e Retire e/ou com outras aplicações de internet. Internet Protocol (IP), tipo de navegador, bem como datas e horas das interações do Usuário com as plataformas, são alguns exemplos desta coleta.
    • Registro de visita aos restaurantes da RAIZES DO NORDESTE e cadastro às redes de Wi-fi. A RAIZES DO NORDESTE poderá coletar e armazenar algumas informações que recebe automaticamente toda vez que o Cliente visita os restaurantes da RAIZES DO NORDESTE, tais como as imagens capturadas pelas câmeras de segurança posicionadas na entrada e no interior do restaurante. Ademais, a RAIZES DO NORDESTE também poderá coletar e armazenar informações quando o Cliente realiza um cadastro nas redes de Wi-fi oferecidas nos restaurantes da RAIZES DO NORDESTE.
    • Informações que são recebidas de serviços de delivery Terceiros. A RAIZES DO NORDESTE poderá receber e armazenar algumas informações a seu respeito que recebe de aplicativos de serviços de delivery que são operados por terceiros (por exemplo, iFood).
    • Outras fontes. Por fim, a RAIZES DO NORDESTE poderá receber e armazenar outras informações a seu respeito, tais como as informações fornecidas por entidades de apoio ao crédito, para fins de evitar fraudes e demais riscos relacionados a transações financeiras eletrônicas.
    \n
    Para quais finalidades coletamos seus dados?
    Os dados pessoais dos Titulares e/ou Clientes, conforme o caso, são tratados pela RAIZES DO NORDESTE para as seguintes finalidades:
    • Disponibilizar aos Titulares um ambiente eletrônico por meio do qual os Usuários podem obter mais informações sobre os produtos e serviços da RAIZES DO NORDESTE; • Viabilizar a formalização da compra de um produto e/ou a contratação de um serviço através do Site, do App, do RaizesND Zap, do RaizesDelivery, do Peça e Retire, do Programa Meu RaizesND ou dos restaurantes da RAIZES DO NORDESTE; • Viabilizar a entrega e/ou retirada de produtos adquiridos através do Site, do App, do RaizesND Zap, do RaizesDelivery ou do Peça e Retire; • Formalizar a participação de Titulares em concursos, prêmios e demais ações promocionais promovidas pela RAIZES DO NORDESTE; • Prestar e aprimorar o serviço de atendimento aos Titulares, o que podem envolver diversas atividades relacionadas aos produtos adquiridos e/ou aos serviços contratados. Tais atividades incluem, mas não se limitam, ao cadastro de nova senha no Site e/ou no App, geração e emissão de nota fiscal, troca de produtos (por exemplo quando constatado que o seu lacre está rompido), processamento de reclamações, sugestões ou dúvidas sobre produtos, serviços, etc.; • Entrar em contato com os Titulares para informar sobre o processamento de seus pedidos e solicitações, assim como para informar-lhe sobre ofertas, programas, sorteios ou promoções da RAIZES DO NORDESTE ou de seus parceiros comerciais, incluindo através de notificações de push, enviadas de acordo com a localização do Titular; • Entrar em contato com os Titulares, para enviar informações sobre: (a) produtos e/ou serviços oferecidos pela RAIZES DO NORDESTE e demais informações relevantes sobre a RAIZES DO NORDESTE, (b) alterações relevantes nas funcionalidades do Site, do App, do RaizesND Zap, do RaizesDelivery e Peça e Retire (c) outros assuntos que a RAIZES DO NORDESTE julgue que possam interessar os Titulares; • Aprimorar os serviços e/ou funcionalidades do Site, do App, do RaizesND Zap, do RaizesDelivery e/ou do Peça e Retire;
     • Aprimorar as iniciativas comerciais e promocionais da RAIZES DO NORDESTE, bem como melhorar nossa oferta de conteúdos e produtos personalizados que possam interessar os Titulares, o que pode incluir o desenvolvimento de campanhas de marketing e o envio de notificações de push, enviadas de acordo com a localização do Titular;
     • Aprimorar mecanismos de segurança e prevenção de fraudes nos serviços e funcionalidades do site e app; • Analisar as informações de compras de nossos produtos em diferentes canais (incluindo, mas não se limitando, as compras realizadas nos restaurantes da RAIZES DO NORDESTE, no App e no RaizesNDZap) para identificar as preferências do Titular e apresentar produtos, serviços e ofertas que possam interessar o Titular; • Fornecer serviços de conectividade WI-FI nos restaurantes da RAIZES DO NORDESTE; e
     • Classificar e agrupar informações relativas aos Titulares, assim como consolidar dados estatísticos a respeito desses, inclusive para definir a composição da base de Usuários do Site, do App, do RaizesND Zap, do RaizesDelivery e o Peça e Retire, bem como analisar o volume de tráfego em nossos servidores.
    \n
    Com quem compartilhamos seus dados pessoais?
    A RAIZES DO NORDESTE poderá compartilhar seus dados pessoais com terceiros ou parceiros de negócios que sejam relevantes para fins de viabilizar a utilização do Site, do App, do RaizesND Zap, do RaizesDelivery e/ou do Peça e Retire pelos Titulares ou viabilizar a prestação dos serviços ao Cliente. Referido compartilhamento ocorre com base nos seguintes critérios e para as finalidades descritas abaixo.
    • Prestadores de serviços ou parceiros comerciais: Podemos compartilhar seus dados pessoais com prestadores de serviços ou parceiros comerciais da RAIZES DO NORDESTE para fins de: (a) fornecimento de software, sistemas antifraude e/ou ferramenta para gestão de Clientes, (b) processamento das transações por cartão de crédito ou demais meios de pagamento, (c) geração de leads, prospecção de clientes e desenvolvimento de ações de marketing, (d) prestação de serviços logísticos dos pedidos realizados através do Site, do App, do RaizesND Zap, do RaizesDelivery e/ou do Peça e Retire; (e) auxílio no gerenciamento de promoções; (f) prestação de serviços de atendimento ao consumidor; e (f) gestão e aprimoramento do Site, do App, do RaizesND Zap, do RaizesDelivery , do Peça e Retire e/ou do Meu RaizesND. Tais agentes recebem seus dados pessoais para a realização de uma destas atividades, e estão sujeitos a estritas obrigações de confidencialidade e proteção de dados pessoais em relação à RAIZES DO NORDESTE.
    • Requisição de autoridade competente: A RAIZES DO NORDESTE ainda poderá compartilhar seus dados pessoais com terceiros (incluindo órgãos governamentais) a fim de responder a investigações, medidas judiciais, processos judiciais ou investigar, impedir ou adotar medidas acerca de atividades ilegais, suspeita de fraude ou situações que envolvam ameaças em potencial à segurança física de qualquer pessoa ou se de outra maneira exigido pela legislação.
    • Família Raizes do Nordeste: Podemos compartilhar os dados pessoais dos Titulares com as demais empresas pertencentes à Família Raizes do Nordeste, com a finalidade estritamente necessária para viabilizar a fabricação e a entrega de produtos e/ou a prestação dos nossos serviços ao Cliente.
    • Novos negócios: Se a RAIZES DO NORDESTE estiver envolvida em uma fusão, aquisição ou venda de todos ou de parte de seus ativos, seus dados pessoais poderão ser transferidos para a empresa ou pessoa adquirente. Em circunstâncias nas quais a identidade do controlador de seus dados pessoais se alterar como resultado de qualquer transação, você será notificado de quaisquer escolhas que possa ter acerca de seus dados pessoais.
    \n
    E a transferências de seus dados pessoais para fora do Brasil?
    A RAIZES DO NORDESTE pode, conforme necessário, transferir seus dados pessoais a prestadores de serviços ou à Família Raizes do Nordeste localizados em outros países.
    A seguir, apresentamos exemplos de finalidades de transferências e de países para os quais os seus dados pessoais podem ser transferidos.
    Empresas da Família Raizes do Nordeste Para gestão e operação do Site, do App, do RaizesND Zap, do RaizesDelivery, do Peça e Retire, do Programa Meu RaizesND e das demais aplicações de Internet da RAIZES DO NORDESTE, bem como para aprimoramento dos produtos, programas e serviços oferecidos pela RAIZES DO NORDESTE pode transferir seus dados pessoais para empresas pertencentes à Família Raizes do Nordeste localizadas em outros países. País: Argentina
    Empresas de armazenamento em nuvem (Cloud Computing) Para garantir a segurança, confidencialidade, integridade e disponibilidade dos dados pessoais de seus clientes, a RAIZES DO NORDESTE utiliza serviços de armazenamento em nuvem fornecidos por empresas especializadas. Por esse motivo, seus dados pessoais podem ser transferidos para servidores localizados em outros países. País: China
    Empresas prestadoras de serviços Para viabilizar as atividades necessárias à prestação de nossos serviços, a RAIZES DO NORDESTE pode contratar prestadores de serviços ou parceiros comerciais para, por exemplo, fornecimento de software, sistemas antifraude e/ou ferramenta para gestão de Clientes, processamento das transações por cartão de crédito ou demais meios de pagamento, geração de leads, prospecção de clientes e desenvolvimento de ações de marketing, prestação de serviços logísticos dos pedidos realizados através do Site, do App, do RaizesND Zap, do RaizesDelivery e/ou do Peça e Retire; auxílio no gerenciamento de promoções; prestação de serviços de atendimento ao consumidor; e gestão e aprimoramento do Site, do App, do RaizesND Zap, do RaizesDelivery, do Peça e Retire e/ou do Meu RaizesND. Países: Estados Unidos, China, Russia, Argentina, Uruguai, Chile, Venezuela e Espanha.
    Quando seus dados pessoais forem transferidos para outros países pela RAIZES DO NORDESTE, serão adotadas medidas apropriadas para garantir a proteção de seus dados, em conformidade com a legislação aplicável de proteção de dados pessoais. Essas medidas incluem, por exemplo:
    Medidas administrativas: celebração de cláusulas-padrão de transferência internacional de dados com terceiros, quando necessário.
    \n
    Medidas técnicas autenticação multifator, gestão e controle de acesso, registro e monitoramento de atividades, backups criptografados, segmentação de rede, sistemas de detecção de intrusos e testes de segurança.
    \n
    Medidas organizativas: políticas de segurança da informação, classificação de informação, gestão de incidentes, treinamentos, avaliações de risco periódicas e auditorias.
    \n
    Por quanto tempo vamos reter seus dados pessoais?
    A RAIZES DO NORDESTE armazena e mantém suas informações: (i) pelo tempo exigido por lei; (ii) até o término do tratamento de dados pessoais, conforme mencionado abaixo; ou (iii) caso haja base legal válida para justificar a manutenção das informações, como por exemplo, pelo tempo necessário a preservar o legítimo interesse da RAIZES DO NORDESTE ou para cumprimento de obrigação legal ou regulatória.
    O término do tratamento de dados pessoais ocorrerá nos seguintes casos:
    • Quando a finalidade pela qual os dados pessoais do Titular foram coletados for alcançada e/ou os dados pessoais coletados deixarem de ser necessários ou pertinentes ao alcance de tal finalidade; • Quando o Titular estiver em seu direito de solicitar o término do tratamento e a exclusão de seus dados pessoais e o fizer; ou • Quando houver uma determinação legal neste sentido.
    Nesses casos de término de tratamento de dados pessoais, ressalvadas as hipóteses estabelecidas pela legislação aplicável ou pela presente Política de Privacidade, os dados pessoais serão eliminados.
    Quais são os seus direitos em relação aos dados pessoais que tratamos sobre você?
    Você possui direitos em relação aos seus dados pessoais. Tais direitos incluem, mas não se limitam a:
    • Receber informações claras e completas sobre o tratamento de seus dados pessoais, incluindo sobre as hipóteses de compartilhamento de dados pessoais;
    • Solicitar o acesso a seus dados pessoais e/ou a confirmação da existência de tratamento de dados;
    • Solicitar que retifiquemos quaisquer dados pessoais imprecisos, incompletos e desatualizados; • Se opor às atividades de tratamento, solicitar a anonimização e eliminação de dados pessoais, em circunstâncias específicas; • Solicitar a portabilidade de seus dados pessoais; • Revogar o consentimento a qualquer momento, quando a RAIZES DO NORDESTE tratar seus dados pessoais com base no consentimento; e • Solicitar a revisão de decisões automatizadas que possam afetar seus interesses.
    Você pode exercer esses direitos por meio de nossa Central de Privacidade.
    Proteção de dados pessoais
    A RAIZES DO NORDESTE utiliza medidas técnicas e organizacionais apropriadas para proteger seus dados pessoais contra tratamento desautorizado ou ilegal e contra perda acidental, destruição ou danos. Seus dados pessoais são armazenados de maneira segura em equipamentos protegidos. Apenas um número limitado de pessoas terá acesso a tais equipamentos e apenas indivíduos com motivos legítimos terão acesso a seus dados pessoais.
    Alterações a esta Política de Privacidade
    A RAIZES DO NORDESTE se reserva o direito de alterar esta Política de Privacidade a qualquer momento, mediante publicação da versão atualizada no endereço Política Privacidade. Em caso de alterações relevantes nesta Política de Privacidade, o Titular receberá um aviso a esse respeito.
    Interações com sites de terceiros
    Podemos disponibilizar links para outros sites na Internet. A RAIZES DO NORDESTE NÃO SE RESPONSABILIZA POR ESTES SITES E CONTEÚDOS E, AINDA, NÃO COMPARTILHA, SUBSCREVE, MONITORA, VÁLIDA OU ACEITA A FORMA COMO ESSES SITES OU FERRAMENTAS DE ARMAZENAMENTO DE CONTEÚDO COLETAM, PROCESSAM E TRANSFEREM SUAS INFORMAÇÕES PESSOAIS. Recomendamos que o Titular consulte as respectivas políticas de privacidade de tais sites para se informar adequadamente a respeito do uso de suas informações pessoais por outros sites ou outras ferramentas.
    Exercício dos direitos do titular de dados pessoais, dúvidas sobre esta Política de Privacidade e contato com a Encarregada de Proteção de Dados Pessoais
    Caso deseje exercer seus direitos como titular de dados pessoais, acesse nossa Central de Privacidade.
    Se você, tiver dúvidas sobre esta Política de Privacidade ou sobre o tratamento de seus dados pessoais pela RAIZES DO NORDESTE, você pode entrar em contato com a Encarregada de Proteção de Dados Pessoais, Sara Dadosnhol, pelo e-mail privacidade.lgpd@raizesdonordeste.com.br
    Atualizada em: 15/08/2026 """)


        lgpd_checkbox = ft.Checkbox(value=False)

        def abrir_modal(e):
            modal_lgpd.visible = True
            page.update()

        def fechar_modal(e):
            modal_lgpd.visible = False
            page.update()

        def aceitar_termos(e):
            lgpd_checkbox.value = True
            modal_lgpd.visible = False
            page.update()

        modal_lgpd = ft.Container(
            visible=False,
            expand=True,
            bgcolor="black54",
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                bgcolor="white",
                                padding=20,
                                border_radius=12,
                                width=370,
                                height=450,
                                content=ft.Column(
                                    controls=[
                                        ft.Row([
                                            ft.Text("Termos da LGPD", weight="bold", size=16),
                                            ft.TextButton("X", on_click=fechar_modal, style=ft.ButtonStyle(color="red"))
                                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                        ft.Divider(),
                                        ft.Container(
                                            content=ft.Column(
                                                controls=[ft.Text(texto_lgpd_completo, size=12)],
                                                scroll=ft.ScrollMode.AUTO,
                                            ),
                                            expand=True,
                                        ),
                                        ft.Container(height=10),
                                        ft.Button("Entendi e Aceito", on_click=aceitar_termos, bgcolor="orange", color="white", width=330)
                                    ]
                                )
                            )
                        ]
                    )
                ]
            )
        )

        linha_lgpd = ft.Row([
            lgpd_checkbox, 
            ft.Text("Aceito os", size=14),
            ft.TextButton("Termos da LGPD", on_click=abrir_modal, style=ft.ButtonStyle(padding=0))
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        status_text_cad = ft.Text(value="", color="red")

        def realizar_cadastro(e):
            if not lgpd_checkbox.value:
                status_text_cad.value = "Você precisa aceitar os termos da LGPD."
                page.update()
                return

            payload = {
                "nome_completo": nome_cad.value, "email": email_cad.value, "senha": senha_cad.value,
                "endereco_entrega": end_cad.value, "telefone": tel_cad.value, "cpf": cpf_cad.value,
                "data_nascimento": nasc_cad.value, "aceite_lgpd": lgpd_checkbox.value, "tipo": "CLIENTE"
            }

            try:
                res = requests.post(f"{API_URL}/auth/registro", json=payload)
                if res.status_code == 201:
                    page.snack_bar = ft.SnackBar(ft.Text("Cadastro realizado com sucesso! Faça login."))
                    page.snack_bar.open = True
                    ir_para_tela_inicial()
                else:
                    status_text_cad.value = f"Erro: {res.json().get('message', 'Falha')}"
                    page.update()
            except Exception as ex:
                status_text_cad.value = f"Erro de conexão: {ex}"
                page.update()

        conteudo_form = ft.ListView(expand=True, spacing=10, padding=15)
        conteudo_form.controls.extend([
            ft.Text("Criar Nova Conta", size=22, weight="bold"),
            nome_cad, email_cad, senha_cad, cpf_cad, tel_cad, end_cad, nasc_cad, linha_lgpd,
            ft.Button("Cadastrar", on_click=realizar_cadastro, width=300, bgcolor="orange", color="white"),
            ft.TextButton("Voltar", on_click=ir_para_tela_inicial),
            status_text_cad
        ])

        tela_com_modal = ft.Stack(
            controls=[
                conteudo_form,
                modal_lgpd
            ],
            expand=True
        )

        mudar_tela(tela_com_modal)

# ==========================================
    # TELA 3: PAINEL DO GERENTE / FUNCIONÁRIO
    # ==========================================
    def ir_para_painel_gerente():
        pedidos_carregados = []
        coluna_pedidos = ft.ListView(expand=True, spacing=10, padding=10)
        
        filtro_ocultar_finalizados = ft.Checkbox(label="Ocultar Entregues/Cancelados", value=True)
        filtro_canal = ft.Dropdown(
            options=[
                ft.dropdown.Option(key="TODOS", text="Todos os Canais"),
                ft.dropdown.Option(key="APP", text="Delivery (App)"),
                ft.dropdown.Option(key="TOTEM", text="Totem"),
                ft.dropdown.Option(key="BALCAO", text="Balcão")
            ],
            value="TODOS",
            width=200
        )

        def renderizar_pedidos(e=None):
            coluna_pedidos.controls.clear()
            
            if not pedidos_carregados:
                coluna_pedidos.controls.append(ft.Text("Nenhum pedido no momento."))
                
            for p in pedidos_carregados:
                status_atual = p['status']
                canal = p['canal_pedido']
                
                if filtro_ocultar_finalizados.value and status_atual in ["ENTREGUE", "CANCELADO"]:
                    continue
                if filtro_canal.value != "TODOS" and canal != filtro_canal.value:
                    continue

                cor_card = "white"
                botoes_acao = []
                
                if status_atual == "CRIADO":
                    cor_card = "#f0f0f0"
                    botoes_acao.append(ft.Text("Aguardando Pagamento", color="grey"))
                elif status_atual == "COZINHA":
                    cor_card = "#fff3e0"
                    botoes_acao.append(ft.Button("Marcar PRONTO", bgcolor="orange", color="white", on_click=lambda e, pid=p['id']: atualizar_status(pid, "PRONTO")))
                elif status_atual == "PRONTO":
                    cor_card = "#e8f5e9"
                    botoes_acao.append(ft.Button("Marcar ENTREGUE", bgcolor="green", color="white", on_click=lambda e, pid=p['id']: atualizar_status(pid, "ENTREGUE")))
                elif status_atual == "CANCELADO":
                    cor_card = "#ffebee"
                    botoes_acao.append(ft.Text("Cancelado (Pagamento Negado)", color="red"))
                elif status_atual == "ENTREGUE":
                    cor_card = "#e3f2fd"
                    botoes_acao.append(ft.Text("Entregue com Sucesso", color="blue"))
                
                coluna_pedidos.controls.append(ft.Card(bgcolor=cor_card, content=ft.Container(padding=15, content=ft.Column([
                    ft.Text(f"Pedido #{p['id']} - Loja: {p['unidade_id']} - Canal: {canal}", weight="bold"),
                    ft.Text(f"Status: {status_atual}", color="blue"),
                    ft.Text(f"Valor: R$ {p['valor_total']:.2f}"),
                    ft.Row(botoes_acao, alignment=ft.MainAxisAlignment.END)
                ]))))
            page.update()

        filtro_ocultar_finalizados.on_change = renderizar_pedidos
        filtro_canal.on_change = renderizar_pedidos

        def buscar_pedidos(e=None):
            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.get(f"{API_URL}/pedidos", headers=headers)
                if res.status_code == 200:
                    pedidos_carregados.clear()
                    pedidos_carregados.extend(res.json())
                    renderizar_pedidos()
            except Exception as ex:
                coluna_pedidos.controls.append(ft.Text(f"Erro ao buscar pedidos: {ex}"))
                page.update()

        # Função auxiliar de atualizar status colocada DE DENTRO do escopo correto
        def atualizar_status(pedido_id, novo_status):
            headers = {"Authorization": f"Bearer {token_jwt}"}
            res = requests.patch(f"{API_URL}/pedidos/{pedido_id}/status", json={"novo_status": novo_status}, headers=headers)
            if res.status_code == 200: 
                ir_para_painel_gerente()
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao atualizar: {res.text}"))
                page.snack_bar.open = True
                page.update()

        botoes_layout = [
            ft.Button("🏪 Ir para Tela de Vendas", bgcolor="green", color="white", on_click=lambda _: ir_para_home_cliente(), width=400)
        ]
        
        if tipo_usuario in ["ADMIN", "GERENTE"]:
            texto_botao = "👑 Promover Usuários" if tipo_usuario == "ADMIN" else "👥 Gerenciar Equipe"
            botoes_layout.append(
                ft.Button(texto_botao, bgcolor="purple", color="white", on_click=lambda _: ir_para_tela_promocao(), width=400)
            )
            
            botoes_layout.append(
                ft.Button("📦 Gerenciar Estoque", bgcolor="blue", color="white", on_click=lambda _: ir_para_tela_estoque(), width=400)
            )

            botoes_layout.append(
                ft.Button("📊 Relatórios Gerenciais (BI)", bgcolor="teal", color="white", on_click=lambda _: ir_para_tela_bi(), width=400)
            )


        if tipo_usuario == "ADMIN":
            botoes_layout.append(
                ft.Button("📋 Ver Logs de Auditoria", bgcolor="black", color="white", on_click=lambda _: ir_para_tela_auditoria(), width=400)
            )

        layout_painel = ft.Column(expand=True, controls=[
            ft.Row([
                ft.Text("Painel de Gestão", size=20, weight="bold", color="red"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([filtro_ocultar_finalizados, filtro_canal], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                ft.TextButton("🔄 Atualizar", on_click=buscar_pedidos, tooltip="Atualizar")
            ], alignment=ft.MainAxisAlignment.END),
            *botoes_layout,
            ft.Divider(),
            coluna_pedidos,
            ft.TextButton("🚪 Sair", on_click=ir_para_tela_inicial)
        ])
        
        mudar_tela(layout_painel)
        buscar_pedidos()

        
    # ==========================================
    # TELA DE PROMOÇÃO DE USUÁRIOS E GESTÃO DE EQUIPE
    # ==========================================
    def ir_para_tela_promocao(e=None):
        email_input_promo = ft.TextField(label="E-mail do Cliente cadastrado", width=300)
        
        opcoes_cargos = [
            ft.dropdown.Option(key="FUNCIONARIO", text="Funcionário"),
            ft.dropdown.Option(key="CLIENTE", text="Rebaixar para Cliente")
        ]
        
        if tipo_usuario == "ADMIN":
            opcoes_cargos.insert(0, ft.dropdown.Option(key="GERENTE", text="Gerente"))

        tipo_dropdown_promo = ft.Dropdown(
            label="Novo Cargo",
            options=opcoes_cargos,
            width=300,
            value="GERENTE" if tipo_usuario == "ADMIN" else "FUNCIONARIO"
        )
        
        gerente_unidade_id = None
        headers = {"Authorization": f"Bearer {token_jwt}"}
        if tipo_usuario == "GERENTE":
            try:
                res_me = requests.get(f"{API_URL}/usuarios/me", headers=headers)
                if res_me.status_code == 200:
                    gerente_unidade_id = res_me.json().get("unidade_id")
            except Exception:
                pass

        unidades_opcoes = []
        try:
            res = requests.get(f"{API_URL}/unidades")
            if res.status_code == 200:
                for u in res.json():
                    if tipo_usuario == "GERENTE" and gerente_unidade_id and u["id"] != gerente_unidade_id:
                        continue
                    unidades_opcoes.append(ft.dropdown.Option(key=str(u["id"]), text=u["nome"]))
        except Exception:
            pass
            
        if not unidades_opcoes:
            unidades_opcoes.append(ft.dropdown.Option(key="1", text="Matriz Raízes"))

        unidade_dropdown_promo = ft.Dropdown(
            label="Vincular a qual Loja?",
            options=unidades_opcoes,
            width=300,
            value=unidades_opcoes[0].key
        )
        
        if tipo_usuario == "GERENTE":
            unidade_dropdown_promo.disabled = True

        status_texto_promo = ft.Text(value="", color="red")
        
        # Seletor de Classificação / Ordenação
        ordenacao_dropdown = ft.Dropdown(
            label="Classificar por",
            options=[
                ft.dropdown.Option(key="nome", text="Nome (A-Z)"),
                ft.dropdown.Option(key="id", text="ID"),
                ft.dropdown.Option(key="loja", text="Loja"),
                ft.dropdown.Option(key="cargo", text="Cargo"),
            ],
            value="nome",
            width=380,
        )

        equipe_lista_col = ft.ListView(expand=True, spacing=4, padding=5)
        membros_cache = []

        def aplicar_ordenacao_e_renderizar(e=None):
            equipe_lista_col.controls.clear()
            if not membros_cache:
                equipe_lista_col.controls.append(ft.Text("Nenhum colaborador encontrado."))
                page.update()
                return

            criterio = ordenacao_dropdown.value
            if criterio == "nome":
                membros_ordenados = sorted(membros_cache, key=lambda x: x['nome_completo'].lower())
            elif criterio == "id":
                membros_ordenados = sorted(membros_cache, key=lambda x: x['id'])
            elif criterio == "loja":
                membros_ordenados = sorted(membros_cache, key=lambda x: (x['unidade_id'] or 0))
            elif criterio == "cargo":
                membros_ordenados = sorted(membros_cache, key=lambda x: x['tipo'])
            else:
                membros_ordenados = membros_cache

            for m in membros_ordenados:
                texto_linha = f"ID: {m['id']} • {m['nome_completo']} ({m['email']}) • [{m['tipo']}] • Loja: {m['unidade_id']}"
                equipe_lista_col.controls.append(
                    ft.Container(
                        padding=8,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=4,
                        content=ft.Text(texto_linha, size=13, weight=ft.FontWeight.W_500)
                    )
                )
            page.update()

        ordenacao_dropdown.on_change = aplicar_ordenacao_e_renderizar

        def carregar_equipe():
            nonlocal membros_cache
            try:
                res_eq = requests.get(f"{API_URL}/usuarios/equipe", headers=headers)
                if res_eq.status_code == 200:
                    membros_cache = res_eq.json()
                    aplicar_ordenacao_e_renderizar()
                else:
                    equipe_lista_col.controls.append(ft.Text("Erro ao carregar equipe.", color="red"))
                    page.update()
            except Exception as ex:
                equipe_lista_col.controls.append(ft.Text(f"Erro de conexão: {ex}", color="red"))
                page.update()

        carregar_equipe()

        def confirmar_promocao(e):
            email_limpo = email_input_promo.value.strip() if email_input_promo.value else ""
            
            if not email_limpo:
                status_texto_promo.value = "Digite o e-mail do usuário."
                page.update()
                return
            
            payload = {
                "email": email_limpo,
                "novo_tipo": tipo_dropdown_promo.value,
                "unidade_id": int(unidade_dropdown_promo.value)
            }
            
            try:
                res = requests.patch(f"{API_URL}/usuarios/promover", json=payload, headers=headers)
                if res.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("Usuário atualizado com sucesso!"), bgcolor="green")
                    page.snack_bar.open = True
                    email_input_promo.value = ""
                    carregar_equipe()
                else:
                    status_texto_promo.value = f"Erro: {res.json().get('message', res.text)}"
                    page.update()
            except Exception as ex:
                status_texto_promo.value = f"Erro de conexão: {ex}"
                page.update()

        conteudo_promo = ft.Column([
            ft.Text("👑" if tipo_usuario == "ADMIN" else "👥", size=40),
            ft.Text("Painel de Gestão de Equipe", size=22, weight="bold", color="purple"),
            ft.Text("Promova usuários e visualize colaboradores vinculados.", size=12, color="grey"),
            ft.Container(height=10),
            email_input_promo,
            tipo_dropdown_promo,
            unidade_dropdown_promo,
            ft.Button("Confirmar Alteração", bgcolor="purple", color="white", width=300, on_click=confirmar_promocao),
            status_texto_promo,
            ft.Divider(),
            ft.Row([
                ft.Text("Colaboradores Vinculados:", weight="bold", size=15),
            ], alignment=ft.MainAxisAlignment.START),
            ordenacao_dropdown,
            ft.Container(
                content=equipe_lista_col, 
                height=160, 
                width=380, 
                bgcolor=ft.Colors.GREY_50, 
                border_radius=8, 
                padding=5
            ),
            ft.Container(height=10),
            ft.TextButton("Voltar ao Painel", on_click=lambda _: ir_para_painel_gerente())
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        mudar_tela(ft.ListView(expand=True, controls=[conteudo_promo], padding=20))


    # ==========================================
    # TELA DE AUDITORIA (EXCLUSIVA ADMIN)
    # ==========================================
    def ir_para_tela_auditoria(e=None):
        lista_logs_col = ft.ListView(expand=True, spacing=10, padding=10)
        status_texto = ft.Text(value="", color="red")

        def carregar_logs():
            lista_logs_col.controls.clear()
            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.get(f"{API_URL}/auditoria", headers=headers)
                if res.status_code == 200:
                    logs = res.json()
                    if not logs:
                        lista_logs_col.controls.append(ft.Text("Nenhum log registrado ainda.", color="grey"))
                    else:
                        for log in logs:
                            # Formatação da data para leitura amigável
                            data_formatada = log['data_hora'].replace("T", " ")[:19]
                            
                            # Criação do Card para cada Log
                            lista_logs_col.controls.append(
                                ft.Card(
                                    content=ft.Container(
                                        padding=15,
                                        border=ft.border.Border(
                                            left=ft.border.BorderSide(4, "red" if log['acao'] == "PROMOVER_USUARIO" else "blue")
                                        ),
                                        content=ft.Column([
                                            ft.Row([
                                                ft.Text(f"Ação: {log['acao']}", weight="bold", size=14),
                                                ft.Text(f"ID Usuário: {log['usuario_id']}", size=12, color="grey")
                                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                            ft.Text(log['detalhes'], size=16),
                                            ft.Text(f"Data: {data_formatada}", size=12, color="grey", text_align=ft.TextAlign.RIGHT)
                                        ])
                                    )
                                )
                            )
                else:
                    status_texto.value = "Acesso negado ou erro ao buscar logs."
            except Exception as ex:
                status_texto.value = f"Erro de conexão: {ex}"
            page.update()

        carregar_logs()

        conteudo_auditoria = ft.Column([
            ft.Text("📋", size=40),
            ft.Text("Logs de Auditoria", size=22, weight="bold"),
            ft.Text("Histórico das últimas 100 ações críticas do sistema.", size=12, color="grey"),
            ft.Container(height=10),
            status_texto,
            ft.Container(
                content=lista_logs_col, 
                height=450, 
                width=400, 
                bgcolor=ft.Colors.GREY_50, 
                border_radius=8, 
                padding=5
            ),
            ft.Container(height=10),
            ft.Button("🔄 Atualizar Lista", on_click=lambda _: carregar_logs(), bgcolor="grey", color="white", width=300),
            ft.TextButton("Voltar ao Painel", on_click=lambda _: ir_para_painel_gerente())
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        mudar_tela(conteudo_auditoria)


    # ==========================================
    # TELA DE GESTÃO DE ESTOQUE
    # ==========================================
    def ir_para_tela_estoque(e=None):
        status_texto = ft.Text(value="", color="red")
        
        dropdown_produto = ft.Dropdown(label="Selecione o Produto", width=400)
        dropdown_loja_cad = ft.Dropdown(label="Loja (Destino)", width=400, visible=(tipo_usuario == "ADMIN"))
        input_quantidade = ft.TextField(label="Nova Quantidade", width=400, keyboard_type=ft.KeyboardType.NUMBER)
        
        # Filtros de listagem
        filtro_loja_lista = ft.Dropdown(
            label="Filtrar por Loja", 
            width=200, 
            options=[ft.dropdown.Option(key="TODOS", text="Todas as Lojas")],
            value="TODOS"
        )
        filtro_item_lista = ft.Dropdown(
            label="Filtrar por Item", 
            width=200, 
            options=[ft.dropdown.Option(key="TODOS", text="Todos os Itens")],
            value="TODOS"
        )

        estoque_lista_col = ft.ListView(expand=True, spacing=4, padding=5)
        estoque_cache = []

        def aplicar_filtros_e_renderizar(e=None):
            estoque_lista_col.controls.clear()
            if not estoque_cache:
                estoque_lista_col.controls.append(ft.Text("Nenhum registro de estoque encontrado.", color="grey"))
                page.update()
                return

            # Captura segura dos valores considerando o evento disparado
            loja_filtro = filtro_loja_lista.value
            item_filtro = filtro_item_lista.value
            if e and hasattr(e, "control") and e.control:
                if e.control == filtro_loja_lista:
                    loja_filtro = e.control.value
                elif e.control == filtro_item_lista:
                    item_filtro = e.control.value

            filtrados = []
            for est in estoque_cache:
                if loja_filtro != "TODOS" and str(est['unidade_id']) != str(loja_filtro):
                    continue
                if item_filtro != "TODOS" and str(est['item_cardapio_id']) != str(item_filtro):
                    continue
                filtrados.append(est)

            if not filtrados:
                estoque_lista_col.controls.append(ft.Text("Nenhum item corresponde aos filtros.", color="grey"))
            else:
                for est in filtrados:
                    texto_linha = f"[{est.get('unidade_nome', 'Loja')}]  •  {est['nome_item']}"
                    estoque_lista_col.controls.append(
                        ft.Container(
                            padding=8,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=4,
                            content=ft.Row([
                                ft.Text(texto_linha, size=13, weight=ft.FontWeight.W_500),
                                ft.Text(f"{est['quantidade']} un.", size=13, weight=ft.FontWeight.BOLD, color="blue")
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
            page.update()

#        filtro_loja_lista.on_change = aplicar_filtros_e_renderizar
#        filtro_item_lista.on_change = aplicar_filtros_e_renderizar

        def carregar_estoque():
            nonlocal estoque_cache
            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.get(f"{API_URL}/estoque", headers=headers)
                if res.status_code == 200:
                    estoque_cache = res.json()
                    aplicar_filtros_e_renderizar()
                else:
                    estoque_lista_col.controls.append(ft.Text("Erro ao carregar estoque.", color="red"))
                    page.update()
            except Exception as ex:
                estoque_lista_col.controls.append(ft.Text(f"Erro de conexão: {ex}", color="red"))
                page.update()

        def carregar_opcoes():
            try:
                res_card = requests.get(f"{API_URL}/cardapio")
                if res_card.status_code == 200:
                    itens = res_card.json()
                    dropdown_produto.options = [ft.dropdown.Option(key=str(i['id']), text=i['nome']) for i in itens]
                    filtro_item_lista.options = [ft.dropdown.Option(key="TODOS", text="Todos os Itens")] + [
                        ft.dropdown.Option(key=str(i['id']), text=i['nome']) for i in itens
                    ]

                res_un = requests.get(f"{API_URL}/unidades")
                if res_un.status_code == 200:
                    unidades = res_un.json()
                    if tipo_usuario == "ADMIN":
                        dropdown_loja_cad.options = [ft.dropdown.Option(key=str(u['id']), text=u['nome']) for u in unidades]
                        if unidades:
                            dropdown_loja_cad.value = str(unidades[0]['id'])
                    
                    filtro_loja_lista.options = [ft.dropdown.Option(key="TODOS", text="Todas as Lojas")] + [
                        ft.dropdown.Option(key=str(u['id']), text=u['nome']) for u in unidades
                    ]
            except Exception as ex:
                status_texto.value = f"Erro ao carregar opções: {ex}"

        def salvar_estoque(e):
            if not dropdown_produto.value or not input_quantidade.value:
                status_texto.value = "Selecione o produto e preencha a quantidade."
                page.update()
                return
            
            try:
                nova_qtd = int(input_quantidade.value)
            except ValueError:
                status_texto.value = "A quantidade deve ser um número inteiro."
                page.update()
                return

            payload = {
                "item_cardapio_id": int(dropdown_produto.value),
                "quantidade": nova_qtd
            }
            if tipo_usuario == "ADMIN" and dropdown_loja_cad.value:
                payload["unidade_id"] = int(dropdown_loja_cad.value)

            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.put(f"{API_URL}/estoque", json=payload, headers=headers)
                if res.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("Estoque atualizado com sucesso!"), bgcolor="green")
                    page.snack_bar.open = True
                    input_quantidade.value = ""
                    status_texto.value = ""
                    carregar_estoque()
                else:
                    status_texto.value = f"Erro: {res.json().get('message', res.text)}"
                    page.update()
            except Exception as ex:
                status_texto.value = f"Erro de conexão: {ex}"
                page.update()

        carregar_opcoes()
        carregar_estoque()

        controles_formulario = [
            ft.Text("📦 Gestão de Estoque", size=22, weight="bold", color="blue"),
            dropdown_produto,
        ]
        if tipo_usuario == "ADMIN":
            controles_formulario.append(dropdown_loja_cad)
        
        controles_formulario.extend([
            input_quantidade,
            ft.Button("Atualizar Estoque", bgcolor="blue", color="white", width=380, on_click=salvar_estoque),
            status_texto,
            ft.Divider(),

            ft.Container(
                            width=410,
                            content=ft.Column([
                                ft.Text("Filtrar Listagem:", weight="bold", size=14),
                                ft.Row([filtro_loja_lista, filtro_item_lista], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row(
                                    [
                                        ft.Button(
                                            "🔎 Aplicar Filtros", 
                                            on_click=aplicar_filtros_e_renderizar, 
                                            bgcolor=ft.Colors.GREY_300, 
                                            color=ft.Colors.BLACK,
                                            width=160 # Botão compacto
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.END # Empurra o botão para a direita, como na seta!
                                )
                            ])
                        ),
                        
            ft.Container(height=5),
            
            # LISTA ALARGADA (width passou de 380 para 410)
            ft.Container(
                content=estoque_lista_col, 
                height=180, 
                width=410, 
                bgcolor=ft.Colors.GREY_50, 
                border_radius=8, 
                padding=5
            ),
            ft.Container(height=5),
            ft.TextButton("Voltar ao Painel", on_click=lambda _: ir_para_painel_gerente())
        ])

        conteudo_estoque = ft.Column(
            controls=controles_formulario, 
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            expand=True
        )

        mudar_tela(ft.ListView(expand=True, controls=[conteudo_estoque], padding=20))

        
    # ==========================================
    # TELA DE RELATÓRIOS GERENCIAIS (BI)
    # ==========================================
    def ir_para_tela_bi(e=None):
        painel_indicadores = ft.Column(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)
        status_texto = ft.Text(value="Carregando métricas...", color="blue")

        def carregar_dados_bi():
            painel_indicadores.controls.clear()
            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.get(f"{API_URL}/relatorios/bi", headers=headers)
                if res.status_code == 200:
                    dados = res.json()
                    status_texto.value = ""
                    
                    # Cards Superiores (Kpis Gerais)
                    kpis_row = ft.Row([
                        ft.Card(content=ft.Container(padding=15, width=190, bgcolor=ft.Colors.WHITE, content=ft.Column([
                            ft.Text("Faturamento", size=12, color="grey"),
                            ft.Text(f"R$ {dados['faturamento_total']:.2f}", size=20, weight="bold", color="green")
                        ]))),
                        ft.Card(content=ft.Container(padding=15, width=190, bgcolor=ft.Colors.WHITE, content=ft.Column([
                            ft.Text("Ticket Médio", size=12, color="grey"),
                            ft.Text(f"R$ {dados['ticket_medio']:.2f}", size=20, weight="bold", color="blue")
                        ])))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    
                    kpis_row_2 = ft.Row([
                        ft.Card(content=ft.Container(padding=15, width=190, bgcolor=ft.Colors.WHITE, content=ft.Column([
                            ft.Text("Total Pedidos", size=12, color="grey"),
                            ft.Text(f"{dados['total_pedidos']}", size=20, weight="bold", color="black")
                        ]))),
                        ft.Card(content=ft.Container(padding=15, width=190, bgcolor=ft.Colors.WHITE, content=ft.Column([
                            ft.Text("SLA (Tempo Médio)", size=12, color="grey"),
                            ft.Text(f"{dados['sla_medio_minutos']} min", size=20, weight="bold", color="red")
                        ])))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

                    painel_indicadores.controls.extend([kpis_row, kpis_row_2, ft.Divider()])

                    # Itens mais vendidos
                    itens_ui = [ft.Text("🏆 Top 5 Itens Mais Vendidos", weight="bold", size=16)]
                    for item in dados['top_itens']:
                        itens_ui.append(ft.Row([
                            ft.Text(item['nome']),
                            ft.Text(f"{item['quantidade']} un.", weight="bold", color="orange")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                    
                    painel_indicadores.controls.append(
                        ft.Container(padding=15, bgcolor=ft.Colors.GREY_100, border_radius=8, content=ft.Column(itens_ui))
                    )

                    # Desempenho da Equipe
                    equipe_ui = [ft.Text("👥 Vendas por Funcionário (Caixa)", weight="bold", size=16)]
                    for f in dados['vendas_por_funcionario']:
                        equipe_ui.append(ft.Row([
                            ft.Text(f['nome']),
                            ft.Text(f"R$ {f['arrecadado']:.2f} ({f['pedidos']} ped.)", weight="bold", color="teal")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))

                    painel_indicadores.controls.append(
                        ft.Container(padding=15, bgcolor=ft.Colors.GREY_100, border_radius=8, content=ft.Column(equipe_ui))
                    )
                else:
                    status_texto.value = "Erro ao carregar dados do BI."
                    status_texto.color = "red"
            except Exception as ex:
                status_texto.value = f"Erro de conexão: {ex}"
                status_texto.color = "red"
            
            page.update()

        conteudo_bi = ft.Column([
            ft.Text("📊 Relatórios Gerenciais (BI)", size=22, weight="bold", color="teal"),
            ft.Text("Visão Global" if tipo_usuario == "ADMIN" else "Visão Local da Unidade", size=12, color="grey"),
            ft.Container(height=10),
            status_texto,
            ft.Container(content=painel_indicadores, height=500, width=410),
            ft.Container(height=10),
            ft.TextButton("Voltar ao Painel", on_click=lambda _: ir_para_painel_gerente())
        ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        mudar_tela(ft.Container(content=conteudo_bi, padding=20, expand=True))
        carregar_dados_bi()





    # ==========================================
    # CARREGAMENTO DO CARDÁPIO E FUNÇÕES AUXILIARES
    # ==========================================
    def carregar_cardapio_tela():
        cardapio_col = ft.ListView(expand=True, spacing=10, padding=15)
        
        qtd_carrinho = sum(i['quantidade'] for i in carrinho)
        badge_carrinho = ft.Stack([
            ft.TextButton("🛒 Carrinho", on_click=lambda _: abrir_carrinho()),
            ft.Container(
                content=ft.Text(str(qtd_carrinho), size=12, color="white", weight="bold"),
                bgcolor="red", width=20, height=20, border_radius=10,
                alignment=ft.alignment.Alignment(0, 0),
                right=0, top=0,
                visible=qtd_carrinho > 0
            )
        ])

        cardapio_col.controls.append(ft.Row([
            ft.Text(f"Loja: {unidade_atual} | Canal: {canal_atual}", weight="bold", color="blue"),
            badge_carrinho
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
        
        try:
            res = requests.get(f"{API_URL}/cardapio")
            if res.status_code == 200:
                for item in res.json():
                    qtd_no_carrinho = next((c['quantidade'] for c in carrinho if c['item_id'] == item['id']), 0)
                    
                    controles_qtd = ft.Row([
                        ft.TextButton(" ➖ ", on_click=lambda e, p=item: remover_item(p), style=ft.ButtonStyle(color="red")),
                        ft.Text(str(qtd_no_carrinho), weight="bold", size=16),
                        ft.TextButton(" ➕ ", on_click=lambda e, p=item: adicionar_item(p), style=ft.ButtonStyle(color="green"))
                    ], alignment=ft.MainAxisAlignment.CENTER)

                    cardapio_col.controls.append(ft.Card(content=ft.Container(padding=10, content=ft.Column([
                        ft.Text(item['nome'], weight="bold"),
                        ft.Text(f"R$ {item['preco']:.2f}", color="green"),
                        controles_qtd
                    ]))))
        except Exception:
            pass
        
        cardapio_col.controls.append(ft.Container(height=45))
        cardapio_col.controls.append(
            ft.Button(
                "🛒 Ir para o Carrinho / Pagamento", 
                on_click=lambda _: abrir_carrinho(), 
                bgcolor=ft.Colors.GREEN, 
                color=ft.Colors.WHITE, 
                width=250
            )
        )

        cardapio_col.controls.append(ft.TextButton("Voltar para Escolha de Loja", on_click=ir_para_home_cliente))
        mudar_tela(cardapio_col)

    def adicionar_item(produto):
        encontrado = False
        for item in carrinho:
            if item['item_id'] == produto['id']:
                item['quantidade'] += 1
                encontrado = True
                break
        if not encontrado: 
            carrinho.append({"item_id": produto['id'], "nome": produto['nome'], "preco": produto['preco'], "quantidade": 1})
        carregar_cardapio_tela()

    def remover_item(produto):
        for item in carrinho:
            if item['item_id'] == produto['id']:
                item['quantidade'] -= 1
                if item['quantidade'] <= 0: 
                    carrinho.remove(item)
                break
        carregar_cardapio_tela()


# ==========================================
    # TELA 4: FLUXO DO CLIENTE E FUNCIONÁRIO (LOJA, CANAL E PERFIL)
    # ==========================================
    def ir_para_home_cliente(e=None):
        boas_vindas = "Visitante" if tipo_usuario == "VISITANTE" else ("Equipe" if tipo_usuario in ["ADMIN", "GERENTE", "FUNCIONARIO"] else "Cliente")
        
        # --- Lógica do Modal de Perfil via Stack (100% Estável no Web) ---
        conteudo_perfil_col = ft.Column(spacing=8, tight=True)

        def fechar_perfil(e):
            modal_perfil.visible = False
            modal_perfil.update()

        modal_perfil = ft.Container(
            visible=False,
            expand=True,
            bgcolor="black54",
            alignment=ft.alignment.Alignment(0, 0),
            content=ft.Container(
                bgcolor="white",
                padding=20,
                border_radius=12,
                width=350,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row([
                            ft.Text("Meu Perfil", weight="bold", size=18),
                            ft.TextButton("X", on_click=fechar_perfil, style=ft.ButtonStyle(color="red"))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(),
                        conteudo_perfil_col,
                        ft.Container(height=10),
                        ft.Button("Fechar", on_click=fechar_perfil, bgcolor="blue", color="white", width=310)
                    ]
                )
            )
        )

        def abrir_perfil(e):
            conteudo_perfil_col.controls = [ft.Text("Buscando dados no servidor...")]
            modal_perfil.visible = True
            modal_perfil.update()

            headers = {"Authorization": f"Bearer {token_jwt}"}
            try:
                res = requests.get(f"{API_URL}/usuarios/me", headers=headers)
                if res.status_code == 200:
                    dados = res.json()
                    conteudo_perfil_col.controls = [
                        ft.Text(f"Nome: {dados['nome_completo']}", weight="bold"),
                        ft.Text(f"E-mail: {dados['email']}"),
                        ft.Text(f"CPF: {dados['cpf']}"),
                        ft.Divider(),
                        ft.Text(f"Pontos de Fidelidade: {dados['pontos_fidelidade']}", color="green", weight="bold", size=18)
                    ]
                else:
                    conteudo_perfil_col.controls = [ft.Text("Não foi possível carregar os dados.", color="red")]
            except Exception as ex:
                conteudo_perfil_col.controls = [ft.Text(f"Erro de conexão com a API: {ex}", color="red")]
            
            conteudo_perfil_col.update()
        # ----------------------------------

        botoes_topo = []
        if tipo_usuario == "CLIENTE":
            botoes_topo.append(ft.TextButton("👤 Meu Perfil", tooltip="Ver meus dados e pontos", on_click=abrir_perfil))

        usuario_unidade_id = None
        if token_jwt and tipo_usuario in ["GERENTE", "FUNCIONARIO"]:
            try:
                res_me = requests.get(f"{API_URL}/usuarios/me", headers={"Authorization": f"Bearer {token_jwt}"})
                if res_me.status_code == 200:
                    usuario_unidade_id = res_me.json().get("unidade_id")
            except Exception:
                pass

        unidades_opcoes = []
        try:
            res = requests.get(f"{API_URL}/unidades")
            if res.status_code == 200:
                for u in res.json():
                    if usuario_unidade_id and u["id"] != usuario_unidade_id:
                        continue
                    unidades_opcoes.append(ft.dropdown.Option(key=str(u["id"]), text=u["nome"]))
        except Exception:
            pass
            
        if not unidades_opcoes:
            unidades_opcoes.append(ft.dropdown.Option(key="1", text="Matriz Raízes"))

        dropdown_loja = ft.Dropdown(label="Escolha a Loja", options=unidades_opcoes, width=300, value=unidades_opcoes[0].key)
        
        if tipo_usuario in ["GERENTE", "FUNCIONARIO"]:
            dropdown_loja.disabled = True

        dropdown_canal = ft.Dropdown(
            label="Como deseja ser atendido?",
            options=[
                ft.dropdown.Option(key="BALCAO", text="Retirar no Balcão"),
                ft.dropdown.Option(key="APP", text="Delivery (App)"),
                ft.dropdown.Option(key="TOTEM", text="Pedido no Totem"),
            ], width=300, value="APP"
        )

        def confirmar_selecao(e):
            global unidade_atual, canal_atual
            unidade_atual = int(dropdown_loja.value)
            canal_atual = dropdown_canal.value
            carregar_cardapio_tela()

        conteudo_home = ft.Column([
            ft.Row(botoes_topo, alignment=ft.MainAxisAlignment.END),
            ft.Text("🏪", size=50), 
            ft.Text(f"Olá, {boas_vindas}!", size=20, weight="bold"),
            ft.Text("Onde você está hoje?", size=16),
            dropdown_loja,
            dropdown_canal,
            ft.Container(height=20),
            ft.Button("Continuar para o Cardápio", on_click=confirmar_selecao, bgcolor="green", color="white", width=300),
            ft.TextButton("Voltar", on_click=lambda _: ir_para_painel_gerente() if tipo_usuario in ["ADMIN", "GERENTE", "FUNCIONARIO"] else ir_para_tela_inicial())
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

        # Envolve a tela principal e o modal num Stack para sobreposição perfeita
        tela_com_modal = ft.Stack(
            controls=[
                conteudo_home,
                modal_perfil
            ],
            expand=True
        )

        mudar_tela(tela_com_modal)

    # ==========================================
    # TELA 5: CARRINHO E FINALIZAÇÃO
    # ==========================================
    def abrir_carrinho():
        carrinho_col = ft.ListView(expand=True, padding=15)
        carrinho_col.controls.append(ft.Text("Carrinho de Compras", size=20, weight="bold"))
        
        total = sum(i['preco'] * i['quantidade'] for i in carrinho)
        for item in carrinho:
            carrinho_col.controls.append(ft.Text(f"{item['nome']} (x{item['quantidade']}) - R$ {item['preco']*item['quantidade']:.2f}"))
        carrinho_col.controls.append(ft.Text(f"Total: R$ {total:.2f}", weight="bold", size=18))
        
        cpf_cliente_input = None
        if tipo_usuario in ["ADMIN", "GERENTE", "FUNCIONARIO"]:
            cpf_cliente_input = ft.TextField(label="CPF do Cliente (Opcional - Pontos)", width=300)
            carrinho_col.controls.append(ft.Container(height=10))
            carrinho_col.controls.append(cpf_cliente_input)
        
        def finalizar_pedido(e):
            if not carrinho: return
            
            itens_comprados = list(carrinho)
            total_pedido = total
            headers = {"Authorization": f"Bearer {token_jwt}"} if token_jwt else {}
            
            payload = {
                "unidade_id": unidade_atual, 
                "canal_pedido": canal_atual, 
                "itens": [{"item_id": i["item_id"], "quantidade": i["quantidade"]} for i in carrinho]
            }
            
            if cpf_cliente_input and cpf_cliente_input.value:
                payload["cpf_cliente"] = cpf_cliente_input.value
            
            try:
                res = requests.post(f"{API_URL}/pedidos", json=payload, headers=headers)
                if res.status_code == 201:
                    pedido = res.json()
                    carrinho.clear()
                    
                    res_pag = requests.post(f"{API_URL}/pedidos/{pedido['id']}/pagamento", headers=headers)
                    if res_pag.status_code == 200:
                        status_pag_texto = "APROVADO (Enviado para a Cozinha)"
                        cor_status = "green"
                    else:
                        status_pag_texto = "RECUSADO / PEDIDO CANCELADO"
                        cor_status = "red"
                    
                    exibir_tela_confirmacao(pedido, status_pag_texto, cor_status, itens_comprados, total_pedido)
                else:
                    erro_detalhe = res.json().get("message", res.text)
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar pedido: {erro_detalhe}"), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro de conexão: {ex}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

        def voltar_e_limpar(e):
            carrinho.clear()
            carregar_cardapio_tela()

        carrinho_col.controls.append(ft.Container(height=20))
        carrinho_col.controls.append(ft.Button("Finalizar e Pagar", on_click=finalizar_pedido, bgcolor="green", color="white"))
        carrinho_col.controls.append(ft.TextButton("Voltar (Limpa o Carrinho)", on_click=voltar_e_limpar))
        mudar_tela(carrinho_col)

    # ==========================================
    # TELA 6: CONFIRMAÇÃO DO PEDIDO
    # ==========================================
    def exibir_tela_confirmacao(pedido, status_pag_texto, cor_status, itens_comprados, total_pedido):
        identificacao = email_input.value if token_jwt and email_input.value else "Não identificado (Visitante)"
        
        lista_itens_UI = []
        for item in itens_comprados:
            lista_itens_UI.append(ft.Text(f"• {item['quantidade']}x {item['nome']} - R$ {item['preco'] * item['quantidade']:.2f}"))

        def tentar_novamente(e):
            global carrinho
            carrinho.clear()
            carrinho.extend(itens_comprados)
            abrir_carrinho()

        botoes_finais = [ft.Button("Fazer Novo Pedido", on_click=ir_para_home_cliente, bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)]
        
        if status_pag_texto == "RECUSADO / PEDIDO CANCELADO":
            botoes_finais.insert(0, ft.Button("Tentar Novamente", on_click=tentar_novamente, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE))

        conteudo_conf = ft.Column([
            ft.Text("✅" if cor_status == "green" else "❌", size=50),
            ft.Text("Confirmação do Pedido", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Text(f"Número do Pedido: #{pedido['id']}", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(f"Resposta do Pagamento: {status_pag_texto}", color=cor_status, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(f"Canal de Atendimento: {pedido['canal_pedido']} | Loja: {pedido['unidade_id']}"),
            ft.Text(f"Identificação do Cliente: {identificacao}"),
            ft.Divider(),
            ft.Text("Descrição dos Itens:", weight=ft.FontWeight.BOLD), *lista_itens_UI,
            ft.Divider(),
            ft.Text(f"Valor Total: R$ {total_pedido:.2f}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
            ft.Container(height=20),
            ft.Row(botoes_finais, alignment=ft.MainAxisAlignment.CENTER, wrap=True)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
        
        mudar_tela(ft.ListView(expand=True, controls=[conteudo_conf], padding=20))

    page.add(conteudo_principal)
    ir_para_tela_inicial()

ft.run(main, view=ft.AppView.WEB_BROWSER)