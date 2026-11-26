"""Call the private, persistent Chrome MCP connection without exporting sessions."""
import argparse,json,socket
from pathlib import Path

def call(request):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(135);client.connect(str(Path.home()/'.local/share/datogedon-browser/control.sock'))
        client.sendall((json.dumps(request)+'\n').encode());parts=[]
        while chunk:=client.recv(65536):parts.append(chunk)
    return json.loads(b''.join(parts))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('request',help='JSON tool/args or operation/tools');a=p.parse_args()
    try:print(json.dumps(call(json.loads(a.request)),ensure_ascii=False))
    except (OSError,ValueError) as error:raise SystemExit(type(error).__name__+': '+str(error))
