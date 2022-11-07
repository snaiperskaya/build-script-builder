import os
import sys

write_order = [
                'DROPS',
                'ROLES',
                'SEQUENCES',
                'DATABASE_LINKS',
                'SYNONYMS', 
                'TABLES',
                'INDEXES',
                'PACKAGES',
                'CONSTRAINTS',
                'REF_CONSTRAINTS',
                'FUNCTIONS',
                'PROCEDURES',
                'TRIGGERS',
                'VIEWS',
                'PACKAGE_BODIES',
                'JOBS',
                'COMMENTS',
                'GRANTS', 
                'REF_DATA_LOAD'
                ]

clean_order = {
                'VIEWS': 'DROP VIEW',
                'TRIGGERS': 'DROP TRIGGER',
                'PROCEDURES': 'DROP PROCEDURE',
                'PACKAGES': 'DROP PACKAGE',
                'PACKAGE_BODIES': 'DROP PACKAGE',
                'FUNCTIONS': 'DROP FUNCTION',
                'REF_CONSTRAINTS': 'DROP CONSTRAINT',
                'CONSTRAINTS': 'DROP CONSTRAINT',
                'INDEXES': 'DROP INDEX',
                'TABLES': 'DROP TABLE',
                'SYNONYMS': 'DROP SYNONYM',
                'SEQUENCES': 'DROP SEQUENCE'
                }

script_starts = [
                    'CREATE',
                    'OR',
                    'REPLACE',
                    'EDITIONABLE',
                    'UNIQUE',
                    'BODY',
                    'FORCE'
                ]

alter_keywords = [
                    'ALTER',
                    'TABLE',
                    'ADD',
                    'CONSTRAINT'
                ]

script_types = [
                'SEQUENCE',
                'SYNONYM', 
                'TABLE',
                'INDEX',
                'CONSTRAINT',
                'TRIGGER',
                'FUNCTION',
                'PACKAGE',
                'PROCEDURE',
                'VIEW',
                ]

stripable_chars = ['\t', '\n', '(', ')']

packages = []

tab = '    '

cleanfile = 'clean.sql'

buildfile = 'build.sql'

to_build = {'EARLY':[]}

def genBuildScript(filename = buildfile, outDirectory = '.'):
    for i in write_order:
        to_build[i] = []

    for item in write_order:
        path = f'{outDirectory}\\{item}'
        if os.path.exists(path):
            contents = os.scandir(path)
            countFile = 0
            for obj in contents:
                if os.path.isfile(obj) and os.path.splitext(obj)[-1].lower() == '.sql':
                    countFile += 1
                    fname = os.path.basename(obj)
                    if fname.lower().startswith('early'):
                        # Force a script to be loaded at the beginning 
                        # by adding "early" to the beginning of the script name
                        to_build['EARLY'].append(f'@{item}/{fname}\n')
                    else:
                        to_build[item].append(f'@{item}/{fname}\n')
            if countFile == 0:
                to_build[item].append(f'{tab}-- No {item} to add (No files or no usable content found)')
        else:
            to_build[item].append(f'{tab}-- No {item} to add (No directory)')
        to_build[item].append('\n-------------------------\n')
    
    if to_build['EARLY'] != []:
        to_build['EARLY'].append('\n-------------------------\n')

    with open(f'{outDirectory}\\{filename}', 'w') as file:
        file.write('spo build.log\n\n-------------------------\n')
        for key in to_build.keys():
            for line in to_build[key]:
                file.write(line)
        file.write('spo off')

def genCleanScript(filename = cleanfile, outDirectory = '.'):
    with open(f'{outDirectory}\\{filename}', 'w') as file:
        file.write('spo clean.log\n\nprompt --Dropping all objects in this release\n\n-------------------------\n')
        for item in clean_order.keys():
            path = f'{outDirectory}\\{item}'
            if os.path.exists(path):
                contents = os.scandir(path)
                countFile = 0
                for obj in contents:
                    if os.path.isfile(obj) and os.path.splitext(obj)[-1].lower() == '.sql':
                        alters = []
                        creates = []
                        if item in ('CONSTRAINTS', 'REF_CONSTRAINTS'):
                            alters = parseSqlAltersConstraint(obj)
                            for drop in alters:
                                file.write(f'{drop}\n')
                        creates = parseSqlCreates(item, obj)
                        for drop in creates:
                            file.write(f'{clean_order[item]} {drop};\n')
                        if len(creates) > 0 or len(alters) > 0:
                            countFile += 1
                if countFile == 0:
                    file.write(f'{tab}-- No {item} to drop (No files or no usable content found)')
            else:
                file.write(f'{tab}-- No {item} to drop (No directory)')
            file.write('\n-------------------------\n')
        file.write('spo off')

def parseSqlCreates(type, fileobj):
    outList = []
    tempList = []
    with open(fileobj, 'r') as f:
        filecontent = f.readlines()
    for line in filecontent:
        line = line.upper().lstrip('\t ')
        if line.startswith('CREATE '):
            words = line.split()
            index = 0
            while words[index] in script_starts or words[index] in script_types:
                index += 1
            tempList.append(words[index])
    if len(tempList) > 0:
        for i in tempList:
            if type in ('PACKAGES', 'PACKAGE_BODIES') and i not in packages:
                packages.append(i)
                outList.append(i)
            elif type not in ('PACKAGES', 'PACKAGE_BODIES'):
                outList.append(i)
    return outList

def parseSqlAltersConstraint(fileobj):
    outList = []
    with open(fileobj, 'r') as f:
        filecontent = f.read()
    filecontent = formatForAlter(filecontent)
    alterStatements = {}
    index = 0
    isAlter = False
    isAdd = False
    constraint = False
    for word in filecontent.split():
        if word == 'ALTER':
            isAlter = True
        elif isAlter:
            if word == 'ADD':
                isAdd = True
            elif word == 'CONSTRAINT':
                constraint = True
            elif word not in alter_keywords and index not in alterStatements.keys():
                alterStatements[index] = {'table': word}
            elif word not in alter_keywords and index in alterStatements.keys():
                alterStatements[index]['constraint'] = word
                if not isAdd or not constraint:
                    alterStatements.pop(index) #invalid constraint
                isAlter = False
                isAdd = False
                constraint = False
                index += 1
            if word.endswith((';','/')):
                if not isAdd or not constraint:
                    alterStatements.pop(index) #invalid constraint
                isAlter = False
                isAdd = False
                constraint = False
                index += 1
    for i in alterStatements.keys():
        tablename = alterStatements[i]['table']
        constraintname = alterStatements[i]['constraint']
        outString = f'ALTER TABLE {tablename}\n' \
                    f'{tab}DROP CONSTRAINT {constraintname};\n' \
                    '/'
        outList.append(outString)
    return outList

def formatForAlter(string):
    string = string.upper()
    for char in stripable_chars:
        string = string.replace(char, ' ')
    prev_char = ' '
    new_string = ''
    for i in string:
        if i != prev_char or prev_char != ' ':
            new_string = f'{new_string}{i}'
        prev_char = i
    return new_string


def main(runClean):
    genBuildScript()
    if runClean:
        genCleanScript()



if __name__ == '__main__':
    runClean = False
    try:
        for i in sys.argv[1:]:
            if i.startswith('-c'):
                runClean = True
    except:
        pass
    main(runClean)