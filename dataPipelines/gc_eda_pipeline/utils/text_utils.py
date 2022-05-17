import re
from string import punctuation

punct = set(punctuation)

def utf8_pass(text):
    return text.encode("utf-8", "ignore").decode("utf-8")


def clean_text(doc_text: str) -> str:
    """
    The text is cleaned from special characters and extra spaces
    Args:
        doc_text: input text to be cleaned

    Returns:

    """

    text = doc_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    remove = punctuation + "”“"
    remove = remove.replace(".", "")

    text = text.translate({ord(i): None for i in remove})

    return text

def extract_sow_pws(text):
    """
    Extracts out the SOW/PWS for EDA contracts
    Args:
        text: Raw text of the EDA contract

    Returns:SOW/PWS text for the contract if found, if not found, returns None

    """
    sow_regex_list = ['Section C.*-',"'SECTION C.*-'",'PERFORMANCE WORK STATEMENT','STATEMENT OF WORK']
    for sow_regex in sow_regex_list:
        sow_exist = re.search(sow_regex, text)
        if sow_exist:
            sow_pws_start = sow_exist.span()[0]
        else:
            continue
        sow_pws_end = re.search('Section [D-Z].*-', text[sow_pws_start:])
        if sow_pws_end is None:
            sow_pws_end = len(text)
        else:
            sow_pws_end = sow_pws_start + sow_pws_end.span()[0]
        sow_pws_text = text[sow_pws_start:sow_pws_end]
        return sow_pws_text
    return ""

def extract_clin_section(text):
    """
    The text is parsed and the CLIN section is extracted; this elimnates 
    potential parsing errors that might occur from other sections. In particular, 
    the first page is often poorly read in due to its structure and this helps 
    prevent any issues that might arise from trying to read that page.
    Args:
        text: raw text of the entire document

    Returns:
        CLIN: a subset of the text
    """
    section_B_exists = re.search(r"Section B.*-", text)
    if section_B_exists is None:
        item_no_exists = re.search(r"(ITEM NO){s<=1}\s*\n", text, flags=re.IGNORECASE)
        if item_no_exists is None:
            CLIN = 'None'
        else:
            clin_start = item_no_exists.span()[0]
            clin_end = len(text)
            CLIN =  text[clin_start:clin_end]
    else:
        clin_start = section_B_exists.span()[0]
        section_END_exists = re.search('Section [^AB]\s+-', text)
        if section_END_exists is None:
            clin_end = len(text)
        else:
            clin_end = section_END_exists.span()[0]
        CLIN = text[clin_start:clin_end]
    return(CLIN)

def extract_metadata_from_clin(text, regex):
    """
    Extract metadata from the CLIN, such as the PSC code.
    Args:
        text: raw text from the CLIN supplies/services section
        regex: regex to parse for certain 
    Returns:
        result: the extracted metadata, which varies based on regex input
    """
    result = re.search(regex, text, flags=re.IGNORECASE)
    if not result is None:
        result = text[result.span()[0]:result.span()[1]]
        # This should always work based on regex input ALWAYS containing ":" character
        try:
            result = result.split(':')[1].split('\\n')[0].strip()
        except:
            result = "FAILED TO PARSE: " + result
    return result

def parse_clin(text, re_clin=r"(ITEM NO){s<=1}\s*\n", attempt=0):
    """
    Args:
        text: a subset of the full text of a document; just the CLIN section if that could be parsed, else CLIN section to the end
        regex: regex to parse for certain 
    Returns:
        clins: list of dicts; each dictionary is parsed information on one CLIN
    """
    if text == "None":
        return "None"
    clins = []
    clin_start_pointers = re.finditer(re_clin, text)
    
    for clin_start in clin_start_pointers:
        pointer = clin_start.span()[0]
        # Jump to the start of the data
        i = 0
        while i < 6:
            next_line = re.search('\\n', text[pointer:len(text)])
            current_line = text[pointer:pointer + next_line.span()[1]]
            # Sometimes an extra line exists; if it does, we need to iterate over an extra line
            if current_line in ['MAX \n', 'EST. \n', 'EST . \n','ESTIMATED \n', 'NO \n']:
                i -= 1
            pointer = pointer + next_line.span()[1]
            i+=1
            
        clin_data_start = pointer
        
        # Find the end of the data
        for i in range(6):
            next_line = re.search('\\n', text[pointer:len(text)])
            if next_line is None:
                break
            pointer = pointer + next_line.span()[1]
        clin_data_end = pointer
        
        

        clin_text_start = clin_data_end
        
        text_end_pointer = re.search(r"(ITEM NO){s<=1}\s*\n", text[clin_text_start:len(text)])
        if text_end_pointer is None:
            text_end_pointer = re.search('Section [^AB]\s*-', text)
            if text_end_pointer is None:
                clin_text_end = len(text) # who knows
            else:
                clin_text_end = clin_text_start + text_end_pointer.span()[0]
        else:
            clin_text_end = clin_text_start + text_end_pointer.span()[0]
        
        clin_ref_text = text[clin_text_start:clin_text_end]
        
        # Extract PSC Code if it exists
        PSC_code = extract_metadata_from_clin(clin_ref_text, r'(PSC CD: .* \n){s<=1}')
        
        # Extract Purchase_Request_Num if it exists
        Purchase_Request_Num = extract_metadata_from_clin(clin_ref_text, r'(PURCHASE REQUEST NUMBER: .* \n){s<=2}')
        
        clin_data = text[clin_data_start:clin_data_end].split('\n')
        clin_num = clin_data[0].strip()
        clins.append({  'ITEM NO':clin_num,
                        'SUPPLIES/SERVICES':clin_data[1].strip() + '\n' + clin_ref_text,
                        'QUANTITY':clin_data[2].strip(),
                        'UNIT':clin_data[3].strip(),
                        'UNIT PRICE':[clin_data[4].strip()],
                        'AMOUNT':[clin_data[5].strip()],
                        'PSC Code':PSC_code,
                        'Purchase Request Number':Purchase_Request_Num,
                        'GOOD PARSE': clin_num[0:4].isnumeric()
                     })
    
    # If we don't find anything, we can try again but be more lax in our search
    if len(clins) == 0 and attempt == 0:
        clins = parse_clin(text, '\\n\\s*Item\\s*\\n', 1)
    if len(clins) == 0 and attempt == 1:
        clins = parse_clin(text, r"ITEM\s*\n\s*NO\s*\n", 2)
    
    return clins

# Determines if a document was successfully parsed for CLIN
def check_clin_parse(clins):
    if clins == 'None' or len(clins) == 0:
        return True
    else:
        return all(clin['GOOD PARSE'] for clin in clins)

def extract_clin(text):
    """
    Extracts out the CLINs for EDA contracts
    Args:
        text: Raw text of the EDA contract

    Returns:SOW/PWS text for the contract if found, if not found, returns None

    """
    clin_full_text = extract_clin_section(text)
    clins = parse_clin(clin_full_text)

    return clins