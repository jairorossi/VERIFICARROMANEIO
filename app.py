import streamlit as st
import pdfplumber
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import re

st.set_page_config(page_title="Comparador de Romaneio", layout="wide")

st.title("📦 Comparador de Notas - Romaneio x XML")
st.write("Envie o **PDF do romaneio** e o **ZIP com os XML das NF-e**")


pdf_file = st.file_uploader("Upload Romaneio (PDF)", type="pdf")
zip_file = st.file_uploader("Upload XML (ZIP)", type="zip")


# -----------------------------
# Extrair notas do PDF
# -----------------------------
def extrair_notas_pdf(pdf):

    notas = set()

    with pdfplumber.open(pdf) as pdf_doc:

        for page in pdf_doc.pages:

            texto = page.extract_text()

            if not texto:
                continue

            # captura número de 6 dígitos antes de valor monetário
            encontrados = re.findall(r'(\d{6})\s+\d+,\d{2}', texto)

            for nota in encontrados:

                nota_limpa = nota.strip().lstrip("0")

                notas.add(nota_limpa)

    return notas


# -----------------------------
# Extrair notas do ZIP
# -----------------------------
def extrair_notas_zip(zip_file):

    notas = set()

    with zipfile.ZipFile(zip_file) as z:

        for nome in z.namelist():

            if nome.lower().endswith(".xml"):

                with z.open(nome) as arquivo:

                    try:

                        tree = ET.parse(arquivo)
                        root = tree.getroot()

                        for elem in root.iter():

                            if "nNF" in elem.tag:

                                nota = elem.text.strip().lstrip("0")

                                notas.add(nota)

                    except:
                        pass

    return notas


# -----------------------------
# PROCESSAMENTO
# -----------------------------
if pdf_file and zip_file:

    with st.spinner("Processando arquivos..."):

        notas_romaneio = extrair_notas_pdf(pdf_file)
        notas_xml = extrair_notas_zip(zip_file)

        faltando = notas_romaneio - notas_xml
        encontradas = notas_romaneio.intersection(notas_xml)

        df = pd.DataFrame({
            "Nota": sorted(list(notas_romaneio))
        })

        df["Status"] = df["Nota"].apply(
            lambda x: "OK" if x in notas_xml else "FALTANDO"
        )

    st.success("Comparação concluída")

    # -----------------------------
    # RESUMO
    # -----------------------------
    st.subheader("Resumo")

    col1, col2, col3 = st.columns(3)

    col1.metric("Notas Romaneio", len(notas_romaneio))
    col2.metric("XML Encontrados", len(notas_xml))
    col3.metric("Faltando", len(faltando))

    # -----------------------------
    # RESULTADO
    # -----------------------------
    st.subheader("Resultado Completo")

    st.dataframe(df, use_container_width=True)

    # -----------------------------
    # NOTAS FALTANDO
    # -----------------------------
    if faltando:

        st.subheader("❌ Notas faltando no ZIP")

        lista_faltando = sorted(list(faltando))

        st.write(lista_faltando)

    # -----------------------------
    # DOWNLOAD RELATÓRIO
    # -----------------------------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar relatório CSV",
        csv,
        "resultado_notas.csv",
        "text/csv"
    )

    # -----------------------------
    # DEBUG (opcional)
    # -----------------------------
    with st.expander("Debug (visualizar dados)"):

        st.write("Notas do Romaneio (10 primeiras):", sorted(list(notas_romaneio))[:10])
        st.write("Notas do XML (10 primeiras):", sorted(list(notas_xml))[:10])
