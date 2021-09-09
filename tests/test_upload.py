from unittest import mock

import demeter.amex


def test_upload_transaction(download_file, list_dir, sftp_server) -> None:
    mid_file = "somepath/inbox/CHINGS_AXP_MER_REG_200316063833.csv"
    mid_data = b"test mid"

    env = sftp_server["env"].copy()
    env.update(
        {
            "MID_BLOB_STORAGE_ACCOUNT": "2",
            "MID_BLOB_STORAGE_TOKEN": "2",
            "MID_BLOB_STORAGE_CONTAINER": "container2",
        }
    )

    mock_blob_client = mock.Mock()
    mock_class = mock.Mock(return_value=mock_blob_client)

    mock_blob = mock.Mock()
    mock_blob.download_blob.return_value = mock_blob
    mock_blob.readinto = lambda x: x.write(mid_data)

    mock_container = mock.Mock()
    mock_blob_client.get_blob_client.return_value = mock_blob
    mock_blob_client.get_container_client.return_value = mock_container
    mock_container.get_blob_client.return_value = mock_blob

    list_blob_1 = mock.Mock()
    list_blob_1.name = "inbox/test"
    list_blob_2 = mock.Mock()
    list_blob_2.name = mid_file
    mock_container.list_blobs.return_value = [list_blob_1, list_blob_2]

    demeter.amex.run_upload(env=env, client_class=mock_class)

    assert mock_blob.delete_blob.call_count == 1

    files = list_dir("inbox")
    assert "CHINGS_AXP_MER_REG_200316063833.csv" in files

    data = download_file("inbox/CHINGS_AXP_MER_REG_200316063833.csv")
    assert data == mid_data
