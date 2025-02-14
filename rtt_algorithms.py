import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import math
import random
import io
import base64
from main import draw_map, setup, start_app, base_map, create_circlepoint

from matplotlib.animation import FuncAnimation

#############################
# Pomocné funkce
#############################

def distance(a, b):
    """ Euklidovská vzdálenost """
    return math.hypot(a[0] - b[0], a[1] - b[1])

def steer(from_node, to_point, step_size):
    """
    Posune se od from_node směrem k to_point o maximálně step_size.
    Vrací novou pozici (x, y).
    """
    dist = distance(from_node, to_point)
    if dist < step_size:
        return to_point
    else:
        theta = math.atan2(to_point[1] - from_node[1], to_point[0] - from_node[0])
        new_x = from_node[0] + step_size * math.cos(theta)
        new_y = from_node[1] + step_size * math.sin(theta)
        return (new_x, new_y)

def line_collision_check(p1, p2, obstacles, resolution=20):
    """
    Zkontroluje, zda úsečka (p1 -> p2) koliduje s překážkami.
    obstacles = [(ox, oy, r), ...], kde r je poloměr kruhu.
    """
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

def path_length(path):
    if not path or len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        total += distance(path[i], path[i+1])
    return total

#############################
# KLASICKÝ RRT
#############################

def nearest(nodes, random_point):
    """ Najde nejbližší uzel v seznamu nodes k random_point. """
    min_dist = float('inf')
    nearest_node = None
    for node in nodes:
        dist = distance(node, random_point)
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    return nearest_node

def rrt_planner(start, goal, obstacles, x_limit, y_limit, step_size=0.5, max_iter=2000, goal_threshold=0.5):
    """ Klasický RRT """
    nodes = [start]
    parent = {start: None}
    
    for _ in range(max_iter):
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        nearest_node = nearest(nodes, rand_point)
        new_node = steer(nearest_node, rand_point, step_size)
        
        if line_collision_check(nearest_node, new_node, obstacles):
            nodes.append(new_node)
            parent[new_node] = nearest_node
            
            # Pokud jsme blízko cíle, zkusíme rovnou spojit do cíle
            if distance(new_node, goal) < goal_threshold:
                if line_collision_check(new_node, goal, obstacles):
                    parent[goal] = new_node
                    nodes.append(goal)
                    break
    
    if goal not in parent:
        return nodes, parent, None
    
    # Rekonstrukce cesty
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    
    return nodes, parent, path

#############################
# RRT* (ZÁKLADNÍ VERZE)
#############################

def rrt_star_planner(start, goal, obstacles, x_limit, y_limit, step_size=0.5, max_iter=2000, goal_threshold=0.5, radius=1.0):
    """
    Jednoduchá RRT*:
    - Udržujeme cost[u] = délka cesty od startu k uzlu u.
    - Při přidání nového uzlu se podíváme do jeho okolí (do radius) a vybereme nejlepšího rodiče.
    - Poté re-wire: zkusíme zlepšit cesty k sousedům, pokud je to výhodné.
    """
    nodes = [start]
    parent = {start: None}
    cost = {start: 0.0}  # náklady (vzdálenost od startu)
    
    for _ in range(max_iter):
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        # 1) Najdeme nejbližší uzel
        nearest_node = nearest(nodes, rand_point)
        
        # 2) Nový uzel
        new_node = steer(nearest_node, rand_point, step_size)
        
        # 3) Zkontrolujeme kolizi
        if not line_collision_check(nearest_node, new_node, obstacles):
            continue
        
        # 4) Najdeme "nejlepšího rodiče" z uzlů poblíž (v okruhu radius)
        new_cost = cost[nearest_node] + distance(nearest_node, new_node)
        best_parent = nearest_node
        
        # Projdeme uzly v okolí
        near_nodes = []
        for node in nodes:
            if distance(node, new_node) < radius:
                near_nodes.append(node)
        
        # Zkusíme najít levnějšího rodiče
        for node in near_nodes:
            if line_collision_check(node, new_node, obstacles):
                temp_cost = cost[node] + distance(node, new_node)
                if temp_cost < new_cost:
                    new_cost = temp_cost
                    best_parent = node
        
        # 5) Přidáme new_node do stromu
        nodes.append(new_node)
        parent[new_node] = best_parent
        cost[new_node] = new_cost
        
        # 6) Re-wire okolí: zkusíme zlepšit cestu pro near_nodes
        for node in near_nodes:
            if node == best_parent:
                continue
            # zkusíme, zda přes new_node není cesta kratší
            dist_new = cost[new_node] + distance(new_node, node)
            if dist_new < cost[node]:
                # re-wire
                if line_collision_check(new_node, node, obstacles):
                    parent[node] = new_node
                    cost[node] = dist_new
        
        # 7) Ověříme cíl
        if distance(new_node, goal) < goal_threshold:
            if line_collision_check(new_node, goal, obstacles):
                # spojujeme cíl
                cost[goal] = cost[new_node] + distance(new_node, goal)
                parent[goal] = new_node
                nodes.append(goal)
                break
    
    if goal not in parent:
        return nodes, parent, None
    
    # Rekonstrukce cesty
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    path.reverse()
    
    return nodes, parent, path

