from asyncio.windows_events import NULL
import time
from flask import Flask, render_template, request, redirect, url_for , jsonify,flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import subprocess, platform
import paramiko
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import mysql.connector
import json
from croniter import croniter

import requests

import webbrowser

app = Flask(__name__, template_folder='template')
CORS(app)
socketio = SocketIO(app)

# Configuration for the first and second databases
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@192.168.109.137:3306/DEVICE_TRACKER'
app.config['SQLALCHEMY_BINDS'] = {
    'device_info': 'mysql+mysqlconnector://root:password@192.168.109.137:3306/DEVICE_INFO',
    'auth_db': 'mysql+mysqlconnector://root:password@192.168.109.137:3306/AUTHENTICATION'
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'


# Create a single instance of SQLAlchemy for both databases
db = SQLAlchemy(app)


login_manager = LoginManager(app)
login_manager.login_view = 'logins'




class User(db.Model, UserMixin):
    __bind_key__ = 'auth_db'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True , autoincrement=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    tags = db.Column(db.String(200), nullable=False)
    mac = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(17))
    password = db.Column(db.String(50))

# Additional model for the second database
class DeviceInfo(db.Model):
    __bind_key__ = 'device_info'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), unique=True, nullable=False)
    status = db.Column(db.String(20))
    tags = db.Column(db.String(20), nullable=False)

# Creation of the database tables within the application context.
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or None

