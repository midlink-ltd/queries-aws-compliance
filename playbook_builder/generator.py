from genericpath import exists
import os
import yaml
import json
from dotmap import DotMap
from yaml import load,dump, loader

#based on https://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter
class folded_unicode(str): pass
class literal_unicode(str): pass

def folded_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')
def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')

def loadTemplate():
    with open(os.path.dirname(__file__) + "/playbook_template.yaml") as stream:
        try:
            data_map = load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    return data_map

def writePlaybook(data_map, name):
    with open(os.path.dirname(__file__) + "/out/"+name, "w") as stream:
        try:
            noalias_dumper = yaml.dumper.Dumper
            noalias_dumper.ignore_aliases = lambda self, data: True
            yaml.dump(data_map,stream, Dumper=noalias_dumper)
        except yaml.YAMLError as exc:
            print(exc)
    return

def findControlFile(query, controlDir):
    for fname in os.listdir(controlDir):    # change directory as needed
        if os.path.isfile(fname):    # make sure it's a file, not a directory entry
            with open(fname) as f:   # open file
                for line in f:       # process line by line
                    if query in line:    # search for string
                        print(fname)
                        break
                        
    return fname

def parseBenchmark(controlFile):
    benchmark = {}
    benchmark["controls"] = []
    benchmark["children"] = []

    with open(os.path.dirname(__file__) + controlFile) as stream:
        lines = stream.readlines()
        control = {}
        i = 0
        while i < len(lines):
            if(lines[i].startswith("benchmark")):
                benchmark["name"] = lines[i].split(' ')[1].replace('"','')
                while not "children = [" in lines[i]:
                    i+=1
                i+=1
                while not "]" in lines[i]:
                    benchmark["children"].append(lines[i].strip().replace(',',''))
                    i+=1
                while not "}" in lines[i]:
                    i+=1
            if(lines[i].startswith("control")):
                controlName = lines[i].split(' ')[1].replace('"','')
                child = benchmark["children"].index("control."+controlName)
                i+=1
                while not lines[i].startswith("}"):
                    sLine = lines[i].split("=")
                    if len(sLine) > 1 :
                        control[sLine[0].strip()] = sLine[1].strip().replace('"','')
                        
                    i+=1
                benchmark["controls"].append(control.copy())
            i+=1
   
    return benchmark 
            
def getQuery(queryFile):

    with open(queryFile) as stream:
       # query = yaml.load(stream,Loader=yaml.FullLoader)
        lines = stream.read()

    return lines

def convertBenchToPlaybook(bench, playbook):
    playbook["name"] = bench["name"]
    
    with open(os.path.dirname(__file__) + "/section-template.yaml") as stream:
        stepsTemplate = yaml.load(stream,Loader=yaml.FullLoader)
    
    with open(os.path.dirname(__file__) + "/final-steps-template.yaml") as stream:
        last_steps = DotMap(yaml.load(stream,Loader=yaml.FullLoader))

    sectionId = 0
    output_ids = []

    for control in bench["controls"]:
        section = DotMap(stepsTemplate["steps"][0])
        sql = DotMap(stepsTemplate["steps"][1])
        format_message = DotMap(stepsTemplate["steps"][2])

        queryFile = os.path.dirname(__file__) + "/../sqlite/auto/" + control["sql"].replace("query.",'').replace('"','')
        
        if not exists(queryFile):
            queryFile = os.path.dirname(__file__) + "/../sqlite/manual/" + control["sql"].replace("query.",'').replace('"','')
        

        if exists(queryFile):
            # Fill section
            section.text = "#" + control["title"].replace('"','')
            section.description = control["description"].replace('"','')
            # Fill sql query action
            sql.inputs.sql = " \n " + getQuery(queryFile)
            sql.id = "S"+str(sectionId+1)
            
        else:
            # Fill section
            section.text = "#" + control["title"].replace('"','') + " - Not implemented"
            # Fill sql query action
            sql.inputs.sql = ""
            sql.id = "S"+str(sectionId+1)
           
        #fill format message
        format_message.id = "S"+str(sectionId+2)
        format_message.inputs.code = format_message.inputs.code.replace("S1",sql.id ).replace('ControlName',section.text).replace("DefaultSeverity",control['severity'])
        
        playbook["steps"].append(section.toDict())
        playbook["steps"].append(sql.toDict())
        playbook["steps"].append(format_message.toDict())

        output_ids.append(format_message.id)

        sectionId += 2
    
    last_steps.steps[0].inputs.code = last_steps.steps[0].inputs.code.replace("GeneratedStepsIds", str(output_ids)).replace("BenchmarkName", playbook["name"])
    for step in last_steps.steps:
        playbook["steps"].append(step.toDict())

    return playbook


def main():

   #controlFile = findControlFile("query.apigateway_rest_api_stage_use_ssl_certificate", "/Users/jon/workspace/blink/queries-aws-compliance/foundational_security")
    cwd = "/../foundational_security/"
    for file in os.listdir(os.path.dirname(__file__) + cwd):
        if file.endswith(".sp"):
            benchmark = parseBenchmark(cwd + file)
            data_map = loadTemplate()
    
            playbook = convertBenchToPlaybook(benchmark, data_map)
            writePlaybook(playbook, benchmark["name"].replace('"','') + ".yaml")

    
if __name__ == "__main__":
    main()