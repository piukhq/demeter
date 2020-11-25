import socket
import time
import uuid
import io
import os
import platform
from typing import BinaryIO, Union

import pytest
import paramiko
import docker


@pytest.fixture(scope="session")
def docker_client():
    return docker.from_env(assert_hostname=False).api


@pytest.fixture(scope="session")
def unused_port():
    def f():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    return f


@pytest.fixture(scope="module")
def sftp_server(unused_port, docker_client):
    print("\nSTARTUP CONTAINER\n")

    # bound IPs do not work on OSX
    host = "127.0.0.1"
    host_port = unused_port()
    name = "amex-sftp-{}".format(uuid.uuid4().hex)

    if platform.system() == "Darwin":
        os.system(f"docker run --name {name} -d -p {host_port}:22 atmoz/sftp user:pass:::sent,inbox,outbox")
    else:
        container_args = dict(
            image="atmoz/sftp",
            name=name,
            ports=[22],
            detach=True,
            host_config=docker_client.create_host_config(port_bindings={22: (host, host_port)},),
            command="user:pass:::sent,inbox,outbox",
        )

        container = docker_client.create_container(**container_args)
        docker_client.containers.create(**container_args)

    try:
        if platform.system() != "Darwin":
            docker_client.start(container=container["Id"])

        server_params = {
            "host": host,
            "port": host_port,
            "user": "user",
            "password": "pass",
            "env": {"AMEX_SERVER": host, "AMEX_PORT": host_port, "AMEX_USER": "user", "AMEX_PASSWORD": "pass"},
        }
        delay = 0.001
        for i in range(100):
            try:
                # Open a transport
                transport = paramiko.Transport((host, host_port))
                transport.connect(None, server_params["user"], server_params["password"])
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.listdir()

                server_params["sftp"] = sftp
                break
            except Exception:
                time.sleep(delay)
                delay *= 2
        else:
            pytest.fail("Cannot start SFTP server")

        yield server_params

    finally:
        print("\nTEARDOWN CONTAINER\n")

        if platform.system() == "Darwin":
            os.system(f"docker stop {name}")
        else:
            docker_client.kill(container=container["Id"])
            docker_client.remove_container(container["Id"])


@pytest.fixture
def upload_file(sftp_server):
    def _f(path: str, content: Union[str, bytes, BinaryIO]):
        if isinstance(content, str):
            content = content.encode()
        if isinstance(content, bytes):
            content = io.BytesIO(content)

        content.seek(0)
        sftp_server["sftp"].putfo(content, path)

    return _f


@pytest.fixture
def download_file(sftp_server):
    def _f(path: str):
        content = io.BytesIO()
        sftp_server["sftp"].getfo(path, content)
        content.seek(0)
        return content.read()

    return _f


@pytest.fixture
def list_dir(sftp_server):
    def _f(path: str):
        return sftp_server["sftp"].listdir(path)

    return _f
