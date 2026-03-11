import re
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"
BULK_CHUNK_SIZE = 2000  # documentos por request en Crear Bulk (evita timeouts y límites de tamaño)

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

    if st.button("Cargar Restaurantes"):
        response = requests.get(f"{API_URL}/restaurants")
        if response.status_code == 200:
            st.dataframe(response.json())
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

    if st.button("Cargar Menu Items"):
        response = requests.get(f"{API_URL}/menu-items")
        if response.status_code == 200:
            st.dataframe(response.json())
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

    if st.button("Cargar Órdenes"):
        response = requests.get(f"{API_URL}/orders")
        if response.status_code == 200:
            orders = response.json()

            for order in orders:
                order["items"] = ", ".join(
                    [item["name"] for item in order.get("items", [])]
                )

            st.dataframe(orders)
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

    if st.button("Cargar Reviews"):
        response = requests.get(f"{API_URL}/reviews")
        if response.status_code == 200:
            st.dataframe(response.json())
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
        st.metric("Revenue Total", f"${total_revenue}")

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
        if st.button("Categorías Distintas de Restaurantes"):
            r = requests.get(f"{API_URL}/analytics/simple/distinct-categories")
            if r.status_code == 200:
                st.json(r.json())

        if st.button("Conteo por Status de Órdenes"):
            r = requests.get(f"{API_URL}/analytics/simple/counts-by-status")
            if r.status_code == 200:
                st.json(r.json())

    with col4:
        if st.button("Tags Distintos de Menu Items"):
            r = requests.get(f"{API_URL}/analytics/simple/distinct-menu-categories")
            if r.status_code == 200:
                st.json(r.json())

        if st.button("Conteos Generales"):
            r = requests.get(f"{API_URL}/analytics/counts")
            if r.status_code == 200:
                st.json(r.json())

    st.divider()

    # AGREGACIONES COMPLEJAS
    st.subheader("Agregaciones Complejas")
    if st.button("Top Menu Items Vendidos"):
        r = requests.get(f"{API_URL}/analytics/top-menu-items")
        if r.status_code == 200:
            st.dataframe(r.json())

    if st.button("Análisis de Items en Órdenes"):
        r = requests.get(f"{API_URL}/analytics/complex/order-items-analysis")
        if r.status_code == 200:
            st.dataframe(r.json())

    if st.button("Segmentación de Usuarios por Gasto"):
        r = requests.get(f"{API_URL}/analytics/complex/user-spending-brackets")
        if r.status_code == 200:
            st.dataframe(r.json())

    if st.button("Performance Analytics de Restaurantes"):
        r = requests.get(f"{API_URL}/analytics/complex/restaurant-performance-analytics")
        if r.status_code == 200:
            data = r.json()
            if data:
                st.write("Top by Rating:")
                st.dataframe(data[0].get("topByRating", []))
                st.write("Top by Orders:")
                st.dataframe(data[0].get("topByOrders", []))
                st.write("Category Stats:")
                st.dataframe(data[0].get("categoryStats", []))

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
        category = st.text_input("Categoría (opcional)")
        sort = st.selectbox("Ordenar por", ["createdAt", "-createdAt", "name"])
        skip = st.number_input("Skip", min_value=0, value=0)
        limit = st.number_input("Limit", min_value=1, max_value=200, value=20)
        if st.button("Consultar"):
            params = {"sort": sort, "skip": skip, "limit": limit}
            if category:
                params["category"] = category
            r = requests.get(f"{API_URL}/restaurants", params=params)
            if r.status_code == 200:
                st.dataframe(r.json())
            else:
                st.error("Error en consulta")

    elif sub_menu == "Órdenes Enriquecidas":
        st.subheader("Órdenes Enriquecidas (con Lookups)")
        restaurant_id = st.text_input("Restaurant ID (opcional)")
        status_filter = st.selectbox("Status", ["", "pending", "completed", "cancelled"])
        min_total = st.number_input("Min Total Amount", min_value=0.0, value=0.0)
        sort = st.selectbox("Ordenar por", ["-createdAt", "createdAt", "totalAmount"])
        skip = st.number_input("Skip", min_value=0, value=0)
        limit = st.number_input("Limit", min_value=1, max_value=200, value=20)
        lite = st.checkbox("Vista Lite")
        if st.button("Consultar"):
            params = {"sort": sort, "skip": skip, "limit": limit, "lite": lite}
            if restaurant_id:
                params["restaurantId"] = restaurant_id
            if status_filter:
                params["status"] = status_filter
            if min_total > 0:
                params["minTotal"] = min_total
            r = requests.get(f"{API_URL}/orders/enriched/query", params=params)
            if r.status_code == 200:
                st.dataframe(r.json())
            else:
                st.error("Error en consulta")

    elif sub_menu == "Menu Items por Tag":
        st.subheader("Menu Items por Tag")
        tag = st.text_input("Tag")
        skip = st.number_input("Skip", min_value=0, value=0)
        limit = st.number_input("Limit", min_value=1, max_value=200, value=20)
        if st.button("Consultar") and tag:
            params = {"skip": skip, "limit": limit}
            r = requests.get(f"{API_URL}/menu-items/by-tag", params={"tag": tag, **params})
            if r.status_code == 200:
                st.dataframe(r.json())
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
        st.dataframe(st.session_state.files_list_data)
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
    st.header("Manejo de Documentos Embebidos")

    st.subheader("Órdenes con Items Embebidos")
    if st.button("Cargar Órdenes con Items Enriquecidos"):
        r = requests.get(f"{API_URL}/analytics/embedded/orders-with-enriched-items")
        if r.status_code == 200:
            data = r.json()
            for order in data:
                st.write(f"Order ID: {order['_id']}")
                st.write("Items:")
                for item in order.get("enrichedItems", []):
                    st.write(f"  - {item['name']}: {item['quantity']} x ${item['price']} = ${item['subtotal']}")
                st.divider()

    st.subheader("Restaurantes con Menú Embebido")
    if st.button("Cargar Restaurantes con Menú"):
        r = requests.get(f"{API_URL}/analytics/embedded/restaurant-menu-aggregated")
        if r.status_code == 200:
            data = r.json()
            for rest in data:
                st.write(f"Restaurante: {rest['name']}")
                st.write(f"Menú Count: {rest['menuCount']}, Avg Price: ${rest.get('avgPrice', 0):.2f}")
                st.write("Categorías:", rest.get("categories", []))
                st.write("Menú Items (primeros 5):")
                for item in rest.get("menu", [])[:5]:
                    st.write(f"  - {item['name']}: ${item['price']}")
                st.divider()