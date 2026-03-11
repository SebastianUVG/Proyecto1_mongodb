import re
from datetime import datetime as dt
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"
BULK_CHUNK_SIZE = 2000  # documentos por request en Crear Bulk (evita timeouts y límites de tamaño)

LIMIT_OPTIONS = [10, 25, 50, 100, 200]

COLUMN_LABELS = {
    "_id": "ID",
    "id": "ID",
    "name": "Nombre",
    "description": "Descripción",
    "category": "Categoría",
    "location": "Ubicación",
    "ratingAverage": "Valoración",
    "createdAt": "Fecha",
    "price": "Precio",
    "tags": "Etiquetas",
    "restaurantId": "ID Restaurante",
    "userId": "ID Usuario",
    "totalAmount": "Total",
    "status": "Estado",
    "items": "Productos",
    "rating": "Valoración",
    "comment": "Comentario",
    "orderId": "ID Orden",
    "filename": "Nombre archivo",
    "contentType": "Tipo",
    "uploadedAt": "Fecha subida",
    "gridfsId": "ID Archivo",
    "restaurantName": "Restaurante",
    "avgRating": "Valoración media",
    "totalReviews": "Total reseñas",
    "totalRevenue": "Ingresos",
    "totalSold": "Vendidos",
    "totalQuantity": "Cantidad",
    "avgPrice": "Precio medio",
}

STATUS_ES = {"pending": "Pendiente", "completed": "Completada", "cancelled": "Cancelada"}


def _format_date(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, str):
        try:
            d = dt.fromisoformat(val.replace("Z", "+00:00"))
            return d.strftime("%d/%m/%Y %H:%M") if d else val
        except Exception:
            return val
    return str(val)


def _format_currency(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    try:
        n = float(val)
        return f"$ {n:,.2f}"
    except (TypeError, ValueError):
        return str(val)


def format_dataframe_restaurant(df, drop_id=True, currency_cols=None, date_cols=None, status_col="status"):
    """Renombra columnas al español, formatea moneda/fechas/estado. Devuelve DataFrame listo para mostrar."""
    if df is None or df.empty:
        return df
    df = df.copy()
    currency_cols = currency_cols or ["totalAmount", "price", "totalRevenue", "avgPrice", "subtotal"]
    date_cols = date_cols or ["createdAt", "uploadedAt"]
    for c in currency_cols:
        if c in df.columns:
            df[c] = df[c].apply(_format_currency)
    for c in date_cols:
        if c in df.columns:
            df[c] = df[c].apply(_format_date)
    if status_col and status_col in df.columns:
        df[status_col] = df[status_col].apply(lambda x: STATUS_ES.get(str(x).lower(), x) if x is not None else "")
    rename = {k: v for k, v in COLUMN_LABELS.items() if k in df.columns}
    df = df.rename(columns=rename)
    if drop_id and "ID" in df.columns:
        df["ID"] = df["ID"].astype(str).str[:8]
    return df


def _show_simple_analytics(data, title=None):
    """Muestra un dict o lista de analytics como tabla legible en español."""
    if data is None:
        return
    if isinstance(data, dict):
        if not data:
            st.info("Sin datos.")
            return
        rows = [{"Concepto": str(k), "Valor": v} for k, v in data.items()]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    elif isinstance(data, list):
        if not data:
            st.info("Sin datos.")
            return
        df = pd.DataFrame(data)
        df = format_dataframe_restaurant(df)
        st.dataframe(df, use_container_width=True)
    if title:
        st.caption(title)


st.set_page_config(page_title="Restaurant Dashboard", layout="wide")

st.title("Restaurant System Dashboard")

menu = st.sidebar.selectbox(
    "Selecciona una sección",
    ["Restaurantes", "Menu Items", "Órdenes", "Reviews", "Analytics", "Crear Bulk", "Consultas Avanzadas", "Updates", "Deletes", "Archivos", "Manejo de Arrays", "Documentos Embebidos"]
)

# ---------------- RESTAURANTES ----------------
if menu == "Restaurantes":
    st.header("Gestión de Restaurantes")

    st.subheader("Crear Restaurante")

    name = st.text_input("Nombre")
    description = st.text_input("Descripción")
    category = st.text_input("Categoría")

    lat = st.number_input("Latitud", format="%.6f")
    lon = st.number_input("Longitud", format="%.6f")

    if st.button("Crear Restaurante"):
        payload = {
            "name": name,
            "description": description,
            "category": category,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }

        r = requests.post(f"{API_URL}/restaurants", json=payload)

        if r.status_code == 200 or r.status_code == 201:
            st.success("Restaurante creado correctamente")
        else:
            st.error("Error al crear restaurante")

    st.divider()

    st.subheader("Lista de Restaurantes")
    limit_rest = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="rest_limit")
    skip_rest = st.number_input("Saltar primeros", min_value=0, value=0, key="rest_skip")
    if st.button("Cargar Restaurantes", key="rest_btn_load"):
        response = requests.get(f"{API_URL}/restaurants", params={"limit": limit_rest, "skip": skip_rest})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                if "location" in df.columns:
                    df["location"] = df["location"].apply(
                        lambda x: f"{x.get('coordinates', [0,0])[1]:.4f}, {x.get('coordinates', [0,0])[0]:.4f}" if isinstance(x, dict) else str(x)
                    )
                df = format_dataframe_restaurant(df, date_cols=["createdAt"])
                st.dataframe(df, use_container_width=True)
                st.caption(f"Mostrando {len(data)} registros.")
            else:
                st.info("No hay restaurantes.")
        else:
            st.error("Error al cargar restaurantes")

# ---------------- ITEMS ----------------

