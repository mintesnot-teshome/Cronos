import struct, pathlib
base=pathlib.Path(r'D:\\Cronos')
path=next(base.glob('564.*141*'))
data=path.joinpath('CroStru.dat').read_bytes()[:19]
magic,hdrunk,version,encoding,blocksize=struct.unpack('<8sH5sHH',data)
print(magic,hdrunk,version,encoding,blocksize)