#############################
# Bi-RRT
#############################

def birrt_planner(start, goal, obstacles, x_limit, y_limit, step_size=0.5, max_iter=2000, goal_threshold=0.5):
    """
    Jednoduchý bidirekcionální RRT: rosteme z obou stran (start, goal).
    Každou iteraci rozšiřujeme jeden strom, poté se snažíme napojit druhý strom směrem k novému uzlu.
    Pokud se potkají, máme cestu.
    """
    # Dva stromy: A (start) a B (goal)
    nodesA = [start]
    parentA = {start: None}
    
    nodesB = [goal]
    parentB = {goal: None}
    
    def grow_tree(nodes_from, parent_from, target_point):
        """ Přidá novou větev v jednom stromu směrem k target_point. Vrací (new_node či None). """
        nearest_node = nearest(nodes_from, target_point)
        new_node = steer(nearest_node, target_point, step_size)
        if line_collision_check(nearest_node, new_node, obstacles):
            nodes_from.append(new_node)
            parent_from[new_node] = nearest_node
            return new_node
        return None
    
    for i in range(max_iter):
        # 1) Náhodný bod
        rand_point = (random.uniform(*x_limit), random.uniform(*y_limit))
        
        # 2) Rozšíříme strom A směrem k rand_point
        newA = grow_tree(nodesA, parentA, rand_point)
        if newA is None:
            continue
        
        # 3) Zkusíme propojit strom B směrem k newA
        newB = grow_tree(nodesB, parentB, newA)
        if newB is None:
            continue
        
        # 4) Zjistíme, zda se newA a newB dostatečně nepřiblížily (resp. jestli to nejsou totéž)
        #    Případně zkusíme přímo "propojit" newA a newB
        if distance(newA, newB) < step_size:
            # Už to chápeme jako propojení
            # => zrekonstruujeme cestu: start -> newA -> newB -> goal
            #    Přičemž newA je ve stromu A, newB v B.
            
            # ale pro jistotu zkusíme, jestli se opravdu dají spojit přímou úsečkou
            if not line_collision_check(newA, newB, obstacles):
                continue
            
            # Máme cestu
            # Zrekonstruujeme cestu A: start -> ... -> newA
            pathA = []
            cur = newA
            while cur is not None:
                pathA.append(cur)
                cur = parentA[cur]
            pathA.reverse()  # aby šla od startu do newA
            
            # Zrekonstruujeme cestu B: newB -> ... -> goal
            pathB = []
            cur = newB
            while cur is not None:
                pathB.append(cur)
                cur = parentB[cur]
            # ta jde od newB k goal, my ji chceme připojit v pořadí newB -> goal,
            # ale newA a newB se setkaly, tak jen malá úprava
            pathB = pathB  # od newB k goal (už je to "obráceně" logicky)
            
            # Celková cesta je pathA + pathB (krom duplicity newB, která je totéž co newA?)
            # Pokud to chceme spojit "přímo", radši zkontrolujeme, zda newA == newB atp.
            # V praxi to může být trošku upraveno, pro ukázku to stačí:
            if pathB and pathA[-1] == pathB[0]:
                # newA == newB
                path_final = pathA + pathB[1:]
            else:
                # jinak třeba pathA + pathB
                path_final = pathA + pathB
            
            # Přidáme navíc i cíl, pokud tam náhodou není
            if path_final[-1] != goal:
                path_final.append(goal)
            
            # Vytvoříme sjednocené "nodes" a "parent" jen kvůli animaci 
            # (volitelné, pro animaci nepotřebujeme celé stromy).
            all_nodes = list(set(nodesA + nodesB))
            all_parents = {}
            # Kopie parentA
            for k, v in parentA.items():
                all_parents[k] = v
            # Kopie parentB
            for k, v in parentB.items():
                if k not in all_parents:
                    all_parents[k] = v

            return all_nodes, all_parents, path_final
    
    # Pokud jsme zde, cesta se nenašla
    all_nodes = list(set(nodesA + nodesB))
    all_parents = {}
    for k, v in parentA.items():
        all_parents[k] = v
    for k, v in parentB.items():
        if k not in all_parents:
            all_parents[k] = v

    return all_nodes, all_parents, None