elif menu == "Menu Items":
    st.header("Crear Menu Item")

    # Obtener restaurantes
    restaurants_response = requests.get(f"{API_URL}/restaurants")
    restaurants_data = restaurants_response.json() if restaurants_response.status_code == 200 else []

    restaurant_options = {r["name"]: r["id"] for r in restaurants_data} if restaurants_data else {}

    selected_restaurant = st.selectbox("Seleccionar Restaurante", list(restaurant_options.keys()))

    name = st.text_input("Nombre del Item")
    price = st.number_input("Precio", min_value=0.0, format="%.2f")
    category = st.text_input("Categoría")
    tags = st.text_input("Tags (separados por coma)")

    if st.button("Crear Menu Item"):
        payload = {
            "restaurantId": restaurant_options[selected_restaurant],
            "name": name,
            "price": price,
            "category": category,
            "tags": [t.strip() for t in tags.split(",")] if tags else []
        }

        r = requests.post(f"{API_URL}/menu-items", json=payload)

        if r.status_code in [200, 201]:
            st.success("Menu Item creado correctamente")
        else:
            st.error(f"Error: {r.text}")

    st.divider()

    st.subheader("Lista de Menu Items")
    limit_mi = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="menu_limit")
    skip_mi = st.number_input("Saltar primeros", min_value=0, value=0, key="menu_skip")
    if st.button("Cargar Menu Items", key="menu_btn_load"):
        response = requests.get(f"{API_URL}/menu-items", params={"limit": limit_mi, "skip": skip_mi})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                if "tags" in df.columns:
                    df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
                df = format_dataframe_restaurant(df, currency_cols=["price"], date_cols=[])
                st.dataframe(df, use_container_width=True)
                st.caption(f"Mostrando {len(data)} registros.")
            else:
                st.info("No hay ítems de menú.")
        else:
            st.error("Error al cargar menu items")

# ---------------- ÓRDENES ----------------
elif menu == "Órdenes":
    st.header("Crear Orden")

    # Obtener usuarios
    users_response = requests.get(f"{API_URL}/users")
    users_data = users_response.json() if users_response.status_code == 200 else []

    user_options = {u["name"]: u["id"] for u in users_data} if users_data else {}

    # Obtener restaurantes
    restaurants_response = requests.get(f"{API_URL}/restaurants")
    restaurants_data = restaurants_response.json() if restaurants_response.status_code == 200 else []

    restaurant_options = {r["name"]: r["id"] for r in restaurants_data} if restaurants_data else {}

    # Obtener menu items
    menu_response = requests.get(f"{API_URL}/menu-items")
    menu_data = menu_response.json() if menu_response.status_code == 200 else []

    menu_options = {m["name"]: m["id"] for m in menu_data} if menu_data else {}

    # Selectores visuales
    selected_user = st.selectbox("Seleccionar Usuario", list(user_options.keys()))
    selected_restaurant = st.selectbox("Seleccionar Restaurante", list(restaurant_options.keys()))
    selected_item = st.selectbox("Seleccionar Menu Item", list(menu_options.keys()))

    quantity = st.number_input("Cantidad", min_value=1, value=1)
    status = st.selectbox("Estado", ["pending", "completed", "cancelled"])

    if st.button("Crear Orden"):
        payload = {
            "userId": user_options[selected_user],
            "restaurantId": restaurant_options[selected_restaurant],
            "items": [
                {
                    "menuItemId": menu_options[selected_item],
                    "name": selected_item,
                    "quantity": quantity,
                    "price": next((m["price"] for m in menu_data if m["name"] == selected_item), 0)
                }
            ],
            "status": status
        }

        r = requests.post(f"{API_URL}/orders", json=payload)

        if r.status_code in [200, 201]:
            st.success("Orden creada correctamente")
        else:
            st.error(f"Error: {r.text}")

    st.divider()

    st.subheader("Lista de Órdenes")
    limit_ord = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="ord_limit")
    skip_ord = st.number_input("Saltar primeros", min_value=0, value=0, key="ord_skip")
    if st.button("Cargar Órdenes", key="ord_btn_load"):
        response = requests.get(f"{API_URL}/orders", params={"limit": limit_ord, "skip": skip_ord})
        if response.status_code == 200:
            orders = response.json()
            for order in orders:
                order["items"] = ", ".join([item["name"] for item in order.get("items", [])])
            df = pd.DataFrame(orders)
            if not df.empty:
                df = format_dataframe_restaurant(df, currency_cols=["totalAmount"], date_cols=["createdAt"], status_col="status")
                st.dataframe(df, use_container_width=True)
                st.caption(f"Mostrando {len(orders)} registros.")
            else:
                st.info("No hay órdenes.")
        else:
            st.error("Error al cargar órdenes")

