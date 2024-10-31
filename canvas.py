import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import dash_bootstrap_components as dbc  # Bootstrap компоненты
from DataResearch import Scorer


human_lots = pd.read_csv("data/human_lots_by_month_03-2020.csv")
lots = pd.read_csv("data/03-2020.csv")
requests = pd.read_csv("data/request_features_03-2020.csv")

def merge_tables_for_canvas(req_fea, lots, df_human):
    req_fea.drop_duplicates(subset="request_id", inplace=True)
    mr1 = req_fea.merge(lots, on="request_id", how='inner')
    df0 = mr1.merge(df_human, on="request_id", how='inner')
    df0["human_lot_id"], uni = pd.factorize(df0["human_lot_id"])
    return df0


def create_dashboard(df_for_visual, mq, ms):
    # def mq_score(df):
    #     return mq
    #
    # def ms_score(df):
    #     return ms

    # Создаем приложение Dash с Bootstrap стилями
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    # Подготовка данных
    df_for_visual['request_quantity'] = df_for_visual.groupby('lot_id')['request_id'].transform(lambda x: x.nunique())
    df_for_visual['human_request_quantity'] = df_for_visual.groupby('human_lot_id')['request_id'].transform(lambda x: x.nunique())



    # Основная статистика
    unique_lot_count = df_for_visual['lot_id'].nunique()
    unique_human_lot_count = df_for_visual['human_lot_id'].nunique()
    average_lot_cost = df_for_visual.groupby('lot_id')['item_cost'].sum().mean()
    average_human_lot_cost = df_for_visual.groupby('human_lot_id')['item_cost'].sum().mean()

    unique_lot_ids = df_for_visual['lot_id'].unique()

# -------------------------------------------------DYNAMIC----------------------------------------------------

    lot_selection = html.Div([
        html.P("Выберите нужные лоты:", style={'font-weight': 'bold', 'font-size': '20px'}),
        dcc.Checklist(
            id='lot-id-checklist',
            options=[{'label': str(lot), 'value': lot} for lot in unique_lot_ids],
            value=unique_lot_ids.tolist(),
            style={'margin': '20px 20px'},
            labelStyle={'margin': '10px 10px 10px 0'},  # Увеличиваем расстояние между элементами
            inline=True
        )
    ])
    scatter = dcc.Graph(id='scatter-plot', style={'width': '100%'})
    table = dbc.Card([
                    dbc.CardBody([
                        html.H4("Сводная таблица по лотам", style={'textAlign': 'center'}),
                        dash_table.DataTable(
                            id='lot-stats-table',
                            columns=[],
                            data=[],
                            style_table={'height': '300px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'center'},
                            style_data_conditional=[]
                        )
                    ])
                ])

    scatter_and_table = dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            scatter
                        ], className="mb-4"),
                        dbc.Row([
                            table
                        ], className="mb-4")
                    ])
                ], style={'backgroundColor': '#2d95bc'})

    cost_plot = dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dcc.Graph(id='cost-plot', style={'width': '100%'})
                        ], className="mb-4"),
                        dbc.Row([
                            dcc.Graph(id='histogram-plot', style={'width': '100%'})
                        ], className="mb-4")
                    ])
                ], style={'backgroundColor': '#2d95bc'})


    selection_and_plots = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                lot_selection
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([scatter_and_table], width=6),# style={'height': '500px'}),
                dbc.Col([cost_plot], width=6)#, style={'height': '440px'})
            ], className="mb-4"),
        ])
    ], style = {'backgroundColor': '#E0F7FA'})

#-------------------------------------------------STATIC----------------------------------------------------

    lot_totals = df_for_visual.groupby('lot_id')['item_cost'].sum().reset_index()
    lot_totals['type'] = 'Алгоритм'  # Добавляем колонку для обозначения типа

    human_lot_totals = df_for_visual.groupby('human_lot_id')['item_cost'].sum().reset_index()
    human_lot_totals['type'] = 'Человек'  # Добавляем колонку для обозначения типа
    total_costs = pd.concat([lot_totals[['type', 'item_cost']], human_lot_totals[['type', 'item_cost']]])

    total_cost_fig = px.box(total_costs, x='type', y='item_cost', title='Сравнение суммарных стоимостей лотов')
    total_cost_fig.update_layout(xaxis_title = '', yaxis_title='Стоимость')
    total_cost_card = dbc.Card([
        dbc.CardBody([
            dcc.Graph(id='total-cost-plot', figure=total_cost_fig)
        ])
    ], style={'backgroundColor': '#ffe8db'})


    # KDE Curve
    kde_fig = go.Figure()
    x1 = np.linspace(df_for_visual['request_quantity'].min(), df_for_visual['request_quantity'].max(), 100)
    kde1 = stats.gaussian_kde(df_for_visual['request_quantity'])
    kde_fig.add_trace(go.Scatter(
        x=x1,
        y=kde1(x1),
        mode='lines',
        name='Алгоритм',
        line=dict(color='blue')
    ))
    x2 = np.linspace(df_for_visual['human_request_quantity'].min(), df_for_visual['human_request_quantity'].max(), 100)
    kde2 = stats.gaussian_kde(df_for_visual['human_request_quantity'])
    kde_fig.add_trace(go.Scatter(
        x=x2,
        y=kde2(x2),
        mode='lines',
        name='Человек',
        line=dict(color='red')
    ))
    kde_fig.update_layout(title='Ядерная оценка плотности количества заявок в лоте', xaxis_title='Количество заявок',yaxis_title='Плотность')

    kde_plot = dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='kde-plot', figure=kde_fig, style={'width': '100%'})
                    ])
                ], style={'backgroundColor': '#ffe8db'})


    summary_statistic = dbc.Card([
                    dbc.CardBody([
                        html.H4("Основные статистики", style={'textAlign': 'center'}),
                        html.P(f"Количество лотов человека: {unique_human_lot_count}"),
                        html.P(f"Средняя стоимость лота человека: {average_human_lot_cost:.2f}"),
                        html.P(f"Количество лотов алгоритма: {unique_lot_count}"),
                        html.P(f"Средняя стоимость лота алгоритма: {average_lot_cost:.2f}"),
                        html.H5(f"Метрики", style={'textAlign': 'center', 'font-size': '18px'}),
                        html.P(f"MQ Score: {mq:.2f}"),
                        html.P(f"MS Score: {ms:.2f}")
                    ])
                ], style={'backgroundColor': '#ffe8db'})

    static_plots = dbc.Card([
        html.P("Статичные графики для сравнения с человеческим лотированием (не зависят от выбора 'нужных лотов')", style={'textAlign': 'center', 'font-size': '20px'}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([kde_plot], width=4),  # style={'height': '500px'}),
                dbc.Col([total_cost_card], width=4),  # style={'height': '500px'}),
                dbc.Col([summary_statistic], width=4)  # , style={'height': '440px'})
            ], className="mb-4"),
        ])
    ], style={'backgroundColor': '#E0F7FA'})

