import datetime
from sqlalchemy.orm import Session
from database import SessionLocal 
from models import Unidade, Usuario, ItemCardapio, Campanha, Estoque
from security import get_password_hash 

def popular_banco():
    db: Session = SessionLocal()

    try:
        print("Iniciando seeding..")

        # =====================================++=====
        # UNIDADES
        # =========================================
        unidades_payload = [
            {"nome": "Matriz Raízes - Centro", "endereco": "Rua Principal, 100 - Centro"},
            {"nome": "Filial Raízes - Shopping", "endereco": "Av. das Nações, 2000 - Praça de Alimentação"},
            {"nome": "Filial Raízes - Zona Sul", "endereco": "Av. Beira Mar, 500 - Loja 2"}
        ]

        unidades_db = {}
        for u_data in unidades_payload:
            unidade = db.query(Unidade).filter(Unidade.nome == u_data["nome"]).first()
            if not unidade:
                unidade = Unidade(**u_data)
                db.add(unidade)
                db.commit()
                db.refresh(unidade)
                print(f"Unidade '{unidade.nome}' criada. ID:'{unidade.id}'")
            unidades_db[unidade.nome] = unidade

        # =========================================
        # USUARIOS
        # ==========================================
        # Nota: Preenchendo campos obrigatórios do novo esquema (cpf, endereco_entrega, data_nascimento)
        data_nasc_padrao = datetime.date(1990, 1, 1)
        usuarios_payload = [
            # ADMIN
            {"nome_completo": "Administrador Geral", "email": "admin@raizes.com.br", "senha_hash": get_password_hash("admin123"), "endereco_entrega": "N/A", "telefone": "123456789",  "cpf": "00000000000", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "ADMIN", "unidade_id": None},
            
            # GERENTES
            {"nome_completo": "Gerente Matriz", "email": "gerente.centro@raizes.com.br", "senha_hash": get_password_hash("gerente123"), "endereco_entrega": "N/A", "telefone": "123456780",  "cpf": "11111111111", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "GERENTE", "unidade_id": unidades_db["Matriz Raízes - Centro"].id},
            {"nome_completo": "Gerente Shopping", "email": "gerente.shopping@raizes.com.br", "senha_hash": get_password_hash("gerente123"), "endereco_entrega": "N/A", "telefone": "123456781",  "cpf": "22222222222", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "GERENTE", "unidade_id": unidades_db["Filial Raízes - Shopping"].id},
            {"nome_completo": "Gerente Zona Sul", "email": "gerente.zonasul@raizes.com.br", "senha_hash": get_password_hash("gerente123"), "endereco_entrega": "N/A", "telefone": "123456782",  "cpf": "33333333333", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "GERENTE", "unidade_id": unidades_db["Filial Raízes - Zona Sul"].id},
            
            # FUNCIONARIOS
            {"nome_completo": "Funcionario 1 Matriz", "email": "funcionario1.centro@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456783",  "cpf": "11111111112", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Matriz Raízes - Centro"].id},
            {"nome_completo": "Funcionario 2 Matriz", "email": "funcionario2.centro@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456784",  "cpf": "11111111113", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Matriz Raízes - Centro"].id},
            {"nome_completo": "Funcionario 3 Matriz", "email": "funcionario3.centro@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456785",  "cpf": "11111111114", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Matriz Raízes - Centro"].id},
            
            {"nome_completo": "Funcionario 1 Shopping", "email": "funcionario1.shopping@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456786",  "cpf": "22222222223", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Shopping"].id},
            {"nome_completo": "Funcionario 2 Shopping", "email": "funcionario2.shopping@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456787",  "cpf": "22222222226", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Shopping"].id},
            {"nome_completo": "Funcionario 3 Shopping", "email": "funcionario3.shopping@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456788",  "cpf": "22222222229", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Shopping"].id},
            
            {"nome_completo": "Funcionario 1 Zona Sul", "email": "funcionario1.zonasul@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456712",  "cpf": "33333333334", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Zona Sul"].id},
            {"nome_completo": "Funcionario 2 Zona Sul", "email": "funcionario2.zonasul@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456713",  "cpf": "33333333332", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Zona Sul"].id},
            {"nome_completo": "Funcionario 3 Zona Sul", "email": "funcionario3.zonasul@raizes.com.br", "senha_hash": get_password_hash("funcionario123"), "endereco_entrega": "N/A", "telefone": "123456714",  "cpf": "33333333336", "data_nascimento": data_nasc_padrao, "aceite_lgpd": True, "tipo": "FUNCIONARIO", "unidade_id": unidades_db["Filial Raízes - Zona Sul"].id},

            # CLIENTES
            {"nome_completo": "Jão Melao", "email": "jao@email.com", "senha_hash": get_password_hash("cliente123"), "endereco_entrega": "Rua das Orquideas, 12", "telefone": "123456212",  "cpf": "44444444444", "data_nascimento": datetime.date(1995, 5, 20), "aceite_lgpd": True, "tipo": "CLIENTE", "pontos_fidelidade": 50, "unidade_id": None},
            {"nome_completo": "Ria Oliveira", "email": "ria@email.com", "senha_hash": get_password_hash("cliente123"), "endereco_entrega": "Av. Brasil, 450",  "telefone": "123466712", "cpf": "55555555555", "data_nascimento": datetime.date(1988, 10, 15), "aceite_lgpd": True, "tipo": "CLIENTE", "pontos_fidelidade": 120, "unidade_id": None},
            {"nome_completo": "Lule Silva", "email": "lule@email.com", "senha_hash": get_password_hash("cliente123"), "endereco_entrega": "Rua das Camelias, 13", "telefone": "123499992",  "cpf": "13333444444", "data_nascimento": datetime.date(1905, 10, 13), "aceite_lgpd": True, "tipo": "CLIENTE", "pontos_fidelidade": 550, "unidade_id": None},
            {"nome_completo": "Flavie Bolseiro", "email": "flavie@email.com", "senha_hash": get_password_hash("cliente123"), "endereco_entrega": "Rua das Cerejeiras, 22",  "telefone": "155556712", "cpf": "22222444444", "data_nascimento": datetime.date(1915, 10, 22), "aceite_lgpd": True, "tipo": "CLIENTE", "pontos_fidelidade": 550, "unidade_id": None},
           
           
        ]

        for user_data in usuarios_payload:
            user = db.query(Usuario).filter(Usuario.cpf == user_data["cpf"]).first()
            if not user:
                novo_user = Usuario(**user_data)
                db.add(novo_user)
                print(f"👤 Usuário '{novo_user.nome_completo}' ({novo_user.tipo}) criado.")
        db.commit()

        # ==========================================
        # CARDÁPIO
        # =========================================
        cardapio_payload = [
            
            # LANCHES
            {"nome": "O Cabra da Peste", "descricao": "Hambúrguer de carne de sol, queijo coalho.", "preco": 32.90, "categoria": "LANCHES", "disponivel": 1},
            {"nome": "Sanduíche Lampião", "descricao": "Pão francês, pernil desfiado, abacaxi.", "preco": 28.50, "categoria": "LANCHES", "disponivel": 1},
            {"nome": "Sanduíche Maria Bonita", "descricao": "Pão francês, carne de gado, queijo, alface.", "preco": 29.50, "categoria": "LANCHES", "disponivel": 1},
            {"nome": "Sanduíche de Siri", "descricao": "Pão francês, carne de siri desfiado, molho de nata e mostarda.", "preco": 33.00, "categoria": "LANCHES", "disponivel": 1},
            
            # ACOMPANHAMENTOS
            {"nome": "Macaxeira Frita", "descricao": "Porção de 400g de macaxeira frita.", "preco": 18.00, "categoria": "ACOMPANHAMENTOS", "disponivel": 1},
            {"nome": "Dadinhos de Tapioca", "descricao": "10 unidades de dadinhos de tapioca.", "preco": 27.00, "categoria": "ACOMPANHAMENTOS", "disponivel": 1},
            {"nome": "Bolinho de banana", "descricao": "10 bolinho de banana da terra frita.", "preco": 16.00, "categoria": "ACOMPANHAMENTOS", "disponivel": 1},
            {"nome": "Porção de queijo coalho", "descricao": "10 unidades de queijo coalho assado.", "preco": 15.00, "categoria": "ACOMPANHAMENTOS", "disponivel": 1},

            # BEBIDAS
            {"nome": "Suco de Caju 500ml", "descricao": "Suco natural e refrescante de caju.", "preco": 9.50, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Cajuína 330ml", "descricao": "Bebida típica nordestina sem álcool.", "preco": 8.50, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Guaraná Jesu 290ml", "descricao": "Refrigerante nordestino.", "preco": 8.00, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Aluá 500ml", "descricao": "Bebeda fermentada a base de abacaxi adoçada com rapadura.", "preco": 10.00, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Água sem gás 500ml", "descricao": "Água.", "preco": 6.00, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Água com gás 500ml", "descricao": "Água.", "preco": 6.00, "categoria": "BEBIDAS", "disponivel": 1},
            {"nome": "Caldo de Cana", "descricao": "Caldo de cana com limão.", "preco": 8.00, "categoria": "BEBIDAS", "disponivel": 1},            
            
            # SOBREMESAS
            {"nome": "Cartola Tradicional", "descricao": "Banana assada com queijo manteiga e canela.", "preco": 16.00, "categoria": "SOBREMESAS", "disponivel": 1},
            {"nome": "Bolo de Rolo", "descricao": "Bolo de massa fina recheada com goiabada.", "preco": 20.00, "categoria": "SOBREMESAS", "disponivel": 1},
            {"nome": "Cocada", "descricao": "10 unidades de doce de coco.", "preco": 12.00, "categoria": "SOBREMESAS", "disponivel": 1},
            {"nome": "Rapadura", "descricao": "10 unidades de rapadura.", "preco": 12.00, "categoria": "SOBREMESAS", "disponivel": 1},
            
            
            # COMBOS
            {"nome": "Combo Arretado", "descricao": "1 Cabra da Peste + Porção de Macaxeira + Suco de Caju 500ml.", "preco": 55.50, "categoria": "COMBOS", "disponivel": 1},
            {"nome": "Combo do Sertão", "descricao": "1 Lampião + Porção de Dadinhos de tapioca + Guaraná Jesus 290ml.", "preco": 56.50, "categoria": "COMBOS", "disponivel": 1},
            {"nome": "Combo do Agreste", "descricao": "1 Maria bonita + Porção de Queijo Coalho + Suco de Caju 500ml.", "preco": 52.50, "categoria": "COMBOS", "disponivel": 1},
            {"nome": "Combo do Coronel", "descricao": "1 Sanduiche de Siri + Porção de Bolinho de Banana + Aluá 500ml + Bolo de Rolo.", "preco": 58.50, "categoria": "COMBOS", "disponivel": 1},
        ]

        itens_db = []
        for item_data in cardapio_payload:
            item = db.query(ItemCardapio).filter(ItemCardapio.nome == item_data["nome"]).first()
            if not item:
                item = ItemCardapio(**item_data)
                db.add(item)
                db.commit()
                db.refresh(item)
            itens_db.append(item)
        print(f"{len(itens_db)} itens do cardápio validados/criados.")

        # ==========================================
        # ESTOQUE UNIDADES
        # ==========================================
        # adicionar 50 un. cada para as lojas
        estoque_criado = 0
        for unidade_nome, unidade_obj in unidades_db.items():
            for item in itens_db:
                estoque_item = db.query(Estoque).filter(
                    Estoque.unidade_id == unidade_obj.id, 
                    Estoque.item_cardapio_id == item.id
                ).first()
                
                if not estoque_item:
                    novo_estoque = Estoque(
                        unidade_id=unidade_obj.id,
                        item_cardapio_id=item.id,
                        quantidade=50
                    )
                    db.add(novo_estoque)
                    estoque_criado += 1
        
        if estoque_criado > 0:
            db.commit()
            print(f" {estoque_criado} registros de estoque inicializados (50 un. por item em cada loja).")

        # ==========================================
        # CAMPANHAS PROMOCIONAIS
        # ==========================================
        
        campanhas_payload = [
            # Desconto aplicado a todos os itens de uma Categoria
            {"codigo": "LANCHE15", "desconto_percentual": 15.0, "tipo_aplicacao": "CATEGORIA", "categoria_alvo": "LANCHES", "item_alvo_id": None, "ativo": True, "unidade_id": None},
            {"codigo": "BEBIDA10", "desconto_percentual": 10.0, "tipo_aplicacao": "CATEGORIA", "categoria_alvo": "BEBIDAS", "item_alvo_id": None, "ativo": True, "unidade_id": None},
            
            # Desconto aplicado a um Item Específico (usando o ID do primeiro lanche criado: "O Cabra da Peste")
            {"codigo": "PROMO_CABRA", "desconto_percentual": 20.0, "tipo_aplicacao": "ITEM", "categoria_alvo": None, "item_alvo_id": itens_db[0].id, "ativo": True, "unidade_id": unidades_db["Matriz Raízes - Centro"].id}
        ]

        for camp_data in campanhas_payload:
            campanha = db.query(Campanha).filter(Campanha.codigo == camp_data["codigo"]).first()
            if not campanha:
                nova_campanha = Campanha(**camp_data)
                db.add(nova_campanha)
                print(f" Campanha '{nova_campanha.codigo}' criada.")
        db.commit()

        print(" Banco de dados populado com sucesso!")

    except Exception as e:
        db.rollback()
        print(f" Erro ao popular banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()