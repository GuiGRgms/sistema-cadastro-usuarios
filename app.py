"""
Sistema de Cadastro de Usuários
Um aplicativo profissional para gerenciamento de usuários com interface Streamlit
"""

import json
import logging
import shutil
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import streamlit as st
import pandas as pd

# Configuração da Página do Streamlit (Deve ser a primeira linha de comando do Streamlit)
st.set_page_config(
    page_title="Sistema de Cadastro de Usuários",
    page_icon="📝",
    layout="wide"
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sistema_cadastro.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Expressão regular para validação de email
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@dataclass
class Usuario:
    """Modelo de dados para usuário"""
    id: int
    nome: str
    email: str
    telefone: str
    idade: Optional[int]
    data_cadastro: str
    data_atualizacao: Optional[str] = None
    
    def __post_init__(self):
        self.validar()
    
    def validar(self):
        """Valida os dados do usuário"""
        if not self.nome or not self.nome.strip():
            raise ValueError("Nome não pode ser vazio")
        
        if not self.email or not self.email.strip():
            raise ValueError("Email não pode ser vazio")
        
        if not EMAIL_PATTERN.match(self.email):
            raise ValueError("Email inválido")
        
        if self.idade is not None and (self.idade < 0 or self.idade > 150):
            raise ValueError("Idade deve estar entre 0 e 150")
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Usuario':
        """Cria instância a partir de dicionário"""
        return cls(**data)


class SistemaCadastro:
    """Sistema principal de gerenciamento de cadastros"""
    
    def __init__(self, arquivo_dados: str = "data/usuarios.json"):
        self.arquivo_dados = Path(arquivo_dados)
        self.usuarios: List[Usuario] = []
        self.carregar_dados()
    
    def carregar_dados(self) -> None:
        """Carrega dados do arquivo JSON"""
        try:
            if self.arquivo_dados.exists():
                with open(self.arquivo_dados, 'r', encoding='utf-8') as arquivo:
                    dados = json.load(arquivo)
                    self.usuarios = [Usuario.from_dict(user) for user in dados]
                    logger.info(f"Dados carregados com sucesso. Total: {len(self.usuarios)} usuários")
            else:
                logger.info("Arquivo de dados não encontrado. Iniciando com lista vazia.")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            self.usuarios = []
        except Exception as e:
            logger.error(f"Erro ao carregar dados: {e}")
            self.usuarios = []
    
    def salvar_dados(self) -> bool:
        """Salva dados no arquivo JSON"""
        try:
            if self.arquivo_dados.exists():
                backup_path = self.arquivo_dados.with_suffix('.json.bak')
                shutil.copy2(self.arquivo_dados, backup_path)
            
            with open(self.arquivo_dados, 'w', encoding='utf-8') as arquivo:
                json.dump([user.to_dict() for user in self.usuarios], 
                           arquivo, indent=4, ensure_ascii=False)
            logger.info(f"Dados salvos com sucesso. Total: {len(self.usuarios)} usuários")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados: {e}")
            return False
    
    def cadastrar_usuario(self, nome: str, email: str, telephone: str, 
                          idade: Optional[int]) -> Tuple[bool, str]:
        """Cadastra novo usuário"""
        try:
            if self.verificar_email_existente(email):
                return False, "❌ Este e-mail já está cadastrado!"
            
            if idade is not None and (idade < 0 or idade > 150):
                return False, "❌ Idade deve estar entre 0 e 150 anos!"
            
            usuario = Usuario(
                id=self.gerar_id(),
                nome=nome.strip(),
                email=email.strip().lower(),
                telefone=telephone.strip() if telephone else "",
                idade=idade if idade and idade > 0 else None,
                data_cadastro=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            )
            
            self.usuarios.append(usuario)
            
            if self.salvar_dados():
                logger.info(f"Usuário cadastrado: {usuario.nome} (ID: {usuario.id})")
                return True, f"✅ Usuário '{nome}' cadastrado com sucesso!"
            return False, "❌ Erro ao salvar os dados!"
                
        except ValueError as e:
            return False, f"❌ {str(e)}"
        except Exception as e:
            logger.error(f"Erro ao cadastrar usuário: {e}")
            return False, "❌ Erro interno ao cadastrar usuário!"
    
    def verificar_email_existente(self, email: str) -> bool:
        """Verifica se email já está cadastrado"""
        return any(usuario.email == email.strip().lower() for usuario in self.usuarios)
    
    def gerar_id(self) -> int:
        """Gera novo ID automaticamente"""
        if not self.usuarios:
            return 1
        return max(usuario.id for usuario in self.usuarios) + 1
    
    def buscar_usuario(self, id_usuario: int) -> Optional[Usuario]:
        """Busca usuário por ID"""
        try:
            for usuario in self.usuarios:
                if usuario.id == id_usuario:
                    return usuario
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None
    
    def atualizar_usuario(self, id_usuario: int, nome: str, email: str, 
                          telefone: str, idade: Optional[int]) -> Tuple[bool, str]:
        """Atualiza dados do usuário"""
        try:
            usuario = self.buscar_usuario(id_usuario)
            if not usuario:
                return False, "❌ Usuário não encontrado!"
            
            if email and email != usuario.email and self.verificar_email_existente(email):
                return False, "❌ E-mail já está em uso por outro usuário!"
            
            if nome and nome.strip():
                usuario.nome = nome.strip()
            if email and email.strip():
                usuario.email = email.strip().lower()
            if telefone:
                usuario.telefone = telefone.strip()
            if idade is not None:
                if idade < 0 or idade > 150:
                    return False, "❌ Idade deve estar entre 0 e 150 anos!"
                usuario.idade = idade if idade > 0 else None
            
            usuario.data_atualizacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            if self.salvar_dados():
                logger.info(f"Usuário atualizado: ID {id_usuario}")
                return True, "✅ Usuário atualizado com sucesso!"
            return False, "❌ Erro ao salvar os dados!"
                
        except Exception as e:
            logger.error(f"Erro ao atualizar usuário: {e}")
            return False, "❌ Erro interno ao atualizar usuário!"
    
    def excluir_usuario(self, id_usuario: int) -> Tuple[bool, str]:
        """Exclui usuário do sistema"""
        try:
            usuario = self.buscar_usuario(id_usuario)
            if not usuario:
                return False, "❌ Usuário não encontrado!"
            
            self.usuarios = [u for u in self.usuarios if u.id != id_usuario]
            
            if self.salvar_dados():
                logger.info(f"Usuário excluído: {usuario.nome} (ID: {id_usuario})")
                return True, f"✅ Usuário '{usuario.nome}' excluído com sucesso!"
            return False, "❌ Erro ao salvar os dados!"
                
        except Exception as e:
            logger.error(f"Erro ao excluir usuário: {e}")
            return False, "❌ Erro interno ao excluir usuário!"
    
    def buscar_usuarios(self, termo: str = "") -> List[Usuario]:
        """Busca usuários por termo (ID, nome ou email)"""
        if not termo:
            return self.usuarios
        
        termo_lower = termo.lower().strip()
        resultados = []
        
        for usuario in self.usuarios:
            if (termo_lower == str(usuario.id) or 
                termo_lower in usuario.nome.lower() or 
                termo_lower in usuario.email.lower()):
                resultados.append(usuario)
        
        return resultados
    
    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas do sistema"""
        if not self.usuarios:
            return {"total": 0, "media_idade": 0, "mais_velho": None, "mais_novo": None}
        
        idades = [u.idade for u in self.usuarios if u.idade is not None]
        media_idade = sum(idades) / len(idades) if idades else 0
        
        mais_velho = max(self.usuarios, key=lambda x: x.idade if x.idade else 0) if idades else None
        mais_novo = min(self.usuarios, key=lambda x: x.idade if x.idade else 150) if idades else None
        
        return {
            "total": len(self.usuarios),
            "media_idade": media_idade,
            "com_idade": len(idades),
            "sem_idade": len(self.usuarios) - len(idades),
            "mais_velho": mais_velho,
            "mais_novo": mais_novo
        }


# ==========================================
# INTERFACE INTERATIVA DO STREAMLIT
# ==========================================

# Inicializa o sistema de cadastro
sistema = SistemaCadastro()

st.title("📝 Sistema de Cadastro de Usuários")
st.markdown("---")

# Criação das Abas de Navegação
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "➕ Cadastrar", 
    "🔍 Listar / Buscar", 
    "✏️ Atualizar", 
    "❌ Excluir", 
    "📊 Estatísticas"
])

# --- ABA 1: CADASTRAR ---
with aba1:
    st.subheader("Novo Cadastro")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo")
            telefone = st.text_input("Telefone")
        with col2:
            email = st.text_input("E-mail")
            idade = st.number_input("Idade", min_value=0, max_value=120, value=0)
            
        botao_cadastrar = st.form_submit_button("Salvar Cadastro", type="primary")
        
        if botao_cadastrar:
            sucesso, msg = sistema.cadastrar_usuario(nome, email, telefone, idade)
            if sucesso:
                st.success(msg)
            else:
                st.error(msg)

# --- ABA 2: LISTAR / BUSCAR ---
with aba2:
    st.subheader("Listagem e Busca")
    termo = st.text_input("Buscar por ID, Nome ou E-mail").strip()
    
    usuarios_filtrados = sistema.buscar_usuarios(termo)
    
    if usuarios_filtrados:
        # Transforma os objetos em uma tabela usando Pandas para ficar elegante
        lista_dicts = [u.to_dict() for u in usuarios_filtrados]
        df = pd.DataFrame(lista_dicts)
        
        # Renomeia as colunas do Dataframe para exibição
        df.columns = ["ID", "Nome", "E-mail", "Telefone", "Idade", "Data de Cadastro", "Última Atualização"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum usuário encontrado.")

# --- ABA 3: ATUALIZAR ---
with aba3:
    st.subheader("Atualizar Dados de Usuário")
    id_atualizar = st.number_input("Digite o ID do usuário que deseja editar", min_value=1, step=1)
    
    usuario_editar = sistema.buscar_usuario(id_atualizar)
    
    if usuario_editar:
        st.warning(f"Editando dados de: **{usuario_editar.nome}**")
        with st.form("form_atualizar"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Novo Nome", value=usuario_editar.nome)
                novo_tel = st.text_input("Novo Telefone", value=usuario_editar.telefone)
            with col2:
                novo_email = st.text_input("Novo E-mail", value=usuario_editar.email)
                nova_idade = st.number_input("Nova Idade", min_value=0, max_value=120, value=usuario_editar.idade if usuario_editar.idade else 0)
                
            botao_atualizar = st.form_submit_button("Salvar Alterações", type="primary")
            
            if botao_atualizar:
                sucesso, msg = sistema.atualizar_usuario(id_atualizar, novo_nome, novo_email, novo_tel, nova_idade)
                if sucesso:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("Digite um ID válido para carregar as informações.")

# --- ABA 4: EXCLUIR ---
with aba4:
    st.subheader("Remover Usuário do Sistema")
    id_excluir = st.number_input("Digite o ID do usuário que deseja excluir", min_value=1, step=1, key="id_exc")
    
    usuario_deletar = sistema.buscar_usuario(id_excluir)
    
    if usuario_deletar:
        st.error(f"⚠️ Atenção: Você está prestes a deletar o usuário **{usuario_deletar.nome}** (E-mail: {usuario_deletar.email}).")
        botao_excluir = st.button("Confirmar Exclusão Definitiva", type="primary", key="btn_exc")
        
        if botao_excluir:
            sucesso, msg = sistema.excluir_usuario(id_excluir)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
    else:
        st.info("Nenhum usuário selecionado.")

# --- ABA 5: ESTATÍSTICAS ---
with aba5:
    st.subheader("Indicadores do Sistema")
    estatisticas = sistema.obter_estatisticas()
    
    if estatisticas["total"] > 0:
        metric1, metric2, metric3 = st.columns(3)
        with metric1:
            st.metric("Total de Usuários", estatisticas["total"])
        with metric2:
            st.metric("Média de Idade", f"{estatisticas['media_idade']:.1f} anos")
        with metric3:
            st.metric("Usuários com Idade Informada", estatisticas["com_idade"])
            
        st.markdown("---")
        col_velho, col_novo = st.columns(2)
        
        with col_velho:
            if estatisticas["mais_velho"] and estatisticas["mais_velho"].idade:
                st.info(f"🧓 **Mais velho(a):** {estatisticas['mais_velho'].nome} ({estatisticas['mais_velho'].idade} anos)")
        with col_novo:
            if estatisticas["mais_novo"] and  estatisticas["mais_novo"].idade:
                st.success(f"👶 **Mais novo(a):** {estatisticas['mais_novo'].nome} ({estatisticas['mais_novo'].idade} anos)")
    else:
        st.info("Cadastre usuários para gerar os relatórios estatísticos.")