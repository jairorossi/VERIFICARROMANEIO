import streamlit as st
import pdfplumber
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import re
import io

st.title("📦 Comparador de Notas - Romaneio x XML")

st.write("Envie o **PDF do romaneio** e o **ZIP com os XML das NF-e**")

pdf_file = st.file_uploader("Upload Romaneio (PDF)", type="pdf")
zip_file = st.file_uploader("Upload XML (ZIP)", type="zip")


def extrair_notas_pdf(pdf):
    notas = set()

    with pdfplumber.open(pdf) as pdf_doc:
        for page in pdf_doc.pages:
            texto = page.extract_text()

            encontrados = re.findall(r'\b4\d{5}\b', texto)

            for n in encontrados:
                notas.add(n)

    return notas


def extrair_notas_zip(zip_file):
    notas = set()

    with zipfile.ZipFile(zip_file) as z:
        for nome in z.namelist():

            if nome.endswith(".xml"):

                with z.open(nome) as arquivo:
                    tree = ET.parse(arquivo)
                    root = tree.getroot()

                    for elem in root.iter():
                        if "nNF" in elem.tag:
                            notas.add(elem.text)

    return notas


if pdf_file and zip_file:

    with st.spinner("Processando arquivos..."):

        notas_romaneio = extrair_notas_pdf(pdf_file)
        notas_xml = extrair_notas_zip(zip_file)

        faltando = notas_romaneio - notas_xml
        ok = notas_romaneio.intersection(notas_xml)

        df = pd.DataFrame({
            "Nota": list(notas_romaneio),
        })

        df["Status"] = df["Nota"].apply(
            lambda x: "OK" if x in notas_xml else "FALTANDO"
        )

    st.success("Comparação concluída")

    st.subheader("Resumo")

    col1, col2, col3 = st.columns(3)

    col1.metric("Notas Romaneio", len(notas_romaneio))
    col2.metric("XML Encontrados", len(notas_xml))
    col3.metric("Faltando", len(faltando))

    st.subheader("Resultado")

    st.dataframe(df)

    if faltando:
        st.error("Notas faltando no ZIP:")
        st.write(sorted(list(faltando)))

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Baixar relatório CSV",
        csv,
        "resultado_notas.csv",
        "text/csv"
    )
