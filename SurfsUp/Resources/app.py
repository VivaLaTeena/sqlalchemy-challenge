# Dependencies Setup

import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# Database Setup

# Create engine using your 'hawaii.sqlite' database file path
engine = create_engine('sqlite:///path/to/your/hawaii.sqlite')  # Update this path

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to the tables
measurement = Base.classes.measurement
station = Base.classes.station

# Flask Setup

app = Flask(__name__)

# Flask Routes

@app.route("/")
def home():
    print("Server requested climate app home page...")
    return (
        f"Welcome to the Hawaii Climate App!<br/>"
        f"----------------------------------<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date<br/>"
        f"<br>"
        f"Note: Replace 'start_date' and 'end_date' with your query dates. Format for querying is 'YYYY-MM-DD'"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server requested climate app precipitation page...")

    # Create a session from Python to the database
    session = Session(engine)

    # Perform a query to retrieve all the date and precipitation values
    prcp_data = session.query(measurement.date, measurement.prcp).all()

    # Close the session
    session.close()

    # Convert the query results to a dictionary using date as the key and prcp as the value
    prcp_dict = {}
    for date, prcp in prcp_data:
        prcp_dict[date] = prcp

    # Return the JSON representation of your dictionary.
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    print("Server requested climate app station data...")

    # Create a session from Python to the database
    session = Session(engine)

    # Perform a query to retrieve all the station data
    results = session.query(station.id, station.station, station.name).all()

    # Close the session
    session.close()

    # Create a list of dictionaries with station info using a for loop
    list_stations = []

    for st in results:
        station_dict = {}

        station_dict["id"] = st[0]
        station_dict["station"] = st[1]
        station_dict["name"] = st[2]

        list_stations.append(station_dict)

    # Return a JSON list of stations from the dataset
    return jsonify(list_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    print("Server requested climate app temp observation data ...")

    # Create a session from Python to the database
    session = Session(engine)

    # Query the dates and temperature observations of the most active station for the last year of data

    # Identify the most active station
    most_active_station = session.query(measurement.station, func.count(measurement.station)).\
                                        order_by(func.count(measurement.station).desc()).\
                                        group_by(measurement.station).\
                                        first()[0]

    # Identify the last date, convert to datetime and calculate the start date (12 months from the last date)
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    format_str = '%Y-%m-%d'
    last_dt = dt.datetime.strptime(last_date, format_str)
    date_oneyearago = last_dt - dt.timedelta(days=365)

    # Build query for tobs with above conditions
    most_active_tobs = session.query(measurement.date, measurement.tobs).\
                                    filter((measurement.station == most_active_station)\
                                            & (measurement.date >= date_oneyearago)\
                                            & (measurement.date <= last_dt)).all()

    # Close the session
    session.close()

    # Return a JSON list of temperature observations (TOBS) for the previous year
    return jsonify(most_active_tobs)

@app.route("/api/v1.0/<start>")
def temps_from_start(start):
    # Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    # When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.

    print(f"Server requested climate app daily normals from {start}...")

    # Create a function to calculate the daily normals given a certain start date (datetime object in the format "%Y-%m-%d")
    def daily_normals(start_date):

        # Create a session from Python to the database
        session = Session(engine
