import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import random
from main import draw_map, setup, start_app, base_map, create_circlepoint, add_line_to_map
from data import obstacles, blood_spots
from enums import State

index = 1

#############################
# Nastavení celé stránky
#############################
st.set_page_config(page_title="RRT Folium Fullscreen", layout="wide")

#############################
# Pomocné funkce
#############################

def distance(a, b):
    """ Euklidovská vzdálenost """
    return math.hypot(a[0] - b[0], a[1] - b[1])

def path_length(path):
    """ Vrátí součet vzdáleností mezi po sobě jdoucími body """
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path)-1):
        total += distance(path[i], path[i+1])
    return total

def steer(from_node, to_point, step_size):
    dist = distance(from_node, to_point)
    if dist < step_size:
        return to_point
    else:
        theta = math.atan2(to_point[1] - from_node[1], to_point[0] - from_node[0])
        new_x = from_node[0] + step_size * math.cos(theta)
        new_y = from_node[1] + step_size * math.sin(theta)
        return (new_x, new_y)

def line_collision_check(p1, p2, obstacles, resolution=20):
    """Zde jen kontrolujeme kruhovou překážku."""
    x1, y1 = p1
    x2, y2 = p2
    for i in range(resolution + 1):
        t = i / resolution
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        for ox, oy, r in obstacles:
            if (x - ox)**2 + (y - oy)**2 <= r**2:
                return False
    return True

def nearest(nodes, random_point):
    min_dist = float('inf')
    nearest_node = None
    for node in nodes:
        dist = distance(node, random_point)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    return nearest_node

#############################
# Jednoduchý RRT
#############################

def rrt_planner(
    start, goal, obstacles=None,
    x_limit=(0,10), y_limit=(0,10),
    step_size=0.5, max_iter=1000,
    goal_threshold=0.5
):
    nodes = [start]
    parent = {start: None}
    
    for _ in range(max_iter):
        rand_point = (
            random.uniform(*x_limit), 
            random.uniform(*y_limit)
        )
        nearest_node = nearest(nodes, rand_point)
        new_node = steer(nearest_node, rand_point, step_size)
        
        if line_collision_check(nearest_node, new_node, obstacles):
            nodes.append(new_node)
            parent[new_node] = nearest_node
            
            if distance(new_node, goal) < goal_threshold:
                if line_collision_check(new_node, goal, obstacles):
                    parent[goal] = new_node
                    nodes.append(goal)
                    break
    
    if goal not in parent:
        return nodes, parent, None
    
    # Rekonstrukce path
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    
    return nodes, parent, path


#############################
# Streamlit aplikace
#############################

def main():
    setup()
    st.title("Plná šířka okna: RRT s Folium mapou")

    obstacles_temp = [(5.0, 5.0, 2.0)]  # jedna překážka

    if "map_object" not in st.session_state:
        st.session_state["nodes"] = None
        st.session_state["path"] = None
        st.session_state["map_object"] = None
        st.session_state["path_found"] = False
        st.session_state["final_length"] = 0.0

    # Sidebar
    start = st.sidebar.selectbox("Start", blood_spots)
    goal = st.sidebar.selectbox("End", blood_spots)

    option = st.sidebar.selectbox(
        'Choose an option:',  # Label for the dropdown
        [State.WEEKDAY, State.WEEKEND]  # List of options
    )

    st.session_state["state"] = option

    step_size = st.sidebar.slider("Krok RRT", 0.00001, 2.0, 0.00001, 0.005)
    max_iter  = st.sidebar.slider("Max Iterací", 100, 5000, 1000, 100)

    # Tlačítko
    if st.sidebar.button("Spustit RRT"):
        nodes, parent, path = rrt_planner(
            start, goal, obstacles_temp,
            x_limit=(0,10), y_limit=(0,10),
            step_size=step_size, max_iter=max_iter,
            goal_threshold=0.5
        )

        st.session_state["nodes"] = nodes
        st.session_state["path"] = path

        st.session_state["path"].append(start)
        st.session_state["path"].append(goal)

        center_lat = 49.7475
        center_lon = 13.3776

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        # Start a cíl
        folium.Marker(
            location=start,
            popup="Start",
            icon=folium.Icon(color="blue")
        ).add_to(m)
        folium.Marker(
            location=goal,
            popup="Goal",
            icon=folium.Icon(color="green")
        ).add_to(m)

        if path:
            path_coords = [[p[0], p[1]] for p in st.session_state["path"]]
            folium.PolyLine(
                locations=path_coords,
                color="red",
                weight=3,
                opacity=1
            ).add_to(m)
            
            st.session_state["final_length"] = path_length(path)
            st.session_state["path_found"] = True
            st.success(f"Cesta nalezena! Délka: {st.session_state['final_length']:.2f}.")
        else:
            st.session_state["final_length"] = 0.0
            st.session_state["path_found"] = False
            st.error("Cesta NENALEZENA.")

        st.session_state["map_object"] = m

    if st.session_state["path"] and index < len(st.session_state["path"]):
        st.fragment(add_line_to_map, run_every=0.5)(st.session_state["path"][index - 1], st.session_state["path"][index])

    draw_map()

    if st.session_state["map_object"] is not None:
        # Zde nastavujeme opravdu velké rozměry
        st_folium(st.session_state["map_object"], width=2000, height=700)
        
        if st.session_state["path_found"]:
            st.info(f"Poslední nalezená cesta: délka {st.session_state['final_length']:.2f}")
        else:
            st.info("Poslední výpočet cestu nenašel.")
    else:
        st.write("Zatím neproběhl žádný výpočet. Zvolte parametry v sidebaru a klikněte na **Spustit RRT**.")

if __name__ == "__main__":
    main()
