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
---------------------------------------------------------------------------------

@app.route('/simulated_terminal/<tag>')
def simulated_terminal(tag):
    return render_template('terminal.html', tag=tag)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_ssh')
def start_ssh(data):
    tag = data['tag']
    ip, ip2, ip3, username, password = get_ssh_credentials(tag)

    for ip_address in [ip, ip2, ip3]:
        try:
            if platform.system().lower() == 'windows':
                # For Windows, use plink for SSH connections
                cmd_command = f'plink -ssh -l {username} -pw {password} -load plink_config.txt {ip_address}'
                subprocess.run(['start', 'cmd', '/K', cmd_command], shell=True, check=True)
            else:
                # For Ubuntu or other platforms, use paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip_address, username=username, password=password)
                ssh.close()

            socketio.emit('ssh_connected', {'tag': tag}, namespace='/terminal')
            return

        except paramiko.AuthenticationException:
            print(f"Failed to connect to {ip_address} with username {username} and password {password}. Authentication failed.")
        except paramiko.SSHException as e:
            print(f"Failed to connect to {ip_address}. {str(e)}")
        except Exception as e:
            print(f"Error connecting to {ip_address}: {str(e)}")

    print(f"Unable to establish an SSH connection for tag {tag}")
    socketio.emit('ssh_failed', {'tag': tag}, namespace='/terminal')
    
    def get_ssh_credentials(tag):
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



-------------------------------------------------------




terminal


<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css" />
</head>
<body>
  <div id="terminal"></div>
  <input id="commandInput" type="text" placeholder="Enter a command" />
  <button onclick="sendCommand()">Send Command</button>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.1.2/socket.io.js"></script>

  <script>
    const socket = io('/terminal');
    const term = new Terminal();
    const tag = '{{ tag }}';

    term.open(document.getElementById('terminal'));
    term.write('Welcome to \x1B[1;3;31mSSH Terminal\x1B[0m\n$ ');

    socket.on('connect', () => {
      console.log('Connected to server');
      startSSH();
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    socket.on('ssh_connected', (data) => {
      console.log(`SSH connection established for tag: ${data.tag}`);
      term.write(`SSH connection established for tag: ${data.tag}\n$ `);
    });

    socket.on('ssh_failed', (data) => {
      console.log(`SSH connection failed for tag: ${data.tag}`);
      term.write(`SSH connection failed for tag: ${data.tag}\n$ `);
    });

    socket.on('command_output', (data) => {
      console.log(`Command output received: ${data.output}`);
      term.write(data.output);
    });

    function startSSH() {
      console.log("Calling SSH");
      socket.emit('start_ssh', { tag });
    }

    function sendCommand() {
      const commandInput = document.getElementById('commandInput');
      const command = commandInput.value;
      term.write(`\n$ ${command} \n`); // Display the entered command in the terminal
      socket.emit('send_command', { tag, command });
      commandInput.value = ''; // Clear the input field after sending the command
    }
  </script>
</body>
</html>
