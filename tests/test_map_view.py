from map_view import create_map

def test_create_map():
    assert isinstance(create_map([]), str)