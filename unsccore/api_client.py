import requests
from unsccore.dbackends.utils import json
# http://www.angryobjects.com/2011/10/15/http-with-python-pycurl-by-example/
import pycurl
# TODO: Works with PyPy but is it more efficient than StringIO?
try:
    from cStringIO import StringIO as StringIO
except ImportError:
    # pypy
    from io import BytesIO as StringIO
try:
    from urllib import urlencode
except:
    # python 3
    from urllib.parse import urlencode

class WSSession(object):
    
    def __init__(self, api_root):
        self.socket = None
        self.api_root = api_root
        self._response = None
        
    def get_headers(self):
        return 'NOHEADERS'
    
    def get(self, url):
        #print(url)
        import asyncio
        import websockets
        
        @asyncio.coroutine
        def _connect():
            self.socket = yield from websockets.connect(self.api_root.rstrip('/'))
        
        if self.socket is None:
            asyncio.get_event_loop().run_until_complete(_connect())
            
        api_path = url[len(self.api_root):]
        
        def _send_and_receive(path):
            yield from self.socket.send(api_path)
            self._response = yield from self.socket.recv()
            
        asyncio.get_event_loop().run_until_complete(_send_and_receive(api_path))
            
        return self._response

class PyCurlSession(object):

    def __init__(self):
        c = self.c = pycurl.Curl()
        c.setopt(c.CONNECTTIMEOUT, 20)
        c.setopt(c.TIMEOUT, 20)
        #c.setopt(c.COOKIEFILE, '')
        #c.setopt(c.URL, 'http://myappserver.com/ses1')
        c.setopt(c.FAILONERROR, True)
        c.setopt(c.HTTPHEADER, ['Accept: text/html',
                                'Accept-Charset: UTF-8',
                                'Connection: keep-alive'])
        self.res = ''

    def get_headers(self):
        return self.headers

    def get(self, url):
        self.res = None
        buf = StringIO()
        headers = StringIO()
        self.c.setopt(self.c.WRITEFUNCTION, buf.write)
        self.c.setopt(self.c.HEADERFUNCTION, headers.write)
        self.c.setopt(self.c.URL, url)
        try:
            self.c.perform()
        except pycurl.error as error:
            #errno, errstr = error
            raise error

        self.res = buf.getvalue()
        buf.close()
        self.headers = headers.getvalue()
        headers.close()
        
        return self.res


class UnscriptedApiError(Exception):
    pass


class API_Client(object):

    def __init__(self, api_root=None):
        '''api_root: e.g. http://localhost:8000/api/1/'''
        
        if api_root is None:
            from django.conf import settings
            api_root = settings.UNSCRIPTED_REMOTE_API
    
        self.api_root = api_root
        
        if self.api_root.startswith('ws'): 
            self.session = WSSession(self.api_root)
        else:
            # PyCurl is faster than requests
            self.session = PyCurlSession()
            #self.session = requests.Session()
        
        self.items = None
        
    def action(self, targetid, action, **kwargs):
        return self.send_request('things/%s/actions/%s' %
                                 (targetid, action), **kwargs)

    def delete(self, **query):
        query['@method'] = 'DELETE'
        return self.send_request('things', **query)

    def create(self, **query):
        query['@method'] = 'POST'
        res = self.send_request(query['module'], **query)
        return res[0]

    def stop(self):
        return self.send_request('stop')
    
    def find(self, **query):
        return self.request_things(**query)

    def first(self, **query):
        res = self.find(**query)
        if len(res):
            return res[0]
        return None

    def request_things(self, **query):
        return self.send_request('things', **query)
    
    def send_request(self, path, **query):
        self.items = None

        # https://stackoverflow.com/questions/17301938/making-a-request-to-a-restful-api-using-python
        qs = urlencode(query)
        url = self.api_root + path + '?' + qs
        #print(url)

        res = None
        try:
            res = self.session.get(url)
        except requests.exceptions.ConnectionError as e:
            # fails silently
            raise e

        if res is not None:
            # print res.headers
            # print self.session.get_headers()
            if hasattr(res, 'content'):
                # for requests
                res_content = json.loads(res.content)
            else:
                # for pycurl
                res_content = json.loads(res)
            error = res_content.get('error')
            if error:
                raise UnscriptedApiError(
                    'WARNING: processing error %s' %
                    res_content['error']['message'])

            if res_content['data']:
                self.items = res_content['data']['items']
            else:
                raise UnscriptedApiError('WARNING: unknown processing error')
        else:
            raise UnscriptedApiError('WARNING: API connection error')

        return self.items
