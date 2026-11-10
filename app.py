"""WSGI entry point for Waitress. Keeps the JSON API shared with the local runner."""
import io
from email.message import Message
from http import HTTPStatus
import server

server.init_db()

def application(environ, start_response):
    method=environ.get('REQUEST_METHOD','GET')
    if method not in ('GET','POST','HEAD'):
        body=b'{"error":"Method not allowed."}'
        start_response('405 Method Not Allowed',[('Content-Type','application/json'),('Allow','GET, POST, HEAD'),('Content-Length',str(len(body)))])
        return [body]
    handler=object.__new__(server.Handler)
    handler.command=method
    handler.path=environ.get('PATH_INFO','/')+('?' + environ['QUERY_STRING'] if environ.get('QUERY_STRING') else '')
    handler.client_address=(environ.get('REMOTE_ADDR','unknown'),0)
    handler.headers=Message()
    for key,value in environ.items():
        if key.startswith('HTTP_'):handler.headers[key[5:].replace('_','-')]=value
    for key in ('CONTENT_TYPE','CONTENT_LENGTH'):
        if environ.get(key):handler.headers[key.replace('_','-')]=environ[key]
    handler.rfile=environ['wsgi.input'];handler.wfile=io.BytesIO()
    result={'status':200,'headers':[]}
    handler.send_response=lambda code:result.update(status=code)
    handler.send_header=lambda key,value:result['headers'].append((key,value))
    handler.end_headers=lambda:None
    if method=='POST':handler.do_POST()
    else:handler.do_GET()
    start_response(f"{result['status']} {HTTPStatus(result['status']).phrase}",result['headers'])
    return [b'' if method=='HEAD' else handler.wfile.getvalue()]
