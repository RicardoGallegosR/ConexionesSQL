from pyproj import CRS, Transformer
from shapely.geometry import Point,Polygon
from functools import partial
from shapely.ops import transform
from fiona.crs import from_epsg
import uuid
import pandas as pd 
import geopandas as gpd
import contextily as cx
import numpy as np
import matplotlib.pyplot as plt
pd.options.display.max_columns = None
import xml.etree.ElementTree as ET
import sqlite3
import os

class GeoAnalisis:
    CRS_WGS84 = CRS.from_epsg(4326)
    CRS_AEQD = CRS(proj="aeqd", datum="WGS84")

    def __init__(self, lat: float, lon: float, dist: int = 1e3) -> None:
        if lat < -90 or lat > 90:
            raise ValueError("La latitud debe estar en el intervalo [-90, 90]")
        if lon < -180 or lon > 180:
            raise ValueError("La longitud debe estar en el intervalo [-180, 180]")
        self.lat:float = lat
        self.lon:float = lon
        self.dist:int = dist
        self.conn = sqlite3.connect(r'src\db.sqlite3')

    def __del__(self) -> None:
        self.conn.close()

    def get_tracts (self) -> gpd.GeoDataFrame:
        df = pd.read_sql_query("SELECT * FROM Gasolineras", self.conn)
        tracts = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=self.CRS_WGS84
        )
        return tracts
    
    def Area (self) -> Polygon:
        crs_aeqd = CRS(proj="aeqd", lat_0=self.lat, lon_0=self.lon, datum="WGS84")
        transformer_wgs84_to_aeqd = Transformer.from_crs(
            self.CRS_WGS84, crs_aeqd, always_xy=True
        )
        transformer_aeqd_to_wgs84 = Transformer.from_crs(
            crs_aeqd, self.CRS_WGS84, always_xy=True
        )
        center = Point(self.lon, self.lat)
        point_transformed = transform(transformer_wgs84_to_aeqd.transform, center)
        buffer = point_transformed.buffer(self.dist)
        circule_poly = transform(transformer_aeqd_to_wgs84.transform, buffer)
        return circule_poly
    
    def get_circule_gdf (self):
        circule_poly = self.Area()
        circule_gdf = gpd.GeoDataFrame(geometry=[circule_poly], crs=self.CRS_WGS84)
        circule_gdf = circule_gdf.to_crs(epsg=3857)
        return circule_gdf
    
    def GetInner (self)->gpd.GeoDataFrame:
        circule_poly = self.Area()
        tracts = self.get_tracts()
        lon_rad, lat_rad = circule_poly.exterior.coords.xy
        a,b = np.array(lon_rad), np.array(lat_rad)
        lon_rad =  (a - lon_cir)/max(a - lon_cir)
        lat_rad = (b - lat_cir)/max(b - lat_cir)
        data = tracts[
            ((min(a) <=tracts['lon']) & (tracts['lon']<= max(a)))&
            ((min(b) <= tracts['lat']) & (tracts['lat'] <= max(b)))
            ].reset_index(drop = True)
        ymax = np.sin(np.arccos(np.clip((data['lon']-lon_cir)/(max(data['lon'])-lon_cir),-1.0, 1.0)))
        radiusx = max(data['lon'])-lon_cir
        radiusy = max(data['lat'])-lat_cir
        new_list = []
        cont = 0
        for i,j,k,l in zip(data['lon'],data['lat'],ymax,data['cre_id']):
            if ((lon_cir-radiusx)<=i) and (i<=(lon_cir+radiusx)): 
                normaly = (j-lat_cir)/radiusy
                if np.abs(normaly)<=np.abs(k):
                    new_list.append([])
                    new_list[cont].append(l)
                    new_list[cont].append(i)
                    new_list[cont].append(j)
                    cont += 1
        new_list = np.array(new_list)
        df = pd.DataFrame({
            'cre_id': list(np.array(new_list[:,0])),
            'lon':list(np.array(new_list[:,1])),
            'lat':list(np.array(new_list[:,2]))
        }).astype({'cre_id':'str','lon':'float','lat':'float'})
        inner_ = data.merge(df, how='inner', on='cre_id' ,indicator=True)
        inner_ = inner_.drop(columns=['lon_y', 'lat_y', '_merge'],axis=1)
        geo_df = gpd.GeoDataFrame(inner_, crs=CRS('WGS84'), geometry = inner_['geometry'])
        geo_df = geo_df.to_crs(epsg=3857)
        return geo_df

    def plot(self, directory:str = r'C:\Users\rgallegos\Desktop\Web2.0\src\static\vendor\Areas') -> None:
        geo_df = self.GetInner()
        circule_gdf = self.get_circule_gdf()
        circule_gdf = circule_gdf.to_crs(geo_df.crs)
        fig, ax = plt.subplots(figsize=(10,10))
        geo_df.plot(ax=ax, alpha=0.5, markersize=10, color='r')
        circule_gdf.plot(ax=ax, alpha=1, edgecolor='b', facecolor='none')
        file_list = os.listdir(os.path.dirname(directory))
        file_list = [f for f in file_list if f.endswith('.jpg')]
        counter = 0
        for file in os.listdir(os.path.dirname(directory)):
            if file.endswith('.jpg'):
                try:
                    file_number = int(file.split('.')[0])
                    if file_number > counter:
                        counter = file_number
                except ValueError:
                    pass
        next_filename = f"{directory}\{counter + 1}.png"
        cx.add_basemap(ax, source=cx.providers.Stamen.TonerLite)
        fig.savefig(next_filename, dpi=300)

