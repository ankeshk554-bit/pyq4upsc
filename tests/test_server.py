import io
import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
import server

class TutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.url = f'http://127.0.0.1:{cls.http.server_port}'
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close()

    def request(self, data, origin=None):
        headers = {'Content-Type':'application/json'}
        if origin: headers['Origin'] = origin
        try:
            with urlopen(Request(self.url+'/api/explain', data=json.dumps(data).encode(), headers=headers)) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def payload(self):
        return {'question':'Article? (a) 15 (b) 17', 'subject':'Polity', 'answer':'b', 'messages':[{'role':'user','content':'Explain'}]}

    def test_missing_key(self):
        with patch.dict(server.os.environ, {'AI_API_KEY':'', 'OPENAI_API_KEY':''}):
            status, body = self.request(self.payload())
        self.assertEqual(status, 503); self.assertIn('not connected', body['error'])

    def test_invalid_input(self):
        data = self.payload(); data['messages'][0]['role'] = 'system'
        self.assertEqual(self.request(data)[0], 400)

    def test_cross_origin(self):
        self.assertEqual(self.request(self.payload(), 'https://example.com')[0], 403)

    def test_provider_context_and_reply(self):
        reply = io.BytesIO(json.dumps({'choices':[{'message':{'content':'Article 17 abolishes untouchability.'}}]}).encode())
        with patch.dict(server.os.environ, {'AI_API_KEY':'test-only-key'}), patch.object(server, 'urlopen', return_value=reply) as provider:
            status, body = self.request(self.payload())
        self.assertEqual(status, 200); self.assertIn('Article 17', body['reply'])
        request = provider.call_args.args[0]
        payload = json.loads(request.data)
        self.assertIn('Provided answer key: B', payload['messages'][0]['content'])
        self.assertEqual(payload['messages'][-1]['content'], 'Explain')

    def test_unknown_answer_can_be_explained(self):
        data = self.payload(); data['answer'] = ''
        reply = io.BytesIO(json.dumps({'choices':[{'message':{'content':'No answer key was supplied.'}}]}).encode())
        with patch.dict(server.os.environ, {'AI_API_KEY':'test-only-key'}), patch.object(server, 'urlopen', return_value=reply) as provider:
            status, body = self.request(data)
        self.assertEqual(status, 200)
        self.assertIn('Provided answer key: unavailable', json.loads(provider.call_args.args[0].data)['messages'][0]['content'])

    def test_provider_routing(self):
        for provider, key_name, endpoint, model in (
            ('deepseek', 'DEEPSEEK_API_KEY', 'https://api.deepseek.com/chat/completions', 'deepseek-chat'),
            ('openrouter', 'OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1/chat/completions', 'openrouter/free'),
        ):
            with self.subTest(provider=provider):
                reply = io.BytesIO(json.dumps({'choices':[{'message':{'content':'Study explanation.'}}]}).encode())
                with patch.dict(server.os.environ, {'AI_PROVIDER':provider, key_name:'provider-test-key'}), patch.object(server, 'urlopen', return_value=reply) as call:
                    status, body = self.request(self.payload())
                self.assertEqual(status, 200)
                request = call.call_args.args[0]
                self.assertEqual(request.full_url, endpoint)
                self.assertEqual(request.get_header('Authorization'), 'Bearer provider-test-key')
                self.assertEqual(json.loads(request.data)['model'], model)

    def test_private_files_not_served(self):
        for path in ('/.git/config', '/server.py', '/.env'):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.url+path)
            self.assertEqual(error.exception.code, 404)

if __name__ == '__main__': unittest.main()