@app.route('/logins', methods=['GET', 'POST'])
def logins():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            login_user(user)
            return redirect(url_for('index'))

    return render_template('logins.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('logins'))

@app.route('/')
@login_required
def index():
    try:
        # Read status data from the text file
        with open('data1.txt', 'r') as json_file:
            data = json.load(json_file)

        # Fetch all fields data
        fields_data = Field.query.all()
        up_devices_count = 0
        down_devices_count = 0

        # Update the status of each tag based on the IP addresses in data1.txt
        for field in fields_data:
            tag = field.tags
            if tag in data:
                tag_data = data[tag]
                if any(status == 'UP' for status in tag_data.values()):
                    field.status = 'UP'
                    up_devices_count += 1
                elif any(status == 'DOWN' for status in tag_data.values()):
                    field.status = 'DOWN'
                    down_devices_count += 1
                else:
                    field.status = 'UNRECOGNIZED'

        # Commit the changes to the database
        db.session.commit()

        # Fetch all fields data again after the update
        fields_data = Field.query.all()

        # Calculate counts
        count_tags = len(fields_data)
        count_devices = len(fields_data)
        up_devices_percentage = up_devices_count/count_devices
        down_devices_percentage = down_devices_count/count_devices

        return render_template('dash.html', fields_data=fields_data, count_tags=count_tags,
                               count_devices=count_devices, up_devices_count=up_devices_count,
                               down_devices_count=down_devices_count,up_devices_percentage=up_devices_percentage,
                               down_devices_percentage=down_devices_percentage)
    except Exception as e:
        return f"Error: {str(e)}"

# Route to handle adding a new field to the UI and the first database
@app.route('/add_fields', methods=['POST'])
def add_fields():
    ip_address = request.form.get('ip')
    tags_data = request.form.get('tags')
    mac = request.form.get('mac')
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        new_field = Field(ip=ip_address, tags=tags_data, mac=mac, username=username, password=password)

        # Add the new field to the first database
        db.session.add(new_field)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Duplicate MAC address'})

    # Redirect to the index route after successfully adding a new field
    return redirect(url_for('index'))

@app.route('/import')
def import_file():
    return render_template('import_file.html')

'''@app.route('/connect_page', methods=['POST'])
def connect_page():
    # Get tag from the form data
    tag='sample'

    # Sample data
    status = 'UP'
    ip1 = '192.168.107.20'
    ip2 = '192.168.109.20'
    ip3 = '192.168.244.20'

    # Pass data to the template as needed
    device_status = {
        tag: {
            'status': status
        }
    }

    device_interface = {
        tag: {
            'lan_ip': ip2,
            'wan_ip': ip1,
            'sec_ip': ip3
        }

    }
    device_interface_status = {
        tag: {
            'ip2': status,
            'ip1': status,
            'ip3': status
        }

    }
    # If not used, remove this dictionary
    device_layer_info = {}

    return render_template('connect_page.html', device_status=device_status, device_interface=device_interface,
                           device_layer_info=device_layer_info ,device_interface_status=device_interface_status) '''

@app.route('/receive_data', methods=['POST'])
def receive_data():
    try:
        data1 = request.json.get('ping_status')
        data2 = request.json.get('interface_status')
        data3 = request.json.get('layer_info')

        # Convert JSON strings to Python dictionaries
        data1 = json.loads(data1)
        data2 = json.loads(data2)
        data3 = json.loads(data3)

        # Write data to three different files
        write_to_file('data1.txt', data1)
        write_to_file('data2.txt', data2)
        write_to_file('data3.txt', data3)

        return "Data received and written to files successfully"
    except Exception as e:
        return f"Error: {str(e)}"


def write_to_file(filename, data):
    try:
        with open(filename, 'w') as file:
            # Write data to the file in insert mode
            file.write(json.dumps(data, indent=2))
            file.write('\n')  # Add a newline for better readability
    except Exception as e:
        print(f"Error writing to {filename}: {str(e)}")


@app.route('/connect_page/<tag>', methods=['GET', 'POST'])
def connect_page(tag):
    if request.method == 'GET':
        result_of_status = {}
        try:
            device_tag = session.get('device_tag')
            with open('data1.txt', 'r') as file:
                data1 = json.load(file)               
            with open('data2.txt', 'r') as file:
                data2 = json.load(file)
            with open('data3.txt', 'r') as file:
                data3 = json.load(file)

            return render_template('connect_page.html',tag=tag, data1=data1[tag],data2=data2[tag],data3=data3[tag])
        except Exception as e:
            return f"Error: {str(e)}"
    elif request.method == 'POST':
        session['device_tag'] = tag
        return jsonify(result="Success", reload=True)
                
@app.route('/refresh', methods=['GET'])
def refresh():
    return redirect(url_for('index'))

# Handle SSH
@app.route('/simulated_terminal/<tag>')
def simulated_terminal(tag):
    Base = declarative_base()
    class Field(Base):
        __tablename__ = 'field'
        id = Column(Integer, primary_key=True)
        tags = Column(String)
        ip = Column(String)
        ip2 = Column(String)
        ip3 = Column(String)
        username = Column(String)
        password = Column(String)
    def sql_connect():
        host = '192.168.109.137'
        port = 3306
        user = "root"
        password = "password"
        database = "DEVICE_TRACKER"
        connection = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
        )
        return connection
    def get_ssh_credentials():
        connection = sql_connect()
        cursor = connection.cursor()

        try:
            # Retrieve IP, username, and password from the 'field' table
            cursor.execute(r"SELECT ip, ip2, ip3, username, password FROM field WHERE tags = %s", (tag,))
            result = cursor.fetchone()

            return result if result else (None, None, None, None, None)
        finally:
            cursor.close()
            connection.close()
    ip, ip2, ip3, username, password = get_ssh_credentials()

    for ip in [ip, ip2, ip3]:
        try:
            if platform.system().lower() == 'windows':
                # For Windows, use plink for SSH connections
                cmd_command = f'plink   -ssh -l {username} -pw {password} -load plink_config.txt {ip}'
                subprocess.run(['start', 'cmd', '/K', cmd_command], shell=True, check=True)
            else:
                # For Ubuntu or other platforms, use paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=username, password=password)
                ssh.close()

            return redirect(url_for('connect_page', tag=tag))

        except paramiko.AuthenticationException:
            print(f"Failed to connect to {ip} with username {username} and password {password}. Authentication failed.")
        except paramiko.SSHException as e:
            print(f"Failed to connect to {ip}. {str(e)}")
        except Exception as e:
            print(f"Error connecting to {ip}: {str(e)}")

    print(f"Unable to establish an SSH connection for tag {tag}")
    return "Unable to establish an SSH connection", 500

@app.route('/calculate_interval', methods=['POST'])
def calculate_interval():
    try:
        data = request.get_json()
        cron_expression = data.get('cronExpression', '')
        print(cron_expression)
        if(cron_expression=='0 0 0 0 0'):
            return jsonify({'interval': 'NaN'})
        now = time.time()
        next_occurrence = croniter(cron_expression, now).get_next()
        interval = next_occurrence - now
        print("Enterval time is ",interval)
        return jsonify({'interval': interval})
    except Exception as e:
        print(f"Failed to convert to interval {e}")
        return None
        
        
        


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
