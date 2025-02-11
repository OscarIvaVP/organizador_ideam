# -*- coding: utf-8 -*-

import os
import pandas as pd
import zipfile
import streamlit as st
import io

st.set_page_config(
    page_title="Procesador de Archivos ZIP",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Organizador de datos del IDEAM")
st.markdown("Sube un archivo **ZIP** que contenga los archivos **ZIPs con archivos CSV** descargados del IDEAM escala mensual, y la aplicación los procesará automáticamente para generar un archivo **Excel estructurado**.")
st.image("diagrama.png", use_container_width=True)

st.sidebar.header("📅 Cargar Archivo ZIP")
uploaded_file = st.sidebar.file_uploader("📂 Selecciona un archivo ZIP", type="zip")

if uploaded_file is not None:
    with st.spinner("⏳ Procesando archivos..."):
        temp_dir = "temp_extracted"
        os.makedirs(temp_dir, exist_ok=True)
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with zipfile.ZipFile(zip_path, "r") as main_zip:
            main_zip.extractall(temp_dir)
        
        inner_extract_dir = os.path.join(temp_dir, "inner_extracted")
        os.makedirs(inner_extract_dir, exist_ok=True)
        inner_zip_files = [os.path.join(root, file) for root, _, files in os.walk(temp_dir) for file in files if file.endswith(".zip")]

        dataframes = []
        for zip_file in inner_zip_files:
            zip_basename = os.path.basename(zip_file)
            with zipfile.ZipFile(zip_file, "r") as inner_zip:
                inner_extract_subdir = os.path.join(inner_extract_dir, zip_basename.replace(".zip", ""))
                os.makedirs(inner_extract_subdir, exist_ok=True)
                inner_zip.extractall(inner_extract_subdir)
                csv_files_in_zip = [os.path.join(inner_extract_subdir, file) for file in os.listdir(inner_extract_subdir) if file.endswith(".csv")]
                for csv_file in csv_files_in_zip:
                    df = pd.read_csv(csv_file, na_values=["", "NA", "N/A"], dtype={11: 'str'})
                    df["Archivo_CSV"] = os.path.basename(csv_file)
                    df["Archivo_ZIP"] = zip_basename
                    dataframes.append(df)

        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            combined_df["Fecha"] = pd.to_datetime(combined_df["Fecha"], errors='coerce')
            combined_df["Fecha"] = combined_df["Fecha"].dt.date
            
            datos_unidos = combined_df[["Fecha", "Valor", "NombreEstacion"]]
            datos_organizados = datos_unidos.pivot_table(index="Fecha", columns="NombreEstacion", values="Valor").reset_index()
            
            total_estaciones = datos_organizados.shape[1] - 1
            
            st.sidebar.subheader("📊 Filtro de completitud")
            min_percentage = st.sidebar.slider("Porcentaje mínimo de datos requeridos (%)", min_value=0, max_value=100, value=50)
            
            completitud_por_estacion = datos_organizados.iloc[:, 1:].notna().mean() * 100
            estaciones_validas = completitud_por_estacion[completitud_por_estacion >= min_percentage].index
            
            datos_filtrados = datos_organizados[["Fecha"] + list(estaciones_validas)]
            
            estaciones_filtradas = datos_filtrados.shape[1] - 1
            estaciones_eliminadas = total_estaciones - estaciones_filtradas
            
            tab1, tab2 = st.tabs(["📊 Datos Filtrados", "🔍 Estadísticas"])
            
            with tab1:
                st.subheader("📊 Datos Filtrados")
                st.dataframe(datos_filtrados.head(10))
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    datos_filtrados.to_excel(writer, index=False, sheet_name="Datos Filtrados")
                output.seek(0)
                st.download_button("📥 Descargar Excel Filtrado", data=output, file_name="Datos_Filtrados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
            with tab2:
                st.write(f"Total de estaciones iniciales: {total_estaciones}")
                st.write(f"Estaciones que cumplen con el {min_percentage}% mínimo: {estaciones_filtradas}")
                st.write(f"Estaciones eliminadas: {estaciones_eliminadas}")
                
        else:
            st.warning("⚠️ No se encontraron archivos CSV dentro del ZIP.")
        
        st.sidebar.button("🔄 Subir Nuevo Archivo", on_click=lambda: st.experimental_rerun())
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)
    
    st.success("✅ ¡Proceso completado con éxito!")

