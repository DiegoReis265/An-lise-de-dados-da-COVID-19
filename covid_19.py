# -*- coding: utf-8 -*-
"""COVID 19.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ROwj50gQVS1aGPiKP2yI1F_mC0hpm6iq

#Projeto  - Análise de dados da COVID-19
### Desafio de projeto para prever a evolução da COVID-19 no Brasil, análise desenvolvida para o Bootcamp da DIO em parceria com a Unimed-BH.
### Estudo ministrado pelo Prof. Dr. Neylson Crepalde
"""

# importando bibliotecas e algumas funções
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# importando dados
url = 'https://github.com/neylsoncrepalde/projeto_eda_covid/blob/master/covid_19_data.csv?raw=true'

df = pd.read_csv(url, parse_dates=['ObservationDate', 'Last Update'])
df
# comando `pd.read_csv` serve para passar quais são as colunas que serão "parseadas" como datas, ou seja, 
# quais colunas que serão utilizadas desta url.

# Conferindo o tipo de dado de cada coluna, obs: object é uma string.
df.dtypes

# Criando uma função para regularizar os nomes das colunas
import re
def corrige_colunas(col_name):
    return re.sub(r"[/| ]", "", col_name).lower()

# Corrigindo as colunas
df.columns = [corrige_colunas(col) for col in df.columns]

# renomeando as colunas para português para ficar mais fácil a compreensão, é opcional
df = df.rename(columns={"observationdate":"datadeobservação", "provincestate": "estado", "countryregion":"país", "lastupdate":"ultimaatualização", "confirmed":"confirmados", "deaths": "mortes", "recovered": "recuperados"})

df

"""#Brasil
## Agora vamos investigar e trabalhar apenas com os dados referente ao nosso país.
"""

# coletando somente informações referentes ao Brasil.
df.loc[df.país == 'Brazil']

"""# Casos confirmados:"""

# coletando dados do país em que o número de casos caonfirmados seja > 0, estes dados serão alocados no df brasil
brasil = df.loc[(df.país == 'Brazil') & (df.confirmados > 0)]

brasil

# Plotando gráfico dos dados referente ao número de casos confirmados no Brasil
px.line(brasil, 'datadeobservação', 'confirmados', 
        labels={'datadeobservação':'Data', 'confirmados':'Número de casos confirmados'},
       title='Casos confirmados no Brasil')

"""# Número de novos casos por dia:"""

# Função para fazer a contagem de novos casos:
brasil['novoscasos'] = list(map(
    lambda x: 0 if (x==0) else brasil['confirmados'].iloc[x] - brasil['confirmados'].iloc[x-1],
    np.arange(brasil.shape[0])
))

brasil

# Visualizando gráfico de novos casos por dia
px.line(brasil, x='datadeobservação', y='novoscasos', title='Novos casos por dia',
       labels={'datadeobservação': 'Data', 'novoscasos': 'Novos casos'})

"""#Mortes no Brasil:"""

fig = go.Figure()

fig.add_trace(
    go.Scatter(x=brasil.datadeobservação, y=brasil.mortes, name='Mortes', mode='lines+markers',
              line=dict(color='red'))
)
#Edita o layout
fig.update_layout(title='Mortes por COVID-19 no Brasil',
                   xaxis_title='Data',
                   yaxis_title='Número de mortes')
fig.show()

"""# Taxa de crescimento:

Taxa de crescimento do COVID desde o primeiro caso.
"""

def taxa_crescimento(data, variable, data_inicio=None, data_fim=None):
    # Se data_inicio for None, define como a primeira data disponível no dataset
    if data_inicio == None:
        data_inicio = data.datadeobservação.loc[data[variable] > 0].min()
    else:
        data_inicio = pd.to_datetime(data_inicio)
        
    if data_fim == None:
        data_fim = data.datadeobservação.iloc[-1]
    else:
        data_fim = pd.to_datetime(data_fim)
    
    # Define os valores de presente e passado
    passado = data.loc[data.datadeobservação == data_inicio, variable].values[0]
    presente = data.loc[data.datadeobservação == data_fim, variable].values[0]
    
    # Define o número de pontos no tempo q vamos avaliar
    n = (data_fim - data_inicio).days
    
    # Calcula a taxa
    taxa = (presente/passado)**(1/n) - 1

    return taxa*100

# Taxa de crescimento médio do COVID no Brasil em todo o período
cresc_medio = taxa_crescimento(brasil, 'confirmados')
print(f"O crescimento médio do COVID no Brasil no período avaliado foi de {cresc_medio.round(2)}%.")

"""#Observando o comportamento da **taxa de crescimento no tempo**:"""

# Função para calcular a taxa de crescimento diário.