# ---------------- REVIEWS ----------------
elif menu == "Reviews":
    st.header("Crear Review")

    # Obtener usuarios
    users_response = requests.get(f"{API_URL}/users")
    users_data = users_response.json() if users_response.status_code == 200 else []
    user_options = {u["name"]: u["id"] for u in users_data} if users_data else {}

    # Obtener restaurantes
    restaurants_response = requests.get(f"{API_URL}/restaurants")
    restaurants_data = restaurants_response.json() if restaurants_response.status_code == 200 else []
    restaurant_options = {r["name"]: r["id"] for r in restaurants_data} if restaurants_data else {}

    # Obtener órdenes
    orders_response = requests.get(f"{API_URL}/orders")
    orders_data = orders_response.json() if orders_response.status_code == 200 else []
    order_options = {o["_id"]: o["_id"] for o in orders_data} if orders_data else {}

    selected_user = st.selectbox("Seleccionar Usuario", list(user_options.keys()))
    selected_restaurant = st.selectbox("Seleccionar Restaurante", list(restaurant_options.keys()))
    selected_order = st.selectbox("Seleccionar Orden", list(order_options.keys()))

    rating = st.slider("Rating", 1, 5, 5)
    comment = st.text_area("Comentario")

    if st.button("Crear Review"):
        payload = {
            "restaurantId": restaurant_options[selected_restaurant],
            "userId": user_options[selected_user],
            "orderId": selected_order,
            "rating": rating,
            "comment": comment
        }

        r = requests.post(f"{API_URL}/reviews", json=payload)

        if r.status_code in [200, 201]:
            st.success("Review creada correctamente")
        else:
            st.error(f"Error: {r.text}")

    st.divider()

    st.subheader("Lista de Reviews")
    limit_rev = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="rev_limit")
    skip_rev = st.number_input("Saltar primeros", min_value=0, value=0, key="rev_skip")
    if st.button("Cargar Reviews", key="rev_btn_load"):
        response = requests.get(f"{API_URL}/reviews", params={"limit": limit_rev, "skip": skip_rev})
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df = format_dataframe_restaurant(df, date_cols=["createdAt"], status_col=None)
                st.dataframe(df, use_container_width=True)
                st.caption(f"Mostrando {len(data)} registros.")
            else:
                st.info("No hay reseñas.")
        else:
            st.error("Error al cargar reviews")

