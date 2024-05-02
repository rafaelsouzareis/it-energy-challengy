# BTG Energy Challenge (RESOLUÇÃO DO DESAFIO)
### Informações
Desafio: BTG Energy Challenge

Nome: Rafael Souza dos Reis

Início: 29/04/2024

Término: 02/05/2024

***O termo "challengy" do repositório se refere à challenge-energy***


### Introdução
Na pasta ***forecast_files***, existem arquivos de previsão de precipitação do modelo meteorológico ETA, desenvolvido pelo INPE. Conforme explicado no arquivo README.md, os nomes dos arquivos seguem o padrão: ***ETA40_pddmmyyaddmmyy.dat***. Neste padrão, a primeira data indica o dia em que a previsão foi realizada e a segunda data representa o dia que a previsão se refere. Dentro dos arquivos temos os dados de latitude, longitude e o valor da precipitação. Por outro lado, existe um arquivo de contorno com coordenadas de latitude e longitude que precisa ser aplicado à malha de dados para determinar quais pontos estão contidos nessa região especificada, sendo esse o maior desafio do BTG Energy Challenge, pois envolve um problema de hull convexo. Em termos matemáticos, um hull convexo é uma forma geométrica que envolve um conjunto de pontos que, nesse caso, é a área delimitada pelo contorno. 

### Contorno na malha de precipitação
Implementar e usar o polígono de contorno de maneira eficiente requer uma combinação de um algoritmo robusto e técnicas de programação que aproveitem as capacidades das operações vetorizadas, pois dependendo da geometria do polígono, o cálculo pode ser complexo e demorado. Nesse caso, para a resolução do problema, utilizamos a biblioteca externa ***GeoPandas***, integrada a biblioteca ***Shapely***, que já possui métodos para calcular o hull convexo de um conjunto de pontos.

O seguinte código (disponível em ***main.py***) é a função ***apply_contour*** que recebe dois dataframes, um com coordenadas de contorno e outro com dados geográficos. Ela converte esses dataframes em GeoDataFrames, cria um polígono a partir das coordenadas de contorno, e usa esse polígono para filtrar e retornar apenas os pontos do segundo dataframe que estão dentro do contorno.

```
def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    
    #Criar um Geo Data Frame  do countour_df e converte-lo para um polígono de contorno
    gpd_contour = gpd.GeoDataFrame(contour_df, geometry = [Point(xy) for xy in zip(contour_df['lat'], contour_df['long'])])
    polygon_contour = Polygon([(xy) for xy in zip(gpd_contour.geometry.x, gpd_contour.geometry.y)])
    
    #Criar um Geo Data Frame do data_df e aplicar uma máscara para os dados dentro do polígono de contorno
    gpd_data = gpd.GeoDataFrame(data_df, geometry = [Point(xy) for xy in zip(data_df['lat'], data_df['long'])])
    mask_contour= gpd_data.geometry.within(polygon_contour)
    filtered_data = gpd_data[mask_contour]
    result_df = pd.DataFrame({'lat': filtered_data['lat'],'long': filtered_data['long'], 'data_value': filtered_data['data_value']})
    
    return result_df
```

A imagem foi criada para demonstrar a localização da Usina Hidrelétrica Camargos dentro da malha de dados de preciptação. Ela mostra claramente quais pontos da malha estão contidos na região da usina. Com isso, podemos precisamente analisar e quantificar a precipitação diária específica para essa região. ***(o código para gerar a imagem está como comentário na função apply_contour vista anteriormente)***

![Contorno de Camargos [Grande]](camargos_grande_malha_contorno.PNG "Contorno de Carmargos")

### Tratamento e visualização de dados
+ A função ***list_files_in_directory*** lista arquivos em um diretório especificado e os organiza em um DataFrame do pandas. Ela utiliza expressões regulares para filtrar os arquivos com base em um padrão fornecido ***ETA40_p(\d{6})a(\d{6})\.dat***, permitindo a identificação e extração de datas específicas dos nomes dos arquivos. Os dados extraídos incluem o nome do arquivo completo e as datas formatadas, armazenados em colunas ***file_name***, ***forecast_date*** e ***forecasted_date***. A função também possui tratamento de erros para lidar com exceções como diretórios inacessíveis ou nomes de arquivos que não correspondem ao padrão esperado, garantindo que a função retorne um DataFrame vazio em caso de erro e exiba uma mensagem de erro relevante.

