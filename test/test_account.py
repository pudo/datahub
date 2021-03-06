import unittest
import json

from datahub import core
from datahub import model

JSON = 'application/json'

from util import make_test_app, tear_down_test_app
from util import create_fixture_user, AUTHZ

class ProfileTestCase(unittest.TestCase):

    def setUp(self):
        self.app = make_test_app()
        create_fixture_user(self.app)

    def tearDown(self):
        tear_down_test_app()

    def test_account_profile_get(self):
        res = self.app.get('/api/v1/account/no-such-user')
        assert res.status.startswith("404"), res.status
        res = self.app.get('/api/v1/account/fixture', 
                headers={'Accept': JSON})
        assert res.status.startswith("200"), res.status
        body = json.loads(res.data)
        assert body['name']=='fixture', body

    def test_account_profile_put(self):
        res = self.app.get('/api/v1/account/fixture', 
                headers={'Accept': JSON})
        body = json.loads(res.data)

        body['name']='fixture-renamed'
        res = self.app.put('/api/v1/account/fixture', 
                data=body, 
                headers={'Accept': JSON, 'Authorization': AUTHZ})
        body = json.loads(res.data)
        assert body['name']=='fixture-renamed', body

        res = self.app.get('/api/v1/stream/account/1', 
                headers={'Accept': JSON})
        body = json.loads(res.data)
        assert body[0]['type']=='account_updated', body

    def test_account_profile_put_noauth(self):
        body = {'name': 'invalid'}
        res = self.app.put('/api/v1/account/fixture', 
                data=body,
                headers={'Accept': JSON})
        assert res.status.startswith("403"), res

    def test_account_profile_put_invalid_name(self):
        body = {'name': 'fixture renamed invalid'}
        res = self.app.put('/api/v1/account/fixture', 
                data=body,
                headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        body = json.loads(res.data)
        assert 'name' in body['errors'], body

        res = self.app.get('/api/v1/stream/account/1', 
                headers={'Accept': JSON})
        body = json.loads(res.data)
        assert len(body)==1, body

    def test_account_profile_put_invalid_email(self):
        body = {'name': 'fixture', 'email': 'bar', 'full_name': 'la la'}
        res = self.app.put('/api/v1/account/fixture', 
                data=body,
                headers={'Accept': JSON, 'Authorization': AUTHZ})
        assert res.status.startswith("400"), res
        body = json.loads(res.data)
        assert 'email' in body['errors'], body


class UserWebInterfaceTestCase(unittest.TestCase):

    def tearDown(self):
        tear_down_test_app()

    def setUp(self):
        self.app = make_test_app()
        create_fixture_user(self.app)

    def test_register_user(self):
        form_content = {'name': 'test_user', 
                        'full_name': 'Test User',
                        'email': 'test_user@datahub.net',
                        'password': 'password',
                        'password_confirm': 'password'}
        res = self.app.post('/register', data=form_content)
        assert res.status.startswith("302"), res
        res = self.app.get('/api/v1/account/test_user', 
                headers={'Accept': JSON})
        assert res.status.startswith("200"), res.status
        body = json.loads(res.data)
        assert body['full_name']=='Test User', body

        res = self.app.get('/test_user')
        assert res.status.startswith("200"), res.status
        assert 'signed up' in res.data, res.data


    def test_register_user_invalid_name(self):
        form_content = {'name': 'test user', 
                        'full_name': 'Test User',
                        'email': 'test_user@datahub.net',
                        'password': 'password',
                        'password_confirm': 'password'}
        res = self.app.post('/register', data=form_content)
        assert res.status.startswith("200"), res
        res = self.app.get('/api/v1/profile/test user', 
                headers={'Accept': JSON})
        assert res.status.startswith("404"), res.status

    def test_login_user(self):
        app = make_test_app(use_cookies=True)
        form_content = {'login': 'fixture', 
                        'password': 'password'}
        res = app.post('/login', data=form_content,
                follow_redirects=True)
        assert res.status.startswith("200"), res
        assert 'fixture' in res.data, res

        form_content = {'login': 'fixture', 
                        'password': 'wrong password'}
        res = self.app.post('/login', data=form_content)
        assert res.status.startswith("200"), res
    
    def test_basic_auth(self):
        auth = 'fixture:password'.encode('base64')
        res = self.app.get('/', 
                headers={'Authorization': 'Basic ' + auth})
        assert res.status.startswith("200"), res
        assert 'fixture' in res.data, res

    def test_basic_auth_invalid_credentials(self):
        auth = 'fixture:buzzword'.encode('base64')
        res = self.app.get('/', 
                headers={'Authorization': 'Basic ' + auth})
        assert res.status.startswith("401"), res

    def test_edit_profile(self):
        auth = 'Basic ' + 'fixture:password'.encode('base64')
        res = self.app.get('/profile', 
                headers={'Authorization': auth})
        assert res.status.startswith("200"), res
        assert 'fixture@datahub.net' in res.data, res

        form_content = {'name': 'fixture', 
                        'full_name': 'Test User',
                        'email': 'test_user@datahub.net',
                        'password': 'password',
                        'password_confirm': 'password'}
        res = self.app.post('/profile', data=form_content,
                headers={'Authorization': auth})
        assert res.status.startswith("200"), res
        assert 'test_user@datahub.net' in res.data, res
        assert 'fixture@datahub.net' not in res.data, res

if __name__ == '__main__':
    unittest.main()

