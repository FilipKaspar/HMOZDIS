import streamlit as st
from random import random
import folium
from streamlit_folium import st_folium
from enum import Enum
from data import obstacles
from enums import State

def create_cords():
    random_lat = (0.5 - random()) + st.session_state.map_config["center"][0]
    random_lon = (0.5 - random()) + st.session_state.map_config["center"][1]

    return random_lat, random_lon

def create_circlepoint(point : tuple):
    # lat, lon = create_cords()

    return folium.CircleMarker(
        location=point,
        fill=True,
        fill_opacity=1,
        popup=f"Nemocnice",
    )

def create_line(point1, point2):
    # lat1, lon1 = create_cords()
    # lat2, lon2 = create_cords()

    return folium.PolyLine(locations=[point1, point2], color="blue", weight=5, opacity=0.7)


@st.cache_data
def base_map():
    m = folium.Map(
        location=st.session_state.map_config["center"],
        zoom_start=st.session_state.map_config["zoom"],
    )
    fg = folium.FeatureGroup(name="Markers")

    return m, fg


@st.fragment(run_every=0.5)
def draw_map():
    m, fg = base_map()

    for marker in st.session_state["markers"]:
        fg.add_child(marker)

    for line in st.session_state["lines"]:
        fg.add_child(line)

    for obstacle in obstacles.get(st.session_state["state"]):
        obs = folium.Polygon(
            locations=obstacle,
            color="red",
            weight=5,
            opacity=0.7,
            fill=True,
            fill_opacity=0.3,
        )
        fg.add_child(obs)

    st_folium(
        m,
        feature_group_to_add=fg,
        center=st.session_state.map_config["center"],
        zoom=st.session_state.map_config["zoom"],
        key="user-map",
        returned_objects=[],
        use_container_width=True,
        height=600,
    )


def add_random_marker():
    st.session_state["markers"].append(create_circlepoint())

def add_line_to_map(point1, point2):
    st.session_state["lines"].append(create_line(point1, point2))

def setup():
    if "markers" not in st.session_state:
        st.session_state["markers"] = []

    if "lines" not in st.session_state:
        st.session_state["lines"] = []

    if "state" not in st.session_state:
        st.session_state["state"] = None

    if "map_config" not in st.session_state:
        st.session_state.map_config = {"center": [49.747, 13.3776], "zoom": 13}

def start_app():
    setup()
    with st.sidebar:
        if st.button("Add random marker"):
            add_random_marker()

        if st.button("Clear markers"):
            st.session_state["markers"].clear()

        option = st.selectbox(
            'Choose an option:',  # Label for the dropdown
            [State.WEEKDAY, State.WEEKEND]  # List of options
        )

        st.session_state["state"] = option

        if st.toggle("Start adding markers automatically"):
            st.fragment(add_random_marker, run_every=0.5)()

    draw_map()


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    start_app()