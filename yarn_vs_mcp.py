import sys
from pathlib import Path
import csv
import tqdm
import re

# Where to get the data:
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp/1.7.10/mcp-1.7.10-srg.zip
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp_stable/12-1.7.10/mcp_stable-12-1.7.10.zip
# [dynamic!] https://repo.legacyfabric.net/repository/legacyfabric/net/legacyfabric/yarn/1.7.10%2Bbuild.458/yarn-1.7.10%2Bbuild.458-mergedv2.jar
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp/1.8.9/mcp-1.8.9-srg.zip
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp_stable/22-1.8.9/mcp_stable-22-1.8.9.zip
# [dynamic!] https://repo.legacyfabric.net/repository/legacyfabric/net/legacyfabric/yarn/1.8.9%2Bbuild.458/yarn-1.8.9%2Bbuild.458-mergedv2.jar
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp/1.12.2/mcp-1.12.2-srg.zip
# https://maven.minecraftforge.net/de/oceanlabs/mcp/mcp_stable/39-1.12/mcp_stable-39-1.12.zip
#
# Yarn is continually updated, visit https://grayray75.github.io/LegacyFabric-Versions/ to find the latest stable version number.
# You can also visit https://github.com/Legacy-Fabric/yarn/tree/experimental_intermediaries and assemble experimental mappings locally.

if len(sys.argv) != 9:
    sys.exit(r'''Usage: {} mcp-1.7.10-srg mcp_stable-12-1.7.10 yarn-1.7.10-mergedv2 mcp-1.8.9-srg mcp_stable-22-1.8.9 yarn-1.8.9-mergedv2 mcp-1.12.2-srg mcp_stable-39-1.12

Compares MCP and Yarn mappings.
'''.format(sys.argv[0]))

# Key formats:
# Class: full/class/name
# Field: full/class/name fieldName fieldDesc
# Method: full/class/name methodName methodDesc
# Parameter: full/class/name methodName methodDesc parameterIndex parameterName
# (we use space as a separator)
# (fieldDesc and parameterName can be ? if unknown)

# mappings[ver][(src, dest)][nameType][name]
mappings = {}

DESCRIPTOR_PATTERN = re.compile(r"\[*L[^;]+;|\[*[ZBCSIFDJ]|[ZBCSIFDJ]")

def getWord(s, i):
    return s.split(" ")[i]

def invertMapping(map):
    inverted = {}
    for type in map.keys():
        inverted[type] = {v: k for k, v in map[type].items()}
    return inverted

def putMappings(ver, mappingsToAdd):
    if ver not in mappings:
        mappings[ver] = {}
    
    for dirAndMapping in mappingsToAdd:
        dir, mapping = dirAndMapping
        mappings[ver][dir] = mapping

def newEmptyMapping():
    return {"class": {}, "field": {}, "method": {}, "parameter": {}}

def replaceLastSlashWithSpace(s):
    lastSlash = s.rfind("/")
    if lastSlash != -1:
        return s[:lastSlash] + " " + s[lastSlash + 1:]
    else:
        return s

def splitDescriptorParams(desc):
    desc = desc[desc.index("(") + 1 : desc.rindex(")")]
    return DESCRIPTOR_PATTERN.findall(desc)