# -------------------------------------------------FINAL_DASHBOARD----------------------------------------------------
    app.layout = dbc.Container([
        html.H1("Визуальный анализ по PackOfLots", style={'textAlign': 'center', 'margin-bottom': '25px'}),
        dbc.Row([
            dbc.Col([selection_and_plots], width=12)
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([static_plots], width=12)
        ], className="mb-4")
    ], fluid=True, style={'backgroundColor': '#a6cbe6'})

# -------------------------------------------------CALLBACKS----------------------------------------------------
    @app.callback(
        Output('lot-stats-table', 'style_data_conditional'),
        Input('lot-stats-table', 'active_cell')
    )
    def update_table_style(selected_cell):
        # Обновление стиля таблицы
        style_data_conditional = [
            {'if': {'column_id': 'unique_recipients'}, 'width': '80px'},
            {'if': {'column_id': 'unique_classes'}, 'width': '80px'},
            {'if': {'column_id': 'unique_orders'}, 'width': '80px'}
        ]

        if selected_cell:
            row_index = selected_cell['row']
            style_data_conditional.append(
                {
                    'if': {'row_index': row_index},
                    'backgroundColor': '#D2F3FF',
                    'color': 'black'
                }
            )

        return style_data_conditional


    # Объединенный callback для обновления графиков и стиля таблицы
    @app.callback(
        [Output('scatter-plot', 'figure'),
         Output('cost-plot', 'figure'),
         Output('histogram-plot', 'figure'),
         Output('lot-stats-table', 'data'),
         Output('lot-stats-table', 'columns')],
        [Input('lot-id-checklist', 'value')]
    )
    def update_output(selected_lots):
        if not selected_lots:
            selected_lots = unique_lot_ids.tolist()

        # Фильтруем данные по выбранным lot_id
        filtered_df = df_for_visual[df_for_visual['lot_id'].isin(selected_lots)]

        # Статистики для таблицы lot_id
        lot_stats = filtered_df.groupby('lot_id').agg(
            средняя_стоимость_позиции=('item_cost', 'mean'),
            уникальные_грузополучатели=('receiver_id', 'nunique'),
            уникальные_заказы=('order_id', 'nunique'),
            уникальные_классы=('class_id', 'nunique'),
        ).reset_index()


        # Scatter Plot
        scatter_fig = go.Figure()
        for lot_id in unique_lot_ids:
            subset = filtered_df[filtered_df['lot_id'] == lot_id]
            scatter_fig.add_trace(go.Scatter(
                x=subset['receiver_address_latitude'],
                y=subset['receiver_address_longitude'],
                mode='markers',
                name=str(lot_id),
                hoverinfo='text',
                text=subset['receiver_address'],
                marker=dict(size=10, opacity=0.8 if lot_id in selected_lots else 0.3)
            ))

        scatter_fig.update_layout(
            title='Расположение грузополучателей в соответствии с лотамим',
            xaxis_title='Широта',
            yaxis_title='Долгота',
            legend_title='lot_id'
        )

        # Cost Plot
        cost_fig = px.box(filtered_df, x='lot_id', y='item_cost', title='Распределение цен позиций в каждом из лотов', color='lot_id')
        cost_fig.update_layout(xaxis_title='Лот', yaxis_title='Цена позиции')


        lot_totals = filtered_df.groupby('lot_id')['item_cost'].sum().reset_index()
        # Создание histogram
        histogram_fig = go.Figure(data=[go.Bar(
            x=lot_totals['lot_id'],
            y=lot_totals['item_cost'],
            marker=dict(color='royalblue')
        )])

        histogram_fig.update_layout(
            title='Суммарная стоимость лота',
            xaxis_title='Лот',
            yaxis_title='Стоимость',
            xaxis=dict(tickmode='linear')  # Установка линейного режима для оси X
        )

        return scatter_fig, cost_fig, histogram_fig, lot_stats.to_dict('records'), [{"name": i, "id": i} for i in lot_stats.columns]

    # Запуск приложения
    app.run_server(debug=True)

# Пример использования
def make_dashboard(requests, lots, human_lots, scorer: Scorer):
    # scorer = Scorer()
    if __name__ == '__main__':
        create_dashboard(merge_tables_for_canvas(requests, lots, human_lots), scorer.mq_score(requests, lots, human_lots), scorer.ms_score(requests, lots))




# make_dashboard(requests, lots, human_lots, Scorer())





# знаки после запятой в таблице
# большой курсор
# checklist заменить на че-то из bootstrap (например multy select)
# html код
# подсказка при наведении на вопросик