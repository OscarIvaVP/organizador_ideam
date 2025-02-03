# -*- coding: utf-8 -*-

# IMPORTAR LIBRERÍAS
import os
import pandas as pd
import zipfile
import streamlit as st
import io

# Configuración de la página
st.set_page_config(page_title="Procesador de Archivos ZIP con CSVs", layout="wide")

# Título
st.title("📂 Procesador de ZIPs con CSVs")

# Subida de archivo ZIP
uploaded_file = st.file_uploader("📥 Sube un archivo ZIP que contenga otros ZIPs con CSVs", type="zip")

if uploaded_file is not None:
    with st.spinner("⏳ Procesando archivos..."):

        # Crear un directorio temporal
        temp_dir = "temp_extracted"
        os.makedirs(temp_dir, exist_ok=True)

        # Guardar el ZIP subido en la carpeta temporal
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extraer el ZIP principal
        with zipfile.ZipFile(zip_path, "r") as main_zip:
            main_zip.extractall(temp_dir)

        # Buscar y extraer los ZIPs internos
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".zip"):
                    zip_inner_path = os.path.join(root, file)
                    
                    # Extraer cada ZIP interno
                    with zipfile.ZipFile(zip_inner_path, "r") as inner_zip:
                        inner_zip.extractall(temp_dir)

        # Buscar y leer los archivos CSV
        data = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".csv"):
                    csv_path = os.path.join(root, file)
                    
                    # Leer el archivo CSV
                    df = pd.read_csv(csv_path, dtype={11: 'str'})  
                    data.append(df)

        # Concatenar los DataFrames
        if data:
            datos_unidos = pd.concat(data, ignore_index=True)

            # Procesar los datos
            datos_unidos['Fecha'] = pd.to_datetime(datos_unidos['Fecha'])  # Convertir Fecha a datetime
            nombre_estacion = datos_unidos['CodigoEstacion'].unique()  # Obtener valores únicos de estaciones
            datos_unidos = datos_unidos[["Fecha", "Valor", "NombreEstacion"]]  # Filtrar columnas relevantes
            datos_organizados = datos_unidos.pivot_table(index="Fecha", columns="NombreEstacion", values="Valor")
            datos_organizados = datos_organizados.reset_index()  # Resetear índice
            datos_organizados['Fecha'] = datos_organizados['Fecha'].dt.date  # Extraer solo la fecha

            # Mostrar vista previa
            st.subheader("📊 Vista previa de los datos organizados")
            st.dataframe(datos_organizados.head())

            # Guardar el resultado final como Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                datos_organizados.to_excel(writer, index=False, sheet_name="Datos Organizados")
            output.seek(0)

            # Botón de descarga del Excel final
            st.download_button(
                label="📥 Descargar Excel Procesado",
                data=output,
                file_name="Datos_Organizados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.warning("⚠️ No se encontraron archivos CSV dentro del ZIP.")

        # Limpiar archivos temporales
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)

    st.success("✅ Proceso completado con éxito!")
