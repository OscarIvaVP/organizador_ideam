# IMPORTAR LIBRERÍAS
import os
import pandas as pd
import zipfile
import streamlit as st
import io

# Configuración de la página
st.set_page_config(page_title="Procesador de Archivos ZIP con CSVs", layout="wide")

# Título
st.title("📂 Procesador de ZIPs con CSVs y Reestructuración de Datos")

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
        inner_extract_dir = os.path.join(temp_dir, "inner_extracted")
        os.makedirs(inner_extract_dir, exist_ok=True)

        inner_zip_files = []
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".zip"):
                    zip_inner_path = os.path.join(root, file)
                    inner_zip_files.append(zip_inner_path)

        # Extraer y procesar cada archivo ZIP interno
        dataframes = []
        for zip_file in inner_zip_files:
            zip_basename = os.path.basename(zip_file)  # Obtener el nombre del ZIP interno

            with zipfile.ZipFile(zip_file, "r") as inner_zip:
                inner_extract_subdir = os.path.join(inner_extract_dir, zip_basename.replace(".zip", ""))
                os.makedirs(inner_extract_subdir, exist_ok=True)
                inner_zip.extractall(inner_extract_subdir)

                # Buscar archivos CSV dentro de este ZIP
                csv_files_in_zip = [os.path.join(inner_extract_subdir, file) for file in os.listdir(inner_extract_subdir) if file.endswith(".csv")]

                for csv_file in csv_files_in_zip:
                    df = pd.read_csv(csv_file, dtype={11: 'str'})  # Leer el CSV
                    df["Archivo_CSV"] = os.path.basename(csv_file)  # Nombre del archivo CSV
                    df["Archivo_ZIP"] = zip_basename  # Nombre del archivo ZIP de origen
                    dataframes.append(df)

        # Concatenar los DataFrames con información mejorada
        if dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)

            # 🔹 REESTRUCTURAR LOS DATOS SEGÚN TU CÓDIGO ORIGINAL 🔹
            # Convertir 'Fecha' a datetime y extraer solo la fecha sin hora
            combined_df["Fecha"] = pd.to_datetime(combined_df["Fecha"], errors='coerce')
            combined_df["Fecha"] = combined_df["Fecha"].dt.date

            # Seleccionar las columnas necesarias
            datos_unidos = combined_df[["Fecha", "Valor", "NombreEstacion"]]

            # Generar tabla pivote con 'Fecha' como índice y 'NombreEstacion' como columnas
            datos_organizados = datos_unidos.pivot_table(index="Fecha", columns="NombreEstacion", values="Valor")

            # Resetear índice para que 'Fecha' vuelva a ser una columna normal
            datos_organizados = datos_organizados.reset_index()

            # 🔹 Mostrar una vista previa en Streamlit
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


