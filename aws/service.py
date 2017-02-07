# coding: utf-8

import sys, os
import glob, re
import requests
import pickle
import json
from urllib import quote
from markdown2 import markdown
from string import Template


web_intro = '''
                <html>
                <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
                <title>The System</title>
                <style>
                * {
                        font-size: 14px;
                        font-family: "PingFang HK", sans-serif;
                        color: #6f4f2c;
                        -webkit-text-size-adjust: none;
                        -webkit-tap-highlight-color: transparent;
                }
                h1 {
                        font-size: larger;
                }
                h3 {
                        font-style: italic;
                }
                h4 {
                        font-weight: normal;
                        font-style: italic;
                }
                code {
                        font-family: monospace;
                }
                li {
                        margin: .4em 0;
                }
                body {
                        #line-height: 1;
                        background: #fff7ee;
                }
                div.item {
                        box-shadow: 5px 5px 5px #6f4f2c;
                        margin: 10px 0px;
                        padding: 10px;
                }
                div.highlight {
                        border: 1px solid #6f4f2c;
                        background: white;
                }
                </style>
                </head>
                <body>
                        <div id="content">
'''

htmlOutro = '''
                        </div>
                </body>
                </html>
'''

def generate_output(key):
  content = resp.json()

  #print json.dumps(content, indent=2, sort_keys=True)

  contents_by_key = {}
  contents = []

  for item in content['Reminders']:
    if item['title'] == key:
      contents.append(item['description'])
    contents_by_key[item['title']] = item['description']

  markd = contents_by_key[key]
  seen = {}
  children = []
  link_regexp = re.compile(r'\[([^\]]*)\]\(awz-([^)]+)\)')
  matches = link_regexp.findall(markd)
  for item in matches:
    key1 = item[1]
    if not key1 in seen:
      children.append(key1)
      seen[key1] = item[0]

  for child_key in children:
    contents.append(contents_by_key[child_key])

  result = ''

  for index, md in enumerate(contents):
    highlight_class = ''
    if index == 0:
      highlight_class = ' highlight'
    result += '<div class = "item' + highlight_class + '">\n'
    result += markdown(md)
    result += '\n</div>\n'

  result = web_intro + result + htmlOutro

  return result


def application(environ, start_response):
  status = '200 OK'
  key = environ['PATH_INFO']
  if not key.startswith('/awz-'):
    status = "400 NOT FOUND"
    response_headers = [("content-type", "text/plain")]
    start_response(status, response_headers, sys.exc_info())
    return ["400 NOT FOUND"]
  output = generate_output(key[5:])
  response_headers = [('Content-type', 'text/html'),
                      ('Content-Length', str(len(output)))]
  start_response(status, response_headers)
  return [output.encode('utf-8')]
