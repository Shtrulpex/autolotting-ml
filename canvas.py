import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import dash_bootstrap_components as dbc  # Bootstrap компоненты

# human_lots = pd.read_csv("data/human_lots_by_month_03-2020.csv")
# lots = pd.read_csv("data/03-2020.csv")
# requests = pd.read_csv("data/request_features_03-2020.csv")

# ----------------------------------------Описание для графиков и таблиц-----------------------------------------
scatter_plot_description = html.Div([
    html.Span("График рассеяния показывает расположение грузополучателей и поставщиков в соответствии с их лотами.",
              style={'display': 'block'}),
    html.Span("На оси X представлена широта, а на оси Y — долгота.", style={'display': 'block'}),
    html.Span(
        "Каждая точка представляет отдельного грузополучателя или поставщиков, и цвет точки указывает на принадлежность к конкретному лоту.",
        style={'display': 'block'}),
    html.Span("[!] Вы можете выделять конкретные лоты, используя диапазонный ползунок или выпадающий список.",
              style={'display': 'block'}),
    html.Span("[!] При наведении на точки отображается дополнительная информация о грузополучателе.",
              style={'display': 'block'}),
    html.Span(
        "[!] Также на легенде справа есть возможность выбирать грузополучателей (цифра) и поставщиков(цифра+'п') выбранного лота.",
        style={'display': 'block'}),
])

cost_plot_description = html.Div([
    html.Span("График стоимости (box plot) иллюстрирует распределение цен позиций в каждом из лотов.",
              style={'display': 'block'}),
    html.Span("Ось X представляет лоты, а ось Y — стоимость позиции.", style={'display': 'block'}),
    html.Span("Каждый 'ящик' показывает медиану, квартиль и выбросы, что позволяет оценить вариативность цен в лотах.",
              style={'display': 'block'}),
    html.Span(
        "[!] Вы можете взаимодействовать с графиком, выбирая определенные лоты через ползунок или выпадающий список.",
        style={'display': 'block'}),
])

histogram_plot_description = html.Div([
    html.Span("Гистограмма демонстрирует суммарную стоимость каждого лота.", style={'display': 'block'}),
    html.Span("Ось X показывает идентификаторы лотов, а ось Y — общую стоимость позиций в этих лотах.",
              style={'display': 'block'}),
    html.Span("Этот график помогает быстро оценить, какие лоты имеют наибольшую суммарную стоимость.",
              style={'display': 'block'}),
    html.Span(
        "[!] Вы можете использовать диапазонный ползунок или выпадающий список, чтобы сосредоточиться на определенных лотах.",
        style={'display': 'block'}),
])

lot_stats_table_description = html.Div([
    html.Span("Таблица сводной информации по лотам предоставляет основные статистические данные о выбранных лотах.",
              style={'display': 'block'}),
    html.Span(
        "Она включает среднюю стоимость позиции, количество уникальных грузополучателей, заказов и классов для каждого лота.",
        style={'display': 'block'}),
    html.Span(
        "Вы можете выделить строку таблицы, кликнув на любую ячейку, что поможет лучше проанализировать конкретный лот.",
        style={'display': 'block'}),
    html.Span(
        "[!] Также таблица автоматически обновляется в зависимости от выбранных лотов через ползунок или выпадающий список.",
        style={'display': 'block'}),
])

summary_statistics_description = html.Div([
    html.Span(
        "Эта секция содержит основные статистики о лотах, включая количество лотов и среднюю стоимость для человека и алгоритма.",
        style={'display': 'block'}),
    html.Span("Это позволяет быстро оценить эффективность алгоритма по сравнению с человеческим подходом.",
              style={'display': 'block'}),
])

kde_plot_description = html.Div([
    html.Span(
        "График ядерной оценки плотности (KDE) показывает распределение количества заявок по лотам для человека и алгоритма.",
        style={'display': 'block'}),
    html.Span("Ось X представляет количество заявок, а ось Y — плотность распределения.", style={'display': 'block'}),
    html.Span(
        "Это полезно для визуализации того, как распределяются заявки между лотами и какие лоты имеют наибольшую плотность заявок.",
        style={'display': 'block'}),
])

total_cost_plot_description = html.Div([
    html.Span("График сравнения суммарных стоимостей лотов (box plot) показывает различия в стоимости между лотами,",
              style={'display': 'block'}),
    html.Span("обработанными человеком и алгоритмом.", style={'display': 'block'}),
    html.Span("Это позволяет оценить, какой подход приводит к меньшим или большим затратам.",
              style={'display': 'block'}),
])

