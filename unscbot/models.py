# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from random import random, randint
import requests
import json

# Create your models here.
class Bot(object):
    
    def __init__(self, botid):
        self.botid = botid
        self.items = []
        
    def initialise(self):
        return self.interact(action='pass')
        
    def live(self):
        ret = self.initialise()
        
        if not ret:
            print 'ERROR: could not connect to the API'
        else:
            import time
            while True:
                #self.interact(action='walk', target=self.world['id'], angle=random())
                self.select_action()
                self.call_selected_action()
                time.sleep(.01)
        
        return ret
    
    def select_action(self):
        actions = [{'action': 'pass'}]
        for item in self.items:
            for action in item.get('actions', []):
                action['targetid'] = item['id']
                actions.append(action)
        # select random action
        self.action = actions[randint(0, len(actions) - 1)]
        # select arguments
        for k in self.action.keys():
            if k not in ['action', 'targetid']:
                self.action[k] = random()
        return self.action
    
    def call_selected_action(self):
        self.interact(**self.action)

    def interact(self, action, targetid=None, **kwargs):
        ret = False
        
        if targetid is None:
            targetid = self.botid
        
        # https://stackoverflow.com/questions/17301938/making-a-request-to-a-restful-api-using-python
        kwargs['actorid'] = self.botid
        import urllib
        qs = urllib.urlencode(kwargs)
        url = 'http://localhost:8000/api/1/things/%s/actions/%s?%s' % (targetid, action, qs)
        print url
        
        res = None
        try:
            res = requests.get(url)
        except requests.exceptions.ConnectionError:
            # fails silently
            pass
        
        if res and res.ok:
            res_content = json.loads(res.content)
            
            if res_content['data']:
                self.items = res_content['data']['items']
                for item in self.items:
                    if item['module'] == 'world':
                        self.world = item
                    if item['id'] == self.botid:
                        self.data = item
                ret = True
            else:
                print 'WARNING: interaction error %s' % res_content['error']
        else:
            if res:
                print 'WARNING: API request error %s' % res.status_code
            else:
                print 'WARNING: API connection error'
        
        return ret