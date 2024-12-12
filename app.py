import sqlite3
import pandas as pd
import streamlit as st
import os 
import plotly.express as px





st.set_page_config(
    page_title="Dashboard Nortwind", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .main {{
        background-color: #2F2F2F;
        color: white;
    }}u j
    .css-18e3th9 {{
        background-color: #2F2F2F;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Dashboard Finanzas")
st.sidebar.write("Filtros")
st.write("Elaborado por Esteban Navarro")




ruta_db = "C:/Users/f/Downloads/cetav/progra_3_naib/WWI_simple.db"
from Utils.cargar_datos import cargar_datos

# Cargo los datos
[pedidos, detalles_pedidos, empleados, clientes, shipper, producto, categoria] = cargar_datos()

# Unifico las tablas paso a paso
try:
    tabla_unificada1 = pedidos.merge(detalles_pedidos, left_on='Id', right_on='OrderId', suffixes=('_pedido', '_detalle'))
    tabla_unificada2 = tabla_unificada1.merge(empleados, left_on='EmployeeId', right_on='Id', suffixes=('', '_empleado'))
    tabla_unificada3 = tabla_unificada2.merge(producto, left_on='ProductId', right_on='Id', suffixes=('', '_producto'))
    tabla_unificada4 = tabla_unificada3.merge(categoria, left_on='CategoryId', right_on='Id', suffixes=('', '_categoria'))
    tabla_unificada5 = tabla_unificada4.merge(clientes, left_on='CustomerId', right_on='Id', suffixes=('', '_cliente'))
    Northwind_unificada = tabla_unificada5.merge(shipper, left_on='ShipVia', right_on='Id', suffixes=('', '_shipper'))
    Northwind_unificada['ShippedDate'] = pd.to_datetime(Northwind_unificada['ShippedDate'], errors='coerce')

except KeyError as e:
    st.error(f"Error al unificar los dataframes : {e}")

#Creo dataframes con las columnas especificas que necesito para el posterior graficado de los datos
tabla_ventas = Northwind_unificada[['Id_pedido', 'UnitPrice', 'ProductName', 'CategoryName', 'Quantity']].copy()
tabla_ventas.loc[:, 'Total'] = tabla_ventas['UnitPrice'] * tabla_ventas['Quantity']

 # Crear la columna 'Total' si no existe
if 'Total' not in Northwind_unificada.columns:
    Northwind_unificada['Total'] = Northwind_unificada['UnitPrice'] * Northwind_unificada['Quantity']

# Filtro por Estado/Provincia (Ciudad)
if "City" in Northwind_unificada.columns:
    estado_seleccionado = st.sidebar.selectbox(
        "Seleccione un estado/ciudad:",
        options=["Todos"] + sorted(Northwind_unificada["City"].dropna().unique()),  # Eliminamos nulos y ordenamos
        index=0
    )
else:
    st.sidebar.warning("La columna 'City' no está disponible en los datos.")
    estado_seleccionado = "Todos"

# Filtro por categoría
if "CategoryName" in Northwind_unificada.columns:
    categoria_seleccionada = st.sidebar.selectbox(
        "Seleccione una categoría:",
        options=["Todos"] + sorted(Northwind_unificada["CategoryName"].dropna().unique()),  # Eliminamos nulos y ordenamos
        index=0
    )
else:
    st.sidebar.warning("La columna 'CategoryName' no está disponible en los datos.")
    categoria_seleccionada = "Todos"

# Filtro por CompanyName
if "CompanyName" in Northwind_unificada.columns:
    company_seleccionada = st.sidebar.selectbox(
        "Seleccione una compañía:",
        options=["Todos"] + sorted(Northwind_unificada["CompanyName"].dropna().unique()),  # Eliminamos nulos y ordenamos
        index=0
    )
else:
    st.sidebar.warning("La columna 'CompanyName' no está disponible en los datos.")
    company_seleccionada = "Todos"

# Filtro por rango de fechas
if "ShippedDate" in Northwind_unificada.columns:
    if Northwind_unificada["ShippedDate"].dtype != 'datetime64[ns]':
        Northwind_unificada["ShippedDate"] = pd.to_datetime(Northwind_unificada["ShippedDate"], errors='coerce')
    
    fecha_minima = Northwind_unificada["ShippedDate"].min().date()
    fecha_maxima = Northwind_unificada["ShippedDate"].max().date()

    fecha_inicio, fecha_fin = st.sidebar.slider(
        "Seleccione un rango de fechas:",
        min_value=fecha_minima,
        max_value=fecha_maxima,
        value=(fecha_minima, fecha_maxima)
    )
else:
    st.sidebar.warning("La columna 'ShippedDate' no está disponible en los datos.")
    fecha_inicio, fecha_fin = None, None

# Aplicación de filtros
datos_filtrados = Northwind_unificada.copy()

if estado_seleccionado != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["City"] == estado_seleccionado]

if categoria_seleccionada != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["CategoryName"] == categoria_seleccionada]

if company_seleccionada != "Todos":
    datos_filtrados = datos_filtrados[datos_filtrados["CompanyName"] == company_seleccionada]

if fecha_inicio and fecha_fin:
    datos_filtrados = datos_filtrados[
        (datos_filtrados["ShippedDate"].dt.date >= fecha_inicio) &
        (datos_filtrados["ShippedDate"].dt.date <= fecha_fin)
    ]

# Mostrar los datos filtrados
st.write("Datos filtrados según los criterios seleccionados:")
st.dataframe(datos_filtrados)


# Crear la columna total
if 'Total' not in datos_filtrados.columns:
    datos_filtrados['Total'] = datos_filtrados['UnitPrice'] * datos_filtrados['Quantity']
    

# Agrupar los datos por categoría y ordenar por ventas totales (de mayor a menor)
ventas_categoria = datos_filtrados.groupby('CategoryName')['Total'].sum().reset_index()
ventas_categoria = ventas_categoria.sort_values(by='Total', ascending=False)

# Crear el gráfico interactivo con Plotly, agregando etiquetas de datos
fig = px.bar(
    ventas_categoria,
    x='CategoryName',
    y='Total',
    title='Ventas Totales por Categoría',
    labels={'CategoryName': 'Categoría', 'Total': 'Ventas Totales ($)'},
    color='Total',
    color_continuous_scale=px.colors.diverging.RdYlGn,
    text='Total'  # Agregar etiquetas de datos
)

# Personalizar el diseño
fig.update_traces(
    texttemplate='%{text:.2s}',  # Formato de las etiquetas (e.g., 1.2k para 1200)
    textposition='inside',
    textfont=dict(
        size=22,
        color ='white'
    )
)
fig.update_layout(
    xaxis=dict(tickangle=45),  # Rotar etiquetas del eje X
    xaxis_title='Categoría',
    yaxis_title='Ventas Totales ($)',
    title_font_size=16,
    height=600
)

# Mostrar el gráfico en Streamlit
st.subheader("Gráfico Interactivo: Ventas Totales por Categoría (Mayor Verde, Menor Rojo)")
st.plotly_chart(fig, use_container_width=True)