def loadNotch2Srg(ver, dir):
    dir = Path(dir)
    joined = [x.strip().split(' ') for x in open(dir / "joined.srg")]
    constructorInfos = dict([x.strip().split('=') for x in open(dir / "joined.exc") if not x.startswith("#") and ".<init>" in x])
    
    notch2srg = newEmptyMapping()
    simpleSrg2notch = newEmptyMapping()
    methodId2srg = newEmptyMapping()
    
    for line in joined:
        if line[0] == "CL:":
            notch2srg["class"][line[1]] = line[2]        
        elif line[0] == "FD:":
            notchFull = replaceLastSlashWithSpace(line[1]) + " ?"
            notch2srg["field"][notchFull] = replaceLastSlashWithSpace(line[2]) + " ?"
            
            lastWord = line[2].split("/")[-1]
            if lastWord.startswith("field_"):
                simpleSrg2notch["field"]["? " + lastWord + " ?"] = notchFull
        elif line[0] == "MD:":
            notchFull = replaceLastSlashWithSpace(line[1]) + " " + line[2]
            srgFull = replaceLastSlashWithSpace(line[3]) + " " + line[4]
            notch2srg["method"][notchFull] = srgFull
            if srgFull.split(" ")[1].startswith("func_"):
                methodId2srg["method"][srgFull.split(" ")[1].split("_")[1]] = srgFull
            
            for parameterIdx in range(len(splitDescriptorParams(line[2]))):
                notch2srg["parameter"][notchFull + " " + str(parameterIdx) + " ?"] = srgFull + " " + str(parameterIdx) + " ?"
            
            lastWord = line[3].split("/")[-1]
            if lastWord.startswith("func_"):
                simpleSrg2notch["method"]["? " + lastWord + " ?"] = notchFull
    
    srg2notch = invertMapping(notch2srg)
    
    for line in joined:
        if line[0] == "CL:":
            for k, v in constructorInfos.items():
                if k.startswith(line[2] + ".<init>"):
                    assert v.count("|") == 1
                    
                    srgClazz = k[:k.index(".")]
                    notchClazz = srg2notch["class"][srgClazz]
                    srgDesc = k[k.index(">") + 1:]
                    notchDesc = remapDesc(srgDesc, srg2notch["class"], "srg2notch-" + ver)
                    notchFull = notchClazz + " <init> " + notchDesc
                    srgFull = srgClazz + " <init> " + srgDesc
                
                    notch2srg["method"][notchFull] = srgFull
                    
                    paramNames = v[v.index("|") + 1:].split(",")
                    
                    methodId2srg["method"][paramNames[0].split("_")[1]] = srgFull
                
                    for paramName in paramNames:
                        parameterIdx = int(paramName.split("_")[2]) - 1
                        notch2srg["parameter"][notchFull + " " + str(parameterIdx) + " ?"] = srgFull + " " + str(parameterIdx) + " ?"
    
    return [
        (("notch", "srg"), notch2srg),
        (("srg", "notch"), srg2notch),
        (("simpleSrg", "notch"), simpleSrg2notch),
        (("methodId", "srg"), methodId2srg),
    ]

def loadSrg2MCP(ver, dir):
    dir = Path(dir)
    methods = list(csv.reader(open(dir / "methods.csv"), delimiter=',', quotechar='"'))
    fields = list(csv.reader(open(dir / "fields.csv"), delimiter=',', quotechar='"'))
    params = list(csv.reader(open(dir / "params.csv"), delimiter=',', quotechar='"'))
    
    mapping = newEmptyMapping()
    
    for line in fields[1:]:
        searge, name, side, desc = line
        fullNotch = translateName("field", "? " + searge + " ?", ver, "simpleSrg", "notch")
        fullSrg = translateName("field", fullNotch, ver, "notch", "srg")
        
        if fullSrg != None:
            mapping["field"][fullSrg] = getWord(fullSrg, 0) + " " + name + fullSrg[2]
    
    for line in methods[1:]:
        searge, name, side, desc = line
        fullNotch = translateName("method", "? " + searge + " ?", ver, "simpleSrg", "notch")
        fullSrg = translateName("method", fullNotch, ver, "notch", "srg")
        
        if fullSrg != None:
            mapping["method"][fullSrg] = getWord(fullSrg, 0) + " " + name + " " + fullSrg.split(" ")[2]
    
    for line in params[1:]:
        param, name, side = line
        
        methodFullSrg = translateName("method", param.split("_")[1], ver, "methodId", "srg")
        
        if not methodFullSrg:
            print("Failed to find method for parameter ", param, "in", dir.name)
            continue
        
        paramIndex = int(param.split("_")[2]) - 1
        
        mapping["parameter"][methodFullSrg + " " + str(paramIndex) + " ?"] = (mapping["method"].get(methodFullSrg) or methodFullSrg) + " " + str(paramIndex) + " " + name
    
    return [
        (("srg", "mcp"), mapping),
        (("mcp", "srg"), invertMapping(mapping))
    ]

