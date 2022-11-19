from pathlib import Path
import json
import requests
import argparse
import numpy as np
import matplotlib.pyplot as plt

import osm_helpers

NOMINATIM_SERVER = 'https://nominatim.openstreetmap.org'


def lookup_geojson_by_id(osm_id: int, element_type: str='W') -> dict:
    """
    Look up the geojson for the id in the OSM database.
    Need to specifiy it is (W)ay, (R)elation or (N)oder.

    Args:
        osm_id (int): The id of the OSM element
        element_type (str, optional): The type of element. Can be 'W', 'R' or 'N'. Defaults to 'W'.

    Returns:
        dict: Returns the geojson for the id
    """
    det = {'type': '', 'geojson': {}}
    url = NOMINATIM_SERVER + 'lookup.php'
    payload = {'osm_ids': element_type + str(osm_id),
               'format': 'jsonv2', 'polygon_geojson': 1}
    resp = requests.get(url, params=payload, timeout=10)
    if resp.ok:
        cont = json.loads(resp.content)
        if len(cont) > 0:
            if 'type' in det:
                det['type'] = cont[0]['type']
            if 'geojson' in det:
                det['geojson'] = cont[0]['geojson']
    return det


def download_map_data_nominatim(way_ids:list=None, node_ids:list=None) -> dict:
    """
    Method that download the coordinates and details on the provided ways and nodes

    Args:
        way_ids (list, optional): A list of ways to fetch details for. Defaults to None.
        node_ids (list, optional): A ist of nodes to fetch details for. Defaults to None.

    Returns:
        dict: Dict containing all the details on the specified ways and nodes available via nominatim
    """
    data_dict = {'ways': {}, 'nodes': {},
                 'way_coords': [],
                 'node_coords': []}
    if way_ids:
        for way in way_ids:
            way_dict = lookup_geojson_by_id(way, element_type='W')
            data_dict['ways'][way] = way_dict
            if 'geojson' in way_dict:
                data_dict['way_coords'] += way_dict['geojson']['coordinates']
    if node_ids:
        for node in node_ids:
            node_dict = lookup_geojson_by_id(node, element_type='N')
            data_dict['nodes'][node] = node_dict
            if 'geojson' in node_dict:
                data_dict['node_coords'] += node_dict['geojson']['coordinates']
    return data_dict


def combine_supertile(x_tile_min: int, x_tile_max: int,
                      y_tile_min: int, y_tile_max: int,
                      zoom: int, tile_path: Path = Path('tiles')) -> np.array:
    """
    Creates one super tile out of the specified tile ranges.
    This supertile can be easily used for plotting

    Args:
        x_tile_min (int): The minimum x tile
        x_tile_max (int): The maximum x tile
        y_tile_min (int): The minimum y tile
        y_tile_max (int): The maximum y tile
        zoom (int): The zoom level corresponding to the tiles
        tile_path (Path, optional): The path to store the tiles. Defaults to Path('tiles').

    Returns:
        np.array: An array of an image containing the supertile
    """
    supertile_size = ((y_tile_max - y_tile_min + 1) * osm_helpers.OSM_TILE_SIZE,
                      (x_tile_max - x_tile_min + 1) * osm_helpers.OSM_TILE_SIZE, 3)
    supertile = np.zeros(supertile_size)
    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile = tile_path.joinpath(f'tile_{zoom}_{x}_{y}.png')
            i = y - y_tile_min
            j = x - x_tile_min
            if tile.exists():
                tile_img = plt.imread(tile)
                supertile[i * osm_helpers.OSM_TILE_SIZE:i * osm_helpers.OSM_TILE_SIZE + osm_helpers.OSM_TILE_SIZE,
                          j * osm_helpers.OSM_TILE_SIZE:j * osm_helpers.OSM_TILE_SIZE + osm_helpers.OSM_TILE_SIZE,
                          :] = tile_img[:, :, :3]
    return supertile


def main(args) -> None:
    fig_folder = Path('./figs')
    fig_folder.mkdir(exist_ok=True, parents=True)
    if not args.json.exists():
        print(f'Provided json file {args.json} does not exist. Returning')
        
    with open(args.json, 'r') as f:
        draw_data = json.load(f)
     
    map_data = download_map_data_nominatim(draw_data['ways'], draw_data['nodes'])
    min_lon = np.min([c[0] for c in map_data['way_coords']])
    max_lon = np.max([c[0] for c in map_data['way_coords']])
    min_lat = np.min([c[1] for c in map_data['way_coords']])
    max_lat = np.max([c[1] for c in map_data['way_coords']])
    # zoom_level = osm_helpers.calculate_zoom_level(min_lon, max_lon, min_lat, max_lat)
    zoom_level = 17
    x_tile_min, y_tile_max = osm_helpers.deg2tile_coord(min_lat, min_lon, zoom_level)
    x_tile_max, y_tile_min = osm_helpers.deg2tile_coord(max_lat, max_lon, zoom_level)
    
    osm_helpers.download_tiles_for_area(x_tile_min, x_tile_max, y_tile_min, y_tile_max, zoom_level)
    supertile = combine_supertile(x_tile_min, x_tile_max, y_tile_min, y_tile_max, zoom_level)
                
    # +1 since the result returns the NW-corner of the tile otherwise.
    # Depending on the bounds, SW or NE corner is needed
    lat_min, lon_min = osm_helpers.num2deg(x_tile_min, y_tile_max + 1, zoom_level)
    lat_max, lon_max = osm_helpers.num2deg(x_tile_max + 1, y_tile_min, zoom_level)

    ms = 2

    fig, ax = plt.subplots()
    ax.imshow(supertile, extent=[lon_min, lon_max, lat_min, lat_max])
    ax.set_aspect(1.0 / np.cos(60 * np.pi / 180))
    for way, way_v in map_data['ways'].items():
        if way_v['type'] == 'motorway':
            ax.plot([c[0] for c in way_v['geojson']['coordinates']],
                    [c[1] for c in way_v['geojson']['coordinates']],
                    color='blue', marker='o', markersize=ms, linewidth=ms/2, linestyle='')
        if way_v['type'] == 'motorway_link':
            ax.plot([c[0] for c in way_v['geojson']['coordinates']],
                    [c[1] for c in way_v['geojson']['coordinates']],
                    color='green', marker='o', markersize=ms, linewidth=ms/2, linestyle='')
    for hway, hway_v in draw_data['highlight_way_nodes'].items():
        if int(hway) in map_data['ways']:
            ax.plot(map_data['ways'][int(hway)]['geojson']['coordinates'][hway_v][0],
                    map_data['ways'][int(hway)]['geojson']['coordinates'][hway_v][1],
                    color='yellow', marker='o', markersize=ms/2)
    for node, node_v in map_data['nodes'].items():
        ax.plot(node_v['geojson']['coordinates'][0],
                   node_v['geojson']['coordinates'][1],
                   color='yellow', marker='o', markersize=ms/2)
    ax.set_axis_off()
    plt.tight_layout()
    fig.savefig(fig_folder.joinpath(args.json.stem + '.svg'), dpi=300)
    
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='osm_plotter.py',
                                   description='Script for plotting osm data on background tiles')
    
    parser.add_argument('json', help='JSON file used to specifiy OSM data',
                        type=Path)
    
    args = parser.parse_args()
    
    main(args)
    