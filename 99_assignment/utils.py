import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd

def make_isochrone_polys(G, center_node, trip_times, buffer=10):
    """Return a list of isochrone polygons
    
    Function was based and edited from: 13-isolines-isochrones.ipynb
    'https://github.com/gboeing/osmnx-examples/blob/v0.13.0/notebooks/'
    Parameters
    ----------
    G : networkx.MultiDiGraph
    center_node : int
    trip_times : list
    buffer : int
    
    Returns
    -------
    isochrone_polys : list
    """
    isochrone_polys = []
    
    for trip_time in sorted(trip_times, reverse=True):
        # Get subgraph based on time
        subgraph = nx.ego_graph(
            G, center_node,
            radius=trip_time,
            distance='time'
        )
        subgraph = ox.project_graph(subgraph, to_crs='epsg:4326')
        
        # Get all latitude and longitude of each node in the subgraph
        node_points = [
            Point((data['x'], data['y']))
            for node, data in subgraph.nodes(data=True)
        ]
        
        # Create a GeoDataFrame
        nodes_gdf = gpd.GeoDataFrame(
            {'id': subgraph.nodes()},
            geometry=node_points
        ).set_index('id')
        
        edge_lines = []
        # Get all edges from the subgraph
        for n_fr, n_to in subgraph.edges():
            f = nodes_gdf.loc[n_fr].geometry
            t = nodes_gdf.loc[n_to].geometry
            edge_lookup = (
                G.get_edge_data(n_fr, n_to)[0]
                .get('geometry', LineString([f, t]))
            )
            edge_lines.append(edge_lookup)

        # Nodes geometries
        n = nodes_gdf.geometry
        
        # Edges geometries with buffer
        e = gpd.GeoSeries(edge_lines).buffer(buffer).geometry
        
        # Combine all results
        all_gs = list(n) + list(e)
        all_series = gpd.GeoSeries(all_gs)
        
        # NEW: use union_all() instead of deprecated unary_union
        new_iso = all_series.union_all()
        
        # Fill the surrounding areas so shapes will appear solid
        new_iso = Polygon(new_iso.exterior)
        isochrone_polys.append(new_iso)
    
    return isochrone_polys
