import streamlit as st
import json
import pandas as pd
from datetime import datetime

# ==========================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Editor JSON Pessoal",
    page_icon="💾",
    layout="centered"
)

# CSS para esconder menu padrão e melhorar visual no celular
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 5rem; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stFileUploader"] {
        padding: 15px; border: 1px dashed #ccc; border-radius: 10px;
    }
    .stButton button {
        width: 100%; font-weight: bold; border-radius: 8px; height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 CONFIGURAÇÃO DO FORMULÁRIO (SEU CÓDIGO)
# ==========================================
# Mantive exatamente a sua estrutura
FORM_CONFIG = [
    {
        "name": "categoria",
        "label": "📂 Categoria",
        "type": "select",
        "options": ["Comida", "Leitura", "Vídeo", "Áudio", "Jogo"]
    },
    {
        "name": "titulo",
        "label": "🏷️ Título / Item",
        "type": "text",
        "placeholder": "Ex: Milkshake, O Alienista..."
    },
    {
        "name": "autor",
        "label": "✍️ Autor / Diretor",
        "type": "text",
        "placeholder": "Quem escreveu/dirigiu?",
        "show_if": {
            "field": "categoria",
            "values": ["Leitura", "Vídeo", "Áudio"]
        }
    },
    {
        "name": "local",
        "label": "📍 Local de Compra/Consumo",
        "type": "text",
        "placeholder": "Ex: Mart Minas, Padaria Pão Nosso...",
        "show_if": {
            "field": "categoria",
            "values": ["Comida"]
        }
    },    
    {
        "name": "preco",
        "label": "💲 Preço (R$)",
        "type": "number", # Usaremos text_input para permitir vírgula
        "placeholder": "Ex: 29,99",
        "show_if": {
            "field": "categoria",
            "values": ["Comida"]
        }
    },
    {
        "name": "ano_lancamento",
        "label": "📆 Ano de Lançamento",
        "type": "number",
        "placeholder": "Ex: 1999",
        "show_if": {
            "field": "categoria",
            "values": ["Vídeo", "Áudio", "Jogo"]
        }
    },
    {
        "name": "nota",
        "label": "🔢 Nota (0,0 a 5,0)",
        "type": "number",
        "placeholder": "Ex: 4,5"
    },
    {
        "name": "data_ref",
        "label": "📅 Data de Referência",
        "type": "date",
    },
    {
        "name": "obs",
        "label": "📝 Observações",
        "type": "textarea",
        "placeholder": "Detalhes adicionais..."
    }
]

# ==========================================
# 🛠️ FUNÇÕES DE GERENCIAMENTO
# ==========================================

# Inicializa Session State (Memória do App)
if "dados" not in st.session_state:
    st.session_state["dados"] = []
if "arquivo_carregado" not in st.session_state:
    st.session_state["arquivo_carregado"] = False

# ==========================================
# 1. ZONA DE UPLOAD
# ==========================================
st.title("💾 Gestor de Dados")

uploaded_file = st.file_uploader("1. Carregar arquivo JSON", type=["json"])

if uploaded_file is not None and not st.session_state["arquivo_carregado"]:
    try:
        dados_lidos = json.load(uploaded_file)
        if isinstance(dados_lidos, list):
            st.session_state["dados"] = dados_lidos
            st.session_state["arquivo_carregado"] = True
            st.success(f"Arquivo carregado! {len(dados_lidos)} registros.")
        else:
            st.error("O JSON precisa ser uma lista.")
    except Exception as e:
        st.error(f"Erro ao ler: {e}")

# ==========================================
# 2. RENDERIZAÇÃO DINÂMICA DO FORMULÁRIO
# ==========================================
st.divider()
st.subheader("2. Novo Registro")

# Dicionário para guardar os valores temporários do form
input_values = {}

# OBS: Não usamos 'with st.form' aqui para permitir que a condicional
# (show_if) funcione instantaneamente ao trocar a categoria.

for field in FORM_CONFIG:
    should_show = True
    
    # Lógica Condicional (Show If)
    if "show_if" in field:
        trigger_field = field["show_if"]["field"]
        allowed_values = field["show_if"]["values"]
        
        # Pega o valor atual do campo gatilho (ex: categoria)
        # Como o Streamlit roda o script de cima para baixo, o gatilho já foi renderizado
        current_trigger_val = input_values.get(trigger_field)
        
        if current_trigger_val not in allowed_values:
            should_show = False
    
    if should_show:
        # Renderiza o componente baseado no tipo
        if field["type"] == "select":
            val = st.selectbox(field["label"], field["options"], key=field["name"])
        
        elif field["type"] == "date":
            # Data padrão: hoje
            val = st.date_input(field["label"], datetime.now(), key=field["name"])
            
        elif field["type"] == "textarea":
            val = st.text_area(field["label"], placeholder=field.get("placeholder", ""), key=field["name"])
            
        elif field["type"] == "number":
            # TRUQUE: Usamos text_input para permitir vírgula, converteremos no final
            val = st.text_input(field["label"], placeholder=field.get("placeholder", ""), key=field["name"])
            
        else: # text
            val = st.text_input(field["label"], placeholder=field.get("placeholder", ""), key=field["name"])
            
        # Guarda o valor no dicionário
        input_values[field["name"]] = val

# Botão de Salvar
if st.button("➕ Adicionar Registro", type="primary"):
    # Monta o objeto final
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    erro_validacao = False
    
    # Processa os valores capturados
    for field in FORM_CONFIG:
        # Só processa se o campo estava visível (está no input_values)
        if field["name"] in input_values:
            raw_val = input_values[field["name"]]
            
            # Tratamento especial para números (Vírgula -> Ponto -> Float)
            if field["type"] == "number" and raw_val:
                try:
                    clean_val = str(raw_val).replace(',', '.')
                    entry[field["name"]] = float(clean_val)
                except ValueError:
                    st.toast(f"Erro: O valor '{raw_val}' em {field['label']} não é um número válido.", icon="❌")
                    erro_validacao = True
            
            # Tratamento para datas (converter para string)
            elif field["type"] == "date":
                entry[field["name"]] = str(raw_val)
                
            # Strings vazias viram None (opcional, gosto pessoal)
            elif isinstance(raw_val, str) and raw_val.strip() == "":
                entry[field["name"]] = None
                
            else:
                entry[field["name"]] = raw_val
    
    if not erro_validacao:
        st.session_state["dados"].append(entry)
        st.toast("Registro salvo com sucesso!", icon="✅")
        # Pequeno atraso para dar tempo do usuário ver o toast antes de recarregar (opcional)
        # st.rerun() # Descomente se quiser limpar o form após salvar

# ==========================================
# 3. DOWNLOAD
# ==========================================
st.divider()
st.subheader("3. Salvar Alterações")

if st.session_state["dados"]:
    # Mostra tabela invertida (últimos primeiro)
    df = pd.DataFrame(st.session_state["dados"])
    st.dataframe(df.tail(3).iloc[::-1], use_container_width=True, hide_index=True)
    
    # Prepara JSON
    json_str = json.dumps(st.session_state["dados"], indent=4, ensure_ascii=False)
    
    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        st.warning("Ao baixar, substitua o arquivo antigo no seu dispositivo.")
    with col_d2:
        st.download_button(
            label="📥 BAIXAR JSON",
            data=json_str,
            file_name="meu_banco.json",
            mime="application/json",
            type="primary"
        )
else:
    st.info("Nenhum dado para salvar.")