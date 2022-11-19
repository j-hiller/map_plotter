# map_plotter

Script used for my thesis to plot specific map data of [OpenStreetMap (OSM)](https://www.openstreetmap.org)
The script uses the reverse geocoding service [Nominatim](https://nominatim.org/) for the OSM details and the default OSM tile server for the background.

Please consider the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) before running the script.

## Usage

The script plots the points belonging to ways and nodes onto OSM tiles.
These ways and nodes are specified as lists in the required json file.
See `kreuz_ac.json` for an example.

With the json file specified, the script can be called via

```bash
python osm_plotter.py to_draw.json
```

The script caches the tiles in `tiles` and saves the figures to `figs` with the name stem of the json file.

## Script details

The script queries Nominatim for the details on the provided ways and nodes.
For each of these, the coordinates are returned by Nominatim.
Using these coordinates, the extent of the tiles necessary for plotting the ways and nodes can be calculated.

The tiles are then downloaded and cached in the `tiles` folder.
In a next step, all the tiles are loaded and put together to one big "supertile" for plotting.
Upon this supertile, the coordinates of the points of the provided nodes and ways are then plotted in different colors.

### Contents of `to_draw.json`

The json file lists all elements that should be drawn on the tile.
`ways` is a list that contains the ids of the ways to be drawn, `nodes` is a list of the nodes to be drawn.

In order to highlight parts of the ways, the `highlight_way_nodes` part can be used.
If `-1` is specified, the last point of the way is highlighted, if `0` is specified, the first point of the ways is highlighted.

```json
{
    "ways": [
        ...
    ],
    "highlight_way_nodes": {
        "145100417": -1,
        "31693609": 0
    },
    "nodes": [
        ...
    ]
}
```

## Additional tile servers

The default tile server is the OSM tile server: `http://a.tile.openstreetmap.org`
Additional tile servers can be found here: [OSM wiki](https://wiki.openstreetmap.org/wiki/Raster_tile_providers)

Additional tile servers can be found here [Bundesamt für Kartographie und Geodäsie](https://gdz.bkg.bund.de/index.php/default/webdienste.html)

## References

The scripts used for most OSM interactions and calculations were taken from [Strava-export-local-heatmap](https://github.com/j-hiller/Strava-export-local-heatmap)
