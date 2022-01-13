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
        if line.strip().startswith("plugin ") or line.strip().startswith("service "):
            sLine = line.split("=")
            tags[nLine[0].strip()].append(sLine[1].strip().replace('"',''))
    return tags

def readFromLocals(value, defaultValue):
    control = DotMap()
    replaceCmd = []
    searchLocal = value
    if value.startswith("local."):
        searchLocal = value.replace("local.","")
    elif value.startswith("replace("):
        replaceCmd = value.replace('replace(','').replace(')','').replace('"','').split(',')
        searchLocal = replaceCmd[0].split('.')[1] 
    

    currentDir = os.getcwd()
    found = False

    base_len = len(currentDir)
    base_level = currentDir.count(os.sep)

    sp_exts =['.sp']

    for root, dirs, files in os.walk(currentDir): 
        rel_dir = '.{1}{0}'.format(os.sep, root[base_len:])
        sp_files =  sorted([f for f in files if not f[0] == '' and os.path.splitext(f)[-1] in sp_exts])
        for fname in sp_files: # change directory as needed
             # make sure it's a file, not a directory entry
            with open(rel_dir+fname) as stream:   # open file
                i = 0
                lines = stream.readlines()
                while i < len(lines):
                    if "locals {" in lines[i]:
                        i+=1
                        while not lines[i].strip().startswith("}"):
                            if lines[i].strip().startswith(searchLocal):    # search for string
                                sLine = lines[i].split('=')
                                if len(replaceCmd) > 1:
                                    defaultValue = sLine[1].strip().replace(replaceCmd[1].strip(),replaceCmd[2].strip()).replace('"','')
                                else:
                                    defaultValue = sLine[1].strip()
                                found = True
                                break
                            i+=1
                    if found:
                        break
                    i+=1
        if found:
            break

    
    return defaultValue

def readControlPropertyValue(line, name):
    key = ""
    value = ""
    sLine = line.split("=")
    if len(sLine) > 1 :
        key = sLine[0].strip()
        value = sLine[1].strip().replace('"','')
        if value.startswith("replace(local.") or value.startswith("local."):
            value = readFromLocals(value, name)
    return key, value


def parseControl(lines, i):
    control = DotMap()
    control.name = lines[i].split(' ')[1].replace('"','')
    i+=1
    while not lines[i].startswith("}"):
                    key, value = readControlPropertyValue(lines[i], control.name)
                    sLine = lines[i].split("=")
                    control[key] = value
                        
                    i+=1
    return control, i


def findControl(controlName,dir):
    control = DotMap()
    searchFilter = 'control "' + controlName + '" {' 
    currentDir = os.path.dirname(__file__) + "/../" + dir
    found = False

    for fname in os.listdir(currentDir):    # change directory as needed
        if fname.endswith(".sp"):    # make sure it's a file, not a directory entry
            with open(currentDir+"/"+fname) as stream:   # open file
                i = 0
                lines = stream.readlines()
                while i < len(lines):       # process line by line
                    if searchFilter in lines[i]:    # search for string
                        control, i = parseControl(lines,i)
                        found = True
                        break
                    i+=1
        if found:
            break

    return control.copy()

def cleanupBenchmark(benchmarks):
    result = DotMap()
    for key in benchmarks:
        #try to get missing sql from external files
        empty_controls = [x for x in benchmarks[key].controls if isinstance(x, str)]
        
        for control in empty_controls:
            temp = findControl(control, "control")
            benchmarks[key].controls[benchmarks[key].controls.index(control)] = temp.copy()

        if len(benchmarks[key].children) > 0 or len([x for x in benchmarks[key].controls if not isinstance(x, str)]) > 0:
            #control query was defined in benchmark file and implemented
            result[key] = benchmarks[key].copy()



    return result

def parseBenchmark(controlFile):
    benchmark = DotMap()
    benchmark.name = ""
    benchmark.description = ""
    benchmark.documentation = ""

    benchmarks = DotMap()
    

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
                benchmark.controls = []
                benchmark.children = []
                benchmark.name = lines[i].split(' ')[1].replace('"','')
                while not "children = [" in lines[i]:
                    if(lines[i].strip().startswith("title")):
                        benchmark.title = lines[i].split('=')[1].replace('"','')
                    elif (lines[i].strip().startswith("description")):
                        benchmark.description = lines[i].split('=')[1].replace('"','')
                    elif (lines[i].strip().startswith("documentation")):
                        benchmark.documentation = lines[i].split('=')[1].replace('"','').replace("file(",'').replace(")",'')
                    i+=1
                i+=1
                while not "]" in lines[i]:
                    child = lines[i].strip().split(".")
                    if child[0].strip() == "benchmark":
                        benchmark.children.append(child[1].replace(',','').capitalize())
                    elif child[0].strip() == "control":
                        benchmark.controls.append(child[1].replace(',',''))
                    i+=1
                while not "}" in lines[i]:
                    i+=1
                benchmarks[benchmark.name] =  benchmark.copy()

            if(lines[i].startswith("control")):
                controlName = lines[i].split(' ')[1].replace('"','')
                i+=1
                while not lines[i].startswith("}"):
                    sLine = lines[i].split("=")
                    if len(sLine) > 1 :
                        control[sLine[0].strip()] = sLine[1].strip().replace('"','')
                        
                    i+=1
                    
                parent_benchmarks = [benchmarks[x] for x in benchmarks if controlName in benchmarks[x].controls]
                for parent in parent_benchmarks:
                    parent.controls[parent.controls.index(controlName)] = control.copy()
            i+=1
    
    return cleanupBenchmark(benchmarks) 
            
def getQuery(queryFile):

    with open(queryFile) as stream:
       # query = yaml.load(stream,Loader=yaml.FullLoader)
        lines = stream.read()

    return lines

