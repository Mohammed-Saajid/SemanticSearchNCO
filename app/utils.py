import pdfplumber
import json
import os
import fitz
import re
import numpy as np

# Constants for PDF dimensions
PAGE_HEIGHT = 595
PAGE_WIDTH = 841
border_rect = fitz.Rect(50, 80, PAGE_HEIGHT-40, PAGE_WIDTH-80)


def update_nested_dict(d, keys, value):
    """
    Safely update nested dict by keys list.
    
    Args:
        d (dict): The dictionary to update.
        keys (list): The list of keys specifying the path to the value.
        value: The new value to set.
    Returns:
        None
    """

    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

def load_json(path):
    """
    Load JSON file safely, returning {} if missing, empty, or invalid.

    Args:
        path (str): The path to the JSON file.
    Returns:
        dict: The loaded JSON data or an empty dict if loading fails.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(f"Warning: {path} is corrupt or not UTF-8 JSON. Starting fresh.")
        return {}

def extract_data(filename="data\\pdfs\\NCO_IDS_Sample.pdf", output_file="data/json/IDs_sample.json"):
    """
    Extract data from a PDF file and save it as a JSON file.
    Args:
        filename (str): The path to the PDF file.
        output_file (str): The path to the output JSON file.
    Returns:
        None
    """

    # Initialize data dictionary
    data = {}

    # Define regex patterns
    role_pattern = re.compile(r"\b\d{4}\.\d{4}\b")

    # Define a list to hold rows for later processing
    later = []

    # Extract tables from PDF
    with pdfplumber.open(filename) as pdf:
        print('PDF Pages:', len(pdf.pages))

        # Extract tables from each page
        for page_no, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            # Skip empty pages
            if not tables:
                continue
            # Check for specific page and table conditions (page 333 is the last page with one table)
            if len(tables)==1 and page_no!=333:

                  # Extract relevant rows
                  for row in tables[0]:
                    if not row or not row[1]:
                        continue
                    # Extract code and label
                    code = row[1].strip()
                    label = row[0].lower().replace('\n', '')

                    # Exceptions which require special handling
                    '''
                    This is due to a mistake in the Original Data.
                    Refer to NCO_2015 Page Number 150
                    '''

                    if code=='7222':
                        update_nested_dict(data, [code[0], code[:2], code[:3], code], {"Family Name": row[2]})
                    if code=='7222.0100':
                        update_nested_dict(data, [code[0], code[:2], code[:3], code[:4], code],
                                               {"Role Name": row[2], "2004 regulation": row[3]})


                    # Extract division, sub-division, group, and family names
                    if label == 'division':
                        update_nested_dict(data, [code], {"Division Name": row[2]})
                    elif label == 'sub-division':
                        update_nested_dict(data, [code[0], code], {"Sub-Division Name": row[2]})
                    elif label == 'group':
                        update_nested_dict(data, [code[0], code[:-1], code], {"Group Name": row[2]})
                    elif label == 'family':
                        update_nested_dict(data, [code[0], code[:2], code[:3], code], {"Family Name": row[2]})
                    elif role_pattern.search(code):
                        if data.get(code[0]):
                            if data[code[0]].get(code[:2]):
                                if data[code[0]][code[:2]].get(code[:3]):
                                    if data[code[0]][code[:2]][code[:3]].get(code[:4]):
                                        update_nested_dict(data, [code[0], code[:2], code[:3], code[:4], code],
                                               {"Role Name": row[2], "2004 regulation": row[3]})
                                    else:
                                        later.append(row)
            else:
                if data.get(code[0]):
                    if data[code[0]].get(code[:2]):
                        if data[code[0]][code[:2]].get(code[:3]):
                            if not data[code[0]][code[:2]][code[:3]].get(code[:4]):
                                update_nested_dict(data,[code[0], code[:2], code[:3], code[:4], code],
                                                   {
                                                     "Role Name": label, "2004 regulation":row[2]      
                                                   })
                        else:
                            update_nested_dict(data, [code[0], code[:-1], code], {"Group Name":"None"})
                    else:
                        update_nested_dict(data, [code[:1], code], {"Sub-Division Name":"None"})

                else:
                    update_nested_dict(data,[code[0]],{"Division Name":"None"})

        # Process later rows
        for row in later:
            code = row[1].strip()
            label = row[0].lower().replace('\n', '')
            update_nested_dict(data, [code[0], code[:2], code[:3], code[:4], code],
                                               {"Role Name": row[2], "2004 regulation": row[3]})

        # Write the output JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"Processed page {page_no}/{len(pdf.pages)}")

    print("Extraction complete!")



def extract_role_descriptions(pdf_path,output_json,max_nos=100000):
    """
    Extract role descriptions from a PDF file and save them as a JSON file.
    Args:
        pdf_path (str): The path to the PDF file.
        output_json (str): The path to the output JSON file.
        max_nos (int): The maximum number of roles to extract.
    Returns:
        None
    """

    # Open the PDF file
    doc = fitz.open(pdf_path)
    role_pattern = re.compile(r"\b\d{4}\.\d{4}\b")   # Role numbers like 1111.0300
    roles_dict = {}
    current_role_number = None
    current_description = []
    count = 0
    flag = False
    prev_role_no = None


    for page in doc:

        # Extract text from the page
        lines = page.get_text("text",clip=border_rect).split("\n")

        for line in lines:

            # Check if we reached the maximum number of roles
            if count>=max_nos:
                break

            # Strip whitespace from the line
            line_stripped = line.strip()

            # Detect a new role number
            match = role_pattern.search(line_stripped)
            if (match!=prev_role_no) and match:    
                flag = False
                count+=1
            
            # Skip unwanted headings or patterns
            if 'isco ' in line.lower():
                flag = True
            if flag:
                continue       

            # Process role description
            if match:
                if current_role_number and current_description:
                    roles_dict[current_role_number] = " ".join(current_description).strip()
                    current_description = []

                current_role_number = match.group(0)
                desc_part = line_stripped.replace(current_role_number, "").strip()
                if desc_part:
                    current_description.append(desc_part)
            else:
                if current_role_number:
                    current_description.append(line_stripped)
            prev_role_no = match

     # Save the last role
    if current_role_number and current_description:
        roles_dict[current_role_number] = " ".join(current_description).strip()

    # Save to UTF-8 JSON
    with open(output_json, "w", encoding="utf-8") as fp:
        json.dump(roles_dict, fp, indent=4, ensure_ascii=False)

    print(f"Extracted {len(roles_dict)} roles.")
    

def merge_jsons(roles_json,hierarchy_json):
    """
    Merge roles and Hierarchy JSON files.
    Args:
        roles_json (str): The path to the roles JSON file.
        hierarchy_json (str): The path to the hierarchy JSON file.
    Returns:
        None
    """

    # Load the roles and hierarchy JSON files
    with open(roles_json,'r',encoding='utf-8') as r:
        roles = json.load(r)
    with open(hierarchy_json,'r',encoding='utf-8') as h:
        hierarchy = json.load(h)

    # Merge the roles into the hierarchy
    for key,values in roles.items():

        # Exceptions - Some roles are not present in hierarchy data
        if key[:4]=='3127':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]] = {}
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Supervisors and Foremen and Related Trades Workers in Painting, Building Structure Cleaning, Other',
                '2004 Regulation': 'Not Mentioned'
            }
        if key=='7321.1100':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Router',
                '2004 Regulation': 'Not Mentioned'
            }
        elif key=='7322.0100':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Job Printer',
                '2004 Regulation': 'Not Mentioned'
            }
        elif key=='7323.0500':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Book Binding Operatives',
                '2004 Regulation': 'Not Mentioned'
            }
        elif key=='7421.0200':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Electronics Fitters, Other',
                '2004 Regulation': 'Not Mentioned'
            }
        elif key=='8112.0100':
            hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key] = {
                'Role Name': 'Electronics Fitters, Other',
                '2004 Regulation': 'Not Mentioned'
            }

        # Add role description
        hierarchy[key[:1]][key[:2]][key[:3]][key[:4]][key]['Role Description'] = values

    # Save the merged JSON
    with open('full.json','w',encoding='utf-8') as full:
        json.dump(hierarchy,full, indent=4,ensure_ascii=False )

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute the cosine similarity between two vectors.
    Args:
        a (np.ndarray): The first vector.
        b (np.ndarray): The second vector.
    Returns:
        float: The cosine similarity between the two vectors.
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def zscore_norm(scores: np.ndarray) -> np.ndarray:
    """
    Apply Z-score normalization to a numpy array.
    Args:
        scores (np.ndarray): The input array to normalize.
    Returns:
        np.ndarray: The Z-score normalized array.
    """
    if np.std(scores) == 0:
        return np.zeros_like(scores)
    return (scores - np.mean(scores)) / np.std(scores)

def format_json(input_file, output_file):
    import json
    import re

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    pattern = re.compile(r'^\d{4}\.\d{4}$')
    results = []

    def extract_roles(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if pattern.match(key):
                    results.append({
                        "role_number": key,
                        "Role Name": value.get("Role Name", ""),
                        "2004 Regulation": value.get("2004 regulation", ""),
                        "Role Description": value.get("Role Description", "")
                    })
                extract_roles(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_roles(item)

    extract_roles(data)

    with open(output_file, 'w', encoding='utf-8') as out:
        json.dump(results, out, ensure_ascii=False, indent=2)
    return results


if __name__ == '__main__':
    format_json('data/json/Complete.json', 'roles_output.json')
