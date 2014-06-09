from __future__ import absolute_import
from django.http import HttpResponse
from copy import copy
from app.logic import SymPyGamma
from app.views import eval_card
from HTMLParser import HTMLParser
import json
import urllib2
import traceback

#for testing
output_test = []

#styling for notebook
styling = '''<style>
li{ list-style-type:none;
    list-style-position:inside;
    margin:0;
    padding:0;}
.cell_input{font-weight:bold;
    margin-left:auto;}
</style>'''

class Parser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.cell_input = []
        self.is_cell_input = False
    def handle_starttag(self, tag, attrs):
        self.is_cell_input = False
        if tag == 'div':
            for attribute, value in attrs:
                if attribute=='class' and value=='cell_input':
                    self.is_cell_input = True
    def handle_data(self, data):
        if self.is_cell_input:
            self.cell_input.append(data)

def result_json(request):

    ''' IPython notebook format generator. Parses the result set and
        converts them into IPython notebook's format. '''

    notebook_format = { "metadata": {"name": ""}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{ "cells": [],"metadata": {} }]}
    code_cell = {"cell_type": "code", "collapsed": "false", "input": [], "language": "python", "metadata": {}, "outputs": [{ "output_type": "pyout", "text": [], "prompt_number": 1}], "prompt_number": 1 },
    markdown_cell = {"cell_type": "markdown","metadata": {},"source":[]},
    heading_cell = {"cell_type": "heading","level": 3,"metadata": {},"source": []},

    exp = request.GET.get('i')
    exp = urllib2.unquote(exp)
    g = SymPyGamma()
    result = g.eval(exp)
    notebook = copy(notebook_format)

    prompt_number = 1 #initial value

    for cell in result:
        title = copy(heading_cell[0])
        title['level'] = 3
        a = str(cell['title'])
        title['source'] = [a]
        notebook['worksheets'][0]['cells'].append(title)

        if 'input' in cell.keys():
            if cell['input'] != None and cell['input'] != '':
                inputs = copy(code_cell[0])
                inputs['input'] = [ str(cell['input']) ]
                inputs['prompt_number'] = prompt_number
                prompt_number = prompt_number + 1
                notebook['worksheets'][0]['cells'].append(inputs)

        if 'output' in cell.keys():
            output = copy(markdown_cell[0])

            if 'pre_output' in cell.keys():
                if cell['pre_output'] !="" and cell['pre_output'] != 'None':
                    pre_output = copy(markdown_cell[0])
                    pre_output['source'] = ['$$'+str(cell['pre_output'])+'=$$']
                    notebook['worksheets'][0]['cells'].append(pre_output)

            if cell['output'] != "" and 'script' in cell['output']:
                output['source'] = [cell['output']]
                notebook['worksheets'][0]['cells'].append(output)

        if 'card' in cell.keys():
            if cell['card'] != 'plot':
                card_name = cell['card']
                variable = cell['var']
                parameters = {}
                if 'pre_output' in cell.keys():
                    if cell['pre_output'] != '' and cell['pre_output'] != 'None':
                        cell_pre_output = copy(markdown_cell[0])
                        cell_pre_output['source'] = ['$$'+str(cell['pre_output'])+ '=$$']
                        notebook['worksheets'][0]['cells'].append(cell_pre_output)

                try:
                    card_json = g.eval_card(card_name, exp, variable, parameters)
                    card_json_output = card_json['output']

                    parser = Parser()
                    parser.feed(card_json_output)
                    parsed_cell_inputs = parser.cell_input #list of data values with <div class='cell_input'>

    #-------------------------------------------------------------------
    #-------------------------------------------------------------------

                    for card_cell_input in parsed_cell_inputs:
                        #output_test.append(card_cell_input)   #for testing


                        if card_cell_input != '\n' and card_cell_input != '</div>' and card_cell_input != '\\':


                            if card_cell_input[:1] == '\n':
                                card_cell_input = card_cell_input[1:]
                            if card_cell_input[-1:] == '\n':
                                card_cell_input = card_cell_input[:-1]

                            #output_test.append(card_cell_input)
                            card_heading = copy(code_cell[0])
                            card_heading['input'] = [card_cell_input]
                            card_heading['prompt_number'] = prompt_number
                            prompt_number = prompt_number + 1
                            notebook['worksheets'][0]['cells'].append(card_heading)

                            card_json_output = card_json_output.split(card_cell_input)
                            if card_json_output[1][:7] == '\n</div>':
                                card_json_output[1] = card_json_output[1][7:]

                            card_result = copy(markdown_cell[0])
                            card_result['source'] = [card_json_output[1]]
                            notebook['worksheets'][0]['cells'].append(card_result)  #storing output after input


                        if len(card_json_output) > 1 :
                            card_json_output = card_json_output[1]
                        else:
                            card_json_output = card_json_output[0]


                    if card_json_output != '<':

                        card_last_result = copy(markdown_cell[0])
                        card_last_result['source'] = [card_json_output]
                        notebook['worksheets'][0]['cells'].append(card_last_result)
                except:
                    card_error = copy(markdown_cell[0])
                    card_error['source'] = [traceback.format_exc(1)]
                    notebook['worksheets'][0]['cells'].append(card_error)
            else:
                card_plot = copy(markdown_cell[0])
                card_plot['source'] = ['Plotting is not yet implemented.']
                notebook['worksheets'][0]['cells'].append(card_plot)



        if 'cell_output' in cell.keys():
            if cell['cell_output'] != "":
                cell_output = copy(markdown_cell[0])
                cell_output['source'] = [cell['cell_output']]
                notebook['worksheets'][0]['cells'].append(cell_output)

        if 'error' in cell.keys():
            cell_error = copy(markdown_cell[0])
            cell_error['source'] = [cell['error']]
            notebook['worksheets'][0]['cells'].append(cell_error)

        else:
                pass


    notebook_styling = copy(markdown_cell[0])
    notebook_styling['source'] = [styling]
    notebook['worksheets'][0]['cells'].append(notebook_styling)

    notebook_json = json.dumps(notebook)
    response =  HttpResponse(notebook_json, content_type = 'text/plain')
    #response['Content-Disposition'] = 'attachment; filename=gamma.ipynb'
    return response
    #return HttpResponse(output_test, content_type = 'text/plain')

