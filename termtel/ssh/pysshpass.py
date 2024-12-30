import sys
import paramiko
import click
from queue import Queue, Empty
import threading
import time
import os
import logging
from pathlib import Path


def setup_logging(host):
    """Configure logging with fallback to current directory"""
    try:
        # Try to create log directory relative to script location
        log_dir = Path(__file__).parent.parent / 'log'
    except NameError:
        # Fallback to current working directory if __file__ is not available (e.g., in wheel)
        log_dir = Path.cwd() / 'log'

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f'{host}.log'

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def ssh_client(host, user, password, cmds, invoke_shell, prompt, prompt_count, timeout,
               disable_auto_add_policy, look_for_keys, inter_command_time, connect_only=False):
    """SSH Client for running remote commands."""
    logger = setup_logging(host)

    client = paramiko.SSHClient()
    if disable_auto_add_policy:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Keep existing SSH configuration code...

    try:
        client.connect(
            hostname=host,
            username=user,
            password=password,
            look_for_keys=look_for_keys,
            timeout=timeout,
            allow_agent=False
        )
        logger.info(f"Connected to {host} using the specified algorithms.")
        if connect_only:
            return client
    except paramiko.AuthenticationException:
        logger.error("Authentication failed, please verify your credentials.")
        sys.exit(1)
    except paramiko.SSHException as e:
        logger.error(f"Could not establish SSH connection: {str(e)}")
        raise ValueError(f"Paramiko: {e}")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        raise ValueError(f"Unexpected Error: {e}")

    def execute_command_in_shell(channel, command):
        command = command.replace('"', '')
        logger.info(f"Executing command: {command}")
        channel.send(command + '\n')
        time.sleep(inter_command_time)

    def execute_direct_command(command, timeout):
        stdin, stdout, stderr = client.exec_command(command)
        start_time = time.time()
        output = ""
        while True:
            if stdout.channel.recv_ready():
                output_chunk = stdout.channel.recv(4096).decode('utf-8')
                logger.info(output_chunk.rstrip())
                output += output_chunk
                start_time = time.time()
            if time.time() - start_time > timeout:
                logger.info("Command timed out.")
                break
        return output

    if invoke_shell:
        try:
            channel = client.invoke_shell()
        except Exception as e:
            logger.error(f"Failed to invoke shell: {str(e)}")
            raise ValueError(f"Unexpected Error: {e}")

        output_queue = Queue()
        read_thread = threading.Thread(
            target=read_output,
            args=(channel, output_queue, prompt, prompt_count, logger)
        )
        read_thread.daemon = True
        read_thread.start()

        for cmd in [cmd.strip() for cmd in cmds.split(',') if cmd.strip()]:
            execute_command_in_shell(channel, cmd)

        try:
            output = output_queue.get(timeout=timeout)
            logger.info("\nExiting: Prompt detected.")
        except Empty:
            logger.info("\nExiting due to timeout.")

        channel.close()
        return
    else:
        output = ""
        for cmd in [cmd.strip() for cmd in cmds.split(',') if cmd.strip()]:
            output += execute_direct_command(cmd, timeout)

        client.close()
        return output


def read_output(channel, output_queue, prompt, prompt_count, logger):
    counter = 0
    output = ""
    while True:
        if channel.recv_ready():
            output_chunk = channel.recv(4096).decode('utf-8').replace('\r', '')
            logger.info(output_chunk.rstrip())
            output += output_chunk

            for line in output_chunk.split("\n"):
                if (prompt in line) and ("-" in line):
                    counter += 1
                    if counter >= prompt_count:
                        output_queue.put(output)
                        return

        if channel.closed:
            output_queue.put(output)
            return