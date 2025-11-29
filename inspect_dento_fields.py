import pathlib
from crodump.crodump import strucrack
from crodump.Database import Database
import crodump.koddecoder
base = pathlib.Path(r"D:/Cronos")
path = next(base.glob("130.*dento.de*"))
args=type('Args',(),{})()
args.dbdir=str(path)
args.sys=False
args.silent=True
key = strucrack(None,args)
db = Database(args.dbdir, crodump.koddecoder.new(key))
rec = db._read_dbinfo_record()[1:]
from crodump.readers import ByteReader
rd = ByteReader(rec)
for i in range(5):
    name = rd.readname()
    val = rd.readdword()
    safe = name.encode('unicode_escape').decode('ascii')
    if val >> 31:
        size = val & 0x7fffffff
        value = rd.readbytes(size)
        print(i, safe, 'inline', size, value[:16])
    else:
        print(i, safe, 'ref', val)
