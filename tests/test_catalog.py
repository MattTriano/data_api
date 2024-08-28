import os
from pathlib import Path
from urllib.request import urlretrieve
import geopandas as gpd
import pandas as pd
import pytest
from shapely import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
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


def test_select_multipoint(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
            SELECT
                ST_GeomFromText('MULTIPOINT(
                    (-87.631304 41.884749), (-87.683887 42.074010),  (-87.633514 41.963258)
                )',
                4326
            ) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, MultiPoint)
    assert geom_value.geom_type == "MultiPoint"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())


def test_select_multipolygon(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
            SELECT ST_GeomFromText(
                'MULTIPOLYGON((
                    (
                        -87.702 41.702,
                        -87.687 41.702,
                        -87.687 41.690,
                        -87.702 41.690,
                        -87.702 41.702
                    ), (
                        -87.695 41.698,
                        -87.692 41.698,
                        -87.692 41.693,
                        -87.695 41.693,
                        -87.695 41.698
                    )
                ))',
                4326
            ) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, MultiPolygon)
    assert geom_value.geom_type == "MultiPolygon"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())


def test_select_multilinestring(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
        SELECT ST_GeomFromText(
            'MULTILINESTRING(
                (-87.717 41.695, -87.699 41.695), (-87.689 41.695, -87.650 41.695)
            )',
            4326
        ) AS geom
        """
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, MultiLineString)
    assert geom_value.geom_type == "MultiLineString"
    assert geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())


def test_select_geometrycollection(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
            SELECT ST_GeomFromText(
                'GEOMETRYCOLLECTION(
                    POINT(-87.6378195 41.8873),
                    LINESTRING(-87.638120 41.888, -87.638120 41.8877),
                    LINESTRING(-87.637500 41.888, -87.637500 41.8877),
                    POLYGON((
                        -87.638666 41.886925,
                        -87.638139 41.886668,
                        -87.637500 41.886668,
                        -87.636973 41.886925,
                        -87.637500 41.886411,
                        -87.638139 41.886411,
                        -87.638666 41.886925
                    ))
                )',
                4326
            ) AS geom"""
    )
    geom_value = gdf["geom"].values[0]
    assert isinstance(gdf, gpd.GeoDataFrame)
    assert gdf["geom"].crs == "EPSG:4326"
    assert isinstance(geom_value, GeometryCollection)
    assert geom_value.geom_type == "GeometryCollection"
    assert geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())
    assert isinstance(geom_value.geoms[0], Point)
    assert isinstance(geom_value.geoms[1], LineString)
    assert isinstance(geom_value.geoms[2], LineString)
    assert isinstance(geom_value.geoms[3], Polygon)


def test_select_multiple_geospatial_columns(catalog, chicago_boundary_gdf):
    gdf = catalog.query(
        sql="""
            SELECT
                ST_GeomFromText(
                    'LINESTRING(
                        -87.921243 41.914808,
                        -87.632352 41.883793,
                        -87.429500 41.877629
                    )',
                    4326
                ) AS ls_geom,
                ST_GeomFromText(
                    'POLYGON((
                        -87.631304 41.884749,
                        -87.683887 42.074010,
                        -87.633514 41.963258,
                        -87.631304 41.884749
                    ))',
                    4326
                ) AS poly_geom,
                ST_GeomFromText('POINT(-87.631304 41.884749)', 4326) AS pt_geom"""
    )
    assert isinstance(gdf, gpd.GeoDataFrame)

    geom_col = "ls_geom"
    geom_value = gdf[geom_col].values[0]
    assert gdf[geom_col].crs == "EPSG:4326"
    assert isinstance(geom_value, LineString)
    assert geom_value.geom_type == "LineString"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())

    geom_col = "poly_geom"
    geom_value = gdf[geom_col].values[0]
    assert gdf[geom_col].crs == "EPSG:4326"
    assert isinstance(geom_value, Polygon)
    assert geom_value.geom_type == "Polygon"
    assert not geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())

    geom_col = "pt_geom"
    geom_value = gdf[geom_col].values[0]
    assert gdf[geom_col].crs == "EPSG:4326"
    assert isinstance(geom_value, Point)
    assert geom_value.geom_type == "Point"
    assert geom_value.within(chicago_boundary_gdf.geometry.union_all())
    assert geom_value.intersects(chicago_boundary_gdf.geometry.union_all())


def test_select_non_geospatial_types(catalog):
    df = catalog.query(
        sql="""
    SELECT
        42                               AS int_column,
        3.14159::DOUBLE PRECISION        AS float_column,
        'Hello, World!'                  AS varchar_column,
        '2024-08-27'::TIMESTAMP          AS date_column,
        '2024-08-27 15:30:00'::TIMESTAMP AS timestamp_column,
        TRUE                             AS t_bool_column,
        FALSE                            AS f_bool_column,
        ARRAY[1, 2, 3, 4, 5]             AS int_array_column,
        ARRAY['apple', 'banana', 'cherry'] AS varchar_array_column
    """
    )

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1

    assert df["int_column"].dtype == "int64"
    assert df["float_column"].dtype == "float64"
    assert df["varchar_column"].dtype == "object"
    assert df["date_column"].dtype == "datetime64[ns]"
    assert df["timestamp_column"].dtype == "datetime64[ns]"
    assert df["t_bool_column"].dtype == "bool"
    assert df["f_bool_column"].dtype == "bool"
    assert df["int_array_column"].dtype == "object"
    assert df["varchar_array_column"].dtype == "object"

    assert df["int_column"].values[0] == 42
    assert pytest.approx(df["float_column"].values[0]) == 3.14159
    assert df["varchar_column"].values[0] == "Hello, World!"
    assert df["date_column"].values[0] == pd.Timestamp("2024-08-27")
    assert df["timestamp_column"].values[0] == pd.Timestamp("2024-08-27 15:30:00")
    assert df["t_bool_column"].values[0]
    assert not df["f_bool_column"].values[0]
    assert df["int_array_column"].values[0] == [1, 2, 3, 4, 5]
    assert df["varchar_array_column"].values[0] == ["apple", "banana", "cherry"]
