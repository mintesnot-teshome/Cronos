import pathlib, binascii
from crodump.crodump import strucrack
from crodump.Database import Database
import crodump.koddecoder
base = pathlib.Path(r"D:\\Cronos")
path = next(base.glob("130.*dento.de*"))
args = type("Args", (), {})()
args.dbdir = str(path)
args.sys = False
args.silent = True
key = strucrack(None, args)
db = Database(args.dbdir, crodump.koddecoder.new(key))
data = db._read_dbinfo_record()
print(len(data))
print(binascii.hexlify(data[:64]))
print(data[:64])
