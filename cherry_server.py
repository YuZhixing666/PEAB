__author__ = 'samyu'

import peab
import cherrypy

from cherrypy._cpcompat import ntou

import json,os




class Content:
    def __init__(self, popName = "pool" ):
        self.population = peab.Population(popName)
        self.population.initialize()


    @cherrypy.expose
    @cherrypy.tools.json_in(content_type=[ntou('application/json'),
                                          ntou('text/javascript'),
                                          ntou('application/json-rpc')
    ])
    def peab(self):
        if cherrypy.request.json:
            obj = cherrypy.request.json
            method = obj["method"]
            _id = obj["id"]

            cherrypy.log('Request:'+method+'   WorkerId: '+_id)
            
            if "params" in obj:
                params = obj["params"]
            else:
                return json.dumps({"result" : None,"error":
                    {"code": -32604, "message": "Params empty"}, "id": _id})
            
            # process the data
            cherrypy.response.headers['Content-Type']= 'text/json-comment-filtered'
            result = None
            if method == "initialize":
                result = self.population.initialize()
                return json.dumps({"result" : result,"error": None, "id": _id})

            if method == "getSample":
                result = self.population.get_sample(params['size'])
                if result:
                    return json.dumps({"result" : result,"error": None, "id": _id})
                else:
                    return json.dumps({"result" : None,"error":
                        {"code": -32601, "message": "PEAB empty"}, "id": _id})
            elif method == "respawn":
                result = self.population.respawn(params[0])
            elif method == "putSample":
                result = self.population.put_sample(params['sample'])
            elif method == "putIndividual":
                result = self.population.put_individual(**params[0])
            elif method == "getIndividual":
                result = {} #todo
            elif method == "put_subpop":
                result = self.population.put_subpopulation(params['subpop'])
            elif method == "size":
                result = self.population.size()
            elif method == "found":
                self.population.found_it()
            elif method == "isFound":
                result = self.population.isFound()

            elif method == "getReunionTime":
                result = self.population.getReunionTime()


            return json.dumps({"result" : result,"error": None, "id": _id})

        else:
            print "blah"
            return "blah"


    @cherrypy.expose
    def index(self):
        return "Server work"

if __name__ == '__main__':


    cherrypy.config.update(
        {
        'server.socket_host': '127.0.0.1',
        'server.socket_port': int(os.environ.get('PORT', '3000')),
        'server.environment':  'production',
        'server.thread_pool':   200,
        'tools.sessions.on':    False,
        'server.socket_timeout': 30
    })

    from cherrypy.process import servers

    def fake_wait_for_occupied_port(host, port):
        return

    servers.wait_for_occupied_port = fake_wait_for_occupied_port

    cherrypy.quickstart(Content('pool'))
    cherrypy.log('starting cherrypy...')