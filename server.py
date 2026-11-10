"""NVTRA local application server: SQLite persistence, private accounts and JSON API.
Run behind an HTTPS reverse proxy in production; see docs/OPERATIONS.md.
"""
import argparse, base64, datetime as dt, hashlib, hmac, ipaddress, json, os, re
import secrets, smtplib, socket, sqlite3, ssl, threading, time, urllib.parse, urllib.request
from email.message import EmailMessage
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('NVTRA_DATA_DIR', str(ROOT / '.data'))).resolve()
DB = DATA / 'nvtra.sqlite3'
PUBLIC_URL = os.environ.get('NVTRA_PUBLIC_URL', 'http://127.0.0.1:8080').rstrip('/')
COOKIE_SECURE = PUBLIC_URL.startswith('https://')
PRICING = json.loads((ROOT / 'config/pricing.json').read_text())
CONTENT = json.loads((ROOT / 'config/content.json').read_text())
RATE_LOCK = threading.Lock()
RATES = {}

class Problem(Exception):
    def __init__(self, status, message): self.status, self.message = status, message

def now(): return int(time.time())

@contextmanager
def database():
    con = sqlite3.connect(DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback(); raise
    finally: con.close()

def init_db():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    with database() as c:
        c.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'client',created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS resets(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS inquiries(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),email TEXT,name TEXT,subject TEXT,message TEXT,brief TEXT,estimate TEXT,created INTEGER,email_status TEXT DEFAULT 'not_configured');
        CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,summary TEXT NOT NULL,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS milestones(id INTEGER PRIMARY KEY,project_id INTEGER REFERENCES projects(id),title TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'planned',design_url TEXT DEFAULT '',updated INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY,project_id INTEGER REFERENCES projects(id),user_id INTEGER REFERENCES users(id),body TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS uploads(id INTEGER PRIMARY KEY,project_id INTEGER REFERENCES projects(id),user_id INTEGER REFERENCES users(id),name TEXT,path TEXT,size INTEGER,created INTEGER);
        CREATE TABLE IF NOT EXISTS slots(id INTEGER PRIMARY KEY,starts TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY,slot_id INTEGER UNIQUE REFERENCES slots(id),user_id INTEGER REFERENCES users(id),note TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS saved(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),title TEXT,configuration TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS showcase(id INTEGER PRIMARY KEY,title TEXT NOT NULL,summary TEXT NOT NULL,category TEXT NOT NULL,url TEXT NOT NULL,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),title TEXT NOT NULL,body TEXT NOT NULL,public INTEGER DEFAULT 0,created INTEGER NOT NULL);
        ''')
    os.chmod(DB, 0o600)

def hash_password(password):
    salt = secrets.token_hex(16)
    result = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return salt + ':' + result.hex()

def verify_password(password, encoded):
    salt, expected = encoded.split(':')
    result = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return hmac.compare_digest(expected, result)

DUMMY_PASSWORD = hash_password('constant-time-fallback-password')

def text(data, key, limit=200, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit: raise Problem(400, f'Invalid {key}.')
    value = value.strip()
    if required and not value: raise Problem(400, f'{key.capitalize()} is required.')
    return value

def email_address(value):
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value) or len(value)>254: raise Problem(400,'Enter a valid email address.')
    return value.lower()

def password_input(data):
    value = text(data, 'password', 128)
    if len(value)<12: raise Problem(400,'Use a password of at least 12 characters.')
    return value

def digest(token): return hashlib.sha256(token.encode()).hexdigest()

def event(c, user, title, body='', public=False):
    c.execute('INSERT INTO activity(user_id,title,body,public,created) VALUES(?,?,?,?,?)',(user,title,body,int(public),now()))

def estimate(data):
    pages = data.get('pages',1)
    if isinstance(pages,bool) or not isinstance(pages,int) or not 1<=pages<=100: raise Problem(400,'Choose between 1 and 100 pages.')
    features = data.get('features',[])
    known = {f['id'] for f in PRICING['features']+PRICING['customFeatures']}
    if not isinstance(features,list) or len(features)>30 or any(not isinstance(f,str) or f not in known for f in features): raise Problem(400,'Unknown estimate feature.')
    features=list(dict.fromkeys(features))
    priced={f['id'] for f in PRICING['features']}
    packages=[p for p in PRICING['packages'] if pages<=p['maxPages']]
    costs=[(p['price']+max(0,len(set(features)&priced)-p['includedFeatures'])*PRICING['featurePrice'],p) for p in packages]
    costs.sort(key=lambda x:x[0])
    low,pkg=costs[0]; high=costs[1][0] if len(costs)>1 else low
    custom=[f['name'] for f in PRICING['customFeatures'] if f['id'] in features]
    for key in ['design','animation']:
        if data.get(key) in ['advanced','bespoke']: custom.append('Advanced '+key)
    return dict(min=low,max=high,monthly=PRICING['maintenanceMonthly'] if data.get('maintenance') is True else 0,currency='ZAR',package=pkg['name'],custom=custom,configuration=data,note=PRICING['note'])

def mail(recipient, subject, body):
    host=os.environ.get('SMTP_HOST')
    sender=os.environ.get('SMTP_FROM')
    if not host or not sender: return 'not_configured'
    msg=EmailMessage();msg['From']=sender;msg['To']=recipient;msg['Subject']=subject;msg.set_content(body)
    try:
        with smtplib.SMTP(host,int(os.environ.get('SMTP_PORT','587')),timeout=10) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if os.environ.get('SMTP_USER'): smtp.login(os.environ['SMTP_USER'],os.environ.get('SMTP_PASSWORD',''))
            smtp.send_message(msg)
        return 'accepted_by_mail_server'
    except Exception: return 'failed'

def safe_url(url):
    parts=urllib.parse.urlsplit(url)
    if parts.scheme not in ('https','http') or not parts.hostname or parts.username or parts.password or parts.fragment: raise Problem(400,'Enter a public HTTP or HTTPS URL without credentials or fragments.')
    try:
        if parts.port not in (None,80,443): raise ValueError()
        addresses=socket.getaddrinfo(parts.hostname,parts.port or 443,type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses): raise ValueError()
    except socket.gaierror: raise Problem(503,'The server cannot resolve the website address. Check the URL or try again when DNS access is available. No audit was generated.')
    except ValueError: raise Problem(400,'Only publicly reachable website addresses are accepted.')
    return url

def json_remote(url, payload=None, headers=None, timeout=45):
    raw=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(url, data=raw, headers={'Content-Type':'application/json',**(headers or {})})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        body=r.read(8*1024*1024+1)
        if len(body)>8*1024*1024: raise ValueError('Response too large')
        return json.loads(body)

def health(url):
    safe_url(url)
    query=[('url',url),('strategy','mobile')]+[('category',c) for c in ['performance','accessibility','best-practices','seo']]
    if os.environ.get('PAGESPEED_API_KEY'): query.append(('key',os.environ['PAGESPEED_API_KEY']))
    try:
        result=json_remote('https://www.googleapis.com/pagespeedonline/v5/runPagespeed?'+urllib.parse.urlencode(query),timeout=65)
        lighthouse=result['lighthouseResult']; audits=lighthouse['audits']; categories=lighthouse['categories']
        metrics={k:{'title':audits[k]['title'],'value':audits[k].get('displayValue','Not available')} for k in ['first-contentful-paint','largest-contentful-paint','cumulative-layout-shift','total-blocking-time'] if k in audits}
        improvements=[{'title':a.get('title','Audit'),'description':a.get('description',''),'score':a['score']} for a in audits.values() if isinstance(a.get('score'),(int,float)) and a['score']<.9 and a.get('scoreDisplayMode') not in ['notApplicable','manual','informative']][:8]
        return {'url':url,'measuredAt':lighthouse.get('fetchTime'),'source':'Google PageSpeed Insights / Lighthouse','strategy':'mobile','scores':{k:round(v['score']*100) if v.get('score') is not None else None for k,v in categories.items()},'metrics':metrics,'improvements':improvements,'mobileNote':'Mobile device emulation; not a test on every physical device.'}
    except Exception: raise Problem(503,'The measurement provider is unavailable or rate-limited. No scores were generated. Try again later or configure a PageSpeed API key.')

class Handler(BaseHTTPRequestHandler):
    server_version='NVTRA'
    def log_message(self,*args): pass  # Never log query strings, credentials or private content.
    def headers_common(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://images.unsplash.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if COOKIE_SECURE: self.send_header('Strict-Transport-Security','max-age=31536000')
    def respond(self,status,data,extra=None):
        body=json.dumps(data).encode();self.send_response(status);self.headers_common()
        self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store')
        for k,v in (extra or {}).items():self.send_header(k,v)
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def limit(self,kind,count=30,seconds=60):
        key=(self.client_address[0],kind)
        with RATE_LOCK:
            cutoff=time.time()-seconds
            if len(RATES)>10000:
                for k in list(RATES):
                    if not RATES[k] or RATES[k][-1]<time.time()-3600:RATES.pop(k,None)
            hits=[t for t in RATES.get(key,[]) if t>cutoff]
            if len(hits)>=count:raise Problem(429,'Too many requests. Please wait and try again.')
            hits.append(time.time());RATES[key]=hits
    def user(self,required=True):
        jar=cookies.SimpleCookie()
        try:jar.load(self.headers.get('Cookie',''));token=jar['nvtra_session'].value if 'nvtra_session' in jar else ''
        except cookies.CookieError:token=''
        with database() as c:
            user=c.execute('SELECT u.id,u.email,u.name,u.role FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token=? AND s.expires>?',(digest(token),now())).fetchone()
        if not user and required:raise Problem(401,'Please sign in to continue.')
        return dict(user) if user else None
    def admin(self):
        u=self.user()
        if u['role']!='admin':raise Problem(403,'Studio access required.')
        return u
    def body(self):
        if self.headers.get('Origin')!=PUBLIC_URL:raise Problem(403,'Request origin is not allowed.')
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise Problem(415,'JSON requests required.')
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:raise Problem(400,'Invalid request size.')
        if not 0<length<=7*1024*1024:raise Problem(413,'Request is too large.')
        try:data=json.loads(self.rfile.read(length))
        except (ValueError,UnicodeDecodeError):raise Problem(400,'Invalid JSON.')
        if not isinstance(data,dict):raise Problem(400,'Expected a JSON object.')
        return data
    def project(self,c,pid,u):
        p=c.execute('SELECT * FROM projects WHERE id=?',(pid,)).fetchone()
        if not p or (u['role']!='admin' and p['user_id']!=u['id']):raise Problem(404,'Project not found.')
        return dict(p)
    def session_cookie(self,uid):
        token=secrets.token_urlsafe(32)
        with database() as c:
            c.execute('DELETE FROM sessions WHERE expires<?',(now(),))
            c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(token),uid,now()+7*86400))
        return 'nvtra_session='+token+'; HttpOnly; SameSite=Lax; Path=/; Max-Age=604800'+('; Secure' if COOKIE_SECURE else '')
    def do_GET(self):
        try:self.get()
        except Problem as e:self.respond(e.status,{'error':e.message})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self.respond(500,{'error':'An unexpected error occurred. Please retry.'})
    def get(self):
        path=urllib.parse.urlsplit(self.path).path
        if path=='/api/config':return self.respond(200,{'pricing':PRICING,'content':CONTENT,'aiAvailable':bool(os.environ.get('GEMINI_API_KEY')),'emailAvailable':bool(os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM')),'timezone':'Africa/Johannesburg'})
        if path=='/api/showcase':
            with database() as c:rows=c.execute('SELECT * FROM showcase ORDER BY created DESC,id DESC').fetchall()
            return self.respond(200,{'projects':[dict(r) for r in rows]})
        if path=='/api/session':return self.respond(200,{'user':self.user(False)})
        if path=='/api/activity':
            with database() as c:rows=c.execute('SELECT id,title,body,created FROM activity WHERE public=1 ORDER BY created DESC,id DESC LIMIT 30').fetchall()
            return self.respond(200,{'items':[dict(r) for r in rows]})
        if path=='/api/slots':
            with database() as c:rows=c.execute('SELECT s.id,s.starts FROM slots s LEFT JOIN bookings b ON b.slot_id=s.id WHERE b.id IS NULL AND s.starts>? ORDER BY s.starts LIMIT 100',(dt.datetime.now(dt.timezone.utc).isoformat(),)).fetchall()
            return self.respond(200,{'slots':[dict(r) for r in rows]})
        if path=='/api/dashboard':
            u=self.user()
            with database() as c:
                result={
                    'user':u,
                    'projects':[dict(r) for r in c.execute('SELECT * FROM projects WHERE user_id=? ORDER BY created DESC',(u['id'],))],
                    'inquiries':[dict(r) for r in c.execute('SELECT id,subject,created,email_status FROM inquiries WHERE user_id=? ORDER BY created DESC',(u['id'],))],
                    'saved':[dict(r) for r in c.execute('SELECT * FROM saved WHERE user_id=? ORDER BY created DESC',(u['id'],))],
                    'bookings':[dict(r) for r in c.execute('SELECT b.id,b.note,s.starts FROM bookings b JOIN slots s ON b.slot_id=s.id WHERE b.user_id=? ORDER BY s.starts',(u['id'],))],
                    'activity':[dict(r) for r in c.execute('SELECT title,body,created FROM activity WHERE user_id=? ORDER BY id DESC LIMIT 30',(u['id'],))]}
            return self.respond(200,result)
        if re.fullmatch(r'/api/projects/\d+',path):
            u=self.user();pid=int(path.split('/')[-1])
            with database() as c:
                result=self.project(c,pid,u)
                result['milestones']=[dict(r) for r in c.execute('SELECT * FROM milestones WHERE project_id=? ORDER BY id',(pid,))]
                result['comments']=[dict(r) for r in c.execute('SELECT comments.id,body,comments.created,users.name FROM comments JOIN users ON user_id=users.id WHERE project_id=? ORDER BY comments.id',(pid,))]
                result['uploads']=[dict(r) for r in c.execute('SELECT id,name,size,created FROM uploads WHERE project_id=?',(pid,))]
            return self.respond(200,result)
        if re.fullmatch(r'/api/uploads/\d+',path):
            u=self.user()
            with database() as c:
                row=c.execute('SELECT * FROM uploads WHERE id=?',(int(path.split('/')[-1]),)).fetchone()
                if not row:raise Problem(404,'File not found.')
                self.project(c,row['project_id'],u)
            body=(DATA/'uploads'/row['path']).read_bytes()
            self.send_response(200);self.headers_common();self.send_header('Content-Type','application/octet-stream');self.send_header('Cache-Control','no-store');self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+urllib.parse.quote(row['name']));self.send_header('Content-Length',str(len(body)));self.end_headers();return self.wfile.write(body)
        if path=='/api/admin':
            self.admin()
            with database() as c:result={table:[dict(r) for r in c.execute(query)] for table,query in {
                'users':'SELECT id,email,name,role FROM users ORDER BY id DESC',
                'projects':'SELECT * FROM projects ORDER BY id DESC',
                'inquiries':'SELECT * FROM inquiries ORDER BY id DESC LIMIT 100',
                'slots':'SELECT s.id,s.starts,b.id AS booking_id,u.email FROM slots s LEFT JOIN bookings b ON b.slot_id=s.id LEFT JOIN users u ON u.id=b.user_id ORDER BY s.starts DESC LIMIT 100'
            }.items()}
            return self.respond(200,result)
        allowed={'/':'index.html','/index.html':'index.html','/nvtra.html':'nvtra.html','/studio.css':'studio.css','/studio.js':'studio.js','/platform.css':'platform.css','/platform.js':'platform.js','/cinematic.css':'cinematic.css','/cinematic.js':'cinematic.js','/robots.txt':'robots.txt'}
        if path not in allowed:raise Problem(404,'Not found.')
        file=ROOT/allowed[path]
        if not file.exists():raise Problem(404,'Not found.')
        body=file.read_bytes();self.send_response(200);self.headers_common();self.send_header('Content-Type',{'html':'text/html; charset=utf-8','css':'text/css','js':'text/javascript','txt':'text/plain'}[file.suffix[1:]]);self.send_header('Cache-Control','no-cache');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        try:
            self.limit('write',120)
            self.post(urllib.parse.urlsplit(self.path).path,self.body())
        except Problem as e:self.respond(e.status,{'error':e.message})
        except sqlite3.IntegrityError:self.respond(409,{'error':'This item already exists or was just reserved. Refresh and try again.'})
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception:self.respond(500,{'error':'An unexpected error occurred. Please retry.'})
    def post(self,path,data):
        if path in ['/api/register','/api/login']:
            self.limit('auth',12,900)
            email=email_address(text(data,'email',254));password=text(data,'password',128)
            if path=='/api/register':
                password=password_input(data);name=text(data,'name',100)
                with database() as c:
                    uid=c.execute('INSERT INTO users(email,name,password,created) VALUES(?,?,?,?)',(email,name,hash_password(password),now())).lastrowid
                    event(c,uid,'Account created')
            else:
                with database() as c:u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                valid=verify_password(password,u['password'] if u else DUMMY_PASSWORD)
                if not u or not valid:raise Problem(401,'Email or password is incorrect.')
                uid=u['id']
            return self.respond(200,{'ok':True},{'Set-Cookie':self.session_cookie(uid)})
        if path=='/api/logout':
            jar=cookies.SimpleCookie(self.headers.get('Cookie',''));token=jar['nvtra_session'].value if 'nvtra_session' in jar else ''
            with database() as c:c.execute('DELETE FROM sessions WHERE token=?',(digest(token),))
            return self.respond(200,{'ok':True},{'Set-Cookie':'nvtra_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0'+('; Secure' if COOKIE_SECURE else '')})
        if path=='/api/password-reset':
            self.limit('reset',3,900);email=email_address(text(data,'email',254))
            if not os.environ.get('SMTP_HOST') or not os.environ.get('SMTP_FROM'):raise Problem(503,'Password-reset email is not configured. Contact the studio for account recovery.')
            with database() as c:
                u=c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
                if u:
                    token=secrets.token_urlsafe(32);c.execute('DELETE FROM resets WHERE user_id=?',(u['id'],));c.execute('INSERT INTO resets VALUES(?,?,?)',(digest(token),u['id'],now()+1800))
            if u:mail(email,'Reset your NVTRA password',PUBLIC_URL+'/#reset?token='+token+'\nThis link expires in 30 minutes.')
            return self.respond(200,{'message':'If an account exists, a reset email has been requested. Check your inbox and spam folder.'})
        if path=='/api/password-reset/confirm':
            self.limit('reset-confirm',10,900);password=password_input(data);token=text(data,'token',200)
            with database() as c:
                c.execute('BEGIN IMMEDIATE')
                reset=c.execute('SELECT * FROM resets WHERE token=? AND expires>?',(digest(token),now())).fetchone()
                if not reset:raise Problem(400,'Reset link is invalid or expired.')
                c.execute('UPDATE users SET password=? WHERE id=?',(hash_password(password),reset['user_id']));c.execute('DELETE FROM resets WHERE user_id=?',(reset['user_id'],));c.execute('DELETE FROM sessions WHERE user_id=?',(reset['user_id'],))
            return self.respond(200,{'message':'Password changed. Please sign in.'})
        if path=='/api/estimate':return self.respond(200,estimate(data))
        if path=='/api/inquiries':
            self.limit('inquiry',6,3600);u=self.user(False)
            name=text(data,'name',100);email=email_address(text(data,'email',254));subject=text(data,'subject',160);message=text(data,'message',5000)
            if data.get('consent') is not True:raise Problem(400,'Please consent to storing your enquiry so we can respond.')
            brief=data.get('brief',{});configuration=data.get('configuration')
            if not isinstance(brief,dict) or len(json.dumps(brief))>12000:raise Problem(400,'Brief is too large.')
            price=estimate(configuration) if isinstance(configuration,dict) else None
            with database() as c:
                iid=c.execute('INSERT INTO inquiries(user_id,email,name,subject,message,brief,estimate,created) VALUES(?,?,?,?,?,?,?,?)',(u['id'] if u else None,email,name,subject,message,json.dumps(brief),json.dumps(price),now())).lastrowid
                if u:event(c,u['id'],'Enquiry received',subject)
            body=f'Enquiry #{iid}\n{name}\n{email}\n{subject}\n\n{message}\n\nBrief:\n{json.dumps(brief,indent=2)}\n\nEstimate:\n{json.dumps(price,indent=2)}'
            agency=mail(os.environ.get('NVTRA_INQUIRY_EMAIL','nvtra.official@icloud.com'),f'NVTRA enquiry #{iid}',body)
            copy=mail(email,f'Your NVTRA brief #{iid}',body) if data.get('emailCopy') is True else 'not_requested'
            with database() as c:c.execute('UPDATE inquiries SET email_status=? WHERE id=?',(agency,iid))
            return self.respond(201,{'id':iid,'stored':True,'agencyEmail':agency,'copyEmail':copy})
        if path=='/api/saved':
            u=self.user();title=text(data,'title',100);cfg=data.get('configuration',{})
            if not isinstance(cfg,dict) or len(json.dumps(cfg))>15000:raise Problem(400,'Configuration is too large.')
            with database() as c:
                if c.execute('SELECT count(*) FROM saved WHERE user_id=?',(u['id'],)).fetchone()[0]>=100:raise Problem(400,'Saved-item limit reached. Delete an item first.')
                sid=c.execute('INSERT INTO saved(user_id,title,configuration,created) VALUES(?,?,?,?)',(u['id'],title,json.dumps(cfg),now())).lastrowid;event(c,u['id'],'Direction saved',title)
            return self.respond(201,{'id':sid})
        if path=='/api/saved/delete':
            u=self.user()
            with database() as c:c.execute('DELETE FROM saved WHERE id=? AND user_id=?',(data.get('id'),u['id']))
            return self.respond(200,{'ok':True})
        if path=='/api/bookings':
            u=self.user();note=text(data,'note',1000,False)
            with database() as c:
                c.execute('BEGIN IMMEDIATE');slot=c.execute('SELECT * FROM slots WHERE id=?',(data.get('slotId'),)).fetchone()
                if not slot or slot['starts']<=dt.datetime.now(dt.timezone.utc).isoformat():raise Problem(400,'This meeting slot is no longer available.')
                bid=c.execute('INSERT INTO bookings(slot_id,user_id,note,created) VALUES(?,?,?,?)',(slot['id'],u['id'],note,now())).lastrowid;event(c,u['id'],'Meeting booked',slot['starts'])
            return self.respond(201,{'id':bid,'starts':slot['starts'],'message':'Your 30-minute meeting is reserved. View it in your dashboard.'})
        if path=='/api/bookings/cancel':
            u=self.user()
            with database() as c:
                deleted=c.execute('DELETE FROM bookings WHERE id=? AND user_id=?',(data.get('id'),u['id'])).rowcount
                if not deleted:raise Problem(404,'Booking not found.')
                event(c,u['id'],'Meeting cancelled')
            return self.respond(200,{'ok':True})
        if path=='/api/health':self.limit('health',3,600);return self.respond(200,health(text(data,'url',2000)))
        if path=='/api/assistant':
            self.limit('assistant',15,600);question=text(data,'message',1200)
            words=set(re.findall(r'\w+',question.lower())) - {'what','does','the','a','an','is','are','do','you','my','i','it','to','can','how','for','of','and','in'}
            ranked=sorted(CONTENT['faqs']+CONTENT['services']+CONTENT['articles'],key=lambda f:3*len(words&set(re.findall(r'\w+',f['title'].lower())))+len(words&set(re.findall(r'\w+',f['body'].lower()))),reverse=True)
            key=os.environ.get('GEMINI_API_KEY')
            if key:
                prompt='You are NVTRA support. Answer only from the following studio facts. Never invent projects, availability, prices or delivery. Do not claim to perform actions. Do not request passwords or payment details. If unknown, suggest an enquiry. Keep the answer under 120 words. Facts: '+json.dumps(CONTENT)+'\nPrices: '+json.dumps(PRICING)+'\nVisitor question: '+question
                try:
                    model=os.environ.get('GEMINI_MODEL','gemini-2.5-flash')
                    if not re.fullmatch(r'[a-zA-Z0-9.-]+',model):raise ValueError()
                    result=json_remote('https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',{'contents':[{'parts':[{'text':prompt}]}],'generationConfig':{'maxOutputTokens':350}}, {'x-goog-api-key':key},25)
                    answer=result['candidates'][0]['content']['parts'][0]['text']
                    return self.respond(200,{'answer':answer,'mode':'Gemini','links':ranked[:2]})
                except Exception:mode='FAQ fallback — AI provider unavailable'
            else:mode='Studio FAQ — AI is not configured'
            return self.respond(200,{'answer':ranked[0]['body'] if words else 'Tell us what you would like to build.','mode':mode,'links':ranked[:2]})
        match=re.fullmatch(r'/api/projects/(\d+)/(comments|uploads|approve)',path)
        if match:
            u=self.user();pid=int(match[1]);action=match[2]
            with database() as c:
                p=self.project(c,pid,u)
                if action=='comments':c.execute('INSERT INTO comments(project_id,user_id,body,created) VALUES(?,?,?,?)',(pid,u['id'],text(data,'body',4000),now()))
                elif action=='approve':
                    changed=c.execute("UPDATE milestones SET status='approved',updated=? WHERE id=? AND project_id=? AND status='review'",(now(),data.get('milestoneId'),pid)).rowcount
                    if not changed:raise Problem(409,'Only milestones awaiting review can be approved.')
                    event(c,p['user_id'],'Milestone approved',p['title'])
                else:
                    name=text(data,'name',120)
                    if '/' in name or '\\' in name or any(ord(ch)<32 for ch in name):raise Problem(400,'Invalid filename.')
                    extension=Path(name).suffix.lower()
                    if extension not in ['.pdf','.png','.jpg','.jpeg','.txt']:raise Problem(400,'Upload PDF, PNG, JPEG or plain text files.')
                    try:raw=base64.b64decode(text(data,'content',7*1024*1024),validate=True)
                    except ValueError:raise Problem(400,'Invalid file encoding.')
                    if not 0<len(raw)<=5*1024*1024:raise Problem(413,'Files must be between 1 byte and 5 MB.')
                    signatures={'.pdf':b'%PDF-', '.png':b'\x89PNG\r\n\x1a\n','.jpg':b'\xff\xd8\xff','.jpeg':b'\xff\xd8\xff'}
                    if extension in signatures and not raw.startswith(signatures[extension]):raise Problem(400,'File contents do not match the extension.')
                    if extension=='.txt':
                        try:raw.decode('utf-8')
                        except UnicodeDecodeError:raise Problem(400,'Text files must use UTF-8.')
                    c.execute('BEGIN IMMEDIATE')
                    size=c.execute('SELECT COALESCE(SUM(size),0) FROM uploads WHERE project_id=?',(pid,)).fetchone()[0]
                    if size+len(raw)>50*1024*1024:raise Problem(413,'Project upload quota is 50 MB. Contact the studio.')
                    folder=DATA/'uploads';folder.mkdir(exist_ok=True,mode=0o700);filename=secrets.token_hex(24)
                    (folder/filename).write_bytes(raw);os.chmod(folder/filename,0o600)
                    c.execute('INSERT INTO uploads(project_id,user_id,name,path,size,created) VALUES(?,?,?,?,?,?)',(pid,u['id'],name,filename,len(raw),now()))
                    event(c,p['user_id'],'Content uploaded',name)
            return self.respond(201,{'ok':True})
        if path.startswith('/api/admin/'):
            self.admin()
            with database() as c:
                if path=='/api/admin/projects':
                    uid=data.get('userId')
                    if not c.execute('SELECT id FROM users WHERE id=?',(uid,)).fetchone():raise Problem(400,'Select an existing client account.')
                    title=text(data,'title',150);pid=c.execute('INSERT INTO projects(user_id,title,summary,created) VALUES(?,?,?,?)',(uid,title,text(data,'summary',3000),now())).lastrowid
                    for stage in ['Discovery','Design','Development','Launch']:c.execute('INSERT INTO milestones(project_id,title,updated) VALUES(?,?,?)',(pid,stage,now()))
                    event(c,uid,'Project accepted',title)
                    c.commit()  # Commit before exposing the new project ID to another request.
                    return self.respond(201,{'id':pid})
                if path=='/api/admin/milestones':
                    status=text(data,'status',30)
                    if status not in ['planned','active','review','approved']:raise Problem(400,'Invalid milestone status.')
                    url=text(data,'designUrl',2000,False)
                    if url and (urllib.parse.urlsplit(url).scheme!='https' or not urllib.parse.urlsplit(url).netloc):raise Problem(400,'Design review links must use HTTPS.')
                    row=c.execute('SELECT p.user_id,p.title FROM milestones m JOIN projects p ON m.project_id=p.id WHERE m.id=?',(data.get('id'),)).fetchone()
                    if not row:raise Problem(404,'Milestone not found.')
                    c.execute('UPDATE milestones SET status=?,design_url=?,updated=? WHERE id=?',(status,url,now(),data.get('id')));event(c,row['user_id'],'Project progress updated',row['title'])
                elif path=='/api/admin/slots':
                    try:
                        starts=dt.datetime.fromisoformat(text(data,'starts',60))
                        if starts.tzinfo is None:raise ValueError()
                        starts=starts.astimezone(dt.timezone.utc)
                    except ValueError:raise Problem(400,'Enter a valid meeting time.')
                    if starts<=dt.datetime.now(dt.timezone.utc):raise Problem(400,'Meeting time must be in the future.')
                    overlap=c.execute('SELECT id FROM slots WHERE starts>? AND starts<?',((starts-dt.timedelta(minutes=30)).isoformat(),(starts+dt.timedelta(minutes=30)).isoformat())).fetchone()
                    if overlap:raise Problem(409,'Meeting slots must be at least 30 minutes apart.')
                    c.execute('INSERT INTO slots(starts) VALUES(?)',(starts.isoformat(),))
                elif path=='/api/admin/slots/delete':
                    if c.execute('SELECT id FROM bookings WHERE slot_id=?',(data.get('id'),)).fetchone():raise Problem(409,'This slot has a booking; contact the client before cancelling.')
                    c.execute('DELETE FROM slots WHERE id=?',(data.get('id'),))
                elif path=='/api/admin/showcase':
                    url=text(data,'url',2000);parts=urllib.parse.urlsplit(url)
                    if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:raise Problem(400,'Use a public HTTPS project link.')
                    title=text(data,'title',150);summary=text(data,'summary',3000);category=text(data,'category',60)
                    c.execute('INSERT INTO showcase(title,summary,category,url,created) VALUES(?,?,?,?,?)',(title,summary,category,url,now()))
                    event(c,None,'Project published: '+title,summary,True)
                elif path=='/api/admin/activity':event(c,None,text(data,'title',150),text(data,'body',3000),True)
                else:raise Problem(404,'Endpoint not found.')
            return self.respond(201,{'ok':True})
        raise Problem(404,'Endpoint not found.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8080);parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--create-admin',metavar='EMAIL');args=parser.parse_args();init_db()
    if args.create_admin:
        import getpass
        email=email_address(args.create_admin);password=password_input({'password':getpass.getpass('New admin password (12+ characters): ')})
        with database() as c:
            c.execute("INSERT INTO users(email,name,password,role,created) VALUES(?,?,?,'admin',?) ON CONFLICT(email) DO UPDATE SET role='admin',password=excluded.password",(email,'NVTRA Studio',hash_password(password),now()))
            c.execute('DELETE FROM sessions WHERE user_id=(SELECT id FROM users WHERE email=?)',(email,))
        print('Studio administrator configured.');return
    print(f'NVTRA listening on {args.host}:{args.port}; public origin {PUBLIC_URL}',flush=True)
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
if __name__=='__main__':main()
