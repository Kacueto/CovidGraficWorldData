from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def fetch_data(query, params=None):
    db_config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',
        'database': 'covid'
    }

    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return results

@app.route('/')
def index():
    return render_template('index.html')

# Grafico 1

@app.route('/grafico1', methods=['GET', 'POST'])
def grafico1():
    graph_url = None

    if request.method == 'POST':
        locations = request.form.getlist('locations')
        end_date = request.form.get('date', '2022-10-30')

        formatted_locations = ', '.join(['%s'] * len(locations))
        query = f"""
        WITH LatestDates AS (
            SELECT location, MAX(date) AS latest_date
            FROM datosnuevos
            WHERE date <= %s AND location IN ({formatted_locations})
            GROUP BY location
        )
        SELECT ld.location, t.total_cases AS total_cases_for_continent
        FROM LatestDates ld
        JOIN datosnuevos t ON ld.location = t.location AND ld.latest_date = t.date
        ORDER BY total_cases_for_continent DESC;
        """
        data = fetch_data(query, (end_date, *locations))

        fig, ax = plt.subplots(figsize=(10, 6))

        bar_colors = ['yellow', 'blue', 'green', 'purple', 'red', 'orange']  # y así sucesivamente

        ax.bar([item['location'] for item in data], [item['total_cases_for_continent'] for item in data], color= bar_colors)
        ax.set_title(f"Total de casos por ubicación hasta {end_date}")
        ax.set_xlabel("Ubicación")
        ax.set_ylabel("Total de Casos")

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode('utf-8')

    return render_template('grafico1.html', graph_url=graph_url)

# Grafico 2

@app.route('/grafico2', methods=['GET', 'POST'])
def grafico2():
    graph2_url = None

    if request.method == 'POST':
        country = request.form.get('country', 'Africa')
        start_date = request.form.get('start_date', '2022-10-01')
        end_date = request.form.get('end_date', '2022-10-30')

        query2 = """
        SELECT 
            date,
            total_deaths
        FROM 
            datosnuevos
        WHERE 
            location = %s
        AND date BETWEEN %s AND %s
        ORDER BY 
            date;
        """

        data2 = fetch_data(query2, (country, start_date, end_date))

        fig2, ax2 = plt.subplots(figsize=(9, 5))
        dates = [item['date'] for item in data2]
        total_deaths = [item['total_deaths'] for item in data2]

        ax2.plot(dates, total_deaths, label='Muertes Totales', color='red')
        ax2.legend(loc='upper left')
        ax2.set_title(f"Muertes en {country} entre {start_date} y {end_date}")
        ax2.set_xlabel("Fecha")
        ax2.set_ylabel("Muertes")

        img2 = io.BytesIO()
        plt.savefig(img2, format='png')
        img2.seek(0)
        graph2_url = base64.b64encode(img2.getvalue()).decode('utf-8')

    return render_template('grafico2.html', graph_url=graph2_url)

# Grafico 3

@app.route('/grafico3', methods=['GET', 'POST'])
def grafico3():
    graph3_url = None

    if request.method == 'POST':
        continent = request.form['continent']
        continent_dates = {
            'Africa': '2023-09-16',
            'Europe': '2023-10-03',
            'Asia': '2023-10-04',
            'North America': '2023-10-09',
            'South America': '2023-10-09',
            'Oceania': '2023-05-09'
        }

        date = continent_dates.get(continent)

        query3 = """
        SELECT 
            population,
            people_fully_vaccinated,
            (population - people_fully_vaccinated) AS difference
        FROM 
            datosnuevos
        WHERE 
            location = %s
            AND DATE = %s
        """
        result = fetch_data(query3, (continent, date))
        data = result[0]  

        labels = ['Vacunados', 'No Vacunados']
        sizes = [data['people_fully_vaccinated'], data['difference']]
        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,colors=['limegreen', 'firebrick'])
        ax.axis('equal')  

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graph3_url = base64.b64encode(img.getvalue()).decode('utf-8')

        return render_template('grafico3.html', graph_url=graph3_url, continent_name=continent, total_population=result[0]['population'])
    return render_template('grafico3.html')

# Grafico 4

@app.route('/grafico4', methods=['GET'])
def grafico4():
    graph4_url = None

    query4 = """
    SELECT 
        location,
        AVG(life_expectancy) AS avg_life_expectancy,
        AVG(hospital_beds_per_thousand) AS avg_beds_per_thousand
    FROM
        datosnuevos
    WHERE
        hospital_beds_per_thousand <> 0
    GROUP BY
        location;
    """
    
    data4 = fetch_data(query4) 

    fig4, ax4 = plt.subplots(figsize=(10, 6))

    continents = [item['location'] for item in data4]
    life_expectancies = [item['avg_life_expectancy'] for item in data4]
    beds_per_thousand = [item['avg_beds_per_thousand'] for item in data4]

    ax4.scatter(life_expectancies, beds_per_thousand, color='blue')

    ax4.set_title("Expectativa de vida vs. Camas de hospital por cada mil habitantes")
    ax4.set_xlabel("Expectativa de vida promedio")
    ax4.set_ylabel("Camas de hospital por cada mil habitantes")

    img4 = io.BytesIO()
    plt.savefig(img4, format='png')
    img4.seek(0)
    graph4_url = base64.b64encode(img4.getvalue()).decode('utf-8')

    return render_template('grafico4.html', graph_url=graph4_url)


if __name__ == '__main__':
    app.run()