def taxa_crescimento_diaria(data, variable, data_inicio=None):
    if data_inicio == None:
        data_inicio = data.datadeobservação.loc[data[variable] > 0].min()
    else:
        data_inicio = pd.to_datetime(data_inicio)
        
    data_fim = data.datadeobservação.max()
    n = (data_fim - data_inicio).days
    taxas = list(map(
        lambda x: (data[variable].iloc[x] - data[variable].iloc[x-1]) / data[variable].iloc[x-1],
        range(1,n+1)
    ))
    return np.array(taxas)*100

tx_dia = taxa_crescimento_diaria(brasil, 'confirmados')

tx_dia

# Gráfico da taxa de crescimento diário

primeiro_dia = brasil.datadeobservação.loc[brasil.confirmados > 0].min()
px.line(x=pd.date_range(primeiro_dia, brasil.datadeobservação.max())[1:],
        y=tx_dia, title='Taxa de crescimento de casos confirmados no Brasil',
       labels={'y':'Taxa de crescimento', 'x':'Data'})

"""# Predições

Construindo um modelo de séries temporais para prever os novos casos. Antes analisemos a série temporal.
"""

from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

novoscasos = brasil.novoscasos
novoscasos.index = brasil.datadeobservação

res = seasonal_decompose(novoscasos)

fig, (ax1,ax2,ax3, ax4) = plt.subplots(4, 1,figsize=(10,8))
ax1.plot(res.observed)
ax2.plot(res.trend)
ax3.plot(res.seasonal)
ax4.scatter(novoscasos.index, res.resid)
ax4.axhline(0, linestyle='dashed', c='black')
plt.show()

"""## Decompondo a série de confirmados:"""

confirmados = brasil.confirmados
confirmados.index = brasil.datadeobservação

res2 = seasonal_decompose(confirmados)

fig, (ax1,ax2,ax3, ax4) = plt.subplots(4, 1,figsize=(10,8))
ax1.plot(res2.observed)
ax2.plot(res2.trend)
ax3.plot(res2.seasonal)
ax4.scatter(confirmados.index, res2.resid)
ax4.axhline(0, linestyle='dashed', c='black')
plt.show()

"""# Predizendo o número de casos confirmados com um AUTO-ARIMA:"""

pip install pmdarima

from pmdarima.arima import auto_arima

modelo = auto_arima(confirmados)

pd.date_range('2020-05-01', '2020-05-19')

fig = go.Figure(go.Scatter(
    x=confirmados.index, y=confirmados, name='Observed'
))

fig.add_trace(go.Scatter(x=confirmados.index, y = modelo.predict_in_sample(), name='Predicted'))

fig.add_trace(go.Scatter(x=pd.date_range('2020-05-20', '2020-06-05'), y=modelo.predict(15), name='Forecast'))

fig.update_layout(title='Previsão de casos confirmados para os próximos 15 dias',
                 yaxis_title='Casos confirmados', xaxis_title='Data')
fig.show()

"""# Modelo de crescimento com Facebook Prophet:

## Esta análise é para prever quando a curva de contágio irá se estabilizar considerando um cenário em que não se aplique medidas de controle ao combate do vírus e todas as pessoas se contaminem.
"""

pip install Prophet

!conda install -c conda-forge fbprophet -y

from prophet import Prophet

# preparando os dados

train = confirmados.reset_index()[:-5]
test = confirmados.reset_index()[-5:]

# renomeia colunas
train.rename(columns={"datadeobservação":"ds","confirmados":"y"},inplace=True)
test.rename(columns={"datadeobservação":"ds","confirmados":"y"},inplace=True)
test = test.set_index("ds")
test = test['y']

estimativa = Prophet(growth="logistic", changepoints=['2020-03-21', '2020-03-30', '2020-04-25', '2020-05-03', '2020-05-10'])

# População brasileira estimada na data de coleta dos dados
pop = 211463256 #https://www.ibge.gov.br/apps/populacao/projecao/box_popclock.php
train['cap'] = pop

# Treina o modelo
estimativa.fit(train)

# Construindo previsões para o futuro
future_dates = estimativa.make_future_dataframe(periods=200)
future_dates['cap'] = pop
forecast =  estimativa.predict(future_dates)

# plotando gráfico
fig = go.Figure()

fig.add_trace(go.Scatter(x=forecast.ds, y=forecast.yhat, name='Predição'))
fig.add_trace(go.Scatter(x=test.index, y=test, name='Observados - Teste'))
fig.add_trace(go.Scatter(x=train.ds, y=train.y, name='Observados - Treino'))
fig.update_layout(title='Predições de casos confirmados no Brasil')
fig.show()