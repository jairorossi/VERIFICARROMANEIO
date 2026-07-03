import streamlit as st
import pdfplumber
import re
import os

# Configuração da página Streamlit
st.set_page_config(
    page_title="Extrator de Romaneios",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilo CSS customizado para garantir uma estética moderna e premium
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Configuração geral de fonte */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Título principal em gradiente moderno */
    .main-title {
        background: linear-gradient(90deg, #4f46e5 0%, #9333ea 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        text-align: center;
        margin-bottom: 0.2rem;
        padding-top: 1rem;
    }
    
    .sub-title {
        color: #9ca3af;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card de resultados premium */
    .result-card {
        background-color: #1e1b4b; /* Fundo roxo muito escuro */
        border-radius: 16px;
        padding: 1.8rem;
        border: 1px solid #4338ca;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -4px rgba(0, 0, 0, 0.3);
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .result-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f3f4f6;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #a78bfa;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Estilização do botão de cópia nativo do Streamlit para torná-lo super visível e premium */
    div[data-testid="stCodeBlock"] button {
        opacity: 1.0 !important;
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border: 1px solid #6366f1 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="stCodeBlock"] button:hover {
        background-color: #6366f1 !important;
        border-color: #818cf8 !important;
        transform: scale(1.08) !important;
    }
</style>
""", unsafe_allow_html=True)

# Título e Subtítulo customizados
st.markdown('<h1 class="main-title">Extrator de Romaneios</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Extraia números de Notas Fiscais ou Pedidos de PDFs de forma rápida e 100% web</p>', unsafe_allow_html=True)

# Container principal
st.write("---")

# Opções de configuração na tela principal em colunas
col1, col2 = st.columns(2)

with col1:
    tipo_extracao = st.radio(
        "O que você deseja extrair?",
        ["Notas Fiscais", "Pedidos"],
        help="Notas Fiscais: Número da coluna DOCUMENTO ou NOTA\nPedidos: Número da coluna PEDIDO"
    )

with col2:
    formato_saida = st.radio(
        "Formato do arquivo de saída:",
        ["Separado por vírgula (,)", "Um número por linha"],
        help="Separado por vírgula é ideal para buscas em massa em sistemas ERP."
    )

st.write("")

# Seletor de arquivo PDF
uploaded_file = st.file_uploader(
    "Carregue seu PDF de Romaneio aqui",
    type=["pdf"],
    accept_multiple_files=False,
    help="Selecione ou arraste qualquer arquivo PDF de romaneio."
)

def processar_pdf(pdf_file, tipo):
    documentos = []
    
    # Regex para o Layout 1 (Romaneio Carga)
    # DOCUMENTO (penúltimo número grande da linha, antes dos volumes)
    regex_doc_layout1 = re.compile(r'(\d{6,})\s+\d+(?:\s+\d+)*\s*$')
    # PEDIDO (número grande antes de um valor monetário formatado em R$)
    regex_ped_layout1 = re.compile(r'(?:[A-Z\s]+|(?<=\w))(\d{6,})\s+\d{1,3}(?:\.\d{3})*,\d{2}')
    
    layout = "romaneio" # Padrão inicial
    
    with pdfplumber.open(pdf_file) as pdf:
        # Detectar layout baseando-se no texto da primeira página
        if len(pdf.pages) > 0:
            texto_p1 = pdf.pages[0].extract_text() or ""
            if "Modelo 3: Transportadora" in texto_p1 or "NOTA PEDIDO CLIENTE" in texto_p1:
                layout = "transportadora"
            elif "ROMANEIO DE ENTREGA" in texto_p1 or "ENT CLIENTE PEDIDO" in texto_p1:
                layout = "romaneio"
        
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
            linhas = texto.split("\n")
            for linha in linhas:
                linha_clean = linha.strip()
                partes = linha_clean.split()
                
                if layout == "transportadora":
                    # Layout 2 (Entregas Transportadora):
                    # NOTA PEDIDO CLIENTE ...
                    # A linha de dados válida começa com a Nota (partes[0]) e o Pedido (partes[1]), ambos numéricos
                    if len(partes) >= 8 and partes[0].isdigit() and partes[1].isdigit():
                        nota = partes[0]
                        pedido = partes[1]
                        if len(nota) >= 6 and len(pedido) >= 6:
                            if tipo == "Notas Fiscais":
                                documentos.append(nota)
                            elif tipo == "Pedidos":
                                documentos.append(pedido)
                else:
                    # Layout 1 (Romaneio Carga):
                    # ENT CLIENTE PEDIDO VALOR PEDIDO ...
                    if len(partes) >= 5 and partes[0].isdigit() and len(partes[0]) <= 3 and partes[1].isdigit():
                        if tipo == "Notas Fiscais":
                            match = regex_doc_layout1.search(linha_clean)
                            if match:
                                documentos.append(match.group(1))
                        elif tipo == "Pedidos":
                            match = regex_ped_layout1.search(linha_clean)
                            if match:
                                documentos.append(match.group(1))
                            
    return layout, documentos

if uploaded_file is not None:
    with st.spinner("Processando o arquivo PDF e extraindo dados..."):
        try:
            layout_detectado, resultados = processar_pdf(uploaded_file, tipo_extracao)
            
            if resultados:
                # Determinar o conteúdo da saída baseado no formato escolhido
                if formato_saida == "Separado por vírgula (,)":
                    conteudo_saida = ",".join(resultados)
                else:
                    conteudo_saida = "\n".join(resultados)
                
                # Definir nome do arquivo de download baseado no PDF carregado
                nome_base = os.path.splitext(uploaded_file.name)[0]
                sufixo = "notas_fiscais" if tipo_extracao == "Notas Fiscais" else "pedidos"
                nome_download = f"{nome_base}_{sufixo}.txt"
                
                # Nome do layout para exibição amigável
                nome_layout = "Romaneio de Carga" if layout_detectado == "romaneio" else "Entregas por Transportadora"
                
                # Exibir Card de Sucesso e Estatísticas
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-header">
                        <span>✨ Extração Concluída com Sucesso!</span>
                    </div>
                    <div style="display: flex; gap: 3rem; margin-top: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
                        <div>
                            <div class="metric-value">{len(resultados)}</div>
                            <div class="metric-label">Itens Encontrados</div>
                        </div>
                        <div>
                            <div class="metric-value">{tipo_extracao}</div>
                            <div class="metric-label">Tipo Extraído</div>
                        </div>
                        <div>
                            <div class="metric-value" style="font-size: 1.2rem; margin-top: 0.8rem; color: #6ee7b7;">{nome_layout}</div>
                            <div class="metric-label">Layout Detectado</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Exibição de todos os resultados para cópia rápida
                st.subheader("Resultados Extraídos (Passe o mouse e clique no botão de copiar no canto superior direito)")
                st.code(conteudo_saida, language="text")
                
                # Centralizar botão de download
                st.write("")
                st.download_button(
                    label=f"📥 Baixar Arquivo {nome_download}",
                    data=conteudo_saida,
                    file_name=nome_download,
                    mime="text/plain",
                    use_container_width=True
                )
                
            else:
                if tipo_extracao == "Notas Fiscais":
                    st.warning("Nenhuma Nota Fiscal foi encontrada no PDF enviado. Verifique se o formato do PDF está correto.")
                else:
                    st.warning("Nenhum Pedido foi encontrado no PDF enviado. Verifique se o formato do PDF está correto.")
                
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o PDF: {str(e)}")

# Rodapé informativo
st.write("---")
st.caption("Desenvolvido para Núcleo Farma - Processamento local e seguro direto no seu navegador.")
