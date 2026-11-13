"""The original reader's packaged resource types; exclude editor/temporary files."""
ASSET_SUFFIXES = frozenset({'.png', '.jpg', '.jpeg', '.svg', '.doc'})

def is_bundled_asset(path):
    return path.is_file() and not path.name.startswith('.') and path.suffix.lower() in ASSET_SUFFIXES

def zip_members(archive):
    """Read AAPT's UTF-8 names even when it omits the ZIP UTF-8 flag.

    This interprets names without rewriting a signed APK or changing any bytes.
    Reject aliases so a duplicate member cannot hide behind different flags.
    """
    result={}
    for info in archive.infolist():
        name=info.filename
        if not info.flag_bits&0x800:
            try:name=name.encode('cp437').decode('utf-8')
            except UnicodeDecodeError:pass
        if name in result:raise ValueError('Duplicate canonical ZIP member: '+name)
        result[name]=info
    return result