#############################
# Streamlit aplikace
#############################

def main():
    st.set_page_config(layout="wide")

    st.title("Plánování trasy: RRT, RRT* a Bi-RRT (pouze GIF)")

    algo_choice = st.sidebar.selectbox("Vyber algoritmus", ["RRT", "RRT*", "Bi-RRT"])

    # Parametry: start a cíl
    start_x = st.sidebar.slider("Start X", 0.0, 10.0, 1.0, 0.1)
    start_y = st.sidebar.slider("Start Y", 0.0, 10.0, 1.0, 0.1)
    goal_x = st.sidebar.slider("Goal X", 0.0, 10.0, 9.0, 0.1)
    goal_y = st.sidebar.slider("Goal Y", 0.0, 10.0, 9.0, 0.1)

    # Parametry: krok, iterace
    step_size = st.sidebar.slider("Krok (step_size)", 0.1, 2.0, 0.5, 0.1)
    max_iter = st.sidebar.slider("Max. počet iterací", 100, 5000, 2000, 100)

    # RRT* – poloměr re-wire
    star_radius = st.sidebar.slider("RRT* re-wire radius", 0.1, 5.0, 1.0, 0.1)

    start_app()

    if st.button("Spustit"):
        start = (start_x, start_y)
        goal = (goal_x, goal_y)

        # Příklad jedné kruhové překážky
        obstacles = [
            (5.0, 5.0, 2.0),
        ]

        # Zvolíme algoritmus
        if algo_choice == "RRT":
            nodes, parent, path = rrt_planner(start, goal, obstacles,
                                              x_limit=(0,10), y_limit=(0,10),
                                              step_size=step_size, 
                                              max_iter=max_iter,
                                              goal_threshold=1.0)
        elif algo_choice == "RRT*":
            nodes, parent, path = rrt_star_planner(start, goal, obstacles,
                                                   x_limit=(0,10), y_limit=(0,10),
                                                   step_size=step_size,
                                                   max_iter=max_iter,
                                                   goal_threshold=1.0,
                                                   radius=star_radius)
        else:  # "Bi-RRT"
            nodes, parent, path = birrt_planner(start, goal, obstacles,
                                                x_limit=(0,10), y_limit=(0,10),
                                                step_size=step_size,
                                                max_iter=max_iter,
                                                goal_threshold=1.0)

        for node in nodes:
            st.session_state["markers"].append(create_circlepoint(node))

        # for point in path:


        # Vypočítáme délku cesty
        if path:
            final_length = path_length(path)
            st.write(f"**Délka nalezené cesty:** {final_length:.2f}")
        else:
            st.write("**Cesta nebyla nalezena.**")

        # Pokud máme cestu, animujeme
        if path and len(path) > 1:
            fig_anim, ax_anim = plt.subplots(figsize=(8,8))
            ax_anim.set_xlim(0, 10)
            ax_anim.set_ylim(0, 10)
            ax_anim.set_aspect('equal')
            ax_anim.set_title(f"Animace nalezené trasy ({algo_choice})")

            # Vykreslíme překážky
            for (ox, oy, r) in obstacles:
                circle = plt.Circle((ox, oy), r, color='red', fill=True, alpha=0.3)
                ax_anim.add_patch(circle)
            
            # Start a cíl
            ax_anim.plot(start[0], start[1], "bs", markersize=8, label='Start')
            ax_anim.plot(goal[0], goal[1], "gs", markersize=8, label='Goal')
            ax_anim.legend()
            
            # Červená linka pro animaci
            line, = ax_anim.plot([], [], 'r-', linewidth=2)

            def init():
                line.set_data([], [])
                return (line,)

            def update(frame):
                segment = path[:frame+1]
                xdata = [p[0] for p in segment]
                ydata = [p[1] for p in segment]
                line.set_data(xdata, ydata)
                return (line,)

            ani = FuncAnimation(
                fig_anim,
                update,
                frames=len(path),
                init_func=init,
                blit=True,
                interval=100  # rychlost animace (ms)
            )

            # Uložíme do GIF
            ani.save("final_path.gif", writer='pillow')
        
            # Zobrazíme GIF
            with open("final_path.gif", "rb") as file_:
                contents = file_.read()
            data_url = base64.b64encode(contents).decode("utf-8")

            st.markdown(
                f'<img src="data:image/gif;base64,{data_url}" alt="rrt gif">',
                unsafe_allow_html=True,
            )

        else:
            st.write("**Animace není k dispozici (cesta nenalezena nebo má jen 1 bod).**")

if __name__ == "__main__":
    main()
