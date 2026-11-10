#!/usr/bin/env python3
"""Collect only new local PDF files from the assigned disposable iOS Simulator."""
import argparse, hashlib, json, os, pathlib, plistlib, re, shutil
def snapshot(device):
    if not re.fullmatch(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}",device):
        raise ValueError("Expected the assigned simulator UUID")
    root=pathlib.Path.home()/"Library/Developer/CoreSimulator/Devices"/device/"data/Containers/Shared/AppGroup"
    if not root.is_dir(): raise ValueError("Assigned simulator AppGroup directory is absent")
    domains=[]; files={}
    for meta in root.glob("*/.com.apple.mobile_container_manager.metadata.plist"):
        if meta.is_symlink() or meta.stat().st_size>65536: continue
        identifier=plistlib.loads(meta.read_bytes()).get("MCMMetadataIdentifier","")
        if not isinstance(identifier,str) or "fileprovider" not in identifier.lower(): continue
        domains.append(identifier)
        if "localstorage" not in identifier.lower(): continue
        group=meta.parent.resolve()
        count=0
        for directory,dirs,names in os.walk(group,followlinks=False):
            dirs[:]=[d for d in dirs if d.lower() not in ("caches","tmp",".trash") and not (pathlib.Path(directory)/d).is_symlink()]
            for name in names:
                count+=1
                if count>25000: raise ValueError("Bound local FileProvider enumeration")
                path=pathlib.Path(directory)/name
                if path.suffix.lower()!=".pdf" or path.is_symlink(): continue
                real=path.resolve()
                if not real.is_relative_to(group): raise ValueError("FileProvider path escape")
                size=real.stat().st_size
                if not 5<size<=64*1024*1024: raise ValueError("Saved PDF size outside QA bounds")
                raw=real.read_bytes()
                if not raw.startswith(b"%PDF-"): raise ValueError("Saved file is not PDF")
                key=identifier+"/"+real.relative_to(group).as_posix()
                files[key]={"bytes":size,"sha256":hashlib.sha256(raw).hexdigest(),"path":str(real)}
    return {"schema":1,"scope":"Assigned simulator local FileProvider only; no physical device or iCloud assertion","domains":domains,"files":files}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=["before","after"]);p.add_argument("device");p.add_argument("prefix")
    args=p.parse_args()
    prefix=pathlib.Path(args.prefix)
    before=pathlib.Path(str(prefix)+"-before.json")
    data=snapshot(args.device)
    if args.phase=="before":
        before.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
        print("SYSTEM_FILES_BEFORE: "+json.dumps({"domains":data["domains"],"pdfs":len(data["files"])}))
        return
    old=json.loads(before.read_text())
    new={k:v for k,v in data["files"].items() if old["files"].get(k,{}).get("sha256")!=v["sha256"]}
    print("SYSTEM_FILES_AFTER: "+json.dumps({"domains":data["domains"],"newPDFs":list(new)}))
    if not new: raise ValueError("UI did not create a new PDF in the assigned local FileProvider")
    hashes={v["sha256"] for v in new.values()}
    if len(hashes)!=1: raise ValueError("More than one distinct new PDF; refuse ambiguous evidence")
    key,chosen=next(iter(new.items()))
    destination=pathlib.Path(str(prefix)+"-saved.pdf")
    shutil.copyfile(chosen["path"],destination)
    if hashlib.sha256(destination.read_bytes()).hexdigest()!=chosen["sha256"]: raise ValueError("Copied PDF digest mismatch")
    data["selected"]={"localProviderRelativePath":key,"bytes":chosen["bytes"],"sha256":chosen["sha256"],"artifact":destination.name}
    for item in data["files"].values(): item.pop("path",None)
    pathlib.Path(str(prefix)+"-after.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("SYSTEM_FILES_PDF: "+json.dumps(data["selected"],ensure_ascii=False))
if __name__=="__main__": main()