# Пример использования
descriptions = {
    "scatter_plot": scatter_plot_description,
    "cost_plot": cost_plot_description,
    "histogram_plot": histogram_plot_description,
    "lot_stats_table": lot_stats_table_description,
    "summary_statistics": summary_statistics_description,
    "kde_plot": kde_plot_description,
    "total_cost_plot": total_cost_plot_description,
}


def make_popover(description_name, target_tooltip):
    return dbc.Popover(
        descriptions[description_name],
        target=target_tooltip,
        placement="right",
        trigger="hover focus",
        style={
            'maxWidth': '700px',  # Ограничение ширины
            'backgroundColor': '#303335',  # Темный фон
            'color': '#f0f0f0',  # Светлый текст
            'padding': '10px',  # Внутренние отступы для улучшенного восприятия
            'borderRadius': '5px',  # Закругленные углы
            'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'  # Небольшая тень для глубины
        }
    )


def merge_tables_for_canvas(req_fea, lots, df_human):
    req_fea.drop_duplicates(subset="request_id", inplace=True)
    mr1 = req_fea.merge(lots, on="request_id", how='inner')
    df0 = mr1.merge(df_human, on="request_id", how='inner')
    df0["human_lot_id"], uni = pd.factorize(df0["human_lot_id"])
    return df0