# ---------------- ANALYTICS ----------------
elif menu == "Analytics":
    st.header("Métricas del Sistema")
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    # Total Restaurantes
    r_rest = requests.get(f"{API_URL}/restaurants")
    total_rest = len(r_rest.json()) if r_rest.status_code == 200 else 0

    # Total Órdenes
    r_orders = requests.get(f"{API_URL}/orders")
    orders_data = r_orders.json() if r_orders.status_code == 200 else []
    total_orders = len(orders_data)

    # Revenue Total
    total_revenue = sum(order.get("totalAmount", 0) for order in orders_data)

    with col_kpi1:
        st.metric("Restaurantes", total_rest)

    with col_kpi2:
        st.metric("Órdenes", total_orders)

    with col_kpi3:
        st.metric("Ingresos totales", _format_currency(total_revenue))

    col1, col2 = st.columns(2)

    # TOP RESTAURANTES
    r = requests.get(f"{API_URL}/analytics/top-restaurants")
    data = r.json()

    if data:
        for item in data:
            if item.get("restaurant"):
                item["restaurantName"] = item["restaurant"][0]["name"]

        df = pd.DataFrame(data)

        with col1:
            fig = px.bar(
                df,
                x="restaurantName",
                y="avgRating",
                title="Top Restaurantes por Rating"
            )
            st.plotly_chart(fig, use_container_width=True)

    # REVENUE
    r2 = requests.get(f"{API_URL}/analytics/revenue-by-restaurant")
    data2 = r2.json()

    if data2:
        # Extraer nombre del restaurante si viene embebido
        for item in data2:
            if item.get("restaurant"):
                item["restaurantName"] = item["restaurant"][0]["name"]

        df2 = pd.DataFrame(data2)

        with col2:
            fig2 = px.bar(
                df2,
                x="restaurantName",
                y="totalRevenue",
                title="Revenue por Restaurante"
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # AGREGACIONES SIMPLES
    st.subheader("Agregaciones Simples")
    col3, col4 = st.columns(2)

    with col3:
        if st.button("Categorías Distintas de Restaurantes", key="an_cat"):
            r = requests.get(f"{API_URL}/analytics/simple/distinct-categories")
            if r.status_code == 200:
                d = r.json()
                if isinstance(d.get("categories"), list):
                    df = pd.DataFrame({"Categoría": d["categories"]})
                    st.dataframe(df, use_container_width=True)
                else:
                    _show_simple_analytics(d)

        if st.button("Conteo por Estado de Órdenes", key="an_status"):
            r = requests.get(f"{API_URL}/analytics/simple/counts-by-status")
            if r.status_code == 200:
                d = r.json()
                rows = [{"Estado": STATUS_ES.get(k, k), "Cantidad": v} for k, v in d.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    with col4:
        if st.button("Tags Distintos de Menu Items", key="an_tags"):
            r = requests.get(f"{API_URL}/analytics/simple/distinct-menu-categories")
            if r.status_code == 200:
                d = r.json()
                if isinstance(d.get("categories"), list) and d["categories"]:
                    st.markdown("**Categorías de platos**")
                    st.dataframe(pd.DataFrame({"Categoría": d["categories"]}), use_container_width=True)
                if isinstance(d.get("tags"), list) and d["tags"]:
                    st.markdown("**Etiquetas**")
                    st.dataframe(pd.DataFrame({"Etiqueta": d["tags"]}), use_container_width=True)
                if not d.get("categories") and not d.get("tags"):
                    st.info("Sin datos.")

        if st.button("Conteos Generales", key="an_counts"):
            r = requests.get(f"{API_URL}/analytics/counts")
            if r.status_code == 200:
                d = r.json()
                rows = [{"Concepto": k, "Cantidad": v} for k, v in d.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.divider()

    # AGREGACIONES COMPLEJAS
    st.subheader("Agregaciones Complejas")
    if st.button("Top Menu Items Vendidos", key="an_top_items"):
        r = requests.get(f"{API_URL}/analytics/top-menu-items")
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = format_dataframe_restaurant(df)
            st.dataframe(df, use_container_width=True)
            st.caption("Productos más vendidos.")

    if st.button("Análisis de Items en Órdenes", key="an_order_items"):
        r = requests.get(f"{API_URL}/analytics/complex/order-items-analysis")
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = format_dataframe_restaurant(df, currency_cols=["avgPrice", "maxPrice"])
            st.dataframe(df, use_container_width=True)
            st.caption("Análisis de productos en órdenes.")

    if st.button("Segmentación de Usuarios por Gasto", key="an_spending"):
        r = requests.get(f"{API_URL}/analytics/complex/user-spending-brackets")
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = format_dataframe_restaurant(df)
            st.dataframe(df, use_container_width=True)
            st.caption("Usuarios por rango de gasto.")

    if st.button("Rendimiento de Restaurantes", key="an_perf"):
        r = requests.get(f"{API_URL}/analytics/complex/restaurant-performance-analytics")
        if r.status_code == 200:
            data = r.json()
            if data:
                st.markdown("**Mejores por valoración**")
                df1 = pd.DataFrame(data[0].get("topByRating", []))
                if not df1.empty:
                    df1 = format_dataframe_restaurant(df1)
                    st.dataframe(df1, use_container_width=True)
                st.markdown("**Mejores por número de órdenes**")
                df2 = pd.DataFrame(data[0].get("topByOrders", []))
                if not df2.empty:
                    df2 = format_dataframe_restaurant(df2)
                    st.dataframe(df2, use_container_width=True)
                st.markdown("**Estadísticas por categoría**")
                df3 = pd.DataFrame(data[0].get("categoryStats", []))
                if not df3.empty:
                    df3 = format_dataframe_restaurant(df3)
                    st.dataframe(df3, use_container_width=True)

# ---------------- CREAR BULK ----------------
elif menu == "Crear Bulk":
    st.header("Creación Masiva de Documentos")
    st.caption("Puedes crear hasta 50.000 o más documentos. Se envían en lotes para evitar timeouts.")

    sub_menu = st.selectbox("Seleccionar entidad", ["Restaurantes", "Menu Items", "Órdenes", "Reviews"], key="bulk_entity")

    if sub_menu == "Restaurantes":
        st.subheader("Crear Restaurantes en Bulk")
        num = int(st.number_input("Número de restaurantes", min_value=1, max_value=100_000, value=500, step=500))
        if st.button("Crear Bulk Restaurantes", key="bulk_btn_restaurants"):
            progress_bar = st.progress(0.0)
            status_placeholder = st.empty()
            total_created = 0
            try:
                for start in range(0, num, BULK_CHUNK_SIZE):
                    end = min(start + BULK_CHUNK_SIZE, num)
                    chunk = [
                        {
                            "name": f"Restaurante Bulk {i}",
                            "description": f"Descripción {i}",
                            "category": "Bulk",
                            "location": {"type": "Point", "coordinates": [-90.5 + (i % 1000) * 0.01, 14.5 + (i % 1000) * 0.01]}
                        }
                        for i in range(start, end)
                    ]
                    r = requests.post(f"{API_URL}/restaurants/bulk", json=chunk, timeout=120)
                    if r.status_code != 200:
                        status_placeholder.error(f"Error en lote {start}-{end}: {r.status_code}")
                        break
                    total_created += len(chunk)
                    progress_bar.progress(total_created / num)
                    status_placeholder.text(f"Creados {total_created} / {num} restaurantes...")
                else:
                    progress_bar.progress(1.0)
                    status_placeholder.empty()
                    st.success(f"Creados {total_created} restaurantes.")
            except requests.exceptions.RequestException as e:
                status_placeholder.error(f"Error de conexión: {e}")
                st.error(f"Creados hasta ahora: {total_created}")

    elif sub_menu == "Menu Items":
        st.subheader("Crear Menu Items en Bulk")
        num = int(st.number_input("Número de items", min_value=1, max_value=100_000, value=500, step=500))
        restaurant_id = st.text_input("Restaurant ID", key="bulk_restaurant_id")
        if st.button("Crear Bulk Menu Items", key="bulk_btn_menu") and restaurant_id:
            progress_bar = st.progress(0.0)
            status_placeholder = st.empty()
            total_created = 0
            try:
                for start in range(0, num, BULK_CHUNK_SIZE):
                    end = min(start + BULK_CHUNK_SIZE, num)
                    chunk = [
                        {
                            "restaurantId": restaurant_id,
                            "name": f"Item Bulk {i}",
                            "price": 25 + (i % 100),
                            "category": "Bulk",
                            "tags": ["bulk"]
                        }
                        for i in range(start, end)
                    ]
                    r = requests.post(f"{API_URL}/menu-items/bulk", json=chunk, timeout=120)
                    if r.status_code != 200:
                        status_placeholder.error(f"Error en lote {start}-{end}: {r.status_code}")
                        break
                    total_created += len(chunk)
                    progress_bar.progress(total_created / num)
                    status_placeholder.text(f"Creados {total_created} / {num} items...")
                else:
                    progress_bar.progress(1.0)
                    status_placeholder.empty()
                    st.success(f"Creados {total_created} menu items.")
            except requests.exceptions.RequestException as e:
                status_placeholder.error(f"Error de conexión: {e}")
                st.error(f"Creados hasta ahora: {total_created}")

    elif sub_menu == "Órdenes":
        st.subheader("Crear Órdenes en Bulk")
        num = int(st.number_input("Número de órdenes", min_value=1, max_value=100_000, value=1000, step=500))
        user_id = st.text_input("User ID", key="bulk_user_id")
        restaurant_id = st.text_input("Restaurant ID", key="bulk_order_restaurant_id")
        if st.button("Crear Bulk Órdenes", key="bulk_btn_orders") and user_id and restaurant_id:
            progress_bar = st.progress(0.0)
            status_placeholder = st.empty()
            total_created = 0
            try:
                for start in range(0, num, BULK_CHUNK_SIZE):
                    end = min(start + BULK_CHUNK_SIZE, num)
                    chunk = [
                        {
                            "userId": user_id,
                            "restaurantId": restaurant_id,
                            "items": [{"menuItemId": "dummy", "name": "Dummy Item", "quantity": 1, "price": 10}],
                            "status": "pending"
                        }
                        for i in range(start, end)
                    ]
                    r = requests.post(f"{API_URL}/orders/bulk", json=chunk, timeout=120)
                    if r.status_code != 200:
                        status_placeholder.error(f"Error en lote {start}-{end}: {r.status_code}")
                        break
                    total_created += len(chunk)
                    progress_bar.progress(total_created / num)
                    status_placeholder.text(f"Creadas {total_created} / {num} órdenes...")
                else:
                    progress_bar.progress(1.0)
                    status_placeholder.empty()
                    st.success(f"Creadas {total_created} órdenes.")
            except requests.exceptions.RequestException as e:
                status_placeholder.error(f"Error de conexión: {e}")
                st.error(f"Creadas hasta ahora: {total_created}")

    elif sub_menu == "Reviews":
        st.subheader("Crear Reviews en Bulk")
        num = int(st.number_input("Número de reviews", min_value=1, max_value=100_000, value=500, step=500))
        restaurant_id = st.text_input("Restaurant ID", key="bulk_review_restaurant_id")
        user_id = st.text_input("User ID", key="bulk_review_user_id")
        if st.button("Crear Bulk Reviews", key="bulk_btn_reviews") and restaurant_id and user_id:
            progress_bar = st.progress(0.0)
            status_placeholder = st.empty()
            total_created = 0
            try:
                for start in range(0, num, BULK_CHUNK_SIZE):
                    end = min(start + BULK_CHUNK_SIZE, num)
                    chunk = [
                        {
                            "restaurantId": restaurant_id,
                            "userId": user_id,
                            "rating": 5,
                            "comment": f"Review bulk {i}"
                        }
                        for i in range(start, end)
                    ]
                    r = requests.post(f"{API_URL}/reviews/bulk", json=chunk, timeout=120)
                    if r.status_code != 200:
                        status_placeholder.error(f"Error en lote {start}-{end}: {r.status_code}")
                        break
                    total_created += len(chunk)
                    progress_bar.progress(total_created / num)
                    status_placeholder.text(f"Creadas {total_created} / {num} reviews...")
                else:
                    progress_bar.progress(1.0)
                    status_placeholder.empty()
                    st.success(f"Creadas {total_created} reviews.")
            except requests.exceptions.RequestException as e:
                status_placeholder.error(f"Error de conexión: {e}")
                st.error(f"Creadas hasta ahora: {total_created}")

# ---------------- CONSULTAS AVANZADAS ----------------
elif menu == "Consultas Avanzadas":
    st.header("Consultas Avanzadas con Filtros, Ordenamiento, etc.")

    sub_menu = st.selectbox("Seleccionar consulta", ["Restaurantes con Filtros", "Órdenes Enriquecidas", "Menu Items por Tag"])

    if sub_menu == "Restaurantes con Filtros":
        st.subheader("Lista de Restaurantes con Filtros")
        category = st.text_input("Categoría (opcional)", key="adv_rest_cat")
        sort = st.selectbox("Ordenar por", ["createdAt", "-createdAt", "name"], key="adv_rest_sort")
        skip_adv = st.number_input("Saltar primeros", min_value=0, value=0, key="adv_rest_skip")
        limit_adv = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="adv_rest_limit")
        if st.button("Consultar", key="adv_rest_btn"):
            params = {"sort": sort, "skip": skip_adv, "limit": limit_adv}
            if category:
                params["category"] = category
            r = requests.get(f"{API_URL}/restaurants", params=params)
            if r.status_code == 200:
                data = r.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    if "location" in df.columns:
                        df["location"] = df["location"].apply(
                            lambda x: f"{x.get('coordinates', [0,0])[1]:.4f}, {x.get('coordinates', [0,0])[0]:.4f}" if isinstance(x, dict) else str(x)
                        )
                    df = format_dataframe_restaurant(df, date_cols=["createdAt"])
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Mostrando {len(data)} registros.")
                else:
                    st.info("No hay resultados.")
            else:
                st.error("Error en consulta")

    elif sub_menu == "Órdenes Enriquecidas":
        st.subheader("Órdenes Enriquecidas (con Lookups)")
        restaurant_id = st.text_input("Restaurant ID (opcional)", key="adv_ord_rid")
        status_filter = st.selectbox("Estado", ["", "pending", "completed", "cancelled"], key="adv_ord_status")
        min_total = st.number_input("Total mínimo", min_value=0.0, value=0.0, key="adv_ord_mintotal")
        sort = st.selectbox("Ordenar por", ["-createdAt", "createdAt", "totalAmount"], key="adv_ord_sort")
        skip_adv = st.number_input("Saltar primeros", min_value=0, value=0, key="adv_ord_skip")
        limit_adv = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="adv_ord_limit")
        lite = st.checkbox("Vista Lite", key="adv_ord_lite")
        if st.button("Consultar", key="adv_ord_btn"):
            params = {"sort": sort, "skip": skip_adv, "limit": limit_adv, "lite": lite}
            if restaurant_id:
                params["restaurantId"] = restaurant_id
            if status_filter:
                params["status"] = status_filter
            if min_total > 0:
                params["minTotal"] = min_total
            r = requests.get(f"{API_URL}/orders/enriched/query", params=params)
            if r.status_code == 200:
                data = r.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    df = format_dataframe_restaurant(df, currency_cols=["totalAmount"], date_cols=["createdAt"], status_col="status")
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Mostrando {len(data)} registros.")
                else:
                    st.info("No hay resultados.")
            else:
                st.error("Error en consulta")

    elif sub_menu == "Menu Items por Tag":
        st.subheader("Menu Items por Tag")
        tag = st.text_input("Tag", key="adv_tag_input")
        skip_adv = st.number_input("Saltar primeros", min_value=0, value=0, key="adv_tag_skip")
        limit_adv = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="adv_tag_limit")
        if st.button("Consultar", key="adv_tag_btn") and tag:
            params = {"skip": skip_adv, "limit": limit_adv}
            r = requests.get(f"{API_URL}/menu-items/by-tag", params={"tag": tag, **params})
            if r.status_code == 200:
                data = r.json()
                df = pd.DataFrame(data)
                if not df.empty:
                    if "tags" in df.columns:
                        df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x))
                    df = format_dataframe_restaurant(df, currency_cols=["price"])
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Mostrando {len(data)} registros.")
                else:
                    st.info("No hay resultados.")
            else:
                st.error("Error en consulta")

