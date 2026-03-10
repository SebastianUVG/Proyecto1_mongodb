import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Restaurant Dashboard", layout="wide")

st.title("Restaurant System Dashboard")

menu = st.sidebar.selectbox(
    "Selecciona una sección",
    ["Restaurantes", "Menu Items", "Órdenes", "Reviews", "Analytics"]
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