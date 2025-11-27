# Telemetry NVIDIA exercise

This is a set of the applications and scripts used as solution for the NVIDIA Telemetry exercise (home task).
Please note, the solution was created using the AI tool (claude.ai).
The solution uses FLASK framework for the web application and SQLite as a database.
The solution consists of the following applications:

- A web application that allows users to submit telemetry data into the database (ingest_server).
- A web application that allows users to query the telemetry data from the database using the defined set of REST APIs (api_server).
- A script to populate the database with sample telemetry data (data_generator.py).
- This README file - instructions on how to run the applications and scripts.

Let's review applications one-by-one.

## Ingest_server
Ingest_server is a Flask web application that provides an endpoint to submit telemetry data into the SQLite database.
On execution start, it is cleaning the database and creating the required set of tables.
There are following tables are used:
* Table 1: metric_definitions

    * id INTEGER PRIMARY KEY,
    * metric_name TEXT,
    * unit TEXT


* Table 2: metric_values 
 
   * id INTEGER PRIMARY KEY,
   * metric_id INTEGER,
   * server_name TEXT,
   * value REAL,
   * timestamp TEXT,
   * FOREIGN KEY (metric_id) REFERENCES metric_definitions(id)

The first table is used to store the metric definitions, while the second table is used to store the actual metric values submitted by users.
Metrics list is updatable, you can add any new metrics whenever you need. To add new metric, you just need to add the metric with new name 
(this way is selected instead of adding an error message on wrong metric names).

### URL and Ports
The ingest_server is running on port 9002; you can use the following URL to access the server: http://127.0.0.1:9002/ingest

### APIs
The following API is implemented in the ingest_server:

* POST /ingest getting the JSON form at data with the following structure:
* data = {'metric_name': <_metric_name_>,'server_name': <_server_name_>, 'value': <_val_>, 'unit': <_unit_>,'timestamp': <_timestamp_>}

* GET /stats - returns statistics on executed session. This API is working with port 9002; The url will be http://127.0.0.1:9002/stats

Example of the request:
{ "metric_name": "cpu_usage", "server_name": "server1", "value": 75.5, "unit": "%", "timestamp": "2025-10-01T12:00:00Z"}



### How to run ingest_server
Just execute the following command in new terminal: python ..\ingest_server\ingest_server.py
(it is assumed that you are in a root directory of the project)
example from  "run_all.cmd": 
* start "Ingest Server" cmd /k python ..\ingest_server\ingest_server.py

## API_server
API_server is a Flask web application that provides a set of REST APIs to query the telemetry data from the SQLite database.
The following APIs are implemented:

* GET /counters - returns a CSV file with all the collected data. This API is working with port 9001; The url will be http://127.0.0.1:9001/counters
* GET /telemetry/ListMetrics?metric=<metric_name> - brings the latest data for specific metric for all servers. This API is working with port 8080; The url will be http://127.0.0.1:8080//telemetry/ListMetrics
* GET /telemetry/GetMetric?metric=<metric_name>&server=<server_name> - brings the latest data for specific metric for specific server. This API is working with port 8080; The url will be http://127.0.0.1:8080//telemetry/GetMetric
* GET /stats - returns statistics on executed session. This API is working with port 8080; The url will be http://127.0.0.1:8080/stats

## Output (CSV) example for /counters command
* server_name,timestamp,bandwidth_mbps,connection_count,cpu_usage_percent,error_count,latency_ms,memory_usage_percent,packet_loss_percent,throughput_gbps
* server-01,2025-11-27T17:53:52.344054,149.7,3654.42,23.25,45.68,2.71,63.32,2.37,6.28
* server-01,2025-11-27T17:54:06.278012,936.52,941.51,33.77,24.47,100.0,62.18,4.91,1.33
* server-02,2025-11-27T17:53:52.344054,453.26,3439.8,68.95,3.72,69.08,58.88,4.11,9.19
* server-02,2025-11-27T17:54:06.278012,302.79,2627.0,11.44,43.62,36.46,76.19,1.58,9.97

### How to run api_server
Just execute the following command in new terminal: python ..\api_server\api_server.py  
(it is assumed that you are in a root directory of the project)
example from  "run_all.cmd":
* start "API Server" cmd /k python ..\api_server\api_server.py

## Data Generator (Simulator)
Data Generator is a Python script that populates the SQLite database with sample telemetry data.

### How to run Data Generator
Just execute the following command in new terminal: python ..\data_generator\data_generator.py
example from  "run_all.cmd":
* start "Data Generator" cmd /k python ..\data_generator\data_generator.py

# Logging
Both applications (ingest_server and api_server) are using logging module to log the events. Logs are printed on terminals
Log can be used for debugging and monitoring purposes.

