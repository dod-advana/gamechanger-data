import re

def make_dict():
    ref_dict = {}
    ref_dict['DoD'] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod ?placeholder)|(dod)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDD"] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod ?directives?)|(dodd)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDI"] = (
        re.compile(r"(([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b(((dod ?instruction)|(dodi)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)",
        re.IGNORECASE)
    )
    ref_dict["DoDM"] = (
        re.compile(r"([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}(( ?,* ?Volume ?[0-9]+)|( ?(- ?V[0-9])))?", re.IGNORECASE),
        re.compile(r"\b(((dod ?manual)|(dodm)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}(( ?,* ?Volume ?[0-9]+)|( ?(- ?V[0-9])))?)",
        re.IGNORECASE)
    )
    ref_dict["DTM"] =(
        re.compile(r"[0-9]{2} ?- ?[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((DTM)|(DT ?Memorandum)) ?\)? ?-? ?[0-9]{2} ?- ?[0-9]{3})", re.IGNORECASE)
    )
    ref_dict["AI"] =(
        re.compile(r"([0-9]+)", re.IGNORECASE),
        re.compile(r"\b(((administrative ?instruction)|(ai)) ?\)? ?[0-9]+)", re.IGNORECASE)
    )
    ref_dict["Title"] =(
        re.compile(r"([0-9]{1,2})", re.IGNORECASE),
        re.compile(r"\b((Title) ?[0-9]{1,2})", re.IGNORECASE)
    )
    ref_dict["ICD"] =(
        re.compile(r"([0-9]{1,3})", re.IGNORECASE),
        re.compile(r"\b(((Intelligence ?Community ?Directive)|(ICD)) ?\)? ?[0-9]{1,3})", re.IGNORECASE)
    )
    ref_dict["ICPG"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{3}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)", re.IGNORECASE),
        re.compile(r"\b((icpg) ?([A-Z]+-)?[0-9]{3}\. ?[0-9]{1,3} ?(-[A-Z]+)?([E])?)", re.IGNORECASE)
    )
    ref_dict["ICPM"] =(
        re.compile(r"([0-9]{4}- ?[0-9]{3}- ?[0-9]{1})", re.IGNORECASE),
        re.compile(r"\b((icpm) ?[0-9]{4}- ?[0-9]{3}- ?[0-9]{1})", re.IGNORECASE)
    )
    ref_dict["CJCSI"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs ?instruction)|(cjcsi)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSM"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs ?manual)|(cjcsm)) ?\)? ?([A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSG"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4} ?([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs ?gde)|(cjcsg)) ?\)? ?([A-Z]+-)?[0-9]{4} ?([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["CJCSN"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{4}(\. ?[0-9]{0,3}([A-Z])?)?)", re.IGNORECASE),
        re.compile(r"\b(((cjcs ?notice)|(cjcsn)) ?\)? ?([A-Z]+-)?[0-9]{4}(\. ?[0-9]{0,3}([A-Z])?)?)",
        re.IGNORECASE)
    )
    ref_dict["JP"] =(
        re.compile(r"(([A-Z]+-)?[0-9]{1,2}-[0-9]{1,3}([A-Z])?)", re.IGNORECASE),
        re.compile(r"\b(((joint ?publication)|(jp)) ?\)? ?([A-Z]+-)?[0-9]{1,2}-[0-9]{1,3}([A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["DCID"] =(
        re.compile(r"[0-9]\/[0-9]{1,2}(P)?", re.IGNORECASE),
        re.compile(r"\b(((Director ?of ?Central ?Intelligence ?Directives)|(DCID)) ?\)? ?[0-9]\/[0-9]{1,2}(P)?)",
        re.IGNORECASE)
    )
    ref_dict["EO"] =(
        re.compile(r"[0-9]{5}", re.IGNORECASE),
        re.compile(r"\b(((Executive ?Order)|(EO)|(E\. ?O\. ?)) ?\)? ?[0-9]{5})", re.IGNORECASE)
    )
    ref_dict["AR"] =(
        re.compile(r"[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{1,3})?", re.IGNORECASE),
        re.compile(r"\b(((AR)|(Army ?regulations?)) ?\)? ?[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{1,3})?)",
        re.IGNORECASE)
    )
    ref_dict["AGO"] =(
        re.compile(r"(19|20)[0-9]{2} ?- ?[0-9]{2,3}", re.IGNORECASE),
        re.compile(r"\b(((AGO)|(Army ?General ?Orders?)) ?\)? ?(19|20)[0-9]{2} ?- ?[0-9]{2,3})",
        re.IGNORECASE)
    )
    ref_dict["ADP"] =(
        re.compile(r"(([1])|([0-9]{1,2} ?- ?[0-9]{1,2}))", re.IGNORECASE),
        re.compile(r"\b(((ADP)|(Army ?Doctrine ?Publications?)) ?\)? ?(([1])|([0-9]{1,2} ?- ?[0-9]{1,2})))",
        re.IGNORECASE)
    )
    ref_dict["PAM"] =(
        re.compile(r"[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{1,3})?", re.IGNORECASE),
        re.compile(r"\b(((PAM)|(DA ?Pam(phlets?)?)) ?\)? ?[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{1,3})?)",
        re.IGNORECASE)
    )
    ref_dict["ATP"] =(
        re.compile(r"[0-9] ?- ?[0-9]{1,2}(\.[0-9]{1,2}( ?- ?[0-9]{1,2})?)?", re.IGNORECASE),
        re.compile(r"\b(((ATP)|(Army ?Techniques ?Publications?)) ?\)? ?[0-9] ?- ?[0-9]{1,2}(\.[0-9]{1,2}( ?- ?[0-9]{1,2})?)?)",
        re.IGNORECASE)
    )
    ref_dict["ARMY"] =(
        re.compile(r"20[0-9]{2} ?- ?[0-9]{2}( ?- ?[0-9]{1,2})?", re.IGNORECASE),
        re.compile(r"\b(((ARMY ?DIR)|(ARMY ?Directives?)) ?\)? ?20[0-9]{2} ?- ?[0-9]{2}( ?- ?[0-9]{1,2})?)",
        re.IGNORECASE)
    )
    ref_dict["TC"] =(
        re.compile(r"[0-9]{1,2} ?- ?((HEAT)|([0-9]{1,3}( ?(\.|-) ?[0-9]{1,3}( ?- ?[0-9])?A?)?))", re.IGNORECASE),
        re.compile(r"\b(((TC)|(Training ?Circular)) ?\)? ?[0-9]{1,2} ?- ?((HEAT)|([0-9]{1,3}( ?(\.|-) ?[0-9]{1,3}( ?- ?[0-9])?A?)?)))",
        re.IGNORECASE)
    )
    ref_dict["STP"] =(
        re.compile(r"[0-9]{1,2} ?- ?[A-Z0-9]{1,6}( ?- ?[A-Z]{2,4}( ?- ?[A-Z]{2})?)?", re.IGNORECASE),
        re.compile(r"\b(((STP)|(Soldier ?Training ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[A-Z0-9]{1,6}( ?- ?[A-Z]{2,4}( ?- ?[A-Z]{2})?)?)",
        re.IGNORECASE)
    )
    ref_dict["TB"] =(
        re.compile(r"((ENG ?[0-9]{2,3})|([0-9]{3} ?- ?[0-9]{1,2})|(MED ?[0-9]{1,3}( ?- ?[0-9]{1,2})?)|([0-9]{1,2} ?- ?[0-9]{3,4}( ?- ?([0-9]{3} ?- ?[0-9]{2})|([A-Z]{3}))?))", re.IGNORECASE),
        re.compile(r"\b(((TB)|(Technical ?Bulletins?)) ?\)? ?((ENG ?[0-9]{2,3})|([0-9]{3} ?- ?[0-9]{1,2})|(MED ?[0-9]{1,3}( ?- ?[0-9]{1,2})?)|([0-9]{1,2} ?- ?[0-9]{3,4}( ?- ?([0-9]{3} ?- ?[0-9]{2})|([A-Z]{3}))?)))",
        re.IGNORECASE)
    )
    ref_dict["DA"] =(
        re.compile(r"[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{2})?", re.IGNORECASE),
        re.compile(r"\b(((DA ?MEMO)|(DA ?MEMORANDUMS?)) ?\)? ?[0-9]{1,3} ?- ?[0-9]{1,3}( ?- ?[0-9]{2})?)",
        re.IGNORECASE)
    )
    ref_dict["FM"] =(
        re.compile(r"[0-9]{1,3} ?- ?([0-9]{1,3}( ?(\.|-) ?[0-9]{1,2}( ?- ?[A-Z]{2})?)?)", re.IGNORECASE),
        re.compile(r"\b(((FM)|(Field ?Manual)) ?\)? ?[0-9]{1,3} ?- ?([0-9]{1,3}( ?(\.|-) ?[0-9]{1,2}( ?- ?[A-Z]{2})?)?))",
        re.IGNORECASE)
    )
    ref_dict["GTA"] =(
        re.compile(r"[0-9]{2} ?- ?[0-9]{2}( ?- ?[0-9]{3})?[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((GTA)|(Graphic ?Training ?Aid)) ?\)? ?[0-9]{2} ?- ?[0-9]{2}( ?- ?[0-9]{3})?[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["HQDA"] =(
        re.compile(r"[0-9]{1,3} ?- ?[0-9]{1}", re.IGNORECASE),
        re.compile(r"\b((HQDA ?POLICY ?NOTICE) ?[0-9]{1,3} ?- ?[0-9]{1})",
        re.IGNORECASE)
    )
    ref_dict["CTA"] =(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((CTA)|(Common ?Table ?of ?Allowances?)) ?\)? ?[[0-9]{1,2} ?- ?[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["ATTP"] =(
        re.compile(r"[0-9]{1} ?- ?[0-9]{2} ?\. ?[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((ATTP)|(ARMY ?TACTICS,? ?TECHNIQUES ?AND ?PROCEDURES?)) ?\)? ?[0-9]{1} ?- ?[0-9]{2} ?\. ?[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["TM"]=(
        re.compile(r"[0-9]{1,2} ?- ?[A-Z0-9]{1,4}(\.[0-9]{2})?( ?- ?[A-Z0-9&]{1,4})*", re.IGNORECASE),
        re.compile(r"\b(((TM)|(Technical ?Manuals?)) ?\)? ?[0-9]{1,2} ?- ?[A-Z0-9]{1,4}(\.[0-9]{2})?( ?- ?[A-Z0-9&]{1,4})*)", re.IGNORECASE)
    )
    ref_dict["AFI"]=(
        re.compile(r"[0-9]{1,2} ?- ?[A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((AFI)|(Air ?Force ?Instructions?)) ?\)? ?[0-9]{1,2} ?- ?[A-Z0-9-_]+)", re.IGNORECASE)
    )
    ref_dict["CFETP"]=(
        re.compile(r"[A-Z0-9]*[0-9][A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((CFETP)|(CAREER ?FIELD ?EDUCATION ?(AND|&) ?TRAINING ?PLAN)) ?\)? ?[A-Z0-9]*[0-9][A-Z0-9-_]+)",
        re.IGNORECASE)
    )
    ref_dict["AFMAN"]=(
        re.compile(r"[0-9]{2} ?- ?[A-Z0-9-_]+", re.IGNORECASE),
        re.compile(r"\b(((AFMAN)|(AIR ?FORCE ?MANUAL)) ?\)? ?[0-9]{2} ?- ?[A-Z0-9-_]+)",
        re.IGNORECASE)
    )
    ref_dict["QTP"]=(
        re.compile(r"[0-9][0-9A-Z]{1,6}( ?- ?[0-9A-Z]{1,6}){0,2}", re.IGNORECASE),
        re.compile(r"\b(((QTP)|(QUALIFICATION ?TRAINING ?PACKAGE)) ?\)? ?[0-9][0-9A-Z]{1,6}( ?- ?[0-9A-Z]{1,6}){0,2})",
        re.IGNORECASE)
    )
    ref_dict["AFPD"]=(
        re.compile(r"((1)|([0-9]{2} ?- ?[0-9]{1,2}( ?- ?[A-Z]{1})?))", re.IGNORECASE),
        re.compile(r"\b(((AFPD)|(AIR ?FORCE ?POLICY ?DIRECTIVE)) ?\)? ?((1)|([0-9]{2} ?- ?[0-9]{1,2}( ?- ?[A-Z]{1})?)))",
        re.IGNORECASE)
    )
    ref_dict["AFTTP"]=(
        re.compile(r"[0-9] ?- ?[0-9]{1,2}(\.[0-9]{1,2})?((V[0-9])|(_[A-Z]{2}))?", re.IGNORECASE),
        re.compile(r"\b(((AFTTP)|(Air ?Force ?Tactics?,? ?Techniques?,? ?(and|&)? ?Procedures?)) ?\)? ?[0-9] ?- ?[0-9]{1,2}(\.[0-9]{1,2})?((V[0-9])|(_[A-Z]{2}))?)",
        re.IGNORECASE)
    )
    ref_dict["AFVA"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{1,4}", re.IGNORECASE),
        re.compile(r"\b(((AFVA)|(Air ?Force ?Visual ?Aids?)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{1,4})",
        re.IGNORECASE)
    )
    ref_dict["AFH"]=(
        re.compile(r"((1)|(([0-9]{1,2} ?- ?[0-9]{3,4})(( ?\( ?I ?\))|( ?V ?[0-9]{1,2})|( ?, ?Vol(ume)? ?[0-9]{1,2}))?))", re.IGNORECASE),
        re.compile(r"\b(((AFH)|(Air ?Force ?Handbook)) ?\)? ?((1)|(([0-9]{1,2} ?- ?[0-9]{3,4})(( ?\( ?I ?\))|( ?V ?[0-9]{1,2})|( ?, ?Vol(ume)? ?[0-9]{1,2}))?)))",
        re.IGNORECASE)
    )
    ref_dict["HAFMD"]=(
        re.compile(r"[0-9] ?- ?[0-9]{1,2}( ?ADDENDUM ?[A-Z])?", re.IGNORECASE),
        re.compile(r"\b(((HAFMD)|(HEADQUARTERS ?AIR ?FORCE ?MISSION ?DIRECTIVE)) ?\)? ?[0-9] ?- ?[0-9]{1,2}( ?ADDENDUM ?[A-Z])?)",
        re.IGNORECASE)
    )
    ref_dict["AFPAM"]=(
        re.compile(r"(\( ?I ?\) ?)?[0-9]{2} ?- ?[0-9]{3,4}( ?V ?[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((AFPAM)|(Air ?Force ?Pamphlet)) ?\)? ?(\( ?I ?\) ?)?[0-9]{2} ?- ?[0-9]{3,4}( ?V ?[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AFMD"]=(
        re.compile(r"[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((AFMD)|(Air ?Force ?MISSION ?DIRECTIVE)) ?\)? ?[0-9]{1,2})", re.IGNORECASE)
    )
    ref_dict["AFM"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((AFM)|(Air ?Force ?Manual)) ?\)? ?[0-9]{2} ?- ?[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["HOI"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((HOI)|(HEADQUARTERS ?OPERATING ?INSTRUCTION)) ?\)? ?[0-9]{2} ?- ?[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["AFJQS"]=(
        re.compile(r"[0-9][0-9A-Z]{4}( ?- ?[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((AFJQS)|(Air ?Force ?Job ?Qualification ?Standard)) ?\)? ?[0-9][0-9A-Z]{4}( ?- ?[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AFJI"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{3,4}", re.IGNORECASE),
        re.compile(r"\b(((AFJI)|(Air ?Force ?Joint ?Instruction)) ?\)? ?[0-9]{2} ?- ?[0-9]{3,4})",
        re.IGNORECASE)
    )
    ref_dict["AFGM"]=(
        re.compile(r"[0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2}([0-9] ?- ?[0-9]{2})?", re.IGNORECASE),
        re.compile(r"\b(((AFGM)|(Air ?Force ?Guidance ?Memorandum)) ?\)? ?[0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2}([0-9] ?- ?[0-9]{2})?)",
        re.IGNORECASE)
    )
    ref_dict["DAFI"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{3,4}( ?V ?[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((DAFI)|(Department ?of ?the ?Air ?Force ?Instruction)) ?\)? ?[0-9]{2} ?- ?[0-9]{3,4}( ?V ?[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["AF"]=(
        re.compile(r"[0-9]{1,4}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((AF)|(Air ?Force)) ?\)? ?(Form ?)?[0-9]{1,4}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SF"]=(
        re.compile(r"[0-9]{2,4}( ?- ?[0-9])?[A-Z]?", re.IGNORECASE),
        re.compile(r"\b((SF) ?\)? ?[0-9]{2,4}( ?- ?[0-9])?[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["AFPM"]=(
        re.compile(r"[0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2}", re.IGNORECASE),
        re.compile(r"\b(((AFPM)|(Air ?Force ?Policy ?Memorandum)) ?\)? ?[0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2})",
        re.IGNORECASE)
    )
    ref_dict["AFJMAN"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b(((AFJMAN)|(Air ?Force ?Joint\sManual)) ?\)? ?[0-9]{2} ?- ?[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["JTA"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{1,3}", re.IGNORECASE),
        re.compile(r"\b(((JTA)|(Joint ?Table ?of\sAllowances?)) ?\)? ?[0-9]{2} ?- ?[0-9]{1,3})",
        re.IGNORECASE)
    )
    ref_dict["DAFPD"]=(
        re.compile(r"[0-9]{2} ?- ?[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b(((DAFPD)|(Department ?of ?\the ?Air ?Force ?Policy ?Directive)) ?\)? ?[0-9]{2} ?- ?[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["MCO"]=(
        re.compile(r"P?[0-9]{4,5}[A-Z]?\.[0-9]{1,3}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((MCO)|(Marine ?Corps ?Orders?)) ?\)? ?P?[0-9]{4,5}[A-Z]?\.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["MCBUL"]=(
        re.compile(r"[0-9]{4,5}", re.IGNORECASE),
        re.compile(r"\b(((MCBUL)|(MARINE ?CORPS ?BULLETIN)) ?\)? ?[0-9]{4,5})",
        re.IGNORECASE)
    )
    ref_dict["NAVMC"]=(
        re.compile(r"[0-9]{4}((\.[0-9]{1,3}[A-Z]?)|( ?- ?[A-Z]))?", re.IGNORECASE),
        re.compile(r"\b((NAVMC) ?\)? ?[0-9]{4}((\.[0-9]{1,3}[A-Z]?)|( ?- ?[A-Z]))?)",
        re.IGNORECASE)
    )
    ref_dict["NAVMC DIR"]=(
        re.compile(r"[0-9]{4}.[0-9]{1,3}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((NAVMC ?DIR)|(NAVMC ?Directive)) ?\)? ?[0-9]{4}.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["MCRP"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{1,2}[A-Z]?(\.[0-9]{1-2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((MCRP)|(MARINE ?CORPS ?Reference ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{1,2}[A-Z]?(\.[0-9]{1-2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["MCTP"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{2}[A-Z]", re.IGNORECASE),
        re.compile(r"\b(((MCTP)|(MARINE ?CORPS ?Tactical ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{2}[A-Z])",
        re.IGNORECASE)
    )
    ref_dict["MCWP"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{2}(\.[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((MCWP)|(MARINE ?CORPS ?Warfighting ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{2}(\.[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["MCDP"]=(
        re.compile(r"[0-9]( ?- ?[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((MCDP)|(MARINE ?CORPS ?Doctrinal ?Publication)) ?\)? ?[0-9]( ?- ?[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["MCIP"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{2}([A-Z]{1,2})?(\.?[0-9]{1,2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((MCIP)|(MARINE ?CORPS ?Interim ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{2}([A-Z]{1,2})?(\.?[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["FMFRP"]=(
        re.compile(r"[0-9]{1,2} ?- ?[0-9]{1,3}( ?- ?I+)?", re.IGNORECASE),
        re.compile(r"\b(((FMFRP)|(Fleet ?Marine ?Force ?Reference ?Publication)) ?\)? ?[0-9]{1,2} ?- ?[0-9]{1,3}( ?- ?I+)?)",
        re.IGNORECASE)
    )
    ref_dict["FMFM"]=(
        re.compile(r"[0-9] ?- ?[0-9]{1,2}( ?- ?[0-9])?", re.IGNORECASE),
        re.compile(r"\b(((FMFM)|(Fleet ?Marine ?Force ?Manuals?)) ?\)? ?[0-9] ?- ?[0-9]{1,2}( ?- ?[0-9])?)",
        re.IGNORECASE)
    )
    ref_dict["IRM"]=(
        re.compile(r"(- ?)?[0-9]{4} ?- ?[0-9]{2}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((IRM)|(Information ?Resource ?Management)) ?\)? ?(- ?)?[0-9]{4} ?- ?[0-9]{2}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SECNAVINST"]=(
        re.compile(r"[0-9]{4}\.[0-9]{1,2}[A-Z]?", re.IGNORECASE),
        re.compile(r"\b(((SECNAVINST)|(SECNAV ?INSTRUCTION)) ?\)? ?[0-9]{4}\.[0-9]{1,2}[A-Z]?)",
        re.IGNORECASE)
    )
    ref_dict["SECNAV"]=(
        re.compile(r"M ?- ?[0-9]{4}\.[0-9]{1,2}", re.IGNORECASE),
        re.compile(r"\b((SECNAV) ?\)? ?M ?- ?[0-9]{4}\.[0-9]{1,2})",
        re.IGNORECASE)
    )
    ref_dict["NAVSUP"]=(
        re.compile(r"((P ?- ?)|(Publication ?))[0-9]{3}", re.IGNORECASE),
        re.compile(r"\b((NAVSUP) ?\)? ?((P ?- ?)|(Publication ?))[0-9]{3})",
        re.IGNORECASE)
    )
    ref_dict["JAGINST"]=(
        re.compile(r"[0-9]{4,5}(\.[0-9]{1,2}[A-Z]?)?", re.IGNORECASE),
        re.compile(r"\b(((JAGINST)|(JAG ?Instruction)) ?\)? ?[0-9]{4,5}(\.[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE)
    )
    ref_dict["OMBM"]=(
        re.compile(r"M-[0-9]{2}-[0-9]{2}", re.IGNORECASE),
        re.compile(r"((M-[0-9]{2}-[0-9]{2}))",
        re.IGNORECASE)
    )
    return ref_dict
