# ssh_manager.py
import paramiko
import asyncio
import base64

class SSHClientManager:
    def __init__(self):
        self.clients = {}

    async def create_client(self, tab_id):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.clients[tab_id] = {'client': ssh_client, 'channel': None}

    async def connect(self, tab_id, hostname, port, username, password, websocket):
        ssh_client = self.clients[tab_id]['client']
        try:
            transport = paramiko.Transport((hostname, int(port)))
            transport.set_keepalive(60)
            transport.connect(username=username, password=password)
            ssh_client._transport = transport
            channel = ssh_client.invoke_shell(term="xterm")
            self.clients[tab_id]['channel'] = channel
        except paramiko.SSHException as e:
            await self.handle_ssh_error(tab_id, hostname, e, websocket)
        except Exception as e:
            print(f"SSH Server error: {e}")

    async def handle_ssh_error(self, tab_id, hostname, error, websocket):
        error_message = f"SSH connection error to {hostname}: {error}"
        encoded_data = base64.b64encode(error_message.encode('utf-8')).decode('utf-8')
        await websocket.send_json({'type': 'ssh_output', 'data': encoded_data, 'tabId': tab_id})

    async def send_input(self, tab_id, input_data):
        channel = self.clients[tab_id]['channel']
        if channel:
            channel.send(input_data)

    async def resize_terminal(self, tab_id, cols, rows):
        channel = self.clients[tab_id]['channel']
        if channel:
            channel.resize_pty(width=cols, height=rows)

    async def disconnect(self, tab_id):
        client_data = self.clients.pop(tab_id, None)
        if client_data:
            channel = client_data['channel']
            client = client_data['client']
            if channel:
                channel.close()
            client.close()

    async def listen_to_ssh_output(self, tab_id, websocket):
        while True:
            await asyncio.sleep(0.1)
            channel = self.clients[tab_id]['channel']
            if channel and channel.recv_ready():
                data = channel.recv(1024)
                encoded_data = base64.b64encode(data).decode('utf-8')
                await websocket.send_json({'type': 'ssh_output', 'data': encoded_data, 'tabId': tab_id})
