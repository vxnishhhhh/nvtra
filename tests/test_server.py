import base64
import concurrent.futures
import datetime as dt
import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        server.DATA=Path(cls.temp.name);server.DB=server.DATA/'test.sqlite3';server.init_db()
        cls.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.port=cls.http.server_address[1];server.PUBLIC_URL=f'http://127.0.0.1:{cls.port}'
        threading.Thread(target=cls.http.serve_forever,daemon=True).start()
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.temp.cleanup()
    def setUp(self):
        server.RATES.clear()
        with server.database() as c:
            for table in ['showcase','activity','uploads','comments','milestones','projects','bookings','slots','saved','inquiries','resets','sessions','users']:c.execute('DELETE FROM '+table)
        self.env=patch.dict(os.environ,{},clear=True);self.env.start()
        self.addCleanup(self.env.stop)
    def request(self,path,body=None,cookie='',origin=None):
        con=http.client.HTTPConnection('127.0.0.1',self.port,timeout=10)
        headers={'Cookie':cookie}
        if body is not None:headers.update({'Content-Type':'application/json','Origin':origin or server.PUBLIC_URL})
        con.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
        r=con.getresponse();raw=r.read();status=r.status;headers=dict(r.getheaders());con.close()
        result=json.loads(raw) if headers.get('Content-Type','').startswith('application/json') else raw
        return status,result,headers
    def account(self,email='client@example.com',admin=False):
        status,_,headers=self.request('/api/register',{'name':'Test Client','email':email,'password':'a-long-test-password'})
        self.assertEqual(status,200)
        with server.database() as c:
            uid=c.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()[0]
            if admin:c.execute("UPDATE users SET role='admin' WHERE id=?",(uid,))
        return uid,headers['Set-Cookie'].split(';')[0]
    def project(self):
        uid,client=self.account();_,admin=self.account('admin@example.com',True)
        status,result,_=self.request('/api/admin/projects',{'userId':uid,'title':'Private project','summary':'Agreed scope'},admin)
        self.assertEqual(status,201);return result['id'],client,admin
    def test_register_login_logout_and_password_storage(self):
        uid,cookie=self.account();self.assertIn('HttpOnly',self.request('/api/login',{'email':'client@example.com','password':'a-long-test-password'})[2]['Set-Cookie'])
        with server.database() as c:hashed=c.execute('SELECT password FROM users WHERE id=?',(uid,)).fetchone()[0]
        self.assertNotIn('a-long-test-password',hashed)
        self.assertEqual(self.request('/api/dashboard',cookie=cookie)[0],200)
        self.assertEqual(self.request('/api/logout',{},cookie)[0],200)
        self.assertEqual(self.request('/api/dashboard',cookie=cookie)[0],401)
        self.assertEqual(self.request('/api/login',{'email':'client@example.com','password':'wrong'})[0],401)
    def test_cross_origin_and_admin_access_denied(self):
        _,cookie=self.account()
        self.assertEqual(self.request('/api/logout',{},cookie,origin='https://evil.example')[0],403)
        self.assertEqual(self.request('/api/admin',cookie=cookie)[0],403)
        self.assertEqual(self.request('/api/admin/activity',{'title':'Fake','body':'Fake'},cookie)[0],403)
    def test_price_recalculated_and_custom_cost_excluded(self):
        status,result,_=self.request('/api/estimate',{'pages':3,'features':['booking','commerce'],'maintenance':True,'min':1})
        self.assertEqual(status,200);self.assertEqual(result['min'],1499);self.assertEqual(result['max'],2400);self.assertEqual(result['monthly'],99);self.assertEqual(result['custom'],['E-commerce checkout'])
        for pages in [0,101,True,2.5]:self.assertEqual(self.request('/api/estimate',{'pages':pages})[0],400)
        self.assertEqual(self.request('/api/estimate',{'features':['unpriced-invention']})[0],400)
    def test_inquiry_saved_without_false_email_success(self):
        uid,cookie=self.account()
        body={'name':'Client','email':'client@example.com','subject':'Build','message':'My business site','consent':True,'emailCopy':True,'configuration':{'pages':1,'features':[]},'brief':{'theme':'light'}}
        status,result,_=self.request('/api/inquiries',body,cookie);self.assertEqual(status,201);self.assertTrue(result['stored']);self.assertEqual(result['copyEmail'],'not_configured')
        self.assertEqual(len(self.request('/api/dashboard',cookie=cookie)[1]['inquiries']),1)
        body['consent']=False;self.assertEqual(self.request('/api/inquiries',body,cookie)[0],400)
    def test_private_projects_files_and_feedback(self):
        pid,cookie,admin=self.project();_,other=self.account('other@example.com')
        self.assertEqual(self.request(f'/api/projects/{pid}',cookie=other)[0],404)
        upload={'name':'brief.txt','content':base64.b64encode(b'private content').decode()}
        self.assertEqual(self.request(f'/api/projects/{pid}/uploads',upload,cookie)[0],201)
        project=self.request(f'/api/projects/{pid}',cookie=cookie)[1];fileid=project['uploads'][0]['id']
        self.assertEqual(self.request(f'/api/uploads/{fileid}',cookie=other)[0],404)
        status,body,headers=self.request(f'/api/uploads/{fileid}',cookie=cookie);self.assertEqual(body,b'private content');self.assertIn('attachment',headers['Content-Disposition'])
        self.assertEqual(self.request(f'/api/projects/{pid}/comments',{'body':'Please revise the heading'},cookie)[0],201)
        self.assertEqual(self.request('/.data/nvtra.sqlite3')[0],404)
        self.assertEqual(self.request('/server.py')[0],404)
        self.assertEqual(self.request(f'/api/projects/{pid}/uploads',{'name':'bad.png','content':base64.b64encode(b'<script>').decode()},cookie)[0],400)
    def test_milestone_approval_requires_review(self):
        pid,cookie,admin=self.project();m=self.request(f'/api/projects/{pid}',cookie=cookie)[1]['milestones'][0]
        self.assertEqual(self.request(f'/api/projects/{pid}/approve',{'milestoneId':m['id']},cookie)[0],409)
        self.assertEqual(self.request('/api/admin/milestones',{'id':m['id'],'status':'review','designUrl':'https://example.com/design'},admin)[0],201)
        self.assertEqual(self.request(f'/api/projects/{pid}/approve',{'milestoneId':m['id']},cookie)[0],201)
        self.assertEqual(self.request(f'/api/projects/{pid}/approve',{'milestoneId':m['id']},cookie)[0],409)
    def test_booking_race_only_reserves_once(self):
        _,admin=self.account('admin@example.com',True);_,a=self.account('a@example.com');_,b=self.account('b@example.com')
        future=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=2)).isoformat()
        self.assertEqual(self.request('/api/admin/slots',{'starts':future},admin)[0],201)
        slot=self.request('/api/slots')[1]['slots'][0]['id']
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda cookie:self.request('/api/bookings',{'slotId':slot,'note':'Discuss website'},cookie)[0],[a,b]))
        self.assertEqual(sorted(results),[201,409]);self.assertEqual(self.request('/api/slots')[1]['slots'],[])
    def test_private_saved_items_isolated(self):
        _,a=self.account('a@example.com');_,b=self.account('b@example.com');self.request('/api/saved',{'title':'My direction','configuration':{'brief':{'theme':'dark'}}},a)
        self.assertEqual(len(self.request('/api/dashboard',cookie=a)[1]['saved']),1);self.assertEqual(self.request('/api/dashboard',cookie=b)[1]['saved'],[])
    def test_activity_is_empty_until_admin_publishes(self):
        self.assertEqual(self.request('/api/activity')[1]['items'],[])
        _,admin=self.account('admin@example.com',True);self.request('/api/admin/activity',{'title':'Studio update','body':'A real announcement'},admin)
        self.assertEqual(self.request('/api/activity')[1]['items'][0]['title'],'Studio update')
    def test_faq_mode_has_no_fake_ai_claim(self):
        status,result,_=self.request('/api/assistant',{'message':'What does maintenance cost?'})
        self.assertEqual(status,200);self.assertIn('not configured',result['mode']);self.assertIn('R99',result['answer'])
    def test_health_rejects_private_targets_and_handles_provider_failure(self):
        for url in ['http://127.0.0.1','http://169.254.169.254/latest/meta-data','file:///etc/passwd']:
            self.assertEqual(self.request('/api/health',{'url':url})[0],400)
        server.RATES.clear()
        with patch.object(server,'safe_url',return_value='https://example.com'),patch.object(server,'json_remote',side_effect=OSError()):
            status,result,_=self.request('/api/health',{'url':'https://example.com'});self.assertEqual(status,503);self.assertNotIn('scores',result)
    def test_health_reports_only_provider_measurements(self):
        fixture={'lighthouseResult':{'fetchTime':'2026-11-10T12:00:00Z','categories':{'performance':{'score':.77},'seo':{'score':None}},'audits':{'largest-contentful-paint':{'title':'Largest Contentful Paint','displayValue':'2.1 s','score':.8,'scoreDisplayMode':'numeric'}}}}
        with patch.object(server,'safe_url',return_value='https://example.com'),patch.object(server,'json_remote',return_value=fixture):
            r=self.request('/api/health',{'url':'https://example.com'})[1];self.assertEqual(r['scores']['performance'],77);self.assertIsNone(r['scores']['seo']);self.assertEqual(r['metrics']['largest-contentful-paint']['value'],'2.1 s')
    def test_reset_link_single_use_and_invalidates_sessions(self):
        _,cookie=self.account()
        with patch.dict(os.environ,{'SMTP_HOST':'smtp.example.com','SMTP_FROM':'studio@example.com'}),patch.object(server,'mail',return_value='accepted_by_mail_server') as sender:
            self.assertEqual(self.request('/api/password-reset',{'email':'client@example.com'})[0],200)
            token=sender.call_args.args[2].split('token=')[1].split('\n')[0]
        body={'token':token,'password':'replacement-long-password'}
        self.assertEqual(self.request('/api/password-reset/confirm',body)[0],200)
        self.assertEqual(self.request('/api/password-reset/confirm',body)[0],400)
        self.assertEqual(self.request('/api/dashboard',cookie=cookie)[0],401)
    def test_public_showcase_requires_admin_and_is_searchable_data(self):
        _,client=self.account();_,admin=self.account('admin@example.com',True)
        body={'title':'Approved client site','summary':'Client-approved facts','category':'Business','url':'https://example.com'}
        self.assertEqual(self.request('/api/admin/showcase',body,client)[0],403)
        self.assertEqual(self.request('/api/admin/showcase',body,admin)[0],201)
        self.assertEqual(self.request('/api/showcase')[1]['projects'][0]['title'],body['title'])
    def test_auth_rate_limit(self):
        for _ in range(12):self.assertEqual(self.request('/api/login',{'email':'absent@example.com','password':'bad'})[0],401)
        self.assertEqual(self.request('/api/login',{'email':'absent@example.com','password':'bad'})[0],429)

if __name__=='__main__':unittest.main()