# ---------------- UPDATES ----------------
elif menu == "Updates":
    st.header("Actualización de Documentos")

    sub_menu = st.selectbox("Seleccionar entidad", ["Restaurantes", "Menu Items", "Órdenes", "Reviews", "Bulk Updates"])

    if sub_menu == "Restaurantes":
        st.subheader("Actualizar Restaurante")
        restaurant_id = st.text_input("Restaurant ID")
        patch = st.text_area("Patch JSON", value='{"description": "Nueva descripción"}')
        if st.button("Actualizar") and restaurant_id:
            try:
                patch_data = eval(patch)
                r = requests.patch(f"{API_URL}/restaurants/{restaurant_id}", json=patch_data)
                if r.status_code == 200:
                    st.success("Actualizado")
                else:
                    st.error("Error")
            except:
                st.error("JSON inválido")

    elif sub_menu == "Menu Items":
        st.subheader("Actualizar Menu Item")
        item_id = st.text_input("Menu Item ID")
        patch = st.text_area("Patch JSON", value='{"price": 50}', key="menu_patch")
        if st.button("Actualizar Menu Item") and item_id:
            try:
                patch_data = eval(patch)
                r = requests.patch(f"{API_URL}/menu-items/{item_id}", json=patch_data)
                if r.status_code == 200:
                    st.success(f"Menu Item actualizado - Modified: {r.json().get('modified', 0)}")
                else:
                    st.error(f"Error: {r.text}")
            except:
                st.error("JSON inválido")

    elif sub_menu == "Órdenes":
        st.subheader("Actualizar Orden")
        order_id = st.text_input("Order ID")
        patch = st.text_area("Patch JSON", value='{"status": "completed"}', key="order_patch")
        if st.button("Actualizar Orden") and order_id:
            try:
                patch_data = eval(patch)
                r = requests.patch(f"{API_URL}/orders/{order_id}", json=patch_data)
                if r.status_code == 200:
                    st.success(f"Orden actualizada - Modified: {r.json().get('modified', 0)}")
                else:
                    st.error(f"Error: {r.text}")
            except:
                st.error("JSON inválido")

    elif sub_menu == "Reviews":
        st.subheader("Actualizar Review")
        review_id = st.text_input("Review ID")
        patch = st.text_area("Patch JSON", value='{"rating": 4, "comment": "Actualizado"}', key="review_patch")
        if st.button("Actualizar Review") and review_id:
            try:
                patch_data = eval(patch)
                r = requests.patch(f"{API_URL}/reviews/{review_id}", json=patch_data)
                if r.status_code == 200:
                    st.success(f"Review actualizada - Modified: {r.json().get('modified', 0)}")
                else:
                    st.error(f"Error: {r.text}")
            except:
                st.error("JSON inválido")

    elif sub_menu == "Bulk Updates":
        st.subheader("Actualizar Múltiples Documentos")
        entity = st.selectbox("Entidad", ["restaurants", "menu-items", "orders", "reviews"])
        filter_json = st.text_area("Filtro JSON", value='{"category": "Bulk"}')
        update_json = st.text_area("Update JSON", value='{"$set": {"category": "Updated"}}')
        if st.button("Bulk Update"):
            try:
                filt = eval(filter_json)
                updt = eval(update_json)
                payload = {"filter": filt, "update": updt}
                r = requests.patch(f"{API_URL}/{entity}/bulk/update-many", json=payload)
                if r.status_code == 200:
                    st.success(f"Actualizados: {r.json().get('modified', 0)}")
                else:
                    st.error("Error")
            except:
                st.error("JSON inválido")

