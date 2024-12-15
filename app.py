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




ruta_db = "Data/Northwind_small.sqlite"
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



# Crear la columna total
if 'Total' not in datos_filtrados.columns:
    datos_filtrados['Total'] = datos_filtrados['UnitPrice'] * datos_filtrados['Quantity']
    
# Dividimos la página en cuatro columnas
col1, col2, col3, col4 = st.columns(4)

# Primera columna: Gráfico de pastel para costos por región
with col1:
    st.subheader("Costos por Región")
    
    # Calculamos los costos por región
    datos_filtrados['Costo'] = datos_filtrados['Quantity'] * datos_filtrados['UnitPrice'] * 0.6  # Margen del 60%
    costos_por_region = datos_filtrados.groupby('Region')['Costo'].sum().reset_index()
    costos_por_region = costos_por_region.rename(columns={'Region': 'Región', 'Costo': 'Costos Totales ($)'})
    
    # Creamos un gráfico de pastel
    fig_pastel_costos = px.pie(
        costos_por_region,
        names='Región',
        values='Costos Totales ($)',
        title='Distribución de Costos por Región',
        hole=0.4,  # Estilo dona
        color_discrete_sequence=['#87CEFA']  # Color celeste
    )
    
    # Mostramos el gráfico de pastel
    st.plotly_chart(fig_pastel_costos, use_container_width=True)

# Segunda columna: Gráfico de ventas por cuatrimestres
with col2:
    st.subheader("Ventas por Cuatrimestre")
    
    # Convertimos las fechas a formato datetime
    datos_filtrados['ShippedDate'] = pd.to_datetime(datos_filtrados['ShippedDate'], errors='coerce')
    datos_filtrados['Cuatrimestre'] = datos_filtrados['ShippedDate'].dt.month // 4 + 1  # Dividimos meses en cuatrimestres
    
    # Agrupamos las ventas por cuatrimestre
    ventas_cuatrimestres = datos_filtrados.groupby('Cuatrimestre')['Total'].sum().reset_index()
    ventas_cuatrimestres = ventas_cuatrimestres.rename(columns={'Total': 'Ventas Totales ($)'})
    
    # Creamos un gráfico de líneas
    fig_ventas_cuatrimestres = px.line(
        ventas_cuatrimestres,
        x='Cuatrimestre',
        y='Ventas Totales ($)',
        title='Ventas Totales por Cuatrimestre',
        markers=True,
        line_shape='linear'
    )
    fig_ventas_cuatrimestres.update_traces(line_color='blue')
    
    # Mostramos el gráfico de líneas
    st.plotly_chart(fig_ventas_cuatrimestres, use_container_width=True)

