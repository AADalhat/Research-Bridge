from pathlib import Path

import pytest

from synaptix.utils.checksum import calculate_sha256


def test_sha256_matches_known_value(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"abc")

    result = calculate_sha256(file_path)

    assert result == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_is_independent_of_chunk_size(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"research-bridge" * 1000)

    assert calculate_sha256(file_path, chunk_size=7) == calculate_sha256(
        file_path,
        chunk_size=1024,
    )


def test_sha256_rejects_invalid_chunk_size(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"abc")

    with pytest.raises(ValueError):
        calculate_sha256(file_path, chunk_size=0)


def test_sha256_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        calculate_sha256(tmp_path / "missing.pdf")