# ---------------- DELETES ----------------
elif menu == "Deletes":
    st.header("Eliminación de Documentos")

    sub_menu = st.selectbox("Seleccionar", ["Eliminar Uno", "Eliminar Múltiples"])

    if sub_menu == "Eliminar Uno":
        entity = st.selectbox("Entidad", ["restaurants", "menu-items", "orders", "reviews"])
        doc_id = st.text_input("ID del Documento")
        if st.button("Eliminar") and doc_id:
            r = requests.delete(f"{API_URL}/{entity}/{doc_id}")
            if r.status_code == 204:
                st.success("Eliminado")
            else:
                st.error("Error")

    elif sub_menu == "Eliminar Múltiples":
        entity = st.selectbox("Entidad", ["restaurants", "menu-items", "orders", "reviews"])
        filter_json = st.text_area("Filtro JSON", value='{"category": "Bulk"}')
        if st.button("Bulk Delete"):
            try:
                filt = eval(filter_json)
                payload = {"filter": filt}
                r = requests.post(f"{API_URL}/{entity}/bulk/delete-many", json=payload)
                if r.status_code == 200:
                    st.success(f"Eliminados: {r.json().get('deleted', 0)}")
                else:
                    st.error("Error")
            except:
                st.error("JSON inválido")

# ---------------- ARCHIVOS (GridFS) ----------------
elif menu == "Archivos":
    if "files_upload_response" not in st.session_state:
        st.session_state.files_upload_response = None
    if "files_list_data" not in st.session_state:
        st.session_state.files_list_data = None
    if "files_download_data" not in st.session_state:
        st.session_state.files_download_data = None  # {"content": bytes, "filename": str}

    st.header("Manejo de Archivos con GridFS")

    st.subheader("Subir Archivo")
    uploaded_file = st.file_uploader("Seleccionar archivo", key="archivos_uploader")
    if uploaded_file and st.button("Subir", key="archivos_btn_subir"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        try:
            r = requests.post(f"{API_URL}/files/upload", files=files)
            if r.status_code == 200:
                st.session_state.files_upload_response = r.json()
                st.session_state.files_download_data = None
                st.success("Archivo subido correctamente.")
            else:
                st.session_state.files_upload_response = None
                st.error(f"Error al subir: {r.status_code} - {r.text[:200] if r.text else ''}")
        except requests.exceptions.RequestException as e:
            st.session_state.files_upload_response = None
            st.error(f"Error de conexión: {e}")
        st.rerun()

    if st.session_state.files_upload_response:
        st.success("Última subida exitosa")
        st.json(st.session_state.files_upload_response)
        st.caption("Copia el **gridfsId** para usarlo en Descargar, o usa la lista más abajo.")
        if st.button("Limpiar resultado de subida", key="archivos_btn_limpiar_subida"):
            st.session_state.files_upload_response = None
            st.rerun()

    st.subheader("Lista de Archivos")
    limit_files = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="archivos_limit")
    if st.button("Cargar Archivos", key="archivos_btn_cargar_lista"):
        try:
            r = requests.get(f"{API_URL}/files")
            if r.status_code == 200:
                st.session_state.files_list_data = r.json()
                st.success("Lista cargada.")
            else:
                st.session_state.files_list_data = None
                st.error(f"Error: {r.status_code}")
        except requests.exceptions.RequestException as e:
            st.session_state.files_list_data = None
            st.error(f"Error de conexión: {e}")
        st.rerun()

    if st.session_state.files_list_data is not None:
        data = st.session_state.files_list_data[:limit_files]
        if data:
            df = pd.DataFrame(data)
            if "gridfsId" in df.columns:
                df["gridfsId"] = df["gridfsId"].astype(str).str[:8]
            df = format_dataframe_restaurant(df, date_cols=["uploadedAt"], status_col=None)
            st.dataframe(df, use_container_width=True)
            st.caption(f"Mostrando {len(data)} de {len(st.session_state.files_list_data)} archivos.")
        else:
            st.info("No hay archivos.")
        if st.button("Limpiar lista", key="archivos_btn_limpiar_lista"):
            st.session_state.files_list_data = None
            st.rerun()

    st.subheader("Descargar Archivo")
    # Permitir elegir de la lista si está cargada
    list_options = [""]
    default_idx = 0
    if st.session_state.files_list_data and len(st.session_state.files_list_data) > 0:
        for i, row in enumerate(st.session_state.files_list_data):
            gid = row.get("gridfsId") or row.get("gridfs_id")
            fname = row.get("filename", "?")
            if gid:
                list_options.append(f"{fname} ({gid})")
    gridfs_id_from_list = st.selectbox(
        "O elegir de la lista (si ya cargaste la lista)",
        options=list_options,
        index=default_idx,
        key="archivos_select_file",
    )
    if gridfs_id_from_list:
        m = re.search(r"\(([a-f0-9A-F]{24})\)\s*$", gridfs_id_from_list)
        if m:
            gridfs_id_from_list = m.group(1)
    gridfs_id = st.text_input(
        "GridFS ID (pega aquí o elige arriba)",
        value=gridfs_id_from_list if gridfs_id_from_list and len(gridfs_id_from_list) == 24 else "",
        key="archivos_input_gridfs_id",
    )
    if st.button("Obtener archivo", key="archivos_btn_obtener"):
        id_to_use = (gridfs_id or "").strip() or (gridfs_id_from_list if isinstance(gridfs_id_from_list, str) and len(gridfs_id_from_list) == 24 else "")
        if not id_to_use:
            st.warning("Escribe o elige un GridFS ID.")
        else:
            try:
                r = requests.get(f"{API_URL}/files/{id_to_use}", timeout=60)
                # Leer todo el cuerpo (el backend puede devolver StreamingResponse)
                body = r.content if r.content else b"".join(r.iter_content(chunk_size=8192))
                if r.status_code == 200 and body:
                    filename = "downloaded_file"
                    if "Content-Disposition" in r.headers:
                        m = re.search(r'filename="?([^";\n]+)"?', r.headers["Content-Disposition"])
                        if m:
                            filename = m.group(1).strip()
                    st.session_state.files_download_data = {"content": body, "filename": filename}
                    st.success(f"Archivo listo: {filename} ({len(body)} bytes)")
                elif r.status_code == 200:
                    st.session_state.files_download_data = None
                    st.warning("El servidor respondió OK pero el archivo está vacío.")
                else:
                    st.session_state.files_download_data = None
                    st.error(f"Error al descargar: {r.status_code}" + (f" - {r.text[:150]}" if r.text else ""))
            except requests.exceptions.RequestException as e:
                st.session_state.files_download_data = None
                st.error(f"Error de conexión: {e}")
            st.rerun()

    if st.session_state.files_download_data:
        d = st.session_state.files_download_data
        st.success(f"Descargar: **{d['filename']}** ({len(d['content'])} bytes)")
        st.download_button(
            "Descargar archivo",
            data=d["content"],
            file_name=d["filename"],
            mime="application/octet-stream",
            key="archivos_btn_descargar",
        )
        if st.button("Limpiar descarga", key="archivos_btn_limpiar_descarga"):
            st.session_state.files_download_data = None
            st.rerun()