descRemapCache = {}

def remapDesc(desc, map, cacheId):
    originalDesc = desc
    
    if cacheId not in descRemapCache:
        descRemapCache[cacheId] = {}
    
    if desc in descRemapCache[cacheId]:
        return descRemapCache[cacheId][desc]
    
    for k, v in map.items():
        sourceRef = "L" + k + ";";
        if sourceRef in desc:
            destRef = "L" + v + ";";
            desc = desc.replace(sourceRef, destRef)
    
    descRemapCache[cacheId][originalDesc] = desc
    
    return desc

def loadNotch2Intermediary2Yarn(ver, dir):
    yarnDir = Path(dir)
    tiny = [[y.strip() for y in x.split('\t')] for x in open(yarnDir / "mappings" / "mappings.tiny")]
    
    notch2intermediary = newEmptyMapping()
    intermediary2yarn = newEmptyMapping()
    
    assert tiny[0] == ["tiny", "2", "0", "official", "intermediary", "named"]
    
    for entry in tiny:
        if entry[0] == "c":
            notch2intermediary["class"][entry[1]] = entry[2]
            intermediary2yarn["class"][entry[2]] = entry[3]
    
    for entry in tqdm.tqdm(tiny):
        if entry[0] == "c":
            cls = entry[1]
        elif entry[0] == "":
            if entry[1] in ["f", "m"]:
                type = "field" if entry[1] == "f" else "method"
                desc = "?" if type == "field" else entry[2]
                intermediaryDesc = "?" if type == "field" else remapDesc(entry[2], notch2intermediary["class"], "notch2intermediary-" + ver)
                notchFull = cls + " " + entry[3] + " " + desc
                intermediaryFull = notch2intermediary["class"][cls] + " " + entry[4] + " " + intermediaryDesc
                yarnFull = notch2intermediary["class"][cls] + " " + entry[5] + " " + intermediaryDesc
                notch2intermediary[type][notchFull] = intermediaryFull
                intermediary2yarn[type][intermediaryFull] = yarnFull                    
            elif entry[1] == "" and entry[2] == "p":
                for parameterIdx in range(len(splitDescriptorParams(intermediaryDesc))):
                    notchParamFull = notchFull + " " + str(parameterIdx) + " ?"
                    intermediaryParamFull = intermediaryFull + " " + str(parameterIdx) + " ?"
                    yarnParamFull = yarnFull + " " + str(parameterIdx) + " " + entry[6]
                    
                    notch2intermediary["parameter"][notchParamFull] = intermediaryParamFull
                    intermediary2yarn["parameter"][intermediaryParamFull] = yarnParamFull
    
    return [
        (("notch", "intermediary"), notch2intermediary),
        (("intermediary", "notch"), invertMapping(notch2intermediary)),
        (("intermediary", "yarn"), intermediary2yarn),
        (("yarn", "intermediary"), invertMapping(intermediary2yarn)),
    ]

def loadMapping(ver, srcDest, dir):
    if srcDest == ("notch", "srg"):
        putMappings(ver, loadNotch2Srg(ver, dir))
    elif srcDest == ("srg", "mcp"):
        putMappings(ver, loadSrg2MCP(ver, dir))
    elif srcDest == ("notch", "intermediary", "yarn"):
        putMappings(ver, loadNotch2Intermediary2Yarn(ver, dir))
    else:
        raise Exception()

def translateName(nameType, name, ver, src, dest, different=False):
    result = (((mappings.get(ver) or {}).get((src, dest)) or {}).get(nameType) or {}).get(name)
    if different and (name == result):
        return None
    else:
        return result

def getKeys(nameType, ver, lang):
    for direction in (mappings.get(ver) or {}).keys():
        if direction[0] == lang:
            return mappings[ver][direction][nameType].keys()
    return []

loadMapping("1.7.10", ("notch", "srg"), sys.argv[1])
loadMapping("1.7.10", ("srg", "mcp"), sys.argv[2])
loadMapping("1.7.10", ("notch", "intermediary", "yarn"), sys.argv[3])
loadMapping("1.8.9", ("notch", "srg"), sys.argv[4])
loadMapping("1.8.9", ("srg", "mcp"), sys.argv[5])
loadMapping("1.8.9", ("notch", "intermediary", "yarn"), sys.argv[6])
loadMapping("1.12.2", ("notch", "srg"), sys.argv[7])
loadMapping("1.12.2", ("srg", "mcp"), sys.argv[8])

