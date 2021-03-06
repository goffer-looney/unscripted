from django.core.management.base import BaseCommand, CommandError
#from unsccore.models import World, Box
from unsccore.things.thing import Thing, ThingParentError
from unsccore.things.world import World
from unsccore import mogels
from unsccore.api_client import API_Client
import time
from unsccore.api import UnscriptedAPI
from unsccore.dbackends.utils import scall

class Command(BaseCommand):
    help = 'Unscripted core management commands'

    def add_arguments(self, parser):
        parser.add_argument('action', metavar='action', nargs=1, type=str)
        parser.add_argument('cargs', metavar='cargs', nargs='*', type=str)

    def handle(self, *args, **options):
        self.options = options
        self.cargs = options['cargs']
        
        self.api = API_Client()
        
        action = options['action'][0]
        
        found = 0
        
        if action == 'runserver':
            self.runserver()
            found = 1

        if action == 'compile':
            self.compile()
            found = 1

        if action == 'info':
            self.info()
            found = 1

        if action == 'crunch':
            self.crunch()
            found = 1

        if action == 'new':
            scall(self.api.create(module='world'))
            found = 1

        if action == 'reindex':
            self.reindex()
            found = 1

        if action == 'uncache':
            from django.core.cache import cache
            cache.clear()
            found = 1

        if not found:
            print('ERROR: action not found (%s)' % action)
            print(self.get_help_string())
        
        print('done')
        
    def get_help_string(self):
        return '''
actions:
    new
    info
    crunch
    compile
    runserver
    reindex
    uncache
        '''

    def info(self):
        worlds = scall(self.api.find(module='world'))
        if worlds is None:
            print('ERROR: cannot connect to the API')
        else:
            for world in worlds:
                things = scall(self.api.find(rootid=world['id']))
                print('%s, %s, %s'  % (world['id'], world['created'], len(things)))
        
    def crunch(self):
        scall(self.api.delete())
        
    def compile(self):
        ret = Thing.cache_actions()
        print(ret)
        
        world = Thing.new(module='world')
        print(world._generate_actions())
        print(world.get_actions())
        
    def reindex(self):
        thing = Thing()
        q = thing.objects.all()
        q.create_index('parentid', unique=False)
        q.create_index('rootid', unique=False)
        q.create_index('module', unique=False)
        
    def runserver(self):
        import asyncio, uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        hostname, port = ('localhost', '8000')
        if self.cargs:
            parts = self.cargs[0].split(':')
            if parts[0]:
                hostname = parts[0]
            if len(parts) > 1:
                port = parts[1]
        print('Websocket server running on %s:%s' % (hostname, port))
        
        server = UnscriptedAPI()
        server.listen_to_websocket(hostname, port)
        
    
