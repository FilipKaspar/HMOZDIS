import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import random
import time

from shapely.geometry import Polygon, LineString
from geopy.distance import geodesic

#############################
# Vlastní krátké definice
#############################

class State:
    WEEKDAY = "Weekend"
    WEEKEND = "Weekday"

blood_spots = {
    "PLASMA PLACE s.r.o.": (49.74832190000001, 13.3753809), 
    "Unilabs - odběry krve": (49.710246, 13.413911),   
    "SYNLAB - Odběry krve": (49.7276366, 13.3738645),    
    "Fakultní nemocnice Plzeň - Transfuzní oddělení": (49.7287571,13.3751242),  
    "SYNLAB - Odběry krve": (49.742039, 13.3273621),    
    "Unilabs - odběry krve": (49.7447234, 13.3674426),   
    "BioLife (sanaplasma s.r.o.)": (49.7464564, 13.3680987), 
    "Amber Plasma Plzeň": (49.72762090000001, 13.3524081),  
    "EUC Odběrové místo Plzeň": (49.7450877, 13.3830692),    
    "Bioptická Laboratoř s.r.o.": (49.7411058, 13.3876321),  
    "Privamed - nemocnice": (49.765284959069405, 13.359354534829086),     
    "PLASMA PLACE s.r.o.": (49.7483219, 13.3753809), 
    "Nemocnice lochotín": (49.763306, 13.379694)
}

def setup():
    pass

def draw_map():
    pass

st.set_page_config(page_title="RRT Folium Fullscreen", layout="wide")

#############################
# Pomocné funkce
#############################

def distance_degs(a, b):
    """ Vzdálenost VE STUPNÍCH (lokální). """
    return math.hypot(a[0] - b[0], a[1] - b[1])

def path_length_meters(path):
    """ Součet geodetických vzdáleností (v metrech) mezi body cesty. """
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        total += geodesic(path[i], path[i+1]).meters
    return total

def meters_to_deg(meters, lat=49.7):
    """ Hrubý převod metrů -> stupně (1° ~ 111.2 km). """
    return meters / 111_200.0

def steer(from_node, to_point, step_size_deg):
    """ Posun ze stávajícího uzlu k random_point o max step_size_deg. """
    dist = distance_degs(from_node, to_point)
    if dist < step_size_deg:
        return to_point
    theta = math.atan2(to_point[1] - from_node[1], to_point[0] - from_node[0])
    new_x = from_node[0] + step_size_deg * math.cos(theta)
    new_y = from_node[1] + step_size_deg * math.sin(theta)
    return (new_x, new_y)

def line_collision_check(p1, p2, polygons):
    """ Kolize úsečky p1->p2 s polygonem (Shapely). """
    line = LineString([p1, p2])
    for poly_coords in polygons:
        poly = Polygon(poly_coords)
        if line.intersects(poly):
            return False
    return True

def nearest(nodes, random_point):
    """ Najde nejbližší uzel v 'nodes' k random_point. """
    min_dist = float('inf')
    near = None
    for node in nodes:
        dist = distance_degs(node, random_point)
        if dist < min_dist:
            min_dist = dist
            near = node
    return near

#############################
# RRT (klasický)
#############################

def rrt_planner(
    start, goal, obstacles=None,
    x_limit=(49.73, 49.76),
    y_limit=(13.35, 13.40),
    step_size_deg=0.00045,
    max_iter=1000,
    goal_threshold=0.0002
):
    """ Jednoduchý RRT. """
    nodes = [start]
    parent = {start: None}
    
    for _ in range(max_iter):
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        near = nearest(nodes, rand_point)
        new_node = steer(near, rand_point, step_size_deg)
        
        if line_collision_check(near, new_node, obstacles):
            nodes.append(new_node)
            parent[new_node] = near
            
            if distance_degs(new_node, goal) < goal_threshold:
                if line_collision_check(new_node, goal, obstacles):
                    parent[goal] = new_node
                    nodes.append(goal)
                    break
    
    # Rekonstrukce cesty
    if goal not in parent:
        return nodes, parent, None

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    
    return nodes, parent, path

#############################
# Bi-RRT (Bidirectional)
#############################

