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
            data_map = DotMap(load(stream, Loader=yaml.FullLoader))
        except yaml.YAMLError as exc:
            print(exc)

    return data_map

def writePlaybook(data_map,controlName, name):
    with open(os.path.dirname(__file__) + "/out/"+controlName+"/"+name, "w") as stream:
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

def getTagsFromLocals(lines, localStartIndex):
    tags = {}
    local_lines = lines[localStartIndex:lines.index("}\n",localStartIndex)]
    for line in local_lines:
        if "tags" in line:
            nLine = line.split("=")
            tags[nLine[0].strip()] = []
        if line.strip().startswith("plugin") or line.strip().startswith("service"):
            sLine = line.split("=")
            tags[nLine[0].strip()].append(sLine[1].strip().replace('"',''))
    return tags

def parseBenchmark(controlFile):
    benchmark = DotMap()
    benchmark.name = ""
    benchmark.controls = []
    benchmark.children = []
    
    with open(os.path.dirname(__file__) + controlFile) as stream:
        lines = stream.readlines()
        control = {}
        local_env = DotMap()
        i = 0
        while i < len(lines):
            if(lines[i].startswith("locals")):
                i+=1
                benchmark.tags = getTagsFromLocals(lines,i)
                

            if(lines[i].startswith("benchmark")):
                benchmark.name = lines[i].split(' ')[1].replace('"','')
                while not "children = [" in lines[i]:
                    if(lines[i].strip().startswith("title")):
                        benchmark.title = lines[i].split(' ')[1].replace('"','')
                    i+=1
                i+=1
                while not "]" in lines[i]:
                    benchmark.children.append(lines[i].strip().replace(',',''))
                    i+=1
                while not "}" in lines[i]:
                    i+=1
            if(lines[i].startswith("control")):
                controlName = lines[i].split(' ')[1].replace('"','')
                child = benchmark.children.index("control."+controlName) if "control."+controlName in benchmark.children else -1
                i+=1
                while not lines[i].startswith("}"):
                    sLine = lines[i].split("=")
                    if len(sLine) > 1 :
                        control[sLine[0].strip()] = sLine[1].strip().replace('"','')
                        
                    i+=1
                benchmark.controls.append(control.copy())
            i+=1
   
    return benchmark 
            
def getQuery(queryFile):

    with open(queryFile) as stream:
       # query = yaml.load(stream,Loader=yaml.FullLoader)
        lines = stream.read()

    return lines

def convertBenchToPlaybook(bench, playbook):
    playbook.name = bench.name
    for tag in bench.tags:
        if bench.tags[tag] not in playbook.tags:
            playbook.tags.extend( bench.tags[tag])
    
    with open(os.path.dirname(__file__) + "/section-template.yaml") as stream:
        stepsTemplate = yaml.load(stream,Loader=yaml.FullLoader)
    
    with open(os.path.dirname(__file__) + "/final-steps-template.yaml") as stream:
        last_steps = DotMap(yaml.load(stream,Loader=yaml.FullLoader))

    sectionId = 0
    output_ids = []

    for control in bench.controls:
        section = DotMap(stepsTemplate["steps"][0])
        description = DotMap(stepsTemplate["steps"][1])
        sql = DotMap(stepsTemplate["steps"][2])
        format_message = DotMap(stepsTemplate["steps"][3])

        queryFile = os.path.dirname(__file__) + "/../sqlite/auto/" + control["sql"].replace("query.",'').replace('"','')
        
        if not exists(queryFile):
            queryFile = os.path.dirname(__file__) + "/../sqlite/manual/" + control["sql"].replace("query.",'').replace('"','')
        

        if exists(queryFile):
            # Fill section
            section.text = "#" + control["title"].replace('"','')
            description.text = control["description"].replace('"','')
            # Fill sql query action
            sql.inputs.sql = " \n " + getQuery(queryFile)
            sql.id = "S"+str(sectionId+1)
            
        else:
            # Fill section
            section.text = "#" + control["title"].replace('"','') + " - Not implemented"
            description.text = control["description"].replace('"','')
            # Fill sql query action
            sql.inputs.sql = "Select * from true"
            sql.id = "S"+str(sectionId+1)
            sql.when = "False"
            format_message.when = "False"
           
        #fill format message
        format_message.id = "S"+str(sectionId+2)
        format_message.inputs.code = format_message.inputs.code.replace("S1",sql.id ).replace('ControlName',section.text)
        if "severity" in control:
            format_message.inputs.code = format_message.inputs.code.replace("DefaultSeverity",control['severity'])
        
        playbook.steps.append(section.toDict())
        playbook.steps.append(description.toDict())
        playbook.steps.append(sql.toDict())
        playbook.steps.append(format_message.toDict())

        output_ids.append(format_message.id)

        sectionId += 2
    
    last_steps.steps[1].inputs.code = last_steps.steps[1].inputs.code.replace("GeneratedStepsIds", str(output_ids)).replace("BenchmarkName", playbook.name)
    for step in last_steps.steps:
        playbook["steps"].append(step.toDict())

    return playbook


def generateControlPlaybooks(controlName, defaultTags=["Compliance"]):
    cwd = "/../"+controlName+"/"
    for file in os.listdir(os.path.dirname(__file__) + cwd):
        if file.endswith(".sp"):
            benchmark = parseBenchmark(cwd + file)
            if(benchmark.name != ""):
                playbook_template = loadTemplate()
                playbook_template.tags.extend(defaultTags)
                playbook = convertBenchToPlaybook(benchmark,playbook_template)
                writePlaybook(playbook.toDict(), controlName, benchmark["name"].replace('"','') + ".yaml")
            else:
                print("Not supported : " + cwd + file)
    return

def main():
    
    generateControlPlaybooks("foundational_security",["AWS", "Compliance"])
    generateControlPlaybooks("cis_v130",["AWS", "Compliance", "cis_v130"])
    generateControlPlaybooks("cis_v140",["AWS", "Compliance", "cis_v140"])
    generateControlPlaybooks("hipaa",["AWS", "Compliance", "hipaa"])
    generateControlPlaybooks("pci_v321",["AWS", "Compliance", "pci_v321"])
    generateControlPlaybooks("rbi_cyber_security",["AWS", "Compliance", "rbi_cyber_security"])
    generateControlPlaybooks("conformance_pack",["AWS", "Compliance", "conformance_pack"])
    # generateControlPlaybooks("test")


    
if __name__ == "__main__":
    main()