from mara_db.formats import ParquetFormat


def test_parquet_format():
    """Validate the __rep__ method"""
    assert str(ParquetFormat), "<ParquetFormat>"
