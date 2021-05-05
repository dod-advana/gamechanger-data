import logging
import re

logger = logging.getLogger(__name__)


def _re_search(text, regex):
    mobj = re.search(regex, text)
    if mobj is None:
        return False
    elif len(mobj.group(1)) > 1:
        return True
    else:
        return False


def contains_entity(text, abbrv_re, orgs_re):
    """
    Simple check if it matches either regular expressions. Return `True` if
    either regular expressions match.

    Args:
        text (str): the text
        abbrv_re (SRE_Pattern): abbreviation regex from `build_entity_lookup()`
        orgs_re (SRE_Pattern): organization regex from `build_entity_lookup()`

    Returns:
        Bool
    """
    if _re_search(text, abbrv_re):
        return True
    elif _re_search(text, orgs_re):
        return True
    else:
        return False


def build_entity_lookup():
    """
    Compiles regular expressions for DoD organizations and abbreviations.

    Sources:
        https://en.wikipedia.org/wiki/List_of_U.S._Department_of_Defense_agencies
        https://en.wikipedia.org/wiki/Joint_Chiefs_of_Staff
        https://en.wikipedia.org/wiki/Office_of_the_Secretary_of_Defense

    Returns:
        SRE_Pattern, SRE_Pattern

    """
    abbrvs = re.compile(
        "(US(?:(?:S(?:O(?:UTH)?|TRAT)|C(?:YBER|ENT)|INDOPA|TRANS|EU)COM|A(?:F(?:RICOM|E)?)?|N(?:ORTHCOM|A)|M(?:EPCOM|C)|UHS)|D(?:(?:[IL]S?|SC|M)A|e(?:pSecDef|CA)|C(?:[AMS]A|IS)|A(?:RPA|&M|U)|T(?:[RS]A|IC)|H(?:R?A|M)|P(?:AA|MO)|OT&E|FAS)|A(?:F(?:(?:S[OP]|GS|M)C|R(?:(?:OT)?C|L)|OSI)|R(?:BA|NG|L)|M(?:EDD|C)|(?:ET|C)C|TSD|&S|DO|NG)|C(?:E(?:(?:S[APW]|N[AW]|LR|MV|PO)D|C(?:ER|RL)|TEC|WES)|(?:JC|S)S|/CFO|CLTF|APE|IC)|N(?:C(?:IS|B)|G[AB]|R[LO]|[DI]U|avy|AG|SA)|P(?:(?:ACA|CTT)F|FPA|&R)|S(?:O/LIC&IC|ecDef|DA)|(?:H(?:D&AS)?|GS|R)A|M(?:AJCOM[Ss]|DA)|O(?:N[IR]|EA)|I(?:P?SA|&E)|J[12345678]|W(?:SMR|HS)|L(?:&MR|A)|ExecSec)"
    )
    orgs = re.compile(
        "(D(?:e(?:fense (?:C(?:o(?:unterintelligence|mmissary|ntract)|riminal)|T(?:echn(?:ology|ical)|hreat)|In(?:telligence|formation)|A(?:cquisition|dvanced)|H(?:UMINT|ealth|uman)|P(?:risoner|OW/MIA)|L(?:ogistics|egal)|Security|Finance|Media)|p(?:uty (?:Secretary|Under)|artment of))|irector(?:, (?:Operational|Joint)| of))|A(?:rm(?:y (?:(?:Nation|Medic)al|C(?:riminal|orps)|Re(?:search|view)|Digitization|and)|ed Services)|ir (?:Education|Mobility|National|Combat|Force)|ssistant (?:Commandant|Secretary|to))|N(?:a(?:tional (?:(?:(?:Reconnaissa|Intellige)nc|Defens)e|G(?:eospatial-Intelligence|uard)|Assessment|Security)|val (?:Criminal|Research))|orth(?: (?:Atlant|Pacif)ic|western Division))|U(?:.S. (?:(?:Transportatio|Europea|Norther)n|S(?:trategic|outhern|pecial)|C(?:entral|yber)|A(?:frica|rmy)|Indo-Pacific)|n(?:i(?:formed Servic|ted Stat)es|der Secretary))|C(?:o(?:m(?:batant Commanders|mandant of)|nstruction Engineering|ld Regions)|h(?:ief Information|airman, Joint)|entral Security|lose Combat)|M(?:i(?:ss(?:i(?:ssippi Valley|le Defense)|ouri River)|litary Postal)|a(?:rine (?:Expeditionary|Corps)|jor Commands))|S(?:outh(?: (?:Atlant|Pacif)ic|western Division)|e(?:rgeant Major|cretary of)|pace Development)|W(?:a(?:shington Headquarters|terways Experiment)|hite Sands)|P(?:acific (?:Ocean|Air)|rotecting Critical|entagon Force)|E(?:lectromagnetic Spectrum|xecutive Secretary)|J(?:oint (?:Personnel|History)|[12345678] -)|(?:O(?:rganization|ffice)|Heads) of|G(?:eneral Counsel|reat Lakes)|Vice (?:Chairman|Director),|Topographic Engineering)"
    )
    return abbrvs, orgs