## Example of Log for api_server:
2025-11-27 17:54:04,494 - api_server - INFO - GetMetric: cpu_usage_percent (0.0009s) <br>
2025-11-27 17:54:04,494 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:04] "GET /telemetry/GetMetric?name=cpu_usage_percent HTTP/1.1" 200 - <br>
2025-11-27 17:54:05,520 - api_server - INFO - GetMetric: error_count (0.0017s)<br>
2025-11-27 17:54:05,521 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:05] "GET /telemetry/GetMetric?name=error_count HTTP/1.1" 200 -<br>
2025-11-27 17:54:06,620 - api_server - INFO - GetMetric: latency_ms (0.0951s)<br>
2025-11-27 17:54:06,621 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:06] "GET /telemetry/GetMetric?name=latency_ms HTTP/1.1" 200 -<br>
2025-11-27 17:54:07,629 - api_server - INFO - GetMetric: memory_usage_percent (0.0012s)<br>
2025-11-27 17:54:07,630 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:07] "GET /telemetry/GetMetric?name=memory_usage_percent HTTP/1.1" 200 -<br>
2025-11-27 17:54:08,738 - api_server - INFO - GetMetric: packet_loss_percent (0.1034s)<br>
2025-11-27 17:54:08,739 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:08] "GET /telemetry/GetMetric?name=packet_loss_percent HTTP/1.1" 200 -<br>
2025-11-27 17:54:09,794 - api_server - INFO - GetMetric: throughput_gbps (0.0481s)<br>
2025-11-27 17:54:09,794 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:09] "GET /telemetry/GetMetric?name=throughput_gbps HTTP/1.1" 200 -<br>
2025-11-27 17:54:10,799 - api_server - INFO - GetMetric: bandwidth_mbps (0.0007s)<br>
2025-11-27 17:54:10,799 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:10] "GET /telemetry/GetMetric?name=bandwidth_mbps HTTP/1.1" 200 -<br>
2025-11-27 17:54:11,822 - api_server - INFO - GetMetric: connection_count (0.0010s)<br>
2025-11-27 17:54:11,823 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:11] "GET /telemetry/GetMetric?name=connection_count HTTP/1.1" 200 -<br>
2025-11-27 17:54:14,832 - api_server - INFO - Counters: server=all (0.0020s)<br>
2025-11-27 17:54:14,832 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:14] "GET /counters HTTP/1.1" 200 -<br>
2025-11-27 17:54:16,840 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:16] "GET /stats HTTP/1.1" 200 -<br>

## Example of log for ingest_server:
2025-11-27 17:54:23,038 - ingest_server - INFO - Ingested: server-01 - cpu_usage_percent = 86.31 (0.0923s)<br>
2025-11-27 17:54:23,038 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,140 - ingest_server - INFO - Ingested: server-01 - memory_usage_percent = 60.1 (0.0842s)<br>
2025-11-27 17:54:23,140 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,223 - ingest_server - INFO - Ingested: server-01 - error_count = 42.98 (0.0802s)<br>
2025-11-27 17:54:23,225 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,323 - ingest_server - INFO - Ingested: server-01 - throughput_gbps = 2.53 (0.0839s)<br>
2025-11-27 17:54:23,324 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,407 - ingest_server - INFO - Ingested: server-01 - connection_count = 3019.21 (0.0798s)<br>
2025-11-27 17:54:23,408 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,506 - ingest_server - INFO - Ingested: server-02 - bandwidth_mbps = 795.31 (0.0815s)<br>
2025-11-27 17:54:23,507 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,598 - ingest_server - INFO - Ingested: server-02 - latency_ms = 44.23 (0.0880s)<br>
2025-11-27 17:54:23,599 - werkzeug - INFO - 127.0.0.1 - - [27/Nov/2025 17:54:23] "POST /ingest HTTP/1.1" 201 -<br>
2025-11-27 17:54:23,732 - ingest_server - INFO - Ingested: server-02 - packet_loss_percent = 3.67 (0.1073s)<br>

# How is it working
System is based on a database. There are two WEB application using REST API, one of which is ingesting the data, the second one ir accessing the data in database; 
The data_generator is a regular application, which is generating the random data and sends it to the ingest_server using REST API.
The ingest_server is receiving the data and storing it into the database.
User can seng GET requests to api_server to retrieve data from the database.

# Application limitation and way to solve them
(Note, the listed limitation are AFTER moving to recommended  WSGI server instead of FLASK debug server)
* The applications are using SQLite as a database, it is not suitable for high-load production environments; 
* As a "database in a file", it is also not compatible with
  * Distributed systems and load balancers
  * Security of the data - SQLite does not provide advanced security features like encryption and access control.
* Scalability - SQLite is not designed to handle large-scale applications with high concurrency and large datasets.
* As a FLASK based WEB application, it inherits the known limitation of FLASK framework, like:
  * Limited scalability - Flask is not designed for high-concurrency applications out of the box.
  * Synchronous request handling - Flask handles requests synchronously, which can lead to performance bottlenecks under heavy load.
  * Limited built-in features - Flask is a micro-framework and does not include many features that are available in larger frameworks like Django.
  * Security concerns - Flask does not provide built-in security features like CSRF protection, authentication, and authorization.
  * Slow data transfers - Flask is not optimized for handling large file uploads or downloads.
* To solve the mentioned limitations, it is recommended to use more advanced database systems like PostgreSQL or MySQL for production environments.
* For WEB applications, it is recommended to use more advanced frameworks like Django or FastAPI, which provide better scalability, security, and performance features.
* It is also possible to use compression for large outputs, like /counters API, to reduce the data transfer size and improve performance.


   