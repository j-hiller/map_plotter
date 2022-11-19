from pathlib import Path
import numpy as np
import requests
import matplotlib.pyplot as plt
from typing import Tuple

MAX_TILE_COUNT = 500  # maximum number of OSM tiles to download

# constants
OSM_TILE_SIZE = 256  # OSM tile size in pixels


def calculate_zoom_level(min_lon: float, max_lon: float,
                         min_lat: float, max_lat: float) -> int:
    """
    Method for calculating a reasonable zoom level from provided coordinates.
    

    Args:
        min_lon (float): Minimum longitude
        max_lon (float): Maximum longitude
        min_lat (float): Minimum latitude
        max_lat (float): Maximum latitude

    Returns:
        int: The zoom level
    """
    z_lon = np.ceil(np.log2(360 / (max_lat - min_lat)));
    z_lat = np.ceil(np.log2(170.1023 / (max_lon - min_lon)));
    zoom_level = np.min([z_lon, z_lat]) + 1;
    zoom_level = np.min([zoom_level, 18]);
    zoom_level = np.max([zoom_level, 0]);
    return int(zoom_level)


def deg2xy(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[float, float]:
    """
    return OSM global x,y coordinates from lat,lon in degrees
    
    Args:
        lat_deg (float): Latitude in degrees to convert to y coordinate
        lon_deg (float): Longitude in degrees to convert to x coordinate
        zoom (int): Zoom level needed
        
    Returns:
        int: Global x and y coordinates
    """
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    x = (lon_deg + 180.0) / 360.0 * n
    y = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n
    return x, y


def deg2tile_coord(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """
    return OSM tile x,y from lat,lon in degrees (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
    Calls deg2xy and converts those values to integers
    
    Args:
        lat_deg (float): Latitude in degrees
        lon_deg (float): Longitude in degrees
        zoom (int): Zoom level
        
    Returns:
        (int, int): The tile numbers for that location
    """
    x, y = deg2xy(lat_deg, lon_deg, zoom)
    return int(x), int(y)


def num2deg(x_tile: int, y_tile: int, zoom: int) -> Tuple[float, float]:
    """
    return lat,lon in degrees from OSM tile x,y (from https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)
    
    Args:
        x_tile (int): X tile number
        y_tile (int): Y tile number
        zoom (int): Zoom level
        
    Returns:
        (float, float): Latitude and longitude in degrees
    """
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * y_tile / n)))
    lat_deg = np.degrees(lat_rad)
    return lat_deg, lon_deg


def sc2deg(sc_value: float) -> float:
    """
    Calculate degrees from semicircle value
    
    Args:
        sc_value (float): semicircle value to convert
        
    Returns:
        float: The degress calculated from the semicircle
    """
    return np.float(sc_value) * 180 / 2**31


def download_tile_file(tile_url: str, tile_file: Path, verbose: bool = False) -> bool:
    """
    download image from url to file
    
    Args:
        tile_url (str): The url of the tile to download
        tile_file (Path): The file to save the tile to
        verbose (bool): Verbosity flag
        
    Returns:
        bool: Returns true or false respectively
    """
    try:
        resp = requests.get(tile_url, headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0'}, 
                            stream=True, timeout=10)
    except requests.exceptions.RequestException as e:
        if verbose:
            print(e)
        return False

    if resp.ok:
        if verbose:
            print('Downloading ' +  tile_url)
        with open(tile_file, 'wb') as file:
            file.write(resp.content)
        return True


def download_tiles_for_area(x_tile_min: int, x_tile_max: int,
                            y_tile_min: int, y_tile_max: int,
                            zoom: int, url: str = 'http://a.tile.openstreetmap.org'):
    """
    Download the tiles specified by the x, y and zoom values
    The tileservers are accessed using the pattern {url}/{zoom}/{x_tile}/{y_tile}.png and the tiles saved as
    {zoom}_{x_tile}_{y_tile}.png
    
    Args:
        x_tile_min (int): Minimum x_tile value
        x_tile_max (int): Maximum x_tile value
        y_tile_min (int): Minimum y_tile value
        y_tile_max (int): Maximum y_tile value
        zoom (int): Zoom at which to download the tiles
        url (str): The url used to download the tiles.
    """
    # total number of tiles
    tile_count = (x_tile_max-x_tile_min+1)*(y_tile_max-y_tile_min+1)
    # Restrict the number of tiles that are downloaded
    if tile_count > MAX_TILE_COUNT:
        print('ERROR zoom value too high')
        return
    # download tiles
    tile_path = Path('tiles')
    tile_path.mkdir(exist_ok=True, parents=True)
    for x in range(x_tile_min, x_tile_max+1):
        for y in range(y_tile_min, y_tile_max+1):
            tile_url = '/'.join([url, str(zoom), str(x), str(y) + '.png'])
            tile_file = tile_path.joinpath('_'.join(['tile', str(zoom), str(x), str(y) + '.png']))
            # check if tile already downloaded
            if not tile_file.exists():
                if not download_tile_file(tile_url, tile_file):
                    tile_image = np.ones((OSM_TILE_SIZE, OSM_TILE_SIZE, 3))
                    plt.imsave(tile_file, tile_image)
