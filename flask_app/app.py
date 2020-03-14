from flask import Flask, render_template, request
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
from bokeh.embed import components

app = Flask(__name__)


def plot_data(_country):
    confirmed_raw_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                        "/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv "
    deaths_raw_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                     "/csse_covid_19_time_series/time_series_19-covid-Deaths.csv "
    recovered_raw_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                        "/csse_covid_19_time_series/time_series_19-covid-Recovered.csv "

    confirmed_df_raw = pd.read_csv(confirmed_raw_url)
    deaths_df_raw = pd.read_csv(deaths_raw_url)
    recovered_df_raw = pd.read_csv(recovered_raw_url)

    latest_date = confirmed_df_raw.columns[-1]

    confirmed_df_raw = confirmed_df_raw.drop(['Province/State', 'Lat', 'Long'], axis=1)
    total_confirmed = confirmed_df_raw.groupby('Country/Region', as_index=False).agg(sum).sort_values(latest_date,
                                                                                                      ascending=False)
    total_confirmed = pd.melt(total_confirmed, id_vars='Country/Region', var_name='Dates', value_name='Confirmed')
    total_confirmed['Dates'] = pd.to_datetime(total_confirmed['Dates'])

    deaths_df_raw = deaths_df_raw.drop(['Province/State', 'Lat', 'Long'], axis=1)
    total_deaths = deaths_df_raw.groupby('Country/Region', as_index=False).agg(sum).sort_values(latest_date,
                                                                                                ascending=False)
    total_deaths = pd.melt(total_deaths, id_vars='Country/Region', var_name='Dates', value_name='Deaths')
    total_deaths['Dates'] = pd.to_datetime(total_deaths['Dates'])

    recovered_df_raw = recovered_df_raw.drop(['Province/State', 'Lat', 'Long'], axis=1)
    total_recovered = recovered_df_raw.groupby('Country/Region', as_index=False).agg(sum).sort_values(latest_date,
                                                                                                      ascending=False)
    total_recovered = pd.melt(total_recovered, id_vars='Country/Region', var_name='Dates', value_name='Recovered')
    total_recovered['Dates'] = pd.to_datetime(total_recovered['Dates'])

    country_names = total_recovered['Country/Region'].unique()

    mask_confirmed = total_confirmed['Country/Region'] == _country
    mask_death = total_deaths['Country/Region'] == _country
    mask_recovered = total_recovered['Country/Region'] == _country

    _confirmed = total_confirmed[mask_confirmed].reset_index()
    _deaths = total_deaths[mask_death].reset_index()
    _recovered = total_recovered[mask_recovered].reset_index()

    _confirmed['Deaths'] = _deaths['Deaths']
    _confirmed['Recovered'] = _recovered['Recovered']

    _confirmed['Active'] = _confirmed['Confirmed'] - _confirmed['Deaths'] - _confirmed['Recovered']
    _active = ColumnDataSource(_confirmed)
    _confirmed = ColumnDataSource(_confirmed)

    p = figure(title="All Cases", x_axis_label='Date', y_axis_label='Count',
               x_axis_type='datetime', plot_width=600, plot_height=400)
    p.line(x='Dates', y='Confirmed', source=_confirmed, color='black', line_width=3, legend="Confirmed Cases")
    p.line(x='Dates', y='Deaths', source=_confirmed, color='red', line_width=3, legend="Confirmed Deaths")
    p.line(x='Dates', y='Recovered', source=_confirmed, color='green', line_width=3, legend="Recoveries")

    hover = HoverTool()
    hover.tooltips = [('Confirmed', '@Confirmed'), ('Deaths', '@Deaths'), ('Recoveries', '@Recovered')]

    p.add_tools(hover)
    p.legend.location = 'top_left'

    p.toolbar.logo = None
    p.toolbar_location = None

    p1 = figure(title="Active Cases", x_axis_label='Date', y_axis_label='Active Cases',
                x_axis_type='datetime', plot_width=600, plot_height=400)
    p1.line(x='Dates', y='Active', source=_active, color='black', line_width=3)

    hover1 = HoverTool()
    hover1.tooltips = [('Active Cases', '@Active')]

    p1.add_tools(hover1)

    p1.toolbar.logo = None
    p1.toolbar_location = None

    return p, p1, country_names


@app.route('/')
def index():
    # Determine the selected country
    current_country_name = request.args.get("country_names")
    if current_country_name is None:
        current_country_name = "China"

    # Create the plot
    plot, plot1, name = plot_data(current_country_name)

    # Embed plot into HTML via Flask Render
    script, div = components(plot)
    script1, div1 = components(plot1)
    return render_template("index.html", script_plot=script, div_plot=div,
                           script_active_plot=script1, div_active_plot=div1,
                           country_names=name, current_country_name=current_country_name)


if __name__ == '__main__':
    app.run()
