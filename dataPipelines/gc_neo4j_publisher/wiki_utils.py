import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import common.utils.text_utils as tu


def flip_nums(text):
    """ flips numbers on string to the end (so 2019_est --> est_2019)"""
    if not text:
        return ''

    i = 0
    s = text + '_'
    while text[i].isnumeric():
        s += text[i]
        i += 1

    if text[i] == '_':
        i += 1

    return s[i:]


def clean_key(k):
    """ cleans key of dictionary so it won't cause neo4j syntax errors """
    k = re.sub(r'[^\x00-\x7f]', r'', k)
    k = re.sub("[\(\[].*?[\)\]]", "", k)
    k = k.replace(" ", "_").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace(",", "")
    k = k.replace(".", "").replace('"', "").replace("-", "_").replace("/", "_").replace("'", "").replace(":", "")
    k = flip_nums(k)
    k = tu.squash_underscores(k)
    if k[-1] == "_":
        k = k[:-1]
    k = tu.drop_underscores_around_words(k)
    k = tu.squash_whitespace_to_spaces(k)
    return k.strip()


def clean_value(ins):
    """ cleans value so it won't cause neo4j syntax errors """
    if isinstance(ins, list):
        new_list = []
        for i in ins:
            i = re.sub("[\(\[].*?[\)\]]", "", i)
            i = re.sub(r'[^\x00-\x7f]', r'', i)
            i = i.replace('\r', '').replace('\n', '').replace('"', "'")
            i = i.replace('(', '').replace(')', '')
            i = tu.squash_underscores(i)
            i = tu.drop_underscores_around_words(i)
            i = tu.squash_whitespace_to_spaces(i)
            i = i.strip()
            new_list.append(i)

        return new_list

    else:
        ins = re.sub("[\(\[].*?[\)\]]", "", ins)
        ins = re.sub(r'[^\x00-\x7f]', r'', ins)
        ins = ins.replace('\r', '').replace('\n', '').replace('"', "'").replace("\t", " ")
        ins = ins.replace('(', '').replace(')', '')
        ins = tu.squash_underscores(ins)
        ins = tu.drop_underscores_around_words(ins)
        ins = tu.squash_whitespace_to_spaces(ins)
        ins = ins.strip()

    return ins


def get_infobox_info(item):
    """ gets information the wikipedia article's infobox and returns it as a dictionary, or an empty dictionary if
     the link does not exist"""
    link_arr = item.split(' ')
    # remove the word "the" from entity name
    if link_arr[0].lower() == 'the':
        link_arr = link_arr[1:]
    link = '_'.join(link_arr)

    url = "https://en.wikipedia.org/wiki/" + link

    # TODO: find a better workaround
    # try adding United States adn US in front of entities (like United States Army, USDOD)
    second_url = 'https://en.wikipedia.org/wiki/United_States_' + link
    third_url = 'https://en.wikipedia.org/wiki/US' + link

    result = get_infobox_from_link(url)
    if not result:
        result = get_infobox_from_link(second_url)

    if not result:
        result = get_infobox_from_link(third_url)

    return result


def get_infobox_from_link(link):
    result = {}

    try:
        response = requests.get(url=link, verify=False)

        soup = BeautifulSoup(response.content, 'html.parser')
        name = soup.find('h1', class_='firstHeading').text
        table = soup.find('table', class_='infobox')
        if table:
            result['Last_Retrieved'] = datetime.utcnow().strftime('%Y/%m/%d-%H:%M:%S') + " UTC"
            result['Redirect_Name'] = name
            for tr in table.find_all('tr'):
                if tr.find('th') and tr.find('td'):
                    info = tr.find('td')
                    li = []
                    k = tr.find('th').text
                    k = clean_key(k)

                    if not k:
                        continue

                    for el in info.find_all('li'):
                        li.append(el.text)
                    if not li:
                        val = tr.find('td').text
                    else:
                        val = [el for el in li]

                    r = clean_value(val)
                    if not r:
                        continue

                    result[k] = r

                else:
                    if tr.find('td'):
                        if tr.find('td').find('a', class_='image'):
                            if 'image' not in result:
                                result['image'] = 'https:' + tr.find('td').find('a', class_='image').img['src']
    except Exception as e:
        print('error in getting page ' + link + ": " + str(e))

    return result