def bi_rrt_planner(
    start, goal, obstacles=None,
    x_limit=(49.73, 49.76),
    y_limit=(13.35, 13.40),
    step_size_deg=0.00045,
    max_iter=1000,
    goal_threshold=0.0002
):
    """
    Jednoduchá verze Bidirectional RRT:
    - Dvě množiny uzlů: tree_a (od startu) a tree_b (od cíle).
    - Střídavě přirůstáme k tree_a, pak se snažíme připojit k tree_b, atd.
    """
    tree_a = [start]
    tree_b = [goal]
    parent_a = {start: None}
    parent_b = {goal: None}
    
    def build_new_node(tree_from, parent_from, rand):
        """ Vnitřní funkce pro rozšíření jednoho stromu. """
        nearest_node = nearest(tree_from, rand)
        new_node = steer(nearest_node, rand, step_size_deg)
        if line_collision_check(nearest_node, new_node, obstacles):
            tree_from.append(new_node)
            parent_from[new_node] = nearest_node
            return new_node
        return None
    
    for i in range(max_iter):
        # 1) random point + extend tree_a
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        new_a = build_new_node(tree_a, parent_a, rand_point)
        if new_a is None:
            continue
        
        # 2) Přiblížit se z tree_b k new_a
        new_b = build_new_node(tree_b, parent_b, new_a)
        if new_b is not None:
            # Ověříme, zda jsme blízko stromu A
            if distance_degs(new_a, new_b) < step_size_deg:
                # Máme spojení? Nebo aspoň hodně blízko?
                # Nebo zkontrolovat, jestli to není v goal_threshold
                if distance_degs(new_b, new_a) < goal_threshold:
                    # Rekonstrukce cesty
                    # path A: new_a -> start
                    path_a = []
                    cur = new_a
                    while cur is not None:
                        path_a.append(cur)
                        cur = parent_a[cur]
                    path_a.reverse()
                    
                    # path B: new_b -> goal
                    path_b = []
                    cur = new_b
                    while cur is not None:
                        path_b.append(cur)
                        cur = parent_b[cur]
                    
                    # Combined
                    path = path_a + path_b
                    return tree_a + tree_b, {**parent_a, **parent_b}, path
    
    # Nenalezena cesta
    return tree_a + tree_b, {**parent_a, **parent_b}, None

#############################
# RRT* (základ)
#############################

