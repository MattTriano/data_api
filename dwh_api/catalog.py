from functools import cached_property
import os
from pathlib import Path
from typing import Optional, Union

import pandas as pd
#from geoalchemy2 import Geometry, Geography
import geopandas as gpd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.engine.url import URL


class DataCatalog:
    def __init__(self, env_file_path: Optional[Path] = None, host: str = "localhost") -> None:
        self.env_file_path = env_file_path
        self.host = host
        self.set_engine(host=self.host)

    def set_engine(self, host: str, port: str = "5431") -> Engine:
        password = user = db_name = None
        if self.env_file_path:
            dwh_creds = self._read_env_to_dict(self.env_file_path)
            password = dwh_creds.get("POSTGRES_PASSWORD")
            user = dwh_creds.get("POSTGRES_USER")
            db_name = dwh_creds.get("POSTGRES_DB")
        if not password:
            password = os.environ.get("POSTGRES_PASSWORD")
        if not user:
            user = os.environ.get("POSTGRES_USER")
        if not db_name:
            db_name = os.environ.get("POSTGRES_DB")
        if all([k is not None for k in [password, user, db_name, host, port]]):
            self.engine = self._get_pg_engine(user, password, host, port, db_name)
        else:
            raise KeyError("At least one of the necessary db cred parts was missing")

    @cached_property
    def geo_dtypes(self):
        with self.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT oid, typname
                FROM pg_type
                WHERE typname IN ('geometry', 'geography')
            """
                )
            )
            return {row[0]: row[1] for row in result}

    def _read_env_to_dict(self, file_path: Path) -> dict:
        env_dict = {}
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                env_dict[key] = value.strip('"')
        return env_dict

    def _get_pg_engine(
        self,
        username: str,
        password: str,
        host: str,
        port: str,
        database: str,
    ) -> Engine:
        return create_engine(
            URL.create(
                "postgresql",
                username=username,
                password=password,
                host=host,
                port=port,
                database=database,
            )
        )

    def _get_inspector(self):
        return inspect(self.engine)

    def get_schema_names(self) -> list[str]:
        insp = self._get_inspector()
        return insp.get_schema_names()

    def get_table_names(self, schema: str) -> list[str]:
        insp = self._get_inspector()
        return insp.get_table_names(schema=schema)

    def get_view_names(self, schema: str) -> list[str]:
        insp = self._get_inspector()
        return insp.get_view_names(schema=schema)

    def command(self, sql: str) -> None:
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text(sql))
        except Exception as e:
            raise Exception(f"Ran into an error when running sql command:\n{sql}\nError: {e}")

    def geospatial_columns_in_query(self, sql):
        with self.engine.connect() as conn:
            result = conn.execute(text(sql))
            geospatial_columns = {
                c.name: self.geo_dtypes[c.type_code]
                for c in result.cursor.description
                if c.type_code in self.geo_dtypes.keys()
            }
        return geospatial_columns

    def query(self, sql: str) -> Union[gpd.GeoDataFrame, pd.DataFrame]:
        geospatial_columns = self.geospatial_columns_in_query(sql)
        with self.engine.connect() as conn:
            if geospatial_columns:
                df = gpd.read_postgis(
                    sql=text(sql), con=conn, geom_col=next(iter(geospatial_columns.keys()), None)
                )
                for col, dtype in geospatial_columns.items():
                    if col != df.geometry.name:
                        df[col] = gpd.GeoSeries.from_wkb(df[col], crs=df.crs)
            else:
                result = conn.execute(text(sql))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
            if self.engine._is_future:
                conn.commit()
            return df
