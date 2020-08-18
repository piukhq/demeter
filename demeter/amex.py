import argparse
import io
import logging
import os
import re
from typing import Dict, Type, cast

import paramiko
import pylogrus
from azure.storage.blob import BlobServiceClient
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.blocking import BlockingScheduler


logging.setLoggerClass(pylogrus.PyLogrus)
logger = cast(pylogrus.PyLogrus, logging.getLogger("demeter.amex"))

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

AMEX_TRANSACTION_FILE = re.compile(r"AXP_CHINGS_TLOG_.+")
AMEX_MID_OUTPUT_FILE = re.compile(r"CHINGS_AXP_MER_REG_RESP_.+")
AMEX_MID_INPUT_FILE = re.compile(r"CHINGS_AXP_MER_REG_\d.+")


def fmt_pw(password: str) -> str:
    return password[0] + ("*" * 7)


def create_sftp_client(host: str, port: int, username: str, password: str, local_logger=logger) -> paramiko.SFTPClient:
    # if keyfilepath is not None:
    #     # Get private key used to authenticate user.
    #     if keyfiletype == 'DSA':
    #         # The private key is a DSA type key.
    #         key = paramiko.DSSKey.from_private_key_file(keyfilepath)
    #     else:
    #         # The private key is a RSA type key.
    #         key = paramiko.RSAKey.from_private_key(keyfilepath)

    # Create Transport object using supplied method of authentication.

    transport = paramiko.Transport((host, port))
    local_logger.withPrefix("SFTP").info(f"Connecting to {host}:{port}")
    transport.connect(username=username, password=password)

    return paramiko.SFTPClient.from_transport(transport)


def run_download(env: Dict[str, str] = os.environ, client_class: Type[BlobServiceClient] = BlobServiceClient) -> None:
    local_logger = logger.withFields({"task": "download"})
    # Technically shouldn't use mutable default arg but
    # we're not modifying it
    amex_server = env["AMEX_SERVER"]
    amex_port = int(env.get("AMEX_PORT", "22"))
    amex_user = env["AMEX_USER"]
    amex_password = env["AMEX_PASSWORD"]

    transaction_storage_account = env["TX_BLOB_STORAGE_ACCOUNT"]
    transaction_storage_token = env["TX_BLOB_STORAGE_TOKEN"]
    transaction_storage_container = env["TX_BLOB_STORAGE_CONTAINER"]

    mid_storage_account = env["MID_BLOB_STORAGE_ACCOUNT"]
    mid_storage_token = env["MID_BLOB_STORAGE_TOKEN"]
    mid_storage_container = env["MID_BLOB_STORAGE_CONTAINER"]

    local_logger.info(f"Amex: sftp://{amex_user}:{fmt_pw(amex_password)}@{amex_server}:{amex_port}")
    local_logger.info(f"TX Storage {transaction_storage_account}:{fmt_pw(transaction_storage_token)}")
    local_logger.info(f"MID Storage {mid_storage_account}:{fmt_pw(mid_storage_token)}")

    try:
        amex_sftp = create_sftp_client(amex_server, amex_port, amex_user, amex_password, local_logger)
    except Exception as err:
        logger.exception("Failed to setup SFTP connection", exc_info=err)
        return

    transaction_client = client_class(account_url=transaction_storage_account, credential=transaction_storage_token)
    mid_client = client_class(account_url=mid_storage_account, credential=mid_storage_token)

    for file in amex_sftp.listdir("./outbox/"):
        full_path = os.path.join("./outbox", file)
        if AMEX_TRANSACTION_FILE.match(file):
            local_logger.info(f"Matched transaction {file}, uploading to blob storage")
            blob = transaction_client.get_blob_client(
                container=transaction_storage_container, blob=f"payment/amex/{file}"
            )

            blob_data = io.BytesIO()
            amex_sftp.getfo(full_path, blob_data)
            blob_data.seek(0)
            blob.upload_blob(blob_data, overwrite=True)
            local_logger.info("Uploaded to blob storage")

        elif AMEX_MID_OUTPUT_FILE.match(file):
            local_logger.info(f"Matched MID {file}, uploading to blob storage")
            blob = mid_client.get_blob_client(container=mid_storage_container, blob=full_path)

            blob_data = io.BytesIO()
            amex_sftp.getfo(full_path, blob_data)
            blob_data.seek(0)
            blob.upload_blob(blob_data, overwrite=True)
            local_logger.info("Uploaded to blob storage")


def run_upload(env: Dict[str, str] = os.environ, client_class: Type[BlobServiceClient] = BlobServiceClient) -> None:
    local_logger = logger.withFields({"task": "upload"})

    amex_server = env["AMEX_SERVER"]
    amex_port = int(env.get("AMEX_PORT", "22"))
    amex_user = env["AMEX_USER"]
    amex_password = env["AMEX_PASSWORD"]

    mid_storage_account = env["MID_BLOB_STORAGE_ACCOUNT"]
    mid_storage_token = env["MID_BLOB_STORAGE_TOKEN"]
    mid_storage_container = env["MID_BLOB_STORAGE_CONTAINER"]

    local_logger.info(f"Amex: sftp://{amex_user}:{fmt_pw(amex_password)}@{amex_server}:{amex_port}")
    local_logger.info(f"MID Storage {mid_storage_account}:{fmt_pw(mid_storage_token)}")

    mid_client = client_class(account_url=mid_storage_account, credential=mid_storage_token)
    mid_container_client = mid_client.get_container_client(mid_storage_container)

    amex_sftp = None

    for blob in mid_container_client.list_blobs():
        if AMEX_MID_INPUT_FILE.match(blob.name):
            local_logger.info(f"Found {blob.name} in blob stoage, attempting to upload to AMEX SFTP")

            if amex_sftp is None:
                try:
                    amex_sftp = create_sftp_client(amex_server, amex_port, amex_user, amex_password, local_logger)
                except Exception as err:
                    logger.exception("Failed to setup SFTP connection", exc_info=err)
                    return

            full_path = os.path.join("inbox", os.path.basename(blob.name))
            blob = mid_container_client.get_blob_client(blob=blob.name)

            blob_data = io.BytesIO()
            blob.download_blob().readinto(blob_data)
            blob_data.seek(0)

            amex_sftp.putfo(blob_data, full_path)
            local_logger.info("Uploaded to AMEX SFTP")

            blob.delete_blob()
            local_logger.info("Deleted from blob storage")


def main():
    logger.setLevel(LOG_LEVEL)
    formatter = pylogrus.TextFormatter(datefmt="Z", colorize=False)
    # formatter = pylogrus.JsonFormatter()  # Can switch to json if needed
    ch = logging.StreamHandler()
    ch.setLevel(LOG_LEVEL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info("Started AMEX SFTP watcher")

    parser = argparse.ArgumentParser()
    parser.add_argument("--now", type=str, default="", choices=("download", "upload"), help="Run database sync now")
    args = parser.parse_args()

    if args.now == "download":
        run_download()
    elif args.now == "upload":
        run_upload()
    else:
        scheduler = BlockingScheduler()
        scheduler.add_job(run_download, trigger=CronTrigger.from_crontab("0 * * * *"))
        scheduler.add_job(run_upload, trigger=CronTrigger.from_crontab("5/15 * * * *"))
        scheduler.start()


if __name__ == "__main__":
    main()
