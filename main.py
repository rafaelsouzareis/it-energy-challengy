import pandas as pd
import re
import time
from functools import wraps

import geopandas as gpd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
import os


def read_data_file(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    list_dados = [line.split() for line in raw_file]
    float_raw_lines = [list(map(float, raw_line)) for raw_line in list_dados]
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long', 'data_value'])


def read_contour_file(file_path: str) -> pd.DataFrame:
    line_split_comp = re.compile(r'\s*,')

    with open(file_path, 'r') as f:
        raw_file = f.readlines()

    l_raw_lines = [line_split_comp.split(raw_file_line.strip()) for raw_file_line in raw_file]
    l_raw_lines = list(filter(lambda item: bool(item[0]), l_raw_lines))
    float_raw_lines = [list(map(float, raw_line))[:2] for raw_line in l_raw_lines]
    header_line = float_raw_lines.pop(0)
    assert len(float_raw_lines) == int(header_line[0])
    return pd.DataFrame(float_raw_lines, columns=['lat', 'long'])


def list_files_in_directory(directory: str, pattern: str = None) -> pd.DataFrame:
    
    try:
        #Listar arquivos do diretório e verificar a Expressão Regular
        files = os.listdir(directory)
        regex = re.compile(pattern) if pattern else None

        #Criar uma lista data contendo nomes dos arquivos, forecast_date e forecasted_date 
        data = [
            [
                f'{directory}{file_name}',
                time.strftime('%d-%m-%Y', time.strptime(match.group(1), '%d%m%y')),
                time.strftime('%d-%m-%Y', time.strptime(match.group(2), '%d%m%y'))
            ]
            for file_name in files
            if regex and (match := regex.search(file_name)) and len(match.groups()) >= 2     
        
        ]

        #Verifica se o diretório está vazio ou se o formato dos arquivos não segue o padrão
        if(len(data) == 0):
            print("Diretório vazio ou nome do arquivo fora padrão.")

        return pd.DataFrame(data, columns=['file_name', 'forecast_date', 'forecasted_date'])
    
    except Exception as e:
        print(e)
        return pd.DataFrame(columns=['file_name', 'forecast_date', 'forecasted_date'])


def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    
    #Criar um Geo Data Frame  do countour_df e converte-lo para um polígono de contorno
    gpd_contour = gpd.GeoDataFrame(contour_df, geometry = [Point(xy) for xy in zip(contour_df['lat'], contour_df['long'])])
    polygon_contour = Polygon([(xy) for xy in zip(gpd_contour.geometry.x, gpd_contour.geometry.y)])
    
    #Criar um Geo Data Frame do data_df e aplicar uma máscara para os dados dentro do polígono de contorno
    gpd_data = gpd.GeoDataFrame(data_df, geometry = [Point(xy) for xy in zip(data_df['lat'], data_df['long'])])
    mask_contour= gpd_data.geometry.within(polygon_contour)
    filtered_data = gpd_data[mask_contour]
    result_df = pd.DataFrame({'lat': filtered_data['lat'],'long': filtered_data['long'], 'data_value': filtered_data['data_value']})
    
    '''
    #Vizualização Gráfica dos pontos data_df e do contour_df
    fig, ax = plt.subplots(figsize=(10, 10))
    gpd.GeoSeries([polygon_contour]).plot(ax=ax, facecolor='none', edgecolor='red')
    gpd_data.plot(ax=ax, color='blue', markersize=5)
    inside_polygon = gpd_data[gpd_data.geometry.within(polygon_contour)]

    #Atribuir etiquetas apenas aos pontos dentro do contorno
    for x, y, label in zip(inside_polygon.geometry.x, inside_polygon.geometry.y, inside_polygon['data_value']):
        ax.text(x, y, f'{label}', fontsize=9, ha='right')

    #Cálculo da preciptação acumulada
    precipitacao = str(filtered_data['data_value'].sum())

    #Definição do título e eixos do gráfico
    ax.set_title(f'Visualização do Polígono e Pontos - Precipitação Acumulada: {precipitacao}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    ax.set_aspect('equal')
    plt.show()
    '''

    return result_df


def plot_precipitation_data(df: pd.DataFrame) -> None:
    
    # Organizar o data frame em ordem crescente pela coluna 'forecasted_date'
    df_sorted = df.sort_values(by='forecasted_date')
    
    # Criar um grid de subplots com 2 gráficos
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 6))

    # Primeiro subplot: Precipitação por Dia
    ax1.plot(df_sorted['forecasted_date'], df_sorted['data_value'], marker='o', linestyle='-', color='b')
    ax1.set_title('Daily Precipitation')
    ax1.set_xlabel('Forecasted Date')
    ax1.set_ylabel('Data Value (mm)')
    ax1.grid(True)

    # Adicionar etiquetas aos pontos no primeiro subplot
    for i, point in df_sorted.iterrows():
        ax1.text(point['forecasted_date'], point['data_value'], f'  {point["data_value"]:.1f}', color='black', ha='left', va='bottom')

    # Segundo subplot: Precipitação Acumulada
    ax2.plot(df_sorted['forecasted_date'], df_sorted['cumulative_precipitation'], marker='o', linestyle='-', color='r')
    ax2.set_title('Accumulated Precipitation')
    ax2.set_xlabel('Forecasted Date')
    ax2.set_ylabel('Cumulative Data Value (mm)')
    ax2.grid(True)

    # Adicionar etiquetas aos pontos no segundo subplot
    for i, point in df_sorted.iterrows():
        ax2.text(point['forecasted_date'], point['cumulative_precipitation'], f'  {point["cumulative_precipitation"]:.1f}', color='black', ha='left', va='bottom')

    # Ajustar layout e mostrar o plot
    plt.tight_layout()
    plt.show()


def main() -> None:

    start_time = time.time()

    contour_df: pd.DataFrame = read_contour_file('PSATCMG_CAMARGOS.bln')
    df_files: pd.DataFrame = list_files_in_directory(directory='forecast_files/', pattern=r'ETA40_p(\d{6})a(\d{6})\.dat')
    

    if(not df_files.empty):

        view_df: pd.DataFrame = pd.DataFrame(
        [
            {   
                'forecast_date': row.forecast_date,  
                'forecasted_date': row.forecasted_date, 
                'data_value': apply_contour(contour_df=contour_df, data_df=read_data_file(row.file_name))['data_value'].sum()
            }
            for row in df_files.itertuples()
        ]).sort_values(by='forecasted_date', ascending=True)


        #Calcular Precipitação Acumulada
        view_df['cumulative_precipitation'] = view_df['data_value'].cumsum()
        
        print(f"Tempo processamento de dados: {time.time() - start_time}")

        plot_precipitation_data(view_df)
    
 
if __name__ == '__main__':
    main()
