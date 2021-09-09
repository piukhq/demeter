from unittest import mock

import demeter.amex


def test_download_transaction(upload_file, sftp_server) -> None:
    tx_file = "AXP_CHINGS_TLOG_200427061702.csv"
    tx_data = b"test transaction"
    mid_file = "CHINGS_AXP_MER_REG_RESP_200316063833.csv"
    mid_data = b"test mid"

    upload_file("outbox/test1", "test content")
    upload_file(f"outbox/{tx_file}", tx_data)
    upload_file(f"outbox/{mid_file}", mid_data)

    env = sftp_server["env"].copy()
    env.update(
        {
            "TX_BLOB_STORAGE_ACCOUNT": "1",
            "TX_BLOB_STORAGE_TOKEN": "1",
            "TX_BLOB_STORAGE_CONTAINER": "container1",
            "MID_BLOB_STORAGE_ACCOUNT": "2",
            "MID_BLOB_STORAGE_TOKEN": "2",
            "MID_BLOB_STORAGE_CONTAINER": "container2",
        }
    )

    mock_blob_client = mock.Mock()
    mock_class = mock.Mock(return_value=mock_blob_client)
    mock_blob = mock.Mock()
    mock_blob_client.get_blob_client.return_value = mock_blob

    demeter.amex.run_download(env=env, client_class=mock_class)

    assert mock_blob_client.get_blob_client.call_count == 2
    assert mock_blob.upload_blob.call_count == 2

    # Check transaction file
    assert (
        mock_blob_client.get_blob_client.call_args_list[0][1]["container"]
        == env["TX_BLOB_STORAGE_CONTAINER"]
    )
    assert tx_file in mock_blob_client.get_blob_client.call_args_list[0][1]["blob"]

    blob_data = mock_blob.upload_blob.call_args_list[0][0][0].read()
    assert blob_data == tx_data

    # Check mid file
    assert (
        mock_blob_client.get_blob_client.call_args_list[1][1]["container"]
        == env["MID_BLOB_STORAGE_CONTAINER"]
    )
    assert mid_file in mock_blob_client.get_blob_client.call_args_list[1][1]["blob"]

    blob_data = mock_blob.upload_blob.call_args_list[1][0][0].read()
    assert blob_data == mid_data
