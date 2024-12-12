import pandas as pd
import sqlite3
import streamlit as st
import os

# Definimos la ruta de la base de datos
ruta_db = r"Data/Northwind_small.sqlite"
#Establecemos la conexión a la base de datos
conn = sqlite3.connect(ruta_db)
def cargar_datos():
    try:
        conn = sqlite3.connect(ruta_db)  # Aseguramos que se abre la conexión
        # Cargar datos desde la base de datos
        pedidos = pd.read_sql_query('SELECT * FROM "Order"', conn)
        detalles_pedidos = pd.read_sql_query('SELECT * FROM OrderDetail', conn)
        empleados = pd.read_sql_query('SELECT * FROM "employee"', conn)
        clientes = pd.read_sql_query('SELECT * FROM "customer"', conn)
        shipper = pd.read_sql_query('SELECT Id, CompanyName FROM Shipper', conn)
        producto = pd.read_sql_query('SELECT * FROM Product', conn)
        categoria = pd.read_sql_query('SELECT Id, CategoryName FROM category', conn)
        # Cerrar la conexión
        conn.close()
        return [pedidos, detalles_pedidos, empleados, clientes, shipper, producto, categoria]

    except sqlite3.Error as e:
        st.error(f"Fallo la carga de datos: {e}")
        return None  # Devuelve None explícitamente en caso de error

    finally:
        if conn:
            conn.close()

    
    
 

 
 

# Llamamos a la función para cargar los datos
pedidos, detalles_pedidos, empleados, clientes, shipper, producto, categoria = cargar_datos()


