import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import random
import time

from shapely.geometry import Polygon, LineString
from geopy.distance import geodesic

#own modules
from knedlo_zelo import get_google_distance

#own modules
from knedlo_zelo import get_google_distance

#############################
# Vlastní krátké definice
#############################

class State:
    WEEKDAY = "Weekend"
    WEEKEND = "Weekday"

blood_spots = {
    "AeskuLab a.s": {
        "Coordinates":(49.710246, 13.413911),
        "Address":"K Rozhraní 944/2, 326 00 Plzeň 2-Slovany"
        },
    "SYNLAB - Odběry krve": {
        "Coordinates":(49.7276366, 13.3738645),
        "Address":"Majerova 2525/7, 301 00 Plzeň 3"
        },    
    "Fakultní nemocnice Plzeň - Transfuzní oddělení": {
        "Coordinates":(49.7287571,13.3751242),
        "Address":"17. listopadu 2479, 301 00 Plzeň 3-Jižní Předměstí"
        },  
    "EUC Odběrové místo Plzeň": {
        "Coordinates":(49.742039, 13.3273621),
        "Address":"Terezie Brzkové 15, 318 00 Plzeň 3"
        },
    "Unilabs - odběry krve": {
        "Coordinates":(49.7447234, 13.3674426),
        "Address":"Tylova 39, 301 00 Plzeň 3"
        },
    "BioLife (sanaplasma s.r.o.)": {
        "Coordinates":(49.7464564, 13.3680987),
        "Address":"Poděbradova 2842/1, 301 00 Plzeň 3"
        },
    "Amber Plasma Plzeň": {
        "Coordinates":(49.72762090000001, 13.3524081),
        "Address":"Technická 3037 /6, 301 00 Plzeň 3"
        },
    "SYNLAB - Odběry krve": {
        "Coordinates":(49.7450877, 13.3830692),
        "Address":"Denisovo nábř. 1000/4, 301 00 Plzeň 3-Východní Předměstí"
        },
    "Bioptická Laboratoř s.r.o.": {
        "Coordinates":(49.7411058, 13.3876321),
        "Address":"Rejskova 10, 326 00 Plzeň 2-Slovany"
        },
    "Privamed - nemocnice": {
        "Coordinates":(49.765284959069405, 13.359354534829086),
        "Address":"Kotíkovská 927/19, 323 00 Plzeň 1-Severní Předměstí"
        },
    "PLASMA PLACE s.r.o.": {
        "Coordinates":(49.7483219, 13.3753809),
        "Address":"K Rozhraní 944/2, 326 00 Plzeň 2-Slovany"
        },
    "Nemocnice Lochotín": {
        "Coordinates":(49.763306, 13.379694),
        "Address":"Alej Svobody 923/80, 323 00 Plzeň 1-Severní Předměstí"
        },
    "AeskuLab a.s": {
        "Coordinates":(49.710246, 13.413911),
        "Address":"K Rozhraní 944/2, 326 00 Plzeň 2-Slovany"
        },
    "SYNLAB - Odběry krve": {
        "Coordinates":(49.7276366, 13.3738645),
        "Address":"Majerova 2525/7, 301 00 Plzeň 3"
        },    
    "Fakultní nemocnice Plzeň - Transfuzní oddělení": {
        "Coordinates":(49.7287571,13.3751242),
        "Address":"17. listopadu 2479, 301 00 Plzeň 3-Jižní Předměstí"
        },  
    "EUC Odběrové místo Plzeň": {
        "Coordinates":(49.742039, 13.3273621),
        "Address":"Terezie Brzkové 15, 318 00 Plzeň 3"
        },
    "Unilabs - odběry krve": {
        "Coordinates":(49.7447234, 13.3674426),
        "Address":"Tylova 39, 301 00 Plzeň 3"
        },
    "BioLife (sanaplasma s.r.o.)": {
        "Coordinates":(49.7464564, 13.3680987),
        "Address":"Poděbradova 2842/1, 301 00 Plzeň 3"
        },
    "Amber Plasma Plzeň": {
        "Coordinates":(49.72762090000001, 13.3524081),
        "Address":"Technická 3037 /6, 301 00 Plzeň 3"
        },
    "SYNLAB - Odběry krve": {
        "Coordinates":(49.7450877, 13.3830692),
        "Address":"Denisovo nábř. 1000/4, 301 00 Plzeň 3-Východní Předměstí"
        },
    "Bioptická Laboratoř s.r.o.": {
        "Coordinates":(49.7411058, 13.3876321),
        "Address":"Rejskova 10, 326 00 Plzeň 2-Slovany"
        },
    "Privamed - nemocnice": {
        "Coordinates":(49.765284959069405, 13.359354534829086),
        "Address":"Kotíkovská 927/19, 323 00 Plzeň 1-Severní Předměstí"
        },
    "PLASMA PLACE s.r.o.": {
        "Coordinates":(49.7483219, 13.3753809),
        "Address":"K Rozhraní 944/2, 326 00 Plzeň 2-Slovany"
        },
    "Nemocnice Lochotín": {
        "Coordinates":(49.763306, 13.379694),
        "Address":"Alej Svobody 923/80, 323 00 Plzeň 1-Severní Předměstí"
        },
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

X_LIM = (49.70, 49.80)
Y_LIM = (13.30, 13.45)

#############################
# RRT (klasický)
#############################

def rrt_planner(
    start, goal, obstacles=None,
    x_limit=X_LIM,
    y_limit=Y_LIM,
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
    x_limit=X_LIM,
    y_limit=Y_LIM,
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
    x_limit=X_LIM,
    y_limit=Y_LIM,
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
        [(49.73448849719914, 13.398027299124262),(49.736263443537325, 13.3971204154081),(49.73331292948039, 13.40128850545247),(49.732764790510835, 13.400260015701262)],
        [(49.7355287473235, 13.399267613309744),(49.73611184046748, 13.40090958817571),(49.734455837632964, 13.40204634000599),(49.73409430837263, 13.400873500816017)],
        [(49.73938027084978, 13.387666252663665),(49.74036514596729, 13.389609858512234),(49.73511224766971, 13.396235787541444),(49.732981973220845, 13.393666817950551)],
        [(49.732575576695034, 13.388603703079053),(49.73317447565059, 13.39048996156059),(49.7294954081862, 13.39363372569649),(49.72851142427407, 13.390721607339026)],
        [(49.72454437107467, 13.393562440671136),(49.72432242511137, 13.399055604251835),(49.72054918849127, 13.398368958804248),(49.72054918849127, 13.394334916799673)],
        [(49.72426991430385, 13.401314964108211),(49.72540814487747, 13.407847473592142),(49.722422294818664, 13.409990953266558),(49.721053031446345, 13.404096384161916)],
        [(49.72974371399711, 13.406404824820855),(49.7302282731068, 13.408934853912102),(49.729138008307494, 13.411933406909133),(49.72796695587544, 13.408778679276839)],
        [(49.73347305456583, 13.40285400680229),(49.73442971444916, 13.405960181942705),(49.73212561429507, 13.411526281019825),(49.73048168646319, 13.409712608400197)],
        [(49.7393983110783, 13.393680837064794),(49.74075902162511, 13.396474310009866),(49.73770073749399, 13.401519238761415),(49.73567973912638, 13.398684072190298)],
        [(49.73216300119244, 13.381047667555594),(49.732459441033335, 13.384966868403904),(49.72936020775973, 13.39036619297684),(49.72891551892584, 13.38821897123548)],
        [(49.72741396584251, 13.390278570445208),(49.7275756763465, 13.395448580074891),(49.72548687421018, 13.396782776108358),(49.725311680268376, 13.392113089991224)],
        [(49.741285021223256, 13.390071879383356),(49.74224152711027, 13.392698577824245),(49.74053058074289, 13.395888140216751),(49.73929111734413, 13.393782612101436)],
        [(49.73108769948174, 13.394305939985642),(49.730748152631485, 13.394759017097485),(49.732585921634545, 13.399197859880722),(49.73301458290821, 13.398692252089246)],
        [(49.731324240633775, 13.322367192896744),
        (49.73107187575135, 13.332437701129628),
        (49.731008282737754, 13.337120772629838),
        (49.731631490687704, 13.322146749587231)],
        [(49.73072022675226, 13.337784943835484),
        (49.73102155406683, 13.337784943835484),
        (49.72978829634455, 13.356244740552235),
        (49.73081851880069, 13.356166033468199)],
        [(49.73210361833622, 13.321713680026377),
        (49.73693539337246, 13.333056132046712),
        (49.736874697724375, 13.33212583816206),
        (49.73270162531655, 13.320689299618621)],
        [(49.737087031829795, 13.333366632289344),
        (49.73715233321465, 13.332893175562324),
        (49.738461942721656, 13.337098830374089),
        (49.738739921324694, 13.33713706360409)],
        [(49.746591847168496, 13.41003299621203), (49.74656893319541, 13.41118060502649), (49.74536359503997, 13.411029175588018), (49.74543031195624, 13.409862480602486)],
        [(49.740988553328016, 13.410187462728924),(49.740966257399506, 13.410530745498816),(49.740180319370296, 13.410492794641417),(49.74024609339538, 13.410113286051589)],
        [(49.76564978624913, 13.39922739761518),(49.76577037121948, 13.402704474541972),(49.748885556651366, 13.401490998030608),(49.748837319758046, 13.399240556336716)],
        [(49.745531354681994, 13.406800964319523),(49.73960175454814, 13.40993415753169),(49.739802633618794, 13.408392427562372),(49.744591344482316, 13.405768999929144)],
        [(49.75376174895541, 13.405713566914686),(49.75269493358226, 13.408862947916296),(49.7537357293592, 13.410820235891784),(49.753303801827926, 13.412036493004939), (49.75597856830325, 13.41431596825674), (49.75697246144169, 13.412237860076653), (49.75530208488301, 13.407098972406509), (49.75370450581124, 13.405914934024828)],
        [(49.748834352508005, 13.410232486284523),(49.748801818480196, 13.410552063415984),(49.74841539223117, 13.410492463819676),(49.74841937602257, 13.410178024584217)],
        [(49.76131468850677, 13.408893739490052),(49.76092212714707, 13.412310152732614),(49.75746481100173, 13.411835225334002),(49.75843803082999, 13.407489384345523), (49.759480509060644, 13.40760173272258), (49.760763782193706, 13.408520947031677)],
        [(49.76019566481976, 13.418515454030976),(49.75913261184019, 13.417290570079235),(49.758908989314406, 13.419045349479665),(49.75928226633911, 13.419199791369232)],
        [(49.75121526921121, 13.42052864242215),(49.748905726783846, 13.418324553006846),(49.747943852208294, 13.426317120632612),(49.75008717379103, 13.428364911466618)],
        [(49.73508852598512, 13.41145746441682),(49.732987714647294, 13.42039210998476),(49.739534129165406, 13.427935914023822),(49.74062836904399, 13.420301403017106),(49.73889406516559, 13.414037452874496),(49.73582706095405, 13.410776417203376)],
        [(49.75450568901668, 13.425317577768547),(49.7546568729956, 13.425973636248829),(49.755279152089386, 13.425601730486122),(49.75511717131527, 13.424928957140098)],
        [(49.77993755333331, 13.362109940225753),
        (49.77854083127577, 13.367992345165796),
        (49.7763883836135, 13.366382529706264),
        (49.777260495931785, 13.360104601289205)],
        [(49.783028591394796, 13.37830570417163),
        (49.78243517511922, 13.381850420186097),
        (49.77866505180286, 13.37985914925933),
        (49.77916362311578, 13.376480286379612)],
        [(49.77944078011835, 13.371658372816103),
        (49.77914115288632, 13.373575809333277),
        (49.77585326433825, 13.371043715031295),
        (49.77620151524494, 13.369281398120576)],
        [(49.77197644747787, 13.368508864304742),
        (49.77134552942092, 13.371157374080072),
        (49.76923487403013, 13.36621599584917),
        (49.76868180439064, 13.371123098071655)],
        [(49.76997178714797, 13.36011506461663),
        (49.769938232640285, 13.36227294337339),
        (49.768260068903054, 13.362313054943266),
        (49.768078239222625, 13.3603446227129)],
        [(49.73369762374064, 13.390749615534585),(49.73366557661141, 13.391790845047717),(49.71960809346285, 13.404679321036854),(49.71929418218895, 13.404072406598939)],
        [(49.705240164162184, 13.336908161657144),
        (49.70812719983047, 13.344312944064184),
        (49.71048355439336, 13.340237089558348),
        (49.71435793026234, 13.342885455894313),
        (49.717928397910335, 13.352295608641636),
        (49.716158302832376, 13.353921458326225),
        (49.71709667599176, 13.359696474568992),
        (49.72026355153715, 13.3566729058555),
        (49.719774849681244, 13.344170449181947),
        (49.716353798715566, 13.338471022009704)],
        [(49.720586758340374, 13.36042164354644),
        (49.726040301331246, 13.365894302917859),
        (49.72453526285514, 13.368766693195674),
        (49.720381505514126, 13.366529252347688)],
        [
        (49.739892468421424, 13.37271827053156),
        (49.740523425080895, 13.372632465960878),
        (49.74035989706512, 13.380058309178924),
        (49.741072801420394, 13.379270349023736)
        ],
        [
        (49.73723781758094, 13.379378024185087),
        (49.73707524374659, 13.38041931337387),
        (49.738009090676194, 13.380717660276275),
        (49.7380884857401, 13.379524272666657)
        ],
        [
        (49.73754832981536, 13.377203169542929),
        (49.7361954524251, 13.376624892016146),
        (49.73561475375183, 13.378417074430594),
        (49.73720239215684, 13.379296438613231)
        ],
        [
        (49.74518453439802, 13.372824494653493),
        (49.74454636148357, 13.377880077504186),
        (49.744995195936205, 13.377801310477018),
        (49.74622599900435, 13.373461963343937)
        ],
        [(49.746574486648605, 13.374080728403397),(49.74595654095998, 13.37390029160494),(49.74559509738036, 13.377707508052396),(49.746189728937054, 13.377707508052396)],
        [(49.747938603005586, 13.370905040677743),(49.74765878738673, 13.37288984546078),(49.74561841637169, 13.371915486749108), (49.745909903199504, 13.370580254440522)],
        [(49.74813680475903, 13.367115867910135),(49.748043533446534, 13.371933530428953),(49.74676103471306, 13.372041792508028),(49.74725072004926, 13.366177596558158)],
        [(49.74316985779076, 13.372943976533548),(49.74272677209573, 13.377689464332983),(49.74091940695015, 13.377905988491133),(49.74098937072457, 13.372456797177712)],
        [(49.74879524461893, 13.38817596440362),(49.7481228038359, 13.39262843152968),(49.75141212903752, 13.399376869655681),(49.753186677605456, 13.392488956655852)],
        [(49.74398115084669, 13.368469208997116),(49.74369029181283, 13.370880472700486),(49.74103092836349, 13.370205318863542),(49.74105170520541, 13.36776190497746)],
        [(49.74410580418451, 13.364225384879182),(49.74389804844352, 13.366508047851704),(49.74128024987909, 13.36637944712086),(49.74215286509462, 13.363775282321217)]
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
    #st.title("RRT varianty: Klasický, Bi-RRT, RRT*")

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
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                obstacles_temp,
                x_limit=X_LIM,
                y_limit=Y_LIM,
                step_size_deg=step_size_deg,
                max_iter=max_iter,
                goal_threshold=goal_threshold_deg
            )
        elif algorithm == "Bi-RRT":
            nodes, parent, path = bi_rrt_planner(
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                obstacles_temp,
                x_limit=X_LIM,
                y_limit=Y_LIM,
                step_size_deg=step_size_deg,
                max_iter=max_iter,
                goal_threshold=goal_threshold_deg
            )
        else:  # RRT*
            nodes, parent, path = rrt_star_planner(
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                blood_spots[start]['Coordinates'],
                blood_spots[goal]['Coordinates'],
                obstacles_temp,
                x_limit=X_LIM,
                y_limit=Y_LIM,
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
            location=blood_spots[start]['Coordinates'],
            location=blood_spots[start]['Coordinates'],
            popup=start,
            icon=folium.Icon(color="blue")
        ).add_to(m)
        folium.Marker(
            location=blood_spots[goal]['Coordinates'],
            location=blood_spots[goal]['Coordinates'],
            popup=goal,
            icon=folium.Icon(color="green")
        ).add_to(m)

        # Ostatní body
        for place in blood_spots:
            if place == start or place == goal:
                continue
            folium.Marker(
                location=blood_spots[place]['Coordinates'],
                location=blood_spots[place]['Coordinates'],
                popup=place,
                icon=folium.Icon(color="orange")
            ).add_to(m)

        # Výsledek
        if path:
            st.session_state["final_path"] = path
            length_m = path_length_meters(path)
            st.session_state["final_length"] = length_m
            st.session_state["path_found"] = True

            google_dist, google_time = get_google_distance(blood_spots[start]["Address"], blood_spots[goal]["Address"])
            st.session_state['google_dist'] = google_dist
            st.session_state['google_time'] = google_time

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
            st.info(f"Poslední nalezená cesta: {st.session_state['final_length']/1000:.1f} km\n\nCesta by trvala: {st.session_state['final_length']/15/60:.1f} minut")
            st.info(f"API z Google Maps doporučuje pozemní cestu o vzdálenosti: {st.session_state['google_dist']}\n\nTa by aktuálně trvala {int(st.session_state['google_time'].split()[0])} minut")
            improvement = int(st.session_state['google_time'].split()[0]) / (st.session_state['final_length']/16.7/60)
            st.markdown(f'To je zrychlení o <span style="color:green; font-size:16px;">{(improvement-1)*100:.2f}%</span>', unsafe_allow_html=True)
        else:
            st.info("Poslední výpočet cestu nenašel.")
    else:
        st.write("Vyberte algoritmus, parametry a klikněte na **Spustit**.")


if __name__ == "__main__":
    main()