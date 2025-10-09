import sys
import datetime
import hashlib

from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from django.core.management.base import BaseCommand

def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

class Command(BaseCommand):
  help = "Dumb a binary tag/member file into a text format"

  def add_arguments(self, parser):
        parser.add_argument("tag", type=str, nargs='*', help="Tags to decrypt/dump for")

  def handle(self, *args, **options):
        rc = 0

        hdr = sys.stdin.buffer.read(4);

        isV2 = False
        if hdr == b"MSL1":
             print("Version: 	MSLv1")
        elif hdr == b"MSL2":
             print("Version: 	MSLv2")
             isV2 = True
        else:
             raise Exception(f"Unknown header: {hdr}");

        identifier = int.from_bytes(sys.stdin.buffer.read(4),'big')
        print(f"Identifier:	{identifier:08x}")
        datadate = int.from_bytes(sys.stdin.buffer.read(4),'big')
        datestr = datetime.datetime.fromtimestamp(datadate)

        print(f"Date:		{datadate:d}")
        print(f"		{datestr}")

        len_tag = int.from_bytes(sys.stdin.buffer.read(4),'big')
        len_mem = int.from_bytes(sys.stdin.buffer.read(4),'big')

        salt = sys.stdin.buffer.read(32)
        print("Salt:		{salt.hex()}")
        keysalt = sys.stdin.buffer.read(32)
        print("Keysalt:	{keysalt.hex()}")
        ivs = sys.stdin.buffer.read(32)
        print("IVector:	{ivs.hex()}")
     
        tags = sys.stdin.buffer.read(len_tag)
        if len(tags) != len_tag:
             raise Exception("Incomplete file, not enough tag data")

        members = sys.stdin.buffer.read(len_mem)
        if len(members) != len_mem:
             raise Exception("Incomplete file, not enough member data")

        i = 0
        ubx = 0
        while len(tags):
             i = i + 1
             entry = tags[0:68]
             tags = tags[68:]
             ubx += 68

             if (len(entry) != 68):
                 raise Exception(f"Tag entry {i} incomplete")

             print(f"Entry {i:04d} - starting at {ubx}")
             salted_tag = entry[0:32]
             print(f"	Salted tag	{salted_tag.hex()}")

             decrypt_key = entry[32:64]
             print(f"	Decrypt key	{decrypt_key.hex()}")

             idx = int.from_bytes(entry[64:68],'big')
             print(f"	Index		{idx}")

             if (idx <= 0):
                 raise Exception(f"Tag entry {i} has 0 reference to members data")
             if (idx > len(members)):
                 raise Exception(f"Tag entry {i} has a OOB reference to members data")

             has =  int.from_bytes(members[idx:idx+1],'big')
             print(f"	Has: 		{has:02x}")

             needs =  int.from_bytes(members[idx+1:idx+2],'big')
             print(f"	Needs: 		{needs:02x}")

             enc_len =  int.from_bytes(members[idx+2:idx+3],'big')
             print(f"	Len: 		{enc_len:02x}")

             encrypted = members[idx+3:idx+3+enc_len]

             if len(encrypted) % 16 != 0:
                  raise Exception("Not properly padded/not a multiple of 16")

             for tag in options['tag']:
                  stag = hashlib.sha256(salt + tag.encode("utf-8")).digest()
                 
                  if salted_tag != stag:
                        continue

                  # Ok - this is one we can decrypt
                  saltedkey = hashlib.sha256(tag.encode("utf-8") + keysalt).digest()
                  tagkey = byte_xor(decrypt_key, saltedkey)

                  print(f"	IV: 		{ivs.hex()}")
                  print(f"	UDX: 		{idx}")
                  taguiv = hashlib.sha256(ivs + idx.to_bytes(4, "big")).digest()[0:16]

                  print(f"	TagUIV:		{taguiv.hex()}")
                  print(f"	TagKey:		{tagkey.hex()}")
                  print(f"	Encrypted	{encrypted.hex()}")
 
                  dec = AES.new(tagkey, AES.MODE_CBC, iv=taguiv).decrypt(encrypted)
                  print(f"	Clear, padded	{dec.hex()}")
                  clr = unpad(dec, AES.block_size)
                  print(f"	Clear, unpadded	{clr.hex()}")
                  if isV2:
                        # New format, UID\0ShortName\0
                        (uid, short, clr) = clr.split(b'\0')
                        print(f"	UID:		{uid.decode('utf-8')}")
                        print(f"	Short name:	{short.decode('utf-8')}")
                  print(f"	Full name:	{clr.decode('utf-8')}")

        if len(sys.stdin.buffer.read(1)):
             raise Exception("Cruft at the end of the file")


        sys.exit(rc)
