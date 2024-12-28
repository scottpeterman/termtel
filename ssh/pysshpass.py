import sys
import paramiko
import click
from queue import Queue, Empty
import threading
import time
import os


def ssh_client(host, user, password, cmds, invoke_shell, prompt, prompt_count, timeout, disable_auto_add_policy, look_for_keys, inter_command_time, connect_only=False):
    """
    SSH Client for running remote commands.

    Sample Usage:
    pysshpass -h "172.16.1.101" -u "cisco" -p "cisco" -c "term len 0,show users,show run,show cdp neigh,show int desc" --invoke-shell --prompt "#" --prompt-count 4 -t 360
    """
    # Set log file path
    # log_file = os.path.join('../log', f'{host}.log')
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'log'))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'{host}.log')

    # Initialize SSH client
    client = paramiko.SSHClient()

    # Set host key policy based on user input
    if disable_auto_add_policy:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Modify the transport defaults for key exchange algorithms, ciphers, and host key algorithms
    paramiko.Transport._preferred_kex = (
        "diffie-hellman-group14-sha1",
        "diffie-hellman-group-exchange-sha1",
        "diffie-hellman-group-exchange-sha256",
        "diffie-hellman-group1-sha1",
        "ecdh-sha2-nistp256",
        "ecdh-sha2-nistp384",
        "ecdh-sha2-nistp521",
        "curve25519-sha256",
        "curve25519-sha256@libssh.org",
        "diffie-hellman-group16-sha512",
        "diffie-hellman-group18-sha512"
    )
    paramiko.Transport._preferred_ciphers = (
        "aes128-cbc",
        "aes128-ctr",
        "aes192-ctr",
        "aes256-ctr",
        "aes256-cbc",
        "3des-cbc",
        "aes192-cbc",
        "aes256-gcm@openssh.com",
        "aes128-gcm@openssh.com",
        "chacha20-poly1305@openssh.com",
        "aes256-gcm",
        "aes128-gcm"
    )
    paramiko.Transport._preferred_keys = (
        "ssh-rsa",
        "ssh-dss",
        "ecdsa-sha2-nistp256",
        "ecdsa-sha2-nistp384",
        "ecdsa-sha2-nistp521",
        "ssh-ed25519",
        "rsa-sha2-256",
        "rsa-sha2-512"
    )

    try:
        # Connect to the SSH server
        client.connect(
            hostname=host,
            username=user,
            password=password,
            look_for_keys=look_for_keys,
            timeout=timeout,
            allow_agent=False  # Ensure we don't use any other key authentication mechanisms
        )
        connect_msg = f"Connected to {host} using the specified algorithms.\n"
        print(connect_msg)
        if connect_only:
            return client
        with open(log_file, 'a') as f:
            f.write(connect_msg)
            f.flush()
    except paramiko.AuthenticationException:
        error_msg = "Authentication failed, please verify your credentials.\n"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(error_msg)
            f.flush()
        sys.exit(1)
    except paramiko.SSHException as e:
        error_msg = f"Could not establish SSH connection: {str(e)}\n"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(error_msg)
            f.flush()
        raise ValueError(f"Paramiko: {e}")
    except Exception as e:
        error_msg = f"Unhandled exception: {str(e)}\n"
        print(error_msg)
        with open(log_file, 'a') as f:
            f.write(error_msg)
            f.flush()
        raise ValueError(f"Unexpected Error: {e}")

    def execute_command_in_shell(channel, command, inter_command_time):
        command = command.replace('"', '')
        cmd_msg = f"Executing command: {command}\n"
        print(cmd_msg)
        with open(log_file, 'a') as f:
            f.write(cmd_msg)
            f.flush()
        channel.send(command + '\n')
        time.sleep(inter_command_time)  # Waiting between commands

    def execute_direct_command(command, timeout):
        stdin, stdout, stderr = client.exec_command(command)
        start_time = time.time()
        output = ""
        with open(log_file, 'a') as f:
            while True:
                if stdout.channel.recv_ready():
                    output_chunk = stdout.channel.recv(4096).decode('utf-8')
                    print(output_chunk, end='')
                    f.write(output_chunk)
                    f.flush()
                    output += output_chunk
                    start_time = time.time()  # Reset the timeout counter on data reception
                if time.time() - start_time > timeout:
                    timeout_msg = "\nCommand timed out.\n"
                    print(timeout_msg)
                    f.write(timeout_msg)
                    f.flush()
                    break
        return output

    output = ""

    # Execute the SSH command in shell mode or directly
    if invoke_shell:
        try:
            channel = client.invoke_shell()
        except Exception as e:
            error_msg = f"Failed to invoke shell: {str(e)}\n"
            print(error_msg)
            with open(log_file, 'a') as f:
                f.write(error_msg)
                f.flush()
            raise ValueError(f"Unexpected Error: {e}")

        output_queue = Queue()
        read_thread = threading.Thread(target=read_output, args=(channel, output_queue, prompt, prompt_count, log_file))
        read_thread.daemon = True
        read_thread.start()

        command_list = [cmd.strip() for cmd in cmds.split(',') if cmd.strip()]
        for cmd in command_list:
            execute_command_in_shell(channel, cmd, inter_command_time)

        try:
            output = output_queue.get(timeout=timeout)
            exit_msg = f"\nExiting: Prompt detected.\n"
            print(exit_msg)
            with open(log_file, 'a') as f:
                f.write(exit_msg)
                f.flush()
        except Empty:
            timeout_msg = "\nExiting due to timeout.\n"
            print(timeout_msg)
            with open(log_file, 'a') as f:
                f.write(timeout_msg)
                f.flush()
            # sys.exit()

        channel.close()
        return
    else:
        command_list = [cmd.strip() for cmd in cmds.split(',') if cmd.strip()]
        for cmd in command_list:
            output += execute_direct_command(cmd, timeout)

            client.close()
        return output

def read_output(channel, output_queue, prompt, prompt_count, log_file):
    counter = 0
    output = ""
    with open(log_file, 'a') as f:
        while True:
            if channel.recv_ready():
                # Receive the chunk and decode it to UTF-8
                output_chunk = channel.recv(4096).decode('utf-8').replace('\r', '')
                print(output_chunk, end='')
                f.write(output_chunk)
                f.flush()
                output += output_chunk

                # Split the chunk into lines to scan for prompt
                lines = output_chunk.split("\n")

                # Loop through lines to look for the prompt
                for line in lines:
                    if (prompt in line) and ("-" in line):
                        counter += 1
                        if counter >= prompt_count:
                            # Stop reading if the prompt appears a specified number of times
                            output_queue.put(output)
                            return

            # Check if the channel is closed
            if channel.closed:
                output_queue.put(output)
                return