coverageMCP17 = {}
coverageMCP112 = {}
coverageMCP = {}
coverageYarn17 = {}
coverageYarn18 = {}
coverageYarn = {}
coverageMCPorYarn = {}
coverageTotal = {}

def incrementCoverage(map, type):
    if type not in map:
        map[type] = 0
    
    map[type] += 1

for nameType in ["class", "method", "field", "parameter"]:
    for key in getKeys(nameType, "1.7.10", "notch"):
        if nameType == "method" and key.split(" ")[1] == "<init>":
            continue
        
        nameMCP17_0 = translateName(nameType, key, "1.7.10", "notch", "srg")
        nameMCP17 = nameMCP17_0 if nameType == "class" else translateName(nameType, nameMCP17_0, "1.7.10", "srg", "mcp", different=True)
        
        nameMCP112_0 = translateName(nameType, key, "1.7.10", "notch", "srg")
        nameMCP112 = nameMCP112_0 if nameType == "class" else translateName(nameType, nameMCP112_0, "1.12.2", "srg", "mcp", different=True)
        
        nameYarn18_0 = translateName(nameType, key, "1.7.10", "notch", "srg")
        nameYarn18_1 = translateName(nameType, nameYarn18_0, "1.8.9", "srg", "notch")
        nameYarn18_2 = translateName(nameType, nameYarn18_1, "1.8.9", "notch", "intermediary")
        nameYarn18 = translateName(nameType, nameYarn18_2, "1.8.9", "intermediary", "yarn", different=True)
        
        nameYarn17_0 = translateName(nameType, key, "1.7.10", "notch", "intermediary")
        nameYarn17 = translateName(nameType, nameYarn17_0, "1.7.10", "intermediary", "yarn", different=True)
        
        if nameMCP17:
            incrementCoverage(coverageMCP17, nameType)
        
        if nameMCP112:
            incrementCoverage(coverageMCP112, nameType)
        
        nameMCP = nameMCP17 or nameMCP112
        
        if nameMCP:
            incrementCoverage(coverageMCP, nameType)
        
        if nameYarn17:
            incrementCoverage(coverageYarn17, nameType)
        
        if nameYarn18:
            incrementCoverage(coverageYarn18, nameType)
        
        nameYarn = nameYarn17 or nameYarn18
        
        if nameYarn:
            incrementCoverage(coverageYarn, nameType)
        
        if nameMCP or nameYarn:
            incrementCoverage(coverageMCPorYarn, nameType)
        
        incrementCoverage(coverageTotal, nameType)
        
        #print(nameType, "notch[", key, "] mcp17[", nameMCP17, "] yarn17[", nameYarn17, "] yarn18[", nameYarn18, "]")

def getCoverage(map, key):
    if key != "total":
        return map.get(key) or 0
    else:
        return sum(map.values())

for nameType in list(coverageMCP.keys()) + ["total"]:
    print(nameType, "coverage:")
    
    totalCoverage = getCoverage(coverageTotal, nameType)
    
    print("    MCP17: ".ljust(16), (getCoverage(coverageMCP17, nameType) / totalCoverage))
    print("    MCP112: ".ljust(16), (getCoverage(coverageMCP112, nameType) / totalCoverage))
    print("    MCP: ".ljust(16), (getCoverage(coverageMCP, nameType) / totalCoverage))
    print("    Yarn17: ".ljust(16), (getCoverage(coverageYarn17, nameType) / totalCoverage))
    print("    Yarn18: ".ljust(16), (getCoverage(coverageYarn18, nameType) / totalCoverage))
    print("    Yarn: ".ljust(16), (getCoverage(coverageYarn, nameType) / totalCoverage))
    print("    MCP+Yarn: ".ljust(16), (getCoverage(coverageMCPorYarn, nameType) / totalCoverage))
