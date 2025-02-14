import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import random

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
    start, goal, obstacles, 
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
    st.title("Plná šířka okna: RRT s Folium mapou")

    if "map_object" not in st.session_state:
        st.session_state["map_object"] = None
        st.session_state["path_found"] = False
        st.session_state["final_length"] = 0.0

    # Sidebar
    start_x = st.sidebar.slider("Start X", 0.0, 10.0, 1.0, 0.1)
    start_y = st.sidebar.slider("Start Y", 0.0, 10.0, 1.0, 0.1)
    goal_x  = st.sidebar.slider("Goal X",  0.0, 10.0, 9.0, 0.1)
    goal_y  = st.sidebar.slider("Goal Y",  0.0, 10.0, 9.0, 0.1)

    step_size = st.sidebar.slider("Krok RRT", 0.1, 2.0, 0.5, 0.1)
    max_iter  = st.sidebar.slider("Max Iterací", 100, 5000, 1000, 100)

    # Tlačítko
    if st.sidebar.button("Spustit RRT"):
        start = (start_x, start_y)
        goal  = (goal_x, goal_y)

        obstacles = [(5.0, 5.0, 2.0)]  # jedna překážka

        nodes, parent, path = rrt_planner(
            start, goal, obstacles,
            x_limit=(0,10), y_limit=(0,10),
            step_size=step_size, max_iter=max_iter,
            goal_threshold=0.5
        )

        center_lat = 49.7475
        center_lon = 13.3776
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

        folium.Circle(
            location=[5.0, 5.0],
            radius=2000,  
            color='red',
            fill=True,
            fill_opacity=0.3
        ).add_to(m)

        # Start a cíl
        folium.Marker(
            location=[start_y, start_x], 
            popup="Start", 
            icon=folium.Icon(color="blue")
        ).add_to(m)
        folium.Marker(
            location=[goal_y, goal_x],
            popup="Goal",
            icon=folium.Icon(color="green")
        ).add_to(m)

        if path:
            path_coords = [[p[1], p[0]] for p in path]
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

    if st.session_state["map_object"] is not None:
        # Zde nastavujeme opravdu velké rozměry
        st_folium(st.session_state["map_object"], width=2000, height=1200)
        
        if st.session_state["path_found"]:
            st.info(f"Poslední nalezená cesta: délka {st.session_state['final_length']:.2f}")
        else:
            st.info("Poslední výpočet cestu nenašel.")
    else:
        st.write("Zatím neproběhl žádný výpočet. Zvolte parametry v sidebaru a klikněte na **Spustit RRT**.")

if __name__ == "__main__":
    main()
