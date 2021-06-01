import re

def make_dict():
    ref_dict = {}
    ref_dict['DoD'] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod\s*placeholder)|(dod))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDD"] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod\s*directives?)|(dodd))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDI"] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod\s*instruction)|(dodi))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDM"] = (
        re.compile(r"([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}((\s*,*\s*Volume\s*[0-9]+)|(\s*(-\s*V[0-9])))?", re.IGNORECASE),
        re.compile(r"\b(((dod\s*manual)|(dodm))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}((\s*,*\s*Volume\s*[0-9]+)|(\s*(-\s*V[0-9])))?)",
        re.IGNORECASE)
    )
    ref_dict["DTM"] =(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((DTM)|(DT\s*Memorandum))\s*\)?\s*-?\s*[0-9]{2}\s*-\s*[0-9]{3})", re.IGNORECASE)
    )
    ref_dict["AI"] =(
        re.compile(r"([0-9]+)", re.IGNORECASE),
        re.compile(r"\b(((administrative\s*instruction)|(ai))\s*\)?\s*[0-9]+)", re.IGNORECASE)
    )
    ref_dict["Title"] =(
        re.compile(r"([0-9]{1,2})", re.IGNORECASE),
        re.compile(r"\b((Title)\s*[0-9]{1,2})", re.IGNORECASE)
    )
    ref_dict["ICD"] =(
        re.compile(r"([0-9]{1,3})", re.IGNORECASE),
        re.compile(r"\b(((Intelligence\s*Community\s*Directive)|(ICD))\s*\)?\s*[0-9]{1,3})", re.IGNORECASE)
    )
    ref_dict["ICPG"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{3}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b((icpg)\s*([A-Z]+-)?[0-9]{3}\.\s*[0-9]{1,3}\s*(-[A-Z]+)?([E])?)", re.IGNORECASE)
    )
    ref_dict["ICPM"] =(
        re.compile(r"([0-9]{4}-\s*[0-9]{3}-\s*[0-9]{1})", re.IGNORECASE),
        re.compile(r"\b((icpm)\s*[0-9]{4}-\s*[0-9]{3}-\s*[0-9]{1})", re.IGNORECASE)
    )
    ref_dict["CJCSI"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs\s*instruction)|(cjcsi))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSM"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs\s*manual)|(cjcsm))\s*\)?\s*([A-Z]+-)?[0-9]{4}\.\s*[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSG"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}\s*([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs\s*gde)|(cjcsg))\s*\)?\s*([A-Z]+-)?[0-9]{4}\s*([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSN"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}(\.\s*[0-9]{0,3}([A-Z])?)?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs\s*notice)|(cjcsn))\s*\)?\s*([A-Z]+-)?[0-9]{4}(\.\s*[0-9]{0,3}([A-Z])?)?)",
        re.IGNORECASE)
    )
    ref_dict["JP"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{1,2}-[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((joint\s*publication)|(jp))\s*\)?\s*([A-Z]+-)?[0-9]{1,2}-[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["DCID"] =(
        re.compile(r"[0-9]\/[0-9]{1,2}(P)?", re.IGNORECASE),
        re.compile(r"\b(((Director\s*of\s*Central\s*Intelligence\s*Directives)|(DCID))\s*\)?\s*[0-9]\/[0-9]{1,2}(P)?)",
        re.IGNORECASE)
    )
    ref_dict["EO"] =(
        re.compile(r"[0-9]{5}", re.IGNORECASE),
        re.compile(r"\b(((Executive\s*Order)|(EO)|(E\.\s*O\.\s*))\s*\)?\s*[0-9]{5})", re.IGNORECASE)
    )
    ref_dict["AR"] =(
        re.compile(r"[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{1,3})?", re.IGNORECASE),
        re.compile(r"\b(((AR)|(Army\s*regulations?))\s*\)?\s*[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{1,3})?)",
        re.IGNORECASE)
    )
    ref_dict["AGO"] =(
        re.compile(r"(19|20)[0-9]{2}\s*-\s*[0-9]{2,3}", re.IGNORECASE),
        re.compile(r"\b(((AGO)|(Army\s*General\s*Orders?))\s*\)?\s*(19|20)[0-9]{2}\s*-\s*[0-9]{2,3})",
        re.IGNORECASE)
    )
    ref_dict["ADP"] =(
        re.compile(r"(([1])|([0-9]{1,2}\s*-\s*[0-9]{1,2}))", re.IGNORECASE),
        re.compile(r"\b(((ADP)|(Army\s*Doctrine\s*Publications?))\s*\)?\s*(([1])|([0-9]{1,2}\s*-\s*[0-9]{1,2})))",
        re.IGNORECASE)
    )
    ref_dict["PAM"] =(
        re.compile(r"[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{1,3})?", re.IGNORECASE),
        re.compile(r"\b(((PAM)|(DA\s*Pam(phlets?)?))\s*\)?\s*[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{1,3})?)",
        re.IGNORECASE)
    )
    ref_dict["ATP"] =(
        re.compile(r"[0-9]\s*-\s*[0-9]{1,2}(\.[0-9]{1,2}(\s*-\s*[0-9]{1,2})?)?", re.IGNORECASE),
        re.compile(r"\b(((ATP)|(Army\s*Techniques\s*Publications?))\s*\)?\s*[0-9]\s*-\s*[0-9]{1,2}(\.[0-9]{1,2}(\s*-\s*[0-9]{1,2})?)?)",
        re.IGNORECASE)
    )
    ref_dict["ARMY"] =(
        re.compile(r"20[0-9]{2}\s*-\s*[0-9]{2}(\s*-\s*[0-9]{1,2})?", re.IGNORECASE),
        re.compile(r"\b(((ARMY\s*DIR)|(ARMY\s*Directives?))\s*\)?\s*20[0-9]{2}\s*-\s*[0-9]{2}(\s*-\s*[0-9]{1,2})?)",
        re.IGNORECASE)
    )
    ref_dict["TC"] =(
        re.compile(r"[0-9]{1,2}\s*-\s*((HEAT)|([0-9]{1,3}(\s*(\.|-)\s*[0-9]{1,3}(\s*-\s*[0-9])?A?)?))", re.IGNORECASE),
        re.compile(r"\b(((TC)|(Training\s*Circular))\s*\)?\s*[0-9]{1,2}\s*-\s*((HEAT)|([0-9]{1,3}(\s*(\.|-)\s*[0-9]{1,3}(\s*-\s*[0-9])?A?)?)))",
        re.IGNORECASE)
    )
    ref_dict["STP"] =(
        re.compile(r"[0-9]{1,2}\s*-\s*[A-Z0-9]{1,6}(\s*-\s*[A-Z]{2,4}(\s*-\s*[A-Z]{2})?)?", re.IGNORECASE),
        re.compile(r"\b(((STP)|(Soldier\s*Training\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[A-Z0-9]{1,6}(\s*-\s*[A-Z]{2,4}(\s*-\s*[A-Z]{2})?)?)",
        re.IGNORECASE)
    )
    ref_dict["TB"] =(
        re.compile(r"((ENG\s*[0-9]{2,3})|([0-9]{3}\s*-\s*[0-9]{1,2})|(MED\s*[0-9]{1,3}(\s*-\s*[0-9]{1,2})?)|([0-9]{1,2}\s*-\s*[0-9]{3,4}(\s*-\s*([0-9]{3}\s*-\s*[0-9]{2})|([A-Z]{3}))?))", re.IGNORECASE),
        re.compile(r"\b(((TB)|(Technical\s*Bulletins?))\s*\)?\s*((ENG\s*[0-9]{2,3})|([0-9]{3}\s*-\s*[0-9]{1,2})|(MED\s*[0-9]{1,3}(\s*-\s*[0-9]{1,2})?)|([0-9]{1,2}\s*-\s*[0-9]{3,4}(\s*-\s*([0-9]{3}\s*-\s*[0-9]{2})|([A-Z]{3}))?)))",
        re.IGNORECASE)
    )
    ref_dict["DA"] =(
        re.compile(r"[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{2})?", re.IGNORECASE),
        re.compile(r"\b(((DA\s*MEMO)|(DA\s*MEMORANDUMS?))\s*\)?\s*[0-9]{1,3}\s*-\s*[0-9]{1,3}(\s*-\s*[0-9]{2})?)",
        re.IGNORECASE)
    )
    ref_dict["FM"] =(
        re.compile(r"[0-9]{1,3}\s*-\s*([0-9]{1,3}(\s*(\.|-)\s*[0-9]{1,2}(\s*-\s*[A-Z]{2})?)?)", re.IGNORECASE),
        re.compile(r"\b(((FM)|(Field\s*Manual))\s*\)?\s*[0-9]{1,3}\s*-\s*([0-9]{1,3}(\s*(\.|-)\s*[0-9]{1,2}(\s*-\s*[A-Z]{2})?)?))",
        re.IGNORECASE)
    )
    ref_dict["GTA"] =(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{2}(\s*-\s*[0-9]{3})?[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((GTA)|(Graphic\s*Training\s*Aid))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{2}(\s*-\s*[0-9]{3})?[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["HQDA"] =(
        re.compile(r"[0-9]{1,3}\s*-\s*[0-9]{1}", re.IGNORECASE),
        re.compile(r"\b((HQDA\s*POLICY\s*NOTICE)\s*[0-9]{1,3}\s*-\s*[0-9]{1})",
        re.IGNORECASE)
    )
    ref_dict["CTA"] =(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((CTA)|(Common\s*Table\s*of\s*Allowances?))\s*\)?\s*[[0-9]{1,2}\s*-\s*[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["ATTP"] =(
        re.compile(r"[0-9]{1}\s*-\s*[0-9]{2}\s*\.\s*[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((ATTP)|(ARMY\s*TACTICS,?\s*TECHNIQUES\s*AND\s*PROCEDURES?))\s*\)?\s*[0-9]{1}\s*-\s*[0-9]{2}\s*\.\s*[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["TM"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[A-Z0-9]{1,4}(\.[0-9]{2})?(\s*-\s*[A-Z0-9&]{1,4})*", re.IGNORECASE),
        re.compile(r"\b(((TM)|(Technical\s*Manuals?))\s*\)?\s*[0-9]{1,2}\s*-\s*[A-Z0-9]{1,4}(\.[0-9]{2})?(\s*-\s*[A-Z0-9&]{1,4})*)", re.IGNORECASE)
    )
    ref_dict["AFI"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((AFI)|(Air\s*Force\s*Instructions?))\s*\)?\s*[0-9]{1,2}\s*-\s*[A-Z0-9-_]+)", re.IGNORECASE)
    )
    ref_dict["CFETP"]=(
        re.compile(r"[A-Z0-9]*[0-9][A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((CFETP)|(CAREER\s*FIELD\s*EDUCATION\s*(AND|&)\s*TRAINING\s*PLAN))\s*\)?\s*[A-Z0-9]*[0-9][A-Z0-9-_]+)",
        re.IGNORECASE)
    )
    ref_dict["AFMAN"]=(
        re.compile(r"[0-9]{2}\s*-\s*[A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((AFMAN)|(AIR\s*FORCE\s*MANUAL))\s*\)?\s*[0-9]{2}\s*-\s*[A-Z0-9-_]+)",
        re.IGNORECASE)
    )
    ref_dict["QTP"]=(
        re.compile(r"[0-9][0-9A-Z]{1,6}(\s*-\s*[0-9A-Z]{1,6}){0,2}", re.IGNORECASE),
        re.compile(r"\b(((QTP)|(QUALIFICATION\s*TRAINING\s*PACKAGE))\s*\)?\s*[0-9][0-9A-Z]{1,6}(\s*-\s*[0-9A-Z]{1,6}){0,2})",
        re.IGNORECASE)
    )
    ref_dict["AFPD"]=(
        re.compile(r"((1)|([0-9]{2}\s*-\s*[0-9]{1,2}(\s*-\s*[A-Z]{1})?))", re.IGNORECASE),
        re.compile(r"\b(((AFPD)|(AIR\s*FORCE\s*POLICY\s*DIRECTIVE))\s*\)?\s*((1)|([0-9]{2}\s*-\s*[0-9]{1,2}(\s*-\s*[A-Z]{1})?)))",
        re.IGNORECASE)
    )
    ref_dict["AFTTP"]=(
        re.compile(r"[0-9]\s*-\s*[0-9]{1,2}(\.[0-9]{1,2})?((V[0-9])|(_[A-Z]{2}))?", re.IGNORECASE),
        re.compile(r"\b(((AFTTP)|(Air\s*Force\s*Tactics?,?\s*Techniques?,?\s*(and|&)?\s*Procedures?))\s*\)?\s*[0-9]\s*-\s*[0-9]{1,2}(\.[0-9]{1,2})?((V[0-9])|(_[A-Z]{2}))?)",
        re.IGNORECASE)
    )
    ref_dict["AFVA"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{1,4}", re.IGNORECASE),
        re.compile(r"\b(((AFVA)|(Air\s*Force\s*Visual\s*Aids?))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{1,4})",
        re.IGNORECASE)
    )
    ref_dict["AFH"]=(
        re.compile(r"((1)|(([0-9]{1,2}\s*-\s*[0-9]{3,4})((\s*\(\s*I\s*\))|(\s*V\s*[0-9]{1,2})|(\s*,\s*Vol(ume)?\s*[0-9]{1,2}))?))", re.IGNORECASE),
        re.compile(r"\b(((AFH)|(Air\s*Force\s*Handbook))\s*\)?\s*((1)|(([0-9]{1,2}\s*-\s*[0-9]{3,4})((\s*\(\s*I\s*\))|(\s*V\s*[0-9]{1,2})|(\s*,\s*Vol(ume)?\s*[0-9]{1,2}))?)))",
        re.IGNORECASE)
    )
    ref_dict["HAFMD"]=(
        re.compile(r"[0-9]\s*-\s*[0-9]{1,2}(\s*ADDENDUM\s*[A-Z])?", re.IGNORECASE),
        re.compile(r"\b(((HAFMD)|(HEADQUARTERS\s*AIR\s*FORCE\s*MISSION\s*DIRECTIVE))\s*\)?\s*[0-9]\s*-\s*[0-9]{1,2}(\s*ADDENDUM\s*[A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["AFPAM"]=(
        re.compile(r"(\(\s*I\s*\)\s*)?[0-9]{2}\s*-\s*[0-9]{3,4}(\s*V\s*[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((AFPAM)|(Air\s*Force\s*Pamphlet))\s*\)?\s*(\(\s*I\s*\)\s*)?[0-9]{2}\s*-\s*[0-9]{3,4}(\s*V\s*[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AFMD"]=(
        re.compile(r"[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((AFMD)|(Air\s*Force\s*MISSION\s*DIRECTIVE))\s*\)?\s*[0-9]{1,2})", re.IGNORECASE)
    )
    ref_dict["AFM"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((AFM)|(Air\s*Force\s*Manual))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["HOI"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((HOI)|(HEADQUARTERS\s*OPERATING\s*INSTRUCTION))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["AFJQS"]=(
        re.compile(r"[0-9][0-9A-Z]{4}(\s*-\s*[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((AFJQS)|(Air\s*Force\s*Job\s*Qualification\s*Standard))\s*\)?\s*[0-9][0-9A-Z]{4}(\s*-\s*[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AFJI"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{3,4}", re.IGNORECASE),
        re.compile(r"\b(((AFJI)|(Air\s*Force\s*Joint\s*Instruction))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{3,4})",
        re.IGNORECASE)
    )
    ref_dict["AFGM"]=(
        re.compile(r"[0-9]{4}\s*-\s*[0-9]{2}\s*-\s*[0-9]{2}([0-9]\s*-\s*[0-9]{2})?", re.IGNORECASE),
        re.compile(r"\b(((AFGM)|(Air\s*Force\s*Guidance\s*Memorandum))\s*\)?\s*[0-9]{4}\s*-\s*[0-9]{2}\s*-\s*[0-9]{2}([0-9]\s*-\s*[0-9]{2})?)",
        re.IGNORECASE)
    )
    ref_dict["DAFI"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{3,4}(\s*V\s*[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((DAFI)|(Department\s*of\s*the\s*Air\s*Force\s*Instruction))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{3,4}(\s*V\s*[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AF"]=(
        re.compile(r"[0-9]{1,4}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((AF)|(Air\s*Force))\s*\)?\s*(Form\s*)?[0-9]{1,4}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SF"]=(
        re.compile(r"[0-9]{2,4}(\s*-\s*[0-9])?[A-Z]?", re.IGNORECASE),
        re.compile(r"\b((SF)\s*\)?\s*[0-9]{2,4}(\s*-\s*[0-9])?[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["AFPM"]=(
        re.compile(r"[0-9]{4}\s*-\s*[0-9]{2}\s*-\s*[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((AFPM)|(Air\s*Force\s*Policy\s*Memorandum))\s*\)?\s*[0-9]{4}\s*-\s*[0-9]{2}\s*-\s*[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["AFJMAN"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((AFJMAN)|(Air\s*Force\s*Joint\sManual))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["JTA"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{1,3}", re.IGNORECASE),
        re.compile(r"\b(((JTA)|(Joint\s*Table\s*of\sAllowances?))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{1,3})",
        re.IGNORECASE)
    )
    ref_dict["DAFPD"]=(
        re.compile(r"[0-9]{2}\s*-\s*[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((DAFPD)|(Department\s*of\s*\the\s*Air\s*Force\s*Policy\s*Directive))\s*\)?\s*[0-9]{2}\s*-\s*[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["MCO"]=(
        re.compile(r"P?[0-9]{4,5}[A-Z]?\.[0-9]{1,3}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((MCO)|(Marine\s*Corps\s*Orders?))\s*\)?\s*P?[0-9]{4,5}[A-Z]?\.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["MCBUL"]=(
        re.compile(r"[0-9]{4,5}", re.IGNORECASE),
        re.compile(r"\b(((MCBUL)|(MARINE\s*CORPS\s*BULLETIN))\s*\)?\s*[0-9]{4,5})",
        re.IGNORECASE)
    )
    ref_dict["NAVMC"]=(
        re.compile(r"[0-9]{4}((\.[0-9]{1,3}[A-Z]?)|(\s*-\s*[A-Z]))?", re.IGNORECASE),
        re.compile(r"\b((NAVMC)\s*\)?\s*[0-9]{4}((\.[0-9]{1,3}[A-Z]?)|(\s*-\s*[A-Z]))?)",
        re.IGNORECASE)
    )
    ref_dict["NAVMC DIR"]=(
        re.compile(r"[0-9]{4}.[0-9]{1,3}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((NAVMC\s*DIR)|(NAVMC\s*Directive))\s*\)?\s*[0-9]{4}.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["MCRP"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{1,2}[A-Z]?(\.[0-9]{1-2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((MCRP)|(MARINE\s*CORPS\s*Reference\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{1,2}[A-Z]?(\.[0-9]{1-2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["MCTP"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{2}[A-Z]", re.IGNORECASE),
        re.compile(r"\b(((MCTP)|(MARINE\s*CORPS\s*Tactical\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{2}[A-Z])",
        re.IGNORECASE)
    )
    ref_dict["MCWP"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{2}(\.[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((MCWP)|(MARINE\s*CORPS\s*Warfighting\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{2}(\.[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["MCDP"]=(
        re.compile(r"[0-9](\s*-\s*[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((MCDP)|(MARINE\s*CORPS\s*Doctrinal\s*Publication))\s*\)?\s*[0-9](\s*-\s*[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["MCIP"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{2}([A-Z]{1,2})?(\.?[0-9]{1,2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((MCIP)|(MARINE\s*CORPS\s*Interim\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{2}([A-Z]{1,2})?(\.?[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["FMFRP"]=(
        re.compile(r"[0-9]{1,2}\s*-\s*[0-9]{1,3}(\s*-\s*I+)?", re.IGNORECASE),
        re.compile(r"\b(((FMFRP)|(Fleet\s*Marine\s*Force\s*Reference\s*Publication))\s*\)?\s*[0-9]{1,2}\s*-\s*[0-9]{1,3}(\s*-\s*I+)?)",
        re.IGNORECASE)
    )
    ref_dict["FMFM"]=(
        re.compile(r"[0-9]\s*-\s*[0-9]{1,2}(\s*-\s*[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((FMFM)|(Fleet\s*Marine\s*Force\s*Manuals?))\s*\)?\s*[0-9]\s*-\s*[0-9]{1,2}(\s*-\s*[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["IRM"]=(
        re.compile(r"(-\s*)?[0-9]{4}\s*-\s*[0-9]{2}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((IRM)|(Information\s*Resource\s*Management))\s*\)?\s*(-\s*)?[0-9]{4}\s*-\s*[0-9]{2}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SECNAVINST"]=(
        re.compile(r"[0-9]{4}\.[0-9]{1,2}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((SECNAVINST)|(SECNAV\s*INSTRUCTION))\s*\)?\s*[0-9]{4}\.[0-9]{1,2}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SECNAV"]=(
        re.compile(r"M\s*-\s*[0-9]{4}\.[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b((SECNAV)\s*\)?\s*M\s*-\s*[0-9]{4}\.[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["NAVSUP"]=(
        re.compile(r"((P\s*-\s*)|(Publication\s*))[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b((NAVSUP)\s*\)?\s*((P\s*-\s*)|(Publication\s*))[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["JAGINST"]=(
        re.compile(r"[0-9]{4,5}(\.[0-9]{1,2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((JAGINST)|(JAG\s*Instruction))\s*\)?\s*[0-9]{4,5}(\.[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["OMBM"]=(
        re.compile(r"M-[0-9]{2}-[0-9]{2}", re.IGNORECASE),
        re.compile(r"((M-[0-9]{2}-[0-9]{2}))",
        re.IGNORECASE)
    )
    return ref_dict