def rrt_star_planner(
    start, goal, obstacles=None,
    x_limit=(49.73, 49.76),
    y_limit=(13.35, 13.40),
    step_size_deg=0.00045,
    max_iter=1000,
    goal_threshold=0.0002,
    radius_deg=0.0009  # "Okolí" pro rewire, ~100 m
):
    """
    Jednoduchá implementace RRT*:
    - Každý nový uzel se přidá, pak se v jeho okolí (poloměr = radius_deg) 
      zkusí "přepojit" k nejbližšímu uzlu s nižší "cost" (kdyby to zkrátilo cestu).
    - 'cost' = součet vzdáleností od startu.
    - Implementace je orientační. 
    """
    nodes = [start]
    parent = {start: None}
    cost = {start: 0.0}  # cost[u] = vzdálenost od startu

    def get_path_cost(u):
        return cost[u]

    def dist(a, b):
        return distance_degs(a, b)

    for _ in range(max_iter):
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        near = nearest(nodes, rand_point)
        new_node = steer(near, rand_point, step_size_deg)

        if not line_collision_check(near, new_node, obstacles):
            continue
        
        # Přidáváme new_node
        nodes.append(new_node)
        parent[new_node] = near
        cost[new_node] = cost[near] + dist(near, new_node)
        
        # RRT* REWIRE
        # Hledáme uzly v okolí radius_deg
        neighbors = []
        for nd in nodes:
            if nd == new_node:
                continue
            if dist(nd, new_node) < radius_deg:
                # Zkusíme, jestli rewire k nd z new_node zkrátí cost?
                if line_collision_check(nd, new_node, obstacles):
                    neighbors.append(nd)

        # 1) Minimální cost pro new_node
        # Zkusíme, zda se nepřipojit k někomu jinému než near
        best_parent = near
        best_cost = cost[new_node]
        for nb in neighbors:
            # cost[nb] + dist(nb, new_node)
            c = cost[nb] + dist(nb, new_node)
            if c < best_cost:
                # Zkontrolujeme, zda je tam volná cesta
                if line_collision_check(nb, new_node, obstacles):
                    best_parent = nb
                    best_cost = c
        # Pokud jsme našli lepšího parenta
        if best_parent != near:
            parent[new_node] = best_parent
            cost[new_node] = best_cost

        # 2) Rewire sousedy k new_node (pokud je to výhodnější)
        for nb in neighbors:
            new_cost_thru_new_node = cost[new_node] + dist(new_node, nb)
            if new_cost_thru_new_node < cost[nb]:
                # Lepší rewire?
                # Zkontrolujeme kolizi
                if line_collision_check(new_node, nb, obstacles):
                    parent[nb] = new_node
                    cost[nb] = new_cost_thru_new_node

        # Kontrola, zda jsme dosáhli goal
        if distance_degs(new_node, goal) < goal_threshold:
            if line_collision_check(new_node, goal, obstacles):
                parent[goal] = new_node
                nodes.append(goal)
                cost[goal] = cost[new_node] + dist(new_node, goal)
                break

    # Rekonstrukce cesty
    if goal not in parent:
        return nodes, parent, None

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

    # OPRAVENÁ STRUKTURA OBSTÁCEK: seznam polygonů
    obstacles_temp = [
        [(49.789742, 13.377459), (49.789503, 13.383207), (49.792489, 13.382967), (49.792489, 13.378221)],
        [(49.789486, 13.389605), (49.788987, 13.391751), (49.793169, 13.394830), (49.796258, 13.400416), (49.798323, 13.393524), (49.793410, 13.390138)],
        [(49.785697, 13.369857), (49.786404, 13.370479), (49.787256, 13.367314), (49.792193, 13.361694), (49.792227, 13.354949), (49.793070, 13.350377), (49.789972, 13.350244)],
        [(49.756130, 13.351048), (49.758085, 13.360942), (49.760251, 13.359258), (49.758501, 13.350890), (49.756935, 13.351562), (49.756628, 13.350737)],
        [(49.765585, 13.302135), (49.764773, 13.300106), (49.760927, 13.308878), (49.761861, 13.310042)],
        [(49.759806, 13.368669), (49.760423, 13.369742), (49.755419, 13.375825), (49.754975, 13.374763)],
        [(49.745201, 13.391218), (49.743821, 13.392080), (49.741359, 13.381861), (49.741777, 13.381497)],
        [(49.74081330463744, 13.365729461040278),(49.740138237303796, 13.364828756160568),(49.740019418350066, 13.370449538300813), (49.74030797816033, 13.37037074228835)],
        [(49.74797303071158, 13.376985477726452),(49.74779179783425, 13.378449233529402),(49.74667040434944, 13.377818153183219),(49.74673270466758, 13.376783882615864)],
        [(49.74151382169769, 13.357973263160405), (49.74044520079958, 13.357457114651659),(49.740204294571605, 13.3627141827963),(49.7409640716896, 13.362733299407733)],
        [(49.750794068449935, 13.384579212622208), (49.750886704609144, 13.3857740008369), (49.749404504830586, 13.38638573240282), (49.74937362518688, 13.385229177410999)],
        [(49.73016579965147, 13.346884853249462),(49.72995404462681, 13.353085788536971),(49.728229719323366, 13.35268799268834), (49.728562488625485, 13.347189050074885)],
        [(49.75037000343024, 13.374469289315966),(49.749981365353506, 13.374927570176839),(49.74633541843774, 13.373409514825195), (49.74642795855087, 13.37300851907193)],
        [(49.730046030957496, 13.367372604049445),(49.729574397818084, 13.368373251074546),(49.7297765269079, 13.371614930662345),(49.7318045084484, 13.370666400669801)],
        [(49.74267608054354, 13.371806297624703),(49.7425020528938, 13.372057025018103),(49.73943799984161, 13.37116869587113),(49.739600035836844, 13.370964399476508)],
        [(49.74352345574658, 13.375366491752187),(49.74332565119359, 13.375241269544615),(49.74337060684903, 13.383311145503825),(49.743532446847915, 13.383185923296251)],
        [(49.75020064445369, 13.36922871234688),(49.749930643165285, 13.370612356110446),(49.74867661748086, 13.370092328924141),(49.74910262984229, 13.36780792378429)],
        [(49.7363066424715, 13.370276586728266),(49.73627722350195, 13.370655908362941),(49.73176610371765, 13.370200722282894),(49.73171706750433, 13.369821400648224)],
        [(49.73547530128439, 13.357048900536238),(49.73537712549911, 13.360532475996507),(49.73260846320267, 13.359410725084741),(49.73299002377244, 13.35687992871055)],
        [(49.735092686928326, 13.350291526379749),(49.734945588222615, 13.35047360076439),(49.73990928155423, 13.36482681895725),(49.73966895832845, 13.36482681895725)],
        [(49.75412777907185, 13.376869211216098),(49.75396761067354, 13.376125475834211),(49.75236589759698, 13.378170748133313),(49.75217368847307, 13.37639817880648)],
        [(49.76449871759597, 13.372234514508522),(49.764433306246126, 13.373490221941879),(49.763020399547784, 13.373135788392139),(49.76311851939896, 13.37176868755744)],
        [(49.74005578459149, 13.386406109886835),(49.74001797896334, 13.386552358375702),(49.738947890940814, 13.386913204217215),(49.73514805356559, 13.390314245390476),(49.734780535269856, 13.39033570306293),(49.73778300888891, 13.387685680514934)],
        [(49.73313689913558, 13.384551776762402),(49.73293896740761, 13.387056807307015),(49.73539860968545, 13.388000966171179),(49.73580618686817, 13.38743810216142)],
        [(49.73364307007585, 13.381497924581375),(49.73358755182353, 13.38241935502391),(49.73269420394294, 13.382278797837653),(49.732764864826144, 13.381365176127007)],
        ]

    # SessionState
    if "map_object" not in st.session_state:
        st.session_state["map_object"] = None
    if "path_found" not in st.session_state:
        st.session_state["path_found"] = False
    if "final_length" not in st.session_state:
        st.session_state["final_length"] = 0.0
    if "final_path" not in st.session_state:
        st.session_state["final_path"] = []

    # Sidebar
    st.title("RRT varianty: Klasický, Bi-RRT, RRT*")

    # Select algorithm
    algorithm = st.sidebar.selectbox(
        "Vyberte algoritmus",
        ["RRT", "Bi-RRT", "RRT*"]
    )

    start = st.sidebar.selectbox("Start", list(blood_spots.keys()))
    goal = st.sidebar.selectbox("End", list(blood_spots.keys()))

    step_size_m = st.sidebar.number_input("Krok RRT (v metrech)", value=50, min_value=1, step=10)
    step_size_deg = meters_to_deg(step_size_m)
    max_iter = st.sidebar.slider("Max Iterací", 100, 5000, 1000, 100)

    # Tlačítko
    if st.sidebar.button("Spustit"):
        # Např. 20 m + ...
        goal_threshold_deg = meters_to_deg(50)

        # Zavoláme zvolený algoritmus
        if algorithm == "RRT":
            nodes, parent, path = rrt_planner(
                blood_spots[start],
                blood_spots[goal],
                obstacles_temp,
                x_limit=(49.73, 49.76),
                y_limit=(13.35, 13.40),
                step_size_deg=step_size_deg,
                max_iter=max_iter,
                goal_threshold=goal_threshold_deg
            )
        elif algorithm == "Bi-RRT":
            nodes, parent, path = bi_rrt_planner(
                blood_spots[start],
                blood_spots[goal],
                obstacles_temp,
                x_limit=(49.73, 49.76),
                y_limit=(13.35, 13.40),
                step_size_deg=step_size_deg,
                max_iter=max_iter,
                goal_threshold=goal_threshold_deg
            )
        else:  # RRT*
            nodes, parent, path = rrt_star_planner(
                blood_spots[start],
                blood_spots[goal],
                obstacles_temp,
                x_limit=(49.73, 49.76),
                y_limit=(13.35, 13.40),
                step_size_deg=step_size_deg,
                max_iter=max_iter,
                goal_threshold=goal_threshold_deg
            )

        # Nová folium mapa
        center_lat, center_lon = 49.7475, 13.3776
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

        # Překážky
        for poly_coords in obstacles_temp:
            folium.Polygon(
                locations=poly_coords,
                color="red",
                fill=True,
                fill_opacity=0.2
            ).add_to(m)

        # Start, cíl
        folium.Marker(
            location=blood_spots[start],
            popup=start,
            icon=folium.Icon(color="blue")
        ).add_to(m)
        folium.Marker(
            location=blood_spots[goal],
            popup=goal,
            icon=folium.Icon(color="green")
        ).add_to(m)

        # Ostatní body
        for place in blood_spots:
            if place == start or place == goal:
                continue
            folium.Marker(
                location=blood_spots[place],
                popup=place,
                icon=folium.Icon(color="orange")
            ).add_to(m)

        # Výsledek
        if path:
            st.session_state["final_path"] = path
            length_m = path_length_meters(path)
            st.session_state["final_length"] = length_m
            st.session_state["path_found"] = True

            folium.PolyLine(
                locations=path,
                color="green",
                weight=3,
                opacity=1
            ).add_to(m)

            st.success(f"[{algorithm}] Cesta nalezena! Délka: {length_m:.2f} m.")
        else:
            st.session_state["final_path"] = []
            st.session_state["final_length"] = 0.0
            st.session_state["path_found"] = False
            st.error(f"[{algorithm}] Cesta NENALEZENA.")

        # Uložit mapu
        st.session_state["map_object"] = m

    # Zobrazení mapy
    draw_map()

    if st.session_state["map_object"] is not None:
        st_folium(st.session_state["map_object"], width=1500, height=700)
        
        if st.session_state["path_found"]:
            st.info(f"Poslední nalezená cesta (v metrech): {st.session_state['final_length']:.2f}")
        else:
            st.info("Poslední výpočet cestu nenašel.")
    else:
        st.write("Vyberte algoritmus, parametry a klikněte na **Spustit**.")


if __name__ == "__main__":
    main()
