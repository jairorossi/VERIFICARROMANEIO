import streamlit as st
import pdfplumber
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="Comparador Romaneio", layout="wide")

st.title("📦 Comparador de Notas - Romaneio x XML")

st.write(
    "Envie o **PDF do romaneio** e o **ZIP contendo os XML das NF-e** para verificar quais notas estão faltando."
)

pdf_file = st.file_uploader("Upload do Romaneio (PDF)", type="pdf")
zip_file = st.file_uploader("Upload dos XML (ZIP)", type="zip")


# -----------------------------------------
# Extrair notas do ROMANEIO
# -----------------------------------------
def extrair_notas_pdf(pdf):

    notas = set()

    with pdfplumber.open(pdf) as pdf_doc:

        for page in pdf_doc.pages:

            texto = page.extract_text()

            if not texto:
                continue

            linhas = texto.split("\n")

            for linha in linhas:

                linha = linha.strip()

                # Apenas linhas que começam com 001
                if linha.startswith("001"):

                    partes = linha.split()

                    if len(partes) >= 4:

                        # nota é o penúltimo campo
                        nota = partes[-2]

                        if nota.isdigit():

                            nota = nota.lstrip("0")

                            notas.add(nota)

    return notas


# -----------------------------------------
# Extrair notas do ZIP (XML)
# -----------------------------------------
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


# -----------------------------------------
# PROCESSAMENTO
# -----------------------------------------
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

    # -----------------------------------------
    # RESUMO
    # -----------------------------------------
    st.subheader("Resumo")

    col1, col2, col3 = st.columns(3)

    col1.metric("Notas Romaneio", len(notas_romaneio))
    col2.metric("XML Encontrados", len(notas_xml))
    col3.metric("Faltando", len(faltando))

    # -----------------------------------------
    # RESULTADO
    # -----------------------------------------
    st.subheader("Resultado Completo")

    st.dataframe(df, use_container_width=True)

    # -----------------------------------------
    # NOTAS FALTANDO
    # -----------------------------------------
    if faltando:

        st.subheader("❌ Notas faltando no ZIP")

        st.write(sorted(list(faltando)))

    else:

        st.success("Todas as notas do romaneio possuem XML.")

    # -----------------------------------------
    # DOWNLOAD RELATÓRIO
    # -----------------------------------------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar relatório CSV",
        csv,
        "resultado_notas.csv",
        "text/csv"
    )

    # -----------------------------------------
    # DEBUG (opcional)
    # -----------------------------------------
    with st.expander("Debug (visualizar dados)"):
        st.write("Primeiras notas do romaneio:", sorted(list(notas_romaneio))[:10])
        st.write("Primeiras notas do XML:", sorted(list(notas_xml))[:10])
