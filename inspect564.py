from crodump.crodump import strucrack
from crodump.Database import Database
import crodump.koddecoder, binascii

class Args: pass
args = Args(); args.dbdir = r"D:\\Cronos\\564.МВД РФ Розыск лиц 141к 01.2025"; args.sys=False; args.silent=True
key = strucrack(None, args)
if not key:
    exit()
db = Database(args.dbdir, crodump.koddecoder.new(key))
dbinfo = db._read_dbinfo_record()
print('len', len(dbinfo))
print('head', binascii.hexlify(dbinfo[:64]))
