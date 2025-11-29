import pathlib
base = pathlib.Path(r"D:\\Cronos")
path = next(base.glob("130.*dento.de*"))
print(path.as_posix().encode("unicode_escape").decode("ascii"))
