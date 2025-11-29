import pathlib, binascii
base = pathlib.Path(r"D:\Cronos")
for path in base.glob("130.*dento.de*"):
    target = path / "CroStru.dat"
    data = target.read_bytes()
    print("PATH", target.as_posix().encode('unicode_escape').decode('ascii'))
    print(len(data))
    print(binascii.hexlify(data[:128]))
