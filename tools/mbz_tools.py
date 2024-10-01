from dataclasses import dataclass
import glob
import os
import re
import shutil
import tarfile
import gzip
from typing import Dict
import xml.etree.ElementTree as ET

from tqdm import tqdm
import subprocess


def extract_mbz_file(file_path):
    if not os.path.exists(file_path):
        print("File does not exist.")
        return
    try:
        if os.path.exists("./tmp"):
            print("INFO: tmp directory already exists.")
            return

        # Create a temporary directory
        os.makedirs('./tmp', exist_ok=True)

        # Decompress the gzip file
        subprocess.run(['tar', '-xzf', file_path, "--directory", './tmp']) #, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print('Extraction successful!')
    except Exception as e:
        print(f'An error occurred: {e}')

def compress_mbz_file(filename: str):
    try:
        # Create a gzip file
        os.chdir('./tmp')
        subprocess.run(['tar', '-czf', f'{filename}_tagged.mbz', '.']) # , stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir('../')
        shutil.move(f'./tmp/{filename}_tagged.mbz', f'{filename}_tagged.mbz')
        # print('Compression successful!')

        # Delete the temporary directory
        shutil.rmtree('./tmp')

    except Exception as e:
        print(f'An error occurred: {e}')


def read_xml_file(file_path):
    if not os.path.exists(file_path):
        print("File does not exist.")
        return None
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return root
    except ET.ParseError:
        print("Error parsing the XML file.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@dataclass  
class CourseModule:
    cmid: int
    id: int
    name: str
    type: str
    section: str

def get_unique_tag_id(tags: Dict[str, id]) -> int:
    if len(tags) == 0:
        return 1
    return max(tags.values()) + 1

def get_module(cmid: str) -> CourseModule:
    pattern = f'*_{cmid}'
    matching_directories = glob.glob(pattern, root_dir='./tmp/activities')
    assert len(matching_directories) == 1, f"Found {len(matching_directories)} directories matching {pattern}"
    
    module_type = matching_directories[0].split('_')[0]
    root = read_xml_file(f'./tmp/activities/{matching_directories[0]}/{module_type}.xml')

    if module_type == 'label':
        # NOTE: label names are shortened, the full text is in the 'intro' field
        name = root.find(module_type).find('intro').text
    else:
        name = root.find(module_type).find('name').text

    return CourseModule(
        cmid=cmid,
        id=int(root.get('id')),
        name=name,
        type=module_type,
        section=None
    )

def add_section_tag(cm: CourseModule, tag_dict: Dict[str, id]):
    # Read the XML file
    root = read_xml_file(f'./tmp/activities/{cm.type}_{cm.cmid}/module.xml')
    # find or create tag
    rawname = f"topic:{cm.section}"
    if not rawname in tag_dict:
        tag_dict[rawname] = get_unique_tag_id(tag_dict)

    # Add the section tag
    tags = root.find('tags')
    tag = ET.SubElement(tags, 'tag')
    tag.attrib['id'] = str(tag_dict[rawname])
    tag_rawname = ET.SubElement(tag, 'rawname')
    tag_rawname.text = rawname
    tag_name = ET.SubElement(tag, 'name')
    tag_name.text = rawname.lower()

    # add first module tag, if appropriate (icecreagame for ZQ, course overview for DQR)
    if cm.name == "Spiel zum Einstieg: Das Eiscremespiel":
        rawname = "first-module"
        if not rawname in tag_dict:
            tag_dict[rawname] = get_unique_tag_id(tag_dict)
        tag = ET.SubElement(tags, 'tag')
        tag.attrib['id'] = str(tag_dict[rawname])
        tag_rawname = ET.SubElement(tag, 'rawname')
        tag_rawname.text = rawname
        tag_name = ET.SubElement(tag, 'name')
        tag_name.text = rawname.lower()
    elif cm.name == "Willkommen und Kursüberblick":
        rawname = "course-overview"
        if not rawname in tag_dict:
            tag_dict[rawname] = get_unique_tag_id(tag_dict)
        tag = ET.SubElement(tags, 'tag')
        tag.attrib['id'] = str(tag_dict[rawname])
        tag_rawname = ET.SubElement(tag, 'rawname')
        tag_rawname.text = rawname
        tag_name = ET.SubElement(tag, 'name')
        tag_name.text = rawname.lower()

    # Save the modified XML file
    tree = ET.ElementTree(root)
    tree.write(f'./tmp/activities/{cm.type}_{cm.cmid}/module.xml')


def find_all_tags(whitelist = ['book', 'resource', 'url', 'quiz', 'label', 'h5pactivity', 'icecreamgame']) -> Dict[str, id]:
    tag_dict = {}
    for activity in tqdm(glob.glob('./tmp/activities/*')):
        activity_type = activity.split("/")[-1].split('_')[0]
        if activity_type not in whitelist:
            continue
        root = read_xml_file(f'{activity}/module.xml')
        tags = root.find('tags')
        for tag in tags:
            id = int(tag.attrib['id'])
            rawname = tag.find('rawname').text
            tag_dict[rawname] = id
    return tag_dict


def get_section_branch(section_name: str, top_level_section_name: str = None) -> str:
    pattern = r'(Video|Thema) ([A-Za-z]\d+(?:-\d+)?[A-Za-z]?):'
    match = re.search(pattern, section_name)
    if match and len(match.groups()) == 2:
        extracted_section_branch = match.group(2)
    else:
        if "quiz" in section_name.lower():
            print(f"WARNING: Quiz section name without branch id: {section_name}")
        elif "Praxisbeispiel zu den Themen A2-1 und A2-2: Trainieren Sie einen Entscheidungsbaum" in section_name:
            return "A2-2a"
        elif section_name == "Spiel zum Einstieg: Bestellen Sie Eis!":
            return "first-section"
        else:
            print(f"WARNING: Section name without branch id: {section_name}")

        if top_level_section_name:
            extracted_section_branch = top_level_section_name
            print(f"WARNING: Section name {section_name} does not contain a branch id. Using {top_level_section_name} instead.")
        else:
            extracted_section_branch = section_name
            print(f"WARNING: Section name {section_name} does not contain a branch id, but no top-level section id was provided")
    return extracted_section_branch

def tag_activities(whitelist = ['book', 'resource', 'url', 'quiz', 'label', 'h5pactivity', 'icecreamgame']):
    # get list of all existing tags
    tags = find_all_tags(whitelist)

    # list all files in the sections directory
    sections = os.listdir('./tmp/sections')
    for section in tqdm(sections):
        root = read_xml_file(f'./tmp/sections/{section}/section.xml')

        section_name = get_section_branch(root.find('name').text)
        top_level_section_name = section_name
        # if the section is from the ZQ, choose the section name as the section name.
        # if the section is from the DQR, choose the next label as section name.

        sequence = root.find('sequence').text
        if sequence is None or sequence == "$@NULL@$":
            print(f'WARNING: Section {section_name}: No sequence found.')
            continue
        for cmid in sequence.split(','):
            module = get_module(int(cmid))
            module.section = section_name
           
            if module.type == 'label' and "kann ich schon" not in module.name.lower():
                section_name = get_section_branch(module.name, top_level_section_name=top_level_section_name)
            else:
                add_section_tag(cm=module, tag_dict=tags)

if __name__ == '__main__':
    filename = "dqr5"
    extract_mbz_file(f"{filename}.mbz")
    tag_activities()
    compress_mbz_file(filename)