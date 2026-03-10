import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

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

    sub_menu = st.selectbox("Seleccionar entidad", ["Restaurantes", "Menu Items", "Órdenes", "Reviews"])

    if sub_menu == "Restaurantes":
        st.subheader("Crear Restaurantes en Bulk")
        num = st.number_input("Número de restaurantes", min_value=1, max_value=100, value=5)
        if st.button("Crear Bulk Restaurantes"):
            restaurants = []
            for i in range(num):
                restaurants.append({
                    "name": f"Restaurante Bulk {i}",
                    "description": f"Descripción {i}",
                    "category": "Bulk",
                    "location": {"type": "Point", "coordinates": [-90.5 + i*0.01, 14.5 + i*0.01]}
                })
            r = requests.post(f"{API_URL}/restaurants/bulk", json=restaurants)
            if r.status_code == 200:
                st.success(f"Creados {len(restaurants)} restaurantes")
            else:
                st.error("Error en bulk create")

    elif sub_menu == "Menu Items":
        st.subheader("Crear Menu Items en Bulk")
        num = st.number_input("Número de items", min_value=1, max_value=100, value=10)
        restaurant_id = st.text_input("Restaurant ID")
        if st.button("Crear Bulk Menu Items") and restaurant_id:
            items = []
            for i in range(num):
                items.append({
                    "restaurantId": restaurant_id,
                    "name": f"Item Bulk {i}",
                    "price": 25 + i,
                    "category": "Bulk",
                    "tags": ["bulk"]
                })
            r = requests.post(f"{API_URL}/menu-items/bulk", json=items)
            if r.status_code == 200:
                st.success(f"Creados {len(items)} items")
            else:
                st.error("Error en bulk create")

    elif sub_menu == "Órdenes":
        st.subheader("Crear Órdenes en Bulk")
        num = st.number_input("Número de órdenes", min_value=1, max_value=100, value=5)
        user_id = st.text_input("User ID")
        restaurant_id = st.text_input("Restaurant ID")
        if st.button("Crear Bulk Órdenes") and user_id and restaurant_id:
            orders = []
            for i in range(num):
                orders.append({
                    "userId": user_id,
                    "restaurantId": restaurant_id,
                    "items": [{"menuItemId": "dummy", "name": "Dummy Item", "quantity": 1, "price": 10}],
                    "status": "pending"
                })
            r = requests.post(f"{API_URL}/orders/bulk", json=orders)
            if r.status_code == 200:
                st.success(f"Creadas {len(orders)} órdenes")
            else:
                st.error("Error en bulk create")

    elif sub_menu == "Reviews":
        st.subheader("Crear Reviews en Bulk")
        num = st.number_input("Número de reviews", min_value=1, max_value=100, value=5)
        restaurant_id = st.text_input("Restaurant ID")
        user_id = st.text_input("User ID")
        if st.button("Crear Bulk Reviews") and restaurant_id and user_id:
            reviews = []
            for i in range(num):
                reviews.append({
                    "restaurantId": restaurant_id,
                    "userId": user_id,
                    "rating": 5,
                    "comment": f"Review bulk {i}"
                })
            r = requests.post(f"{API_URL}/reviews/bulk", json=reviews)
            if r.status_code == 200:
                st.success(f"Creadas {len(reviews)} reviews")
            else:
                st.error("Error en bulk create")

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
                patch_data = eval(patch)  # Simple eval, en producción usar json.loads
                r = requests.patch(f"{API_URL}/restaurants/{restaurant_id}", json=patch_data)
                if r.status_code == 200:
                    st.success("Actualizado")
                else:
                    st.error("Error")
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
    st.header("Manejo de Archivos con GridFS")

    st.subheader("Subir Archivo")
    uploaded_file = st.file_uploader("Seleccionar archivo")
    if uploaded_file and st.button("Subir"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        r = requests.post(f"{API_URL}/files/upload", files=files)
        if r.status_code == 200:
            st.success("Archivo subido")
            st.json(r.json())
        else:
            st.error("Error al subir")

    st.subheader("Lista de Archivos")
    if st.button("Cargar Archivos"):
        r = requests.get(f"{API_URL}/files")
        if r.status_code == 200:
            st.dataframe(r.json())
        else:
            st.error("Error")

    st.subheader("Descargar Archivo")
    gridfs_id = st.text_input("GridFS ID")
    if st.button("Descargar") and gridfs_id:
        r = requests.get(f"{API_URL}/files/{gridfs_id}")
        if r.status_code == 200:
            st.download_button("Descargar", r.content, file_name="downloaded_file")
        else:
            st.error("Error al descargar")

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