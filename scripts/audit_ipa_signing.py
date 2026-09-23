#!/usr/bin/env python3
import argparse, hashlib, json, plistlib, struct, zipfile
from pathlib import Path
def signing(data):
    if data[:4]==b"\xca\xfe\xba\xbe":
        count=struct.unpack_from(">I",data,4)[0]
        return [signing(data[o:o+s]) for _,_,o,s,_ in (struct.unpack_from(">5I",data,8+i*20) for i in range(count))]
    if data[:4] not in (b"\xcf\xfa\xed\xfe",b"\xce\xfa\xed\xfe"): return {"format":"not_supported"}
    pos=32 if data[0]==0xcf else 28; count=struct.unpack_from("<I",data,16)[0]
    out={"signature_present":False,"xml_entitlements":None}
    for _ in range(count):
        cmd,size=struct.unpack_from("<II",data,pos)
        if cmd==0x1d:
            off,length=struct.unpack_from("<II",data,pos+8); blob=data[off:off+length]; out["signature_present"]=True
            if len(blob)>=12 and struct.unpack_from(">I",blob)[0]==0xfade0cc0:
                for i in range(struct.unpack_from(">I",blob,8)[0]):
                    slot,start=struct.unpack_from(">II",blob,12+i*8)
                    if slot==5:
                        end=start+struct.unpack_from(">I",blob,start+4)[0]; out["xml_entitlements"]=plistlib.loads(blob[start+8:end])
                    if slot==7: out["der_entitlements_present"]=True
        pos+=size
    return out
def inventory(path):
    r={"file":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bundles":{}}
    with zipfile.ZipFile(path) as z:
        for n in sorted(set(z.namelist())):
            if not n.endswith("/Info.plist"): continue
            folder=n[:-11]
            if not folder.endswith((".app",".appex",".framework")): continue
            info=plistlib.loads(z.read(n)); e=folder+"/"+info.get("CFBundleExecutable","")
            if e in z.namelist(): r["bundles"][folder]={"info":info,"signing":signing(z.read(e))}
    return r
if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("ipa",type=Path); a=p.parse_args()
    print(json.dumps(inventory(a.ipa),indent=2,sort_keys=True,default=str))
