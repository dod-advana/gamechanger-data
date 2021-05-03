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
        "(US(?:(?:S(?:O(?:UTH)?|TRAT)|C(?:YBER|ENT)|INDOPA|TRANS|MEP|EU)COM|A(?:F(?:RICOM|E)?)?|N(?:ORTHCOM|A)|UHS)|D(?:(?:[IL]S?|PA|SC|M)A|e(?:pSecDef|CA)|C(?:[AMS]A|IS)|T(?:[RS]A|IC)|A(?:RPA|U)|H(?:R?A|M)|FAS)|C(?:E(?:N(?:WD(?:-(?:MR|NP))?|AD)|(?:S[APW]|LR|MV|PO)D|C(?:ER|RL)|TEC|WES)|/CFO|CLTF|IC)|A(?:F(?:(?:R(?:OT)?|S[OP]|GS|M)C|OSI)|R(?:BA|NG|L)|M(?:EDD|C)|(?:ET|C)C|TSD|DO|NG)?|N(?:(?:SA/CS|CI)S|G[AB]|R[LO]|avy|AG|DU)|P(?:(?:ACA|CTT)F|FPA)|M(?:AJCOM[Ss]?|DA)|O(?:N[IR]|EA)|S(?:ecDef|DA)|J[12345678]|W(?:SMR|HS)|ExecSec|LA|N(?:[GS]A|RO))"
    )
    orgs = re.compile(
        "(D(?:e(?:fense (?:C(?:o(?:unterintelligence|mmissary|ntract)|riminal)|T(?:echn(?:ology|ical)|hreat)|In(?:telligence|formation)|A(?:cquisition|dvanced)|H(?:UMINT|ealth|uman)|P(?:risoner|OW/MIA)|L(?:ogistics|egal)|Security|Finance|Media)|p(?:uty (?:Secretary|Under)|artment of))|irector(?:, (?:Operational|Joint)| of)|oD Components)|N(?:a(?:tional (?:(?:(?:Reconnaissa|Intellige)nc|Defens)e|G(?:eospatial-Intelligence|uard)|Assessment|Security)|val (?:Criminal|Research))|orth(?: (?:Atlant|Pacif)ic|western Division))|A(?:rm(?:y (?:(?:Nation|Medic)al|Re(?:search|view)|Digitization|Corps|and)|ed Services)|ir (?:Education|Mobility|National|Combat|Force)|ssistant (?:Commandant|Secretary|to))|U(?:.S. (?:(?:Transportatio|Europea|Norther)n|S(?:trategic|outhern|pecial)|C(?:entral|yber)|A(?:frica|rmy)|Indo-Pacific)|n(?:i(?:formed Servic|ted Stat)es|der Secretary))|C(?:o(?:m(?:(?:batant Command(?:er)?|ponent Head)s|mandant of)|nstruction Engineering|ld Regions)|h(?:ief Information|airman, Joint)|entral Security|lose Combat)|M(?:i(?:ss(?:i(?:ssippi Valley|le Defense)|ouri River)|litary Postal)|a(?:rine (?:Expeditionary|Corps)|jor Commands))|S(?:outh(?: (?:Atlant|Pacif)ic|western Division)|e(?:rgeant Major|cretary of)|pace Development)|W(?:a(?:shington Headquarters|terways Experiment)|hite Sands)|P(?:acific (?:Ocean|Air)|rotecting Critical|entagon Force)|E(?:lectromagnetic Spectrum|xecutive Secretary)|J(?:oint (?:Personnel|History)|[12345678] -)|G(?:eneral Counsel|reat Lakes)|Vice (?:Chairman|Director),|O(?:rganization|ffice) of|Topographic Engineering)"
    )
    return abbrvs, orgs
