#!/usr/bin/env python3
"""
Magic eight-ball web service that can be used from mattermost
"""

from argparse import ArgumentParser
import json
import os
import re
from random import Random

import urllib3
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule

RANDOM = Random()
ADHOC_RESPONSE_CHANCE = 0.01


CHECKER = re.compile(r"(@?)eightbot|eightball(:?)\s*.*\?$")


def choose() -> str:
    """choose a random response"""
    responses = [
        "It is certain",
        "It is decidedly so",
        "Without a doubt",
        "Yes definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
        "Reply hazy, try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful",
    ]
    return RANDOM.choice(responses)



class Eightbot:
    """Eight-ball routing and such"""

    def __init__(self):
        self.url_map = Map([
            Rule('/', endpoint='root'),
            Rule('/outgoing', endpoint='outgoing'),
            Rule('/slash', endpoint='slash'),
            Rule('/resources/icon.svg', endpoint='icon'),
        ])

    def wsgi_app(self, environ, start_response):
        """do stuff"""
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def dispatch_request(self, request):
        """dispatch the request"""
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            (endpoint, values) = adapter.match()
            return getattr(self, f'on_{endpoint}')(request, **values)
        except HTTPException as err:
            return err

    @staticmethod
    def on_icon(_request):
        """return the icon"""
        root = os.path.dirname(os.path.realpath(__file__))
        image = os.path.join(root, 'resources/8_ball_icon.svg')
        fptr = open(image, 'rb')
        return Response(fptr, direct_passthrough=True, mimetype='image/svg+xml')

    @staticmethod
    def on_root(_request):
        """handle root case"""
        return Response(choose())

    @staticmethod
    def on_slash(request):
        """handle slash command"""
        args = decode_args(request)
        text: str = args['text']
        username = args['user_name']
        eightball = choose()
        response_text = f"{username} asks: {text}\n{eightball}"
        response_data = {"response_type": "in_channel",
                         "text": response_text,
                         "username": "eightbot",
                         "icon_url": get_image_url(request)}
        print(f"respond {response_data}")
        response_str = json.dumps(response_data)
        return Response(response_str, mimetype='application/json')

    @staticmethod
    def on_outgoing(request):
        """handle outgoing webhook"""
        args = decode_args(request)
        text: str = args['text']
        if re.match(CHECKER, text):
            eightball = choose()
            response_data = {"response_type": "in_channel",
                             "text": eightball,
                             "username": "eightbot",
                             "icon_url": get_image_url(request)}
            print(f"respond {response_data}")
            response_str = json.dumps(response_data)
            return Response(response_str, mimetype='application/json')
        elif text.endswith('?') and should_give_adhoc_response():
            print("TIME FOR AN AD-HOC RESPONSE, BOYS")
            response_data = {"response_type": "in_channel",
                             "text": choose(),
                             "username": "eightbot"}
            return Response(json.dumps(response_data), mimetype='application/json')
        # Don't respond
        return Response("")

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def decode_args(request: Request) -> dict:
    """Decode json data"""
    if request.content_type == 'application/json':
        return json.loads(request.get_data())
    return request.form


def should_give_adhoc_response():
    """return True if we should give a response randomly"""
    return RANDOM.random() <= ADHOC_RESPONSE_CHANCE


def get_image_url(request: Request) -> str:
    """get the url for the eightbot image"""
    # return "https://upload.wikimedia.org/wikipedia/commons/e/e3/8_ball_icon.svg"
    host = get_host(request)
    return f"{host}/resources/icon.svg"


def get_host(request: Request) -> str:
    """get the host from the Request"""
    base = request.base_url
    url = urllib3.util.url.parse_url(base)
    host = f"{url.scheme}://{url.host}"
    if url.port:
        host += f":{url.port}"
    return host


def main():
    """main function"""
    from werkzeug.serving import run_simple
    matches = add_args(ArgumentParser()).parse_args()
    app = Eightbot()
    if matches.certificate:
        print("Running with TLS")
        run_simple("0.0.0.0", matches.port, app,
                   ssl_context=(f'{matches.certificate}.crt',
                                f'{matches.certificate}.key'))
    elif matches.insecure:
        print("RUNNING UNSECURED")
        run_simple("0.0.0.0", matches.port, app)
    else:
        print("Running with TLS (ad-hoc)")
        run_simple("0.0.0.0", matches.port, app, ssl_context='adhoc')


def add_args(parser: ArgumentParser) -> ArgumentParser:
    """add arguments to the argument parser"""
    cert = parser.add_mutually_exclusive_group()
    cert.add_argument("--certificate", help="TLS certificate to use")
    cert.add_argument("--insecure", action='store_true',
                      help="Run over HTTP instead of over HTTPS")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port to bind to")
    return parser

if __name__ == '__main__':
    main()