def create_dashboard(df_for_visual, mq, ms):
    # Создаем приложение Dash с Bootstrap стилями
    app = Dash(__name__, external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css"  # Font Awesome
    ])

    # Подготовка данных
    df_for_visual['request_quantity'] = df_for_visual.groupby('lot_id')['request_id'].transform(lambda x: x.nunique())
    df_for_visual['human_request_quantity'] = df_for_visual.groupby('human_lot_id')['request_id'].transform(
        lambda x: x.nunique())

    # Основная статистика
    unique_lot_count = df_for_visual['lot_id'].nunique()
    unique_human_lot_count = df_for_visual['human_lot_id'].nunique()
    average_lot_cost = df_for_visual.groupby('lot_id')['item_cost'].sum().mean()
    average_human_lot_cost = df_for_visual.groupby('human_lot_id')['item_cost'].sum().mean()

    unique_lot_ids = df_for_visual['lot_id'].unique()

    # -------------------------------------------------DYNAMIC----------------------------------------------------

    # Define the range of lot_id
    lot_selection = html.Div([
        dbc.Row([
            dbc.Col([
                html.P("Выберите интервал лотов:", style={'font-weight': 'bold', 'font-size': '22px', 'color': '#333'}),
                dcc.RangeSlider(
                    id='lot-id-range-slider',
                    min=int(df_for_visual['lot_id'].min()),
                    max=int(df_for_visual['lot_id'].max()),
                    value=[int(df_for_visual['lot_id'].min()), int(df_for_visual['lot_id'].max())],
                    marks={i: str(i) for i in
                           range(int(df_for_visual['lot_id'].min()), int(df_for_visual['lot_id'].max()) + 1, 5)},
                    tooltip={"placement": "bottom", "always_visible": True},
                    pushable=5,
                ),
            ], width=10),
            dbc.Col([
                html.P("Отдельные лоты:", style={'font-weight': 'bold', 'font-size': '22px', 'color': '#333'}),
                dcc.Dropdown(
                    id='lot-id-dropdown',
                    options=[{'label': str(lot), 'value': lot} for lot in unique_lot_ids],
                    multi=True,
                    placeholder="Выберите отдельные лоты",
                    style={'border-color': '#007bff'}
                )
            ], width=2)
        ], className="mb-4"),
    ])

    scatter = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                html.Div([
                    html.I(className="fas fa-question-circle", id="tooltip-scatter",
                           style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
                    dcc.Graph(id='scatter-plot', style={'width': '100%'}),
                    make_popover("scatter_plot", "tooltip-scatter")
                ])
            ])
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})

    table = dbc.Card([
        dbc.CardBody([
            html.I(className="fas fa-question-circle", id="tooltip-table",
                   style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
            html.H4("Сводная таблица по лотам", style={'textAlign': 'center'}),
            dash_table.DataTable(
                id='lot-stats-table',
                columns=[],
                data=[],
                style_table={'height': '414px', 'overflowY': 'auto'},
                style_cell={'textAlign': 'center'},
                style_data_conditional=[]
            ),
            make_popover("lot_stats_table", "tooltip-table")
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})

    scatter_and_table = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                scatter
            ], className="mb-4", style={'padding-left': '15px', 'padding-right': '15px'}),
            dbc.Row([
                table
            ], className="mb-4", style={'padding-left': '15px', 'padding-right': '15px'})
        ])
    ], style={'backgroundColor': '#ffe8db'})

    lot_item_cost = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                html.Div([
                    html.I(className="fas fa-question-circle", id="tooltip-lot_item_cost",
                           style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
                    dcc.Graph(id='cost-plot', style={'width': '100%'}),
                    make_popover("cost_plot", "tooltip-lot_item_cost")
                ])
            ])
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})

    histogram = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                html.Div([
                    html.I(className="fas fa-question-circle", id="tooltip-histogram",
                           style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
                    dcc.Graph(id='histogram-plot', style={'width': '100%'}),
                    make_popover("histogram_plot", "tooltip-histogram")
                ])
            ])
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})

    cost_plot = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                lot_item_cost
            ], className="mb-4", style={'padding-left': '15px', 'padding-right': '15px'}),
            dbc.Row([
                histogram
            ], className="mb-4", style={'padding-left': '15px', 'padding-right': '15px'})
        ])
    ], style={'backgroundColor': '#ffe8db'})

    selection_and_plots = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                lot_selection
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([scatter_and_table], width=6),  # style={'height': '500px'}),
                dbc.Col([cost_plot], width=6)  # , style={'height': '440px'})
            ], className="mb-4"),
        ])
    ], style={'backgroundColor': '#E0F7FA'})
    # E0F7FA

    # -------------------------------------------------STATIC----------------------------------------------------

    lot_totals = df_for_visual.groupby('lot_id')['item_cost'].sum().reset_index()
    lot_totals['type'] = 'Алгоритм'  # Добавляем колонку для обозначения типа

    human_lot_totals = df_for_visual.groupby('human_lot_id')['item_cost'].sum().reset_index()
    human_lot_totals['type'] = 'Человек'  # Добавляем колонку для обозначения типа
    total_costs = pd.concat([lot_totals[['type', 'item_cost']], human_lot_totals[['type', 'item_cost']]])

    total_cost_fig = px.box(total_costs, x='type', y='item_cost')
    total_cost_fig.update_layout(
        xaxis_title='',
        yaxis_title='Стоимость',
        title={
            'text': "<b>Сравнение суммарных стоимостей лотов</b>",
            'font': {'size': 18},  # Adjust size as needed
            'x': 0.5,  # Center the title
        }
    )

    total_cost_card = dbc.Card([
        dbc.CardBody([
            html.I(className="fas fa-question-circle", id="tooltip-total_cost_card",
                   style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
            dcc.Graph(id='total-cost-plot', figure=total_cost_fig),
            make_popover("total_cost_plot", "tooltip-total_cost_card")
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})

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
    kde_fig.update_layout(
        xaxis_title='Количество заявок',
        yaxis_title='Плотность',
        title={
            'text': "<b>Ядерная оценка плотности кол-ва заявок в лоте</b>",
            'font': {'size': 18},  # Adjust size as needed
            'x': 0.5,  # Center the title
        }
    )

    kde_plot = dbc.Card([
        dbc.CardBody([
            html.I(className="fas fa-question-circle", id="tooltip-kde",
                   style={'cursor': 'pointer', 'margin-left': '10px', 'color': '#007bff'}),
            dcc.Graph(id='kde-plot', figure=kde_fig, style={'width': '100%'}),
            make_popover("kde_plot", "tooltip-kde")
        ])
    ], style={'border': '1px solid #22262a', 'borderRadius': '10px', 'padding': '15px'})
    if mq:
        MQ_html = html.P(f"MQ Score: {mq:.2f}")
    else:
        MQ_html = ""

    summary_statistic = dbc.Card([
        dbc.CardBody([
            html.H4("Основные статистики", style={'textAlign': 'center'}),
            html.P(f"Количество лотов человека: {unique_human_lot_count}"),
            html.P(f"Средняя стоимость лота человека: {average_human_lot_cost:.2f}"),
            html.P(f"Количество лотов алгоритма: {unique_lot_count}"),
            html.P(f"Средняя стоимость лота алгоритма: {average_lot_cost:.2f}"),
            html.H5(f"Метрики", style={'textAlign': 'center', 'font-size': '18px'}),
            html.P(f"MS Score: {ms:.2f}"),
            MQ_html
        ])
    ], style={'backgroundColor': '#ffe8db'})

    kde_and_total = dbc.Card(
        dbc.CardBody([
            dbc.Row(
                [
                    dbc.Col([kde_plot], width=6),
                    dbc.Col([total_cost_card], width=6),
                ]
            )
        ]), style={'backgroundColor': '#ffe8db'}
    )

    static_plots = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([kde_and_total], width=8),  # style={'height': '500px'}),
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
    ], fluid=True, style={'backgroundColor': '#c9e1ef'})

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
        [Input('lot-id-range-slider', 'value'),
         Input('lot-id-dropdown', 'value')]
    )
    def update_output(selected_range, selected_individuals):
        # Merge selected lot_ids from range and dropdown
        if selected_range:
            range_lots = list(range(int(selected_range[0]), int(selected_range[1]) + 1))
        else:
            range_lots = []
        selected_lots = set(range_lots + (selected_individuals if selected_individuals else []))

        # if not selected_lots:
        #     selected_lots = unique_lot_ids.tolist()

        # Фильтруем данные по выбранным lot_id
        filtered_df = df_for_visual[df_for_visual['lot_id'].isin(selected_lots)]

        # Статистики для таблицы lot_id
        lot_stats = filtered_df.groupby('lot_id').agg(
            средняя_стоимость_позиции=('item_cost', lambda x: round(x.mean(), 2)),
            уникальные_грузополучатели=('receiver_id', 'nunique'),
            уникальные_заказы=('order_id', 'nunique'),
            уникальные_классы=('class_id', 'nunique'),
        ).reset_index()

        # Scatter Plot
        scatter_fig = go.Figure()
        for lot_id in unique_lot_ids:
            subset = filtered_df[filtered_df['lot_id'] == lot_id]
            scatter_fig.add_trace(go.Scattermapbox(
                lat=subset['receiver_address_latitude'],
                lon=subset['receiver_address_longitude'],
                mode='markers',
                name=str(lot_id),
                hoverinfo='text',
                text=subset['receiver_address'],
                marker=dict(size=10, opacity=0.8)
            ))

        # Для поставщиков
        for lot_id in unique_lot_ids:
            subset = filtered_df[filtered_df['lot_id'] == lot_id]
            scatter_fig.add_trace(go.Scattermapbox(
                lat=subset['supplier_address_latitude'],
                lon=subset['supplier_address_longitude'],
                mode='markers',
                name=str(lot_id) + "п",
                hoverinfo='text',
                text=subset['supplier_address'],
                marker=dict(size=10, opacity=0.8)
            ))

        center_lat = filtered_df['receiver_address_latitude'].mean()
        center_lon = filtered_df['receiver_address_longitude'].mean()

        scatter_fig.update_layout(
            mapbox=dict(
                style="open-street-map",  # стиль карты, можно выбрать "carto-positron", "stamen-terrain" и другие
                center=dict(lat=center_lat, lon=center_lon),
                zoom=2  # регулирует степень масштабирования карты
            ),
            margin={"r": 0, "t": 25, "l": 0, "b": 0},
            xaxis_title='Широта',
            yaxis_title='Долгота',
            legend_title='lot_id',
            title={
                'text': "<b>Расположение грузополучателей в соответствии с лотамим</b>",
                'font': {'size': 18},  # Adjust size as needed
                'x': 0.5,  # Center the title
            }

        )

        # Cost Plot
        cost_fig = px.box(filtered_df, x='lot_id', y='item_cost', color='lot_id')
        cost_fig.update_layout(
            xaxis_title='Лот',
            yaxis_title='Цена позиции',
            title={
                'text': "<b>Распределение цен позиций в каждом из лотов</b>",
                'font': {'size': 18},  # Adjust size as needed
                'x': 0.5,  # Center the title
            }
        )

        lot_totals = filtered_df.groupby('lot_id')['item_cost'].sum().reset_index()
        # Создание histogram
        histogram_fig = go.Figure(data=[go.Bar(
            x=lot_totals['lot_id'],
            y=lot_totals['item_cost'],
            marker=dict(color='royalblue')
        )])

        histogram_fig.update_layout(
            title={
                'text': "<b>Суммарная стоимость лота</b>",
                'font': {'size': 18},  # Adjust size as needed
                'x': 0.5,  # Center the title
            },
            xaxis_title='Лот',
            yaxis_title='Стоимость',
            xaxis=dict(tickmode='linear')  # Установка линейного режима для оси X
        )

        return scatter_fig, cost_fig, histogram_fig, lot_stats.to_dict('records'), [{"name": i, "id": i} for i in
                                                                                    lot_stats.columns]

    # Сохраняем всю страницу как HTML
    with open('dashboard.html', 'w') as f:
        f.write(app.index())

    # Запуск приложения
    app.run_server(debug=True)


# Пример использования
def make_dashboard(requests, lots, human_lots, ms, mq=None):
    create_dashboard(merge_tables_for_canvas(requests, lots, human_lots), mq, ms)


# make_dashboard(requests, lots, human_lots, 0.6, 6)