# ---------------- MANEJO DE ARRAYS ----------------
elif menu == "Manejo de Arrays":
    st.header("Manejo de Arrays ($push, $pull, $addToSet)")

    sub_menu = st.selectbox("Seleccionar operación", ["Agregar Item a Orden", "Remover Item de Orden", "Agregar Tag a Menu Item", "Remover Tag de Menu Item"])

    if sub_menu == "Agregar Item a Orden":
        st.subheader("$push: Agregar Item a Orden")
        order_id = st.text_input("Order ID")
        menu_item_id = st.text_input("Menu Item ID")
        name = st.text_input("Nombre")
        quantity = st.number_input("Cantidad", min_value=1, value=1)
        price = st.number_input("Precio", min_value=0.0, value=10.0)
        if st.button("Push Item") and order_id and menu_item_id:
            payload = {"menuItemId": menu_item_id, "name": name, "quantity": quantity, "price": price}
            r = requests.post(f"{API_URL}/orders/{order_id}/items:push", json=payload)
            if r.status_code == 200:
                st.success("Item agregado")
                st.json(r.json())
            else:
                st.error("Error")

    elif sub_menu == "Remover Item de Orden":
        st.subheader("$pull: Remover Item de Orden")
        order_id = st.text_input("Order ID")
        menu_item_id = st.text_input("Menu Item ID a Remover")
        if st.button("Pull Item") and order_id and menu_item_id:
            r = requests.post(f"{API_URL}/orders/{order_id}/items:pull", json={"menuItemId": menu_item_id})
            if r.status_code == 200:
                st.success("Item removido")
                st.json(r.json())
            else:
                st.error("Error")

    elif sub_menu == "Agregar Tag a Menu Item":
        st.subheader("$addToSet: Agregar Tag a Menu Item")
        item_id = st.text_input("Menu Item ID")
        tag = st.text_input("Tag a Agregar")
        if st.button("Add Tag") and item_id and tag:
            r = requests.post(f"{API_URL}/menu-items/{item_id}/tags:add", json=[tag])
            if r.status_code == 200:
                st.success("Tag agregado")
                st.json(r.json())
            else:
                st.error("Error")

    elif sub_menu == "Remover Tag de Menu Item":
        st.subheader("$pull: Remover Tag de Menu Item")
        item_id = st.text_input("Menu Item ID")
        tag = st.text_input("Tag a Remover")
        if st.button("Remove Tag") and item_id and tag:
            r = requests.post(f"{API_URL}/menu-items/{item_id}/tags:remove", json=[tag])
            if r.status_code == 200:
                st.success("Tag removido")
                st.json(r.json())
            else:
                st.error("Error")