+ O código abaixo verifica se o DataFrame ***df_files*** não está vazio e, em seguida, cria um novo DataFrame ***view_df***. Este DataFrame é construído iterando sobre cada registro em ***df_files***, aplicando um contorno especificado ao ler os dados de precipitação de um arquivo e somando esses dados. ***view_df*** é então organizado por ***forecasted_date*** e uma coluna de precipitação acumulada é calculada usando a soma cumulativa dos valores diários de precipitação.

```
view_df: pd.DataFrame = pd.DataFrame(
        [
            {   
                'forecast_date': row.forecast_date,  
                'forecasted_date': row.forecasted_date, 
                'data_value': apply_contour(contour_df=contour_df, data_df=read_data_file(row.file_name))['data_value'].sum()
            }
            for row in df_files.itertuples()
        ]).sort_values(by='forecasted_date', ascending=True)
```

+ A função ***plot_precipitation_data*** recebe um DataFrame de precipitação, organiza os dados por data prevista, e cria dois gráficos: um mostrando a precipitação diária e outro a precipitação acumulada.

### Resultados
Com base nos dados processados nos arquivos do diretório ***forecast_files***, chegamos na precipitação diária e acumulada do desafio, confome a figura abaixo.

![Precipitação Contorno de Camargos [Grande]](resultado.PNG "Precipitação Contorno de Carmargos")

### Melhorias e otimização
Embora a utilização de operações vetorizadas através das bibliotecas ***GeoPandas*** e ***Shapely*** ofereça uma maneira eficiente e poderosa de manipular dados geográficos, como a criação de hulls convexos e outros cálculos geométricos, o processamento de grandes conjuntos de dados ainda pode resultar em consumo significativo de recursos e tempo computacional, em especial à geometrias de contorno mais complexas. Para processar os arquivos de ***forecast_files***, o código demorou em torno de ***1 segundo (computador com baixo processamento)***, sendo um tempo de execução relativamente alto quando comparamos com a quantidade de arquivos processados. 

Com  base na analise dos dados disponíveis no diretório ***forecast_files***, verificamos que os pontos da malha sempre estão alocados na mesma latitude e longitude, mudando apenas os valores de preciptação nessas coordenadas. Assim, podemos otimizar a função ***apply_contour*** para evitar aplicar o contorno repetidamente, pois estamos assumindo que a coleta de dados é sempre a mesma para as mesmas latitudes e longitudes. Sendo assim, a otimização envolve aplicar ***apply_contour*** apenas uma vez (no primeiro arquivo) e reutilizar o ***contour_df_data*** filtrado para as outras iterações. Isso reduz a necessidade de recalcular o contorno para cada arquivo, economizando tempo e recursos computacionais.

Assim, alteramos a função ***apply_contour*** para retornar apenas uma máscara de coordenadas geométricas, conforme o código a seguir.

```
def apply_contour(contour_df: pd.DataFrame, data_df: pd.DataFrame) -> pd.DataFrame:
    
    gpd_contour = gpd.GeoDataFrame(contour_df, geometry = [Point(xy) for xy in zip(contour_df['lat'], contour_df['long'])])
    polygon_contour = Polygon([(xy) for xy in zip(gpd_contour.geometry.x, gpd_contour.geometry.y)])
    gpd_data = gpd.GeoDataFrame(data_df, geometry = [Point(xy) for xy in zip(data_df['lat'], data_df['long'])])
    mask_contour= gpd_data.geometry.within(polygon_contour)
    filtered_data = gpd_data[mask_contour]
    result_df = pd.DataFrame({'lat': filtered_data['lat'],'long': filtered_data['long']})
    return result_df
```

Na função principal ***main***, substiuímos o trecho e código ***view_df*** pelo código a seguir, que aplica o contorno apenas ao primeiro arquivo de dados, reutilizando a máscara nos dados subsequentes.

```
view_list: list = []

    for row in df_files.itertuples():
        data_df: pd.DataFrame = read_data_file(row.file_name)
        if(row.Index != 0):
            filtered_df = pd.merge(data_df, contour_df_data, on=['lat', 'long'])
        else:
            contour_df_data: pd.DataFrame = apply_contour(contour_df=contour_df, data_df=data_df)
            filtered_df = pd.merge(data_df, contour_df_data, on=['lat', 'long']) 
        view_list.append({'forecast_date': row.forecast_date,  'forecasted_date': row.forecasted_date, 'data_value':filtered_df['data_value'].sum()})

    view_df: pd.DataFrame = pd.DataFrame(view_list).sort_values(by='forecasted_date', ascending=True)
```

Assim, conseguimos otimizar o código para processar o dados em ***0.3 segundos (computador com baixo processamento)***, diminuindo em 2/3 em relação ao código anterior. 
