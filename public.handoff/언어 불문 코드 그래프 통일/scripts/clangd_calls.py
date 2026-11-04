import json,subprocess,sys,time,os
P=sys.argv[1]
p=subprocess.Popen(["clangd","--compile-commands-dir="+P,"--log=error"],cwd=P,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
i=0
def send(m,params=None,notify=False):
    global i
    o={"jsonrpc":"2.0","method":m,"params":params or {}}
    if not notify: i+=1; o["id"]=i
    b=json.dumps(o).encode(); p.stdin.write(b"Content-Length: %d\r\n\r\n"%len(b)+b); p.stdin.flush(); return i
def read():
    n=0
    while True:
        l=p.stdout.readline().strip()
        if not l: break
        if l.lower().startswith(b"content-length"): n=int(l.split(b":")[1])
    return json.loads(p.stdout.read(n))
def req(m,params):
    k=send(m,params)
    while True:
        r=read()
        if r.get("id")==k: return r
uri="file://"+P+"/a.cpp"
req("initialize",{"processId":None,"rootUri":"file://"+P,"capabilities":{}}); send("initialized",{},True)
send("textDocument/didOpen",{"textDocument":{"uri":uri,"languageId":"cpp","version":1,"text":open(P+"/a.cpp").read()}},True)
time.sleep(2)
# free_fn 는 4번째 줄 4열
it=req("textDocument/prepareCallHierarchy",{"textDocument":{"uri":uri},"position":{"line":3,"character":5}}).get("result") or []
print("prepare",[x["name"] for x in it])
if it:
    o=req("callHierarchy/outgoingCalls",{"item":it[0]}); print("outgoing",o.get("error") or [c["to"]["name"] for c in (o.get("result") or [])])
    n=req("callHierarchy/incomingCalls",{"item":it[0]}); print("incoming",n.get("error") or [c["from"]["name"] for c in (n.get("result") or [])])
p.kill()