# ---------------- DOCUMENTOS EMBEBIDOS ----------------
elif menu == "Documentos Embebidos":
    st.header("Órdenes y Menús (documentos embebidos)")
    st.caption("Vista simplificada de órdenes con sus productos y de restaurantes con su menú.")

    limit_emb = st.selectbox("Mostrar hasta", LIMIT_OPTIONS, index=1, key="emb_limit")

    st.subheader("Órdenes con productos")
    if st.button("Cargar órdenes con productos", key="emb_btn_orders"):
        r = requests.get(f"{API_URL}/analytics/embedded/orders-with-enriched-items")
        if r.status_code == 200:
            data = r.json()[:limit_emb]
            if not data:
                st.info("No hay órdenes.")
            else:
                for order in data:
                    oid = str(order.get("_id", ""))[:8]
                    total = order.get("totalAmount")
                    total_str = _format_currency(total) if total is not None else ""
                    with st.expander(f"Orden #{oid} — Total: {total_str}", expanded=True):
                        st.markdown("**Productos:**")
                        for item in order.get("enrichedItems", []):
                            sub = item.get("subtotal")
                            sub_str = _format_currency(sub) if sub is not None else ""
                            st.markdown(f"- {item.get('name', '—')}: {item.get('quantity', 0)} × {_format_currency(item.get('price'))} = {sub_str}")
                st.caption(f"Mostrando {len(data)} órdenes.")

    st.subheader("Restaurantes con menú")
    if st.button("Cargar restaurantes con menú", key="emb_btn_rest"):
        r = requests.get(f"{API_URL}/analytics/embedded/restaurant-menu-aggregated")
        if r.status_code == 200:
            data = r.json()[:limit_emb]
            if not data:
                st.info("No hay restaurantes.")
            else:
                for rest in data:
                    with st.expander(f"Restaurante: {rest.get('name', '—')}", expanded=True):
                        st.markdown(f"**Platos en menú:** {rest.get('menuCount', 0)} — Precio medio: {_format_currency(rest.get('avgPrice'))}")
                        cats = rest.get("categories", [])
                        if cats:
                            st.markdown(f"**Categorías:** {', '.join(str(c) for c in cats)}")
                        st.markdown("**Algunos platos:**")
                        for item in rest.get("menu", [])[:5]:
                            st.markdown(f"- {item.get('name', '—')}: {_format_currency(item.get('price'))}")
                st.caption(f"Mostrando {len(data)} restaurantes.")