# Tercera columna: Número de viajes por el Top 5 de naves
with col3:
    st.subheader("Top 5 Naves por Número de Viajes")
    
    # Agrupamos por nave y contamos el número de viajes
    top_naves = datos_filtrados.groupby('ShipName')['Id_pedido'].count().reset_index()
    top_naves = top_naves.rename(columns={'ShipName': 'Nave', 'Id_pedido': 'Número de Viajes'})
    top_5_naves = top_naves.sort_values(by='Número de Viajes', ascending=False).head(5)
    
    # Creamos un gráfico de barras
    fig_top_naves = px.bar(
        top_5_naves,
        x='Nave',
        y='Número de Viajes',
        title='Top 5 Naves por Número de Viajes',
        text='Número de Viajes',
        color='Número de Viajes',
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    # Mostramos el gráfico de barras
    st.plotly_chart(fig_top_naves, use_container_width=True)

# Cuarta columna: Compañía con mayor número de compras
with col4:
    # Título centrado arriba
    st.markdown("<h3 style='text-align: center;'>Compañía con Más Compras</h3>", unsafe_allow_html=True)
    
    # Espaciamos verticalmente para centrar métricas abajo
    st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
    
    # Métricas centradas
    top_compradores = datos_filtrados.groupby('CompanyName')['Id_pedido'].count().reset_index()
    top_compradores = top_compradores.rename(columns={'CompanyName': 'Compañía', 'Id_pedido': 'Número de Compras'})
    top_comprador = top_compradores.sort_values(by='Número de Compras', ascending=False).head(1)
    
    # Mostramos las métricas centradas
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.metric(label="Compañía", value=top_comprador['Compañía'].values[0])
    st.metric(label="Número de Compras", value=int(top_comprador['Número de Compras'].values[0]))
    st.markdown("</div>", unsafe_allow_html=True)
    

# Dividimos la página en dos columnas
col1, col2 = st.columns(2)

# Primera columna: Gráfico de Ventas Totales por Categoría
with col1:
    st.subheader("Ventas Totales por Categoría")

    # Agrupar los datos por categoría y ordenar por ventas totales de mayor a menor
    ventas_categoria = datos_filtrados.groupby('CategoryName')['Total'].sum().reset_index()
    ventas_categoria = ventas_categoria.sort_values(by='Total', ascending=False)

    # Gráfico interactivo con Plotly, agregando etiquetas de datos
    fig_categoria = px.bar(
        ventas_categoria,
        x='CategoryName',
        y='Total',
        title='Ventas Totales por Categoría',
        labels={'CategoryName': 'Categoría', 'Total': 'Ventas Totales ($)'},
        color='Total',  # Color basado en la columna 'Total'
        color_continuous_scale=['#D3D3D3', '#1E90FF'],  # Gradiente de gris claro a azul cielo
        text='Total'  # Agregar etiquetas de datos
    )

    # Personalizar el diseño del gráfico
    fig_categoria.update_traces(
        texttemplate='%{text:.2s}',  # Formato de las etiquetas (e.g., 1.2k para 1200)
        textposition='inside',
        textfont=dict(
            size=22,
            color='black'
        )
    )
    fig_categoria.update_layout(
        xaxis=dict(tickangle=45),  # Rotar etiquetas del eje X
        xaxis_title='Categoría',
        yaxis_title='Ventas Totales ($)',
        title_font_size=16,
        height=600
    )

    # Mostrar el gráfico
    st.plotly_chart(fig_categoria, use_container_width=True)


# Segunda columna: Gráfico de Totales de Ingresos vs Costos
with col2:
    st.subheader("Totales de Ingresos vs Costos")

    # Calculamos los costos e ingresos totales
    datos_filtrados['Costo'] = datos_filtrados['Quantity'] * datos_filtrados['UnitPrice'] * 0.6

    # Creamos un dataframe con los totales globales para ingresos y costos
    totales = pd.DataFrame({
        'Indicador': ['Ingresos', 'Costos'],  # Estos son nuestros dos indicadores
        'Monto': [datos_filtrados['Total'].sum(), datos_filtrados['Costo'].sum()]  # Sumamos todo
    })

    # Creamos el gráfico de barras apiladas horizontal
    fig_totales_horizontal = px.bar(
        totales,
        y='Indicador',  # Indicador en el eje Y (Ingresos y Costos)
        x='Monto',  # Los montos totales en el eje X1
        title='Totales de Ingresos vs Costos',
        labels={'Indicador': 'Indicador', 'Monto': 'Monto ($)'},  # Etiquetas amigables para los ejes
        color='Indicador',  # Usamos el indicador como base para los colores
        text='Monto',  # Mostramos el monto total como etiqueta
        orientation='h',  # Este es el truco para hacerlo horizontal
        color_discrete_map={'Ingresos': '#1E90FF', 'Costos': 'gray'}  # Azul cielo para ingresos, gris para costos
    )

    # Personalizamos el diseño del gráfico
    fig_totales_horizontal.update_traces(
        texttemplate='%{text:.2f}',  # Mostramos los valores con dos decimales
        textposition='outside'  # Colocamos las etiquetas fuera de las barras
    )
    fig_totales_horizontal.update_layout(
        xaxis_title='Monto ($)',  # Etiqueta para el eje X
        yaxis_title='Indicador',  # Etiqueta para el eje Y
        height=400,  # Ajustamos la altura del gráfico
        showlegend=False  # Quitamos la leyenda
    )

    # Mostrar el gráfico en la segunda columna
    st.plotly_chart(fig_totales_horizontal, use_container_width=True)