def getDescriptionFromDocumentation(doc):
    desc = "Autogenerated playbook - no description available for parser"
    filePath = os.path.dirname(__file__) + "/../" + doc.strip()
    if os.path.isfile(filePath):
        with open(filePath) as stream:
            lines = stream.readlines()
            i = 0
            while i < len(lines):
                while not lines[i].strip().endswith("Overview") and not lines[i].strip().endswith("Description"):
                    i+=1
                i+=1
                while lines[i].strip().replace("\n","") == "":
                    i+=1
                desc = lines[i]
                break 
                    

    return desc

def convertBenchToPlaybook(bench, playbook):
    playbook.name = bench.name
    playbook.desc = bench.description if bench.description != "" else getDescriptionFromDocumentation(bench.documentation)
    for tag in bench.tags:
        if bench.tags[tag] not in playbook.tags:
            playbook.tags.extend( bench.tags[tag])
    
    with open(os.path.dirname(__file__) + "/section-template.yaml") as stream:
        stepsTemplate = yaml.load(stream,Loader=yaml.FullLoader)
    
    with open(os.path.dirname(__file__) + "/final-steps-template.yaml") as stream:
        last_steps = DotMap(yaml.load(stream,Loader=yaml.FullLoader))

    sectionId = 0
    playbook.outputs = DotMap()
    output_ids = []

    playbook.type = "Subflow.playbook"
        
    for child in bench.children:
        section = DotMap(stepsTemplate["steps"][0])
        description = DotMap(stepsTemplate["steps"][1])
        action = DotMap(stepsTemplate["steps"][4])
        
        section.text = "# " + child + " checks" 
        
        action.action = "playbooks." + child
        action.id = "S"+ str(sectionId+1)
        action.name = child
        
        playbook.outputs[child] = "{{steps." + action.id + ".output}}"
        
        output_ids.append(action.id)

        playbook.steps.append(section.toDict())
        playbook.steps.append(description.toDict())
        playbook.steps.append(action.toDict())
        sectionId +=1
        
    for control in bench.controls:
        section = DotMap(stepsTemplate["steps"][0])
        description = DotMap(stepsTemplate["steps"][1])
        sql = DotMap(stepsTemplate["steps"][2])
        format_message = DotMap(stepsTemplate["steps"][3])

        queryFile = os.path.dirname(__file__) + "/../sqlite/auto/" + control["sql"].replace("query.",'').replace('"','')
        
        if not os.path.isfile(queryFile):
            queryFile = os.path.dirname(__file__) + "/../sqlite/manual/" + control["sql"].replace("query.",'').replace('"','')
        

        if os.path.isfile(queryFile):
            # Fill section
            section.text = "# " + control["title"].replace('"','')
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
        format_message.inputs.code = format_message.inputs.code.replace("S1",sql.id ).replace('ControlName', control["title"].replace('"','')).replace("\\",'')
        if "severity" in control:
            format_message.inputs.code = format_message.inputs.code.replace("DefaultSeverity",control['severity'])
        
        playbook.steps.append(section.toDict())
        playbook.steps.append(description.toDict())
        playbook.steps.append(sql.toDict())
        playbook.steps.append(format_message.toDict())

        playbook.outputs[format_message.id] = "{{steps." + format_message.id + ".output}}"
        output_ids.append(format_message.id)

        sectionId += 2

    #add section step
    playbook["steps"].append(last_steps.steps[0].toDict())
    #add format step depending on subflow or parent
    if len(bench.children) > 0:
        last_steps.steps[2].inputs.code = last_steps.steps[2].inputs.code.replace("GeneratedStepsIds", str(output_ids)).replace("BenchmarkName", playbook.name)
        playbook["steps"].append(last_steps.steps[2].toDict())
    else:   
        last_steps.steps[1].inputs.code = last_steps.steps[1].inputs.code.replace("GeneratedStepsIds", str(output_ids)).replace("BenchmarkName", playbook.name)
        playbook["steps"].append(last_steps.steps[1].toDict())
    #add send slack message action
    playbook["steps"].append(last_steps.steps[3].toDict())

    playbook.outputs["check_name"] = playbook.name
    playbook.outputs["execution_url"] = "{{execution_url}}"

    return playbook


def generateControlPlaybooks(controlName, defaultTags=["Compliance"], defaultConnection=DotMap({"kubernetes":"kubernetes_connection"})):
    cwd = "/../"+controlName+"/"
    for file in os.listdir(os.path.dirname(__file__) + cwd):
        if file.endswith(".sp"):
            benchmarks = parseBenchmark(cwd + file)
            for key in benchmarks:
                if(benchmarks[key].name != ""):
                    playbook_template = loadTemplate()
                    playbook_template.tags.extend(defaultTags)
                    playbook_template.connections = defaultConnection
                    playbook = convertBenchToPlaybook(benchmarks[key],playbook_template)
                    writePlaybook(playbook.toDict(), controlName, benchmarks[key].name.replace('"','') + ".yaml")
                else:
                    print("Not supported : " + cwd + file)
    return

def main():
    
    # generateControlPlaybooks("foundational_security",["AWS", "Compliance"])
    # generateControlPlaybooks("cis_v130",["AWS", "Compliance", "cis_v130"])
    # generateControlPlaybooks("cis_v140",["AWS", "Compliance", "cis_v140"])
    # generateControlPlaybooks("pci_v321",["AWS", "Compliance", "pci_v321"])
    # generateControlPlaybooks("hipaa",["AWS", "Compliance", "hipaa"])
    # generateControlPlaybooks("conformance_pack",["AWS", "Compliance", "conformance_pack"])
    generateControlPlaybooks("test")


    
if __name__ == "__main__":
    main()