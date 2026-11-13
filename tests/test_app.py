import os
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from app.phones import needs_unicode, normalize_phone


def _app(directory, **extra):
    config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'DATA_DIR': directory,
        'WTF_CSRF_ENABLED': False,
        'SESSION_COOKIE_SECURE': False,
        'READ_ONLY_MODE': False,
        'LERTIFY_API_KEY': 'test-key',
        'LERTIFY_SENDER': 'Aiolos',
        'DEFAULT_COUNTRY_CODE': '386',
    }
    config.update(extra)
    return create_app(config)


class PhoneTests(unittest.TestCase):
    def test_local_slovenian_number(self):
        self.assertEqual(normalize_phone('040 123 456'), '+38640123456')

    def test_international_forms(self):
        self.assertEqual(normalize_phone('+38640123456'), '+38640123456')
        self.assertEqual(normalize_phone('0038640123456'), '+38640123456')
        self.assertEqual(normalize_phone('38640123456'), '+38640123456')

    def test_rejects_garbage(self):
        with self.assertRaises(ValueError):
            normalize_phone('abc')
        with self.assertRaises(ValueError):
            normalize_phone('')

    def test_unicode_detection(self):
        self.assertFalse(needs_unicode('Hello'))
        self.assertTrue(needs_unicode('Živjo'))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = _app(self.tmp.name)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _setup_admin(self, username='admin', password='secret'):
        return self.client.post('/setup/', data={
            'username': username,
            'password': password,
            'password_2': password,
        }, follow_redirects=True)

    def test_setup_login_and_dashboard(self):
        first = self.client.get('/', follow_redirects=True)
        self.assertIn(b'Create the first admin account', first.data)

        created = self._setup_admin()
        self.assertIn(b'Dashboard', created.data)
        self.assertNotIn(b'$6$', created.data)

        self.client.get('/logout/', follow_redirects=True)
        signed_in = self.client.post('/login/', data={
            'username': 'admin',
            'password': 'secret',
        }, follow_redirects=True)
        self.assertIn(b'Dashboard', signed_in.data)
        send_page = self.client.get('/send/')
        self.assertEqual(send_page.status_code, 200)
        self.assertIn(b'id="sms-body"', send_page.data)

    def test_api_send_stores_hash_and_logs(self):
        self._setup_admin()
        self.client.post('/admin/users/new/', data={
            'id': 'new',
            'username': 'home',
            'password': 'secret',
            'password_2': 'secret',
            'role': '2',
            'status': '1',
        }, follow_redirects=True)

        issued = self.client.post('/admin/users/2/token/', follow_redirects=True)
        token = self._token_from(issued.data)
        self.assertTrue(token)
        self.assertNotIn(token.encode(), self.client.get('/admin/users/').data)

        with self.app.app_context():
            from app.db import get_db
            row = get_db().execute('SELECT api_token_hash FROM users WHERE username = ?', ('home',)).fetchone()
            self.assertNotEqual(row['api_token_hash'], token)
            self.assertEqual(len(row['api_token_hash']), 64)

        payload = {
            'messages': [{'messageId': 'msg-1', 'destination': '+38640123456'}],
            'status': 'accepted',
            'segmentCount': 1,
        }
        with patch('app.lertify.requests.post') as post:
            post.return_value.status_code = 202
            post.return_value.json.return_value = payload
            response = self.client.post('/api/v1/sms', json={
                'to': '040123456',
                'message': 'Živjo',
            }, headers={'Authorization': f'Bearer {token}'})

        self.assertEqual(response.status_code, 202)
        body = response.get_json()
        self.assertEqual(body['destination'], '+38640123456')
        self.assertEqual(body['messageId'], 'msg-1')
        sent = post.call_args.kwargs['json']
        self.assertEqual(sent['sender'], 'Aiolos')
        self.assertEqual(sent['destinations'], ['+38640123456'])
        self.assertTrue(sent['message']['isUnicode'])
        self.assertEqual(post.call_args.kwargs['headers']['apikey'], 'test-key')

        with patch('app.lertify.requests.post') as web_post:
            web_post.return_value.status_code = 202
            web_post.return_value.json.return_value = {
                'messages': [{'messageId': 'msg-2', 'destination': '+38640999888'}],
                'status': 'accepted',
                'segmentCount': 1,
            }
            page = self.client.post('/send/', data={'to': '040999888', 'message': 'Hello'},
                                    follow_redirects=True)
        self.assertIn(b'+38640999888', page.data)
        self.assertFalse(web_post.call_args.kwargs['json']['message']['isUnicode'])

        log = self.client.get('/messages/')
        self.assertIn(b'+38640123456', log.data)
        self.assertIn('Živjo'.encode(), log.data)

        self.client.post('/admin/users/2/token/revoke/', follow_redirects=True)
        revoked = self.client.post('/api/v1/sms', json={'to': '040123456', 'message': 'again'},
                                   headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(revoked.status_code, 401)

    def test_read_only_user_cannot_send(self):
        self._setup_admin()
        self.client.post('/admin/users/new/', data={
            'id': 'new',
            'username': 'guest',
            'password': 'secret',
            'password_2': 'secret',
            'role': '3',
            'status': '1',
        })
        issued = self.client.post('/admin/users/2/token/', follow_redirects=True)
        token = self._token_from(issued.data)
        response = self.client.post('/api/v1/sms', json={'to': '040123456', 'message': 'Hi'},
                                    headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 403)

    def test_missing_lertify_config(self):
        bare = _app(os.path.join(self.tmp.name, 'bare'), LERTIFY_API_KEY='', LERTIFY_SENDER='')
        client = bare.test_client()
        client.post('/setup/', data={
            'username': 'admin',
            'password': 'secret',
            'password_2': 'secret',
        })
        client.post('/admin/users/new/', data={
            'id': 'new',
            'username': 'home',
            'password': 'secret',
            'password_2': 'secret',
            'role': '2',
            'status': '1',
        })
        issued = client.post('/admin/users/2/token/', follow_redirects=True)
        token = self._token_from(issued.data)
        response = client.post('/api/v1/sms', json={'to': '040123456', 'message': 'Hi'},
                               headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 503)

    def test_bad_number_and_bad_token(self):
        self._setup_admin()
        missing = self.client.post('/api/v1/sms', json={'to': '040123456', 'message': 'Hi'})
        self.assertEqual(missing.status_code, 401)

        self.client.post('/admin/users/new/', data={
            'id': 'new',
            'username': 'home',
            'password': 'secret',
            'password_2': 'secret',
            'role': '2',
            'status': '1',
        })
        issued = self.client.post('/admin/users/2/token/', follow_redirects=True)
        token = self._token_from(issued.data)
        bad = self.client.post('/api/v1/sms', json={'to': 'nope', 'message': 'Hi'},
                               headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(bad.status_code, 400)

    def _token_from(self, page: bytes) -> str:
        marker = b'id="new-api-token"'
        start = page.find(marker)
        self.assertNotEqual(start, -1)
        chunk = page[start:start + 400]
        open_end = chunk.find(b'>')
        close = chunk.find(b'</code>')
        return chunk[open_end + 1:close].decode().strip()


if __name__ == '__main__':
    unittest.main()
