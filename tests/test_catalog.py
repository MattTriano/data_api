import os
from pathlib import Path
from urllib.request import urlretrieve
import geopandas as gpd
import pytest
from shapely import (
    #Geometry,
    #GeometryCollection,
    #GeometryType,
    LineString,
    #MultiLineString,
    #MultiPoint,
    #MultiPolygon,
    Point,
    Polygon,
)
from dwh_api.catalog import DataCatalog


TEST_DATA_DIR = Path(__file__).parent.resolve().joinpath("test_data")
TEST_DATA_DIR.mkdir(exist_ok=True, parents=False)


@pytest.fixture(scope="module")
def catalog():
    dotenv_path = os.environ.get("DWH_DOTENV_PATH")
    all_env_vars_avail = all(
        [
            k in os.environ.keys()
            for k in ["POSTGRES_PASSWORD", "POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PORT"]
        ]
    )
    if dotenv_path:
        path_to_dotenv = Path(dotenv_path).resolve()
        if path_to_dotenv.is_file():
            yield DataCatalog(path_to_dotenv)
        elif all_env_vars_avail:
            yield DataCatalog()
        else:
            raise FileNotFoundError(
                "Expected to find a path to a .env file in the DWH_DOTENV_PATH env-var, "
                "or expected env-vars [POSTGRES_PASSWORD, POSTGRES_USER, POSTGRES_DB, "
                "POSTGRES_PORT(, and POSTGRES_HOST if not 'localhost')."
            )
    elif all_env_vars_avail:
        yield DataCatalog()
    else:
        raise Exception("Couldn't get an engine")


@pytest.fixture(scope="module")
def chicago_boundary_gdf():
    chicago_boundary_path = TEST_DATA_DIR.joinpath("chicago_boundary.geojson")
    url = "https://data.cityofchicago.org/api/geospatial/qqq8-j68g?method=export&format=GeoJSON"
    if not chicago_boundary_path.is_file():
        urlretrieve(url, filename=chicago_boundary_path)
    if chicago_boundary_path.is_file():
        return gpd.read_file(chicago_boundary_path)
    else:
        raise FileNotFoundError("Failed to retrieve the required chicago_boundary.geojson data")


def test_select_point(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""SELECT ST_GeomFromText('POINT(-87.631304 41.884749)', 4326) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, Point)
    assert geom_value.geom_type == "Point"
    assert geom_value.within(chicago_boundary_gdf.geometry.union_all())


def test_select_linestring(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
        SELECT ST_GeomFromText(
            'LINESTRING(-87.921243 41.914808, -87.632352 41.883793, -87.429500 41.877629)',
            4326
        ) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, LineString)
    assert geom_value.geom_type == "LineString"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())

def test_select_polygon(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
            SELECT
                ST_GeomFromText('POLYGON((
                    -87.631304 41.884749,
                    -87.683887 42.074010,
                    -87.633514 41.963258,
                    -87.631304 41.884749
                ))',
                4326
            ) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, Polygon)
    assert geom_value.geom_type == "Polygon"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())
