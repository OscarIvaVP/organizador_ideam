# IMPORTAR LIBRERÍAS
import os
import pandas as pd
import zipfile
import streamlit as st
import io

# 🎨 CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Procesador de Archivos ZIP",
    page_icon="📂",
    layout="wide"
)

# 📌 ENCABEZADO
st.title("📂 Procesador de Archivos ZIP con CSVs")
st.markdown("Sube un archivo **ZIP** que contenga otros **ZIPs con archivos CSV**, y la aplicación los procesará automáticamente para generar un archivo **Excel estructurado**.")

# 📥 SUBIDA DE ARCHIVO ZIP
st.sidebar.header("📥 Cargar Archivo")
uploaded_file = st.sidebar.file_uploader("📂 Selecciona un archivo ZIP", type="zip")

if uploaded_file is not None:
    with st.spinner("⏳ Procesando archivos..."):

        # 🗂️ CREAR CARPETA TEMPORAL
        temp_dir = "temp_extracted"
        os.makedirs(temp_dir, exist_ok=True)

        # 📥 GUARDAR EL ZIP SUBIDO
        zip_path = os.path.join(temp_dir, "uploaded.zip")
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 🔓 EXTRAER EL ZIP PRINCIPAL
        with zipfile.ZipFile(zip_path, "r") as main_zip:
            main_zip.extractall(temp_dir)

        # 🔍 BUSCAR Y EXTRAER LOS ZIPs INTERNOS
        inner_extract_dir = os.path.join(temp_dir, "inner_extracted")
        os.makedirs(inner_extract_dir, exist_ok=True)

        inner_zip_files = [os.path.join(root, file) for root, _, files in os.walk(temp_dir) for file in files if file.endswith(".zip")]

        # 🔄 PROCESAR CADA ARCHIVO ZIP INTERNO
        dataframes = []
        for zip_file in inner_zip_files:
            zip_basename = os.path.basename(zip_file)

            with zipfile.ZipFile(zip_file, "r") as inner_zip:
                inner_extract_subdir = os.path.join(inner_extract_dir, zip_basename.replace(".zip", ""))
                os.makedirs(inner_extract_subdir, exist_ok=True)
                inner_zip.extractall(inner_extract_subdir)

                # 📂 BUSCAR ARCHIVOS CSV DENTRO DEL ZIP
                csv_files_in_zip = [os.path.join(inner_extract_subdir, file) for file in os.listdir(inner_extract_subdir) if file.endswith(".csv")]

                for csv_file in csv_files_in_zip:
                    df = pd.read_csv(csv_file, dtype={11: 'str'})  # Leer CSV
                    df["Archivo_CSV"] = os.path.basename(csv_file)  # Nombre del CSV
                    df["Archivo_ZIP"] = zip_basename  # Nombre del ZIP de origen
                    dataframes.append(df)

        # 🔄 CONCATENAR LOS DATOS Y REESTRUCTURAR
        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)

            # 🔹 CONVERTIR "Fecha" A FORMATO DATETIME
            combined_df["Fecha"] = pd.to_datetime(combined_df["Fecha"], errors='coerce')
            combined_df["Fecha"] = combined_df["Fecha"].dt.date

            # 🔹 SELECCIONAR COLUMNAS RELEVANTES
            datos_unidos = combined_df[["Fecha", "Valor", "NombreEstacion"]]

            # 🔹 CREAR TABLA PIVOTANTE
            datos_organizados = datos_unidos.pivot_table(index="Fecha", columns="NombreEstacion", values="Valor")
            datos_organizados = datos_organizados.reset_index()

            # 📌 INTERFAZ MEJORADA CON PESTAÑAS
            tab1, tab2 = st.tabs(["📊 Datos Procesados", "🔍 Vista Previa CSVs"])

            with tab1:
                st.subheader("📊 Datos Organizados")
                st.dataframe(datos_organizados.head(10))  # Mostrar primeras 10 filas

                # 📥 BOTÓN PARA DESCARGAR EXCEL
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    datos_organizados.to_excel(writer, index=False, sheet_name="Datos Organizados")
                output.seek(0)

                st.download_button(
                    label="📥 Descargar Excel",
                    data=output,
                    file_name="Datos_Organizados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with tab2:
                st.subheader("🔍 Datos Crudos de los CSVs")
                st.dataframe(combined_df.head(10))  # Mostrar primeras 10 filas de los datos originales

        else:
            st.warning("⚠️ No se encontraron archivos CSV dentro del ZIP.")

        # 🚀 BOTÓN PARA REINICIAR
        st.sidebar.button("🔄 Subir Nuevo Archivo", on_click=lambda: st.experimental_rerun())

        # 🧹 LIMPIAR ARCHIVOS TEMPORALES
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)

    st.success("✅ ¡Proceso completado con éxito!")


