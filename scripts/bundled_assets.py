"""The original reader's packaged resource types; exclude editor/temporary files."""
ASSET_SUFFIXES = frozenset({'.png', '.jpg', '.jpeg', '.svg', '.doc'})

def is_bundled_asset(path):
    return path.is_file() and not path.name.startswith('.') and path.suffix.lower() in ASSET_SUFFIXES
