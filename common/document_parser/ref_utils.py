import re


def pattern(raw_string, flags=re.IGNORECASE | re.VERBOSE):
    return re.compile(raw_string, flags=flags)


def preprocess_text(text):
    """Preprocess text to extract references from.

    1. Replace unicode characters with "-"
    2. Remove parenthesis
    3. Normalize all whitespace to be single space.

    Args:
        text (str)

    Returns:
        str
    """
    # Interpret the unicode as a -
    text = text.replace("\u2013", "-")
    # Remove parenthesis
    text = re.sub(r"[()]", "", text)
    # Normalize whitespace to make regex simpler
    text = " ".join(text.split())

    return text


def make_dict():
    # Each pattern should have only 1 capturing group that is the numerical
    # part of the reference.
    ref_dict = {}
    ref_dict["DoD"] = re.compile(
        r"\b(?:dod ?placeholder|dod) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(?:-[A-Z]+)?E?)",
        re.IGNORECASE,
    )
    ref_dict["DoDD"] = re.compile(
        r"\b(?:dod ?directives?|dodd) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(?:-[A-Z]+)?E?)",
        re.IGNORECASE,
    )
    ref_dict["DoDI"] = re.compile(
        r"\b(?:dod ?instruction|dodi) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3} ?(?:-[A-Z]+)?E?)",
        re.IGNORECASE,
    )
    ref_dict["DoDM"] = re.compile(
        r"\b(?:dod ?manual|dodm) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}(?: ?,* ?Volume ?[0-9]+| ?- ?V[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["DTM"] = re.compile(
        r"\b(?:DTM|DT ?Memorandum) ?-? ?([0-9]{2} ?- ?[0-9]{3})",
        re.IGNORECASE,
    )
    ref_dict["AI"] = re.compile(
        r"\b(?:administrative ?instruction|ai) ?([0-9]+)", re.IGNORECASE
    )

    # United States Code
    ref_dict["USC"] = re.compile(
        r"""
            (?:
                ([0-9]{1,3})
                ,?
                \s
                (?:
                    U\.?\s?S\.\s??C\.?\s?   # USC with optional period and/ or space between letters
                    |United\sStates\sCode
                    |U\.?\s?S\.?\s?Code
                )
            )
            |(?:
                (?:
                    U\.?\s?S\.?\s?C\.?
                    |United\sStates\sCode
                    |U\.?\s?S\.?\s?Code     # USC with optional period and/ or space between letters
                )
                (?:,?\s?Title)?             # optional group: optional comma, optional space, Title
                \s
                ([0-9]{1,3})
            )
        """,
        re.VERBOSE|re.IGNORECASE
    )

    ref_dict["ICD"] = re.compile(
        r"\b(?:Intelligence ?Community ?Directive|ICD) ?([0-9]{1,3})",
        re.IGNORECASE,
    )
    ref_dict["ICPG"] = re.compile(
        r"\bicpg ?((?:[A-Z]+-)?[0-9]{3}\. ?[0-9]{1,3} ?(?:-[A-Z]+)?E?)",
        re.IGNORECASE,
    )
    ref_dict["ICPM"] = re.compile(
        r"\bicpm ?([0-9]{4}- ?[0-9]{3}- ?[0-9]{1})", re.IGNORECASE
    )
    ref_dict["CJCSI"] = re.compile(
        r"\b(?:cjcs ?instruction|cjcsi) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["CJCSM"] = re.compile(
        r"\b(?:cjcs ?manual|cjcsm) ?((?:[A-Z]+-)?[0-9]{4}\. ?[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["CJCSG"] = re.compile(
        r"\b(?:cjcs ?gde|cjcsg) ?((?:[A-Z]+-)?[0-9]{4} ?[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["CJCSN"] = re.compile(
        r"\b(?:cjcs ?notice|cjcsn) ?((?:[A-Z]+-)?[0-9]{4}(?:\. ?[0-9]{0,3}[A-Z]?)?)",
        re.IGNORECASE,
    )

    # Joint Publication
    ref_dict["JP"] = re.compile(
        r"""
            (?:Joint\s?Publication|\bJ[ \.]?P[ \.]?)  
            \s?
            (
                [0-9]{1,3}
                (?:[-\.][0-9]{1,3}){0,3}        # 0-3 iterations of: hyphen or period, 1-3 digits
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    ref_dict["DCID"] = re.compile(
        r"\b(?:Director ?of ?Central ?Intelligence ?Directives|DCID) ?([0-9]\/[0-9]{1,2}P?)",
        re.IGNORECASE,
    )
    ref_dict["EO"] = re.compile(
        r"\b(?:Executive ?Order|EO|E\. ?O\. ?) ?([0-9]{5})", re.IGNORECASE
    )
    
    ref_dict["AR"] = re.compile(
        r"""
            (?:\bAR|Army\s?Regulations?)
            \s?
            (
                [0-9]{1,3}
                (?:\s?-\s?[0-9]{1,3}){0,2}      # 0-2 iterations of: optional space, hyphen, optional space, 1-3 digits
            )
        """,
        re.VERBOSE|re.IGNORECASE
    )
    
    ref_dict["AGO"] = re.compile(
        r"\b(?:AGO|Army ?General ?Orders?) ?((?:19|20)[0-9]{2} ?- ?[0-9]{2,3})",
        re.IGNORECASE,
    )
    ref_dict["ADP"] = re.compile(
        r"\b(?:ADP|Army ?Doctrine ?Publications?) ?(1|[0-9]{1,2} ?- ?[0-9]{1,2})",
        re.IGNORECASE,
    )
    ref_dict["PAM"] = re.compile(
        r"\b(?:PAM|DA ?Pam(?:phlets?)?) ?([0-9]{1,3} ?- ?[0-9]{1,3}(?: ?- ?[0-9]{1,3})?)",
        re.IGNORECASE,
    )
    ref_dict["ATP"] = re.compile(
        r"\b(?:ATP|Army ?Techniques ?Publications?) ?([0-9] ?- ?[0-9]{1,2}(?:\.[0-9]{1,2}(?: ?- ?[0-9]{1,2})?)?)",
        re.IGNORECASE,
    )
    ref_dict["ARMY"] = re.compile(
        r"\b(?:ARMY ?DIR|ARMY ?Directives?) ?(20[0-9]{2} ?- ?[0-9]{2}(?: ?- ?[0-9]{1,2})?)",
        re.IGNORECASE,
    )
    ref_dict["TC"] = re.compile(
        r"\b(?:TC|Training ?Circular) ?([0-9]{1,2} ?- ?(?:HEAT|[0-9]{1,3}(?: ?(?:\.|- ?[0-9]{1,3}(?: ?- ?[0-9])?A?)?)))",
        re.IGNORECASE,
    )
    ref_dict["STP"] = re.compile(
        r"\b(?:STP|Soldier ?Training ?Publication) ?([0-9]{1,2} ?- ?[A-Z0-9]{1,6}(?: ?- ?[A-Z]{2,4}(?: ?- ?[A-Z]{2})?)?)",
        re.IGNORECASE,
    )
    ref_dict["TB"] = re.compile(
        r"\b(?:TB|Technical ?Bulletins?) ?(ENG ?[0-9]{2,3}|[0-9]{3} ?- ?[0-9]{1,2}|MED ?[0-9]{1,3}(?:- ?[0-9]{1,2})?|[0-9]{1,2} ?- ?[0-9]{3,4} ?(?:- ?(?:[0-9]{3} ?- ?[0-9]{2})|(?:[A-Z]{3})?))",
        re.IGNORECASE,
    )
    ref_dict["DA"] = re.compile(
        r"\b(?:DA ?MEMO|DA ?MEMORANDUMS?) ?([0-9]{1,3} ?- ?[0-9]{1,3}(?: ?- ?[0-9]{2})?)",
        re.IGNORECASE,
    )

    # Army Field Manual
    ref_dict["FM"] = re.compile(
        r"""
            (?:\bFM|Field\s?Manual)
            \s?
            (
                (?:[0-9]{1,3}[-\.]){1,3}        # 1-3 iterations of: 1-3 digits, hyphen or period
                [0-9A-Z]{0,3}                   # 0-3 digits or letters
            )

        """,
        re.VERBOSE | re.IGNORECASE,
    )

    ref_dict["GTA"] = re.compile(
        r"\b(?:GTA|Graphic ?Training ?Aid) ?([0-9]{2} ?- ?[0-9]{2}(?: ?- ?[0-9]{3})?[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["HQDA"] = re.compile(
        r"\bHQDA ?POLICY ?NOTICE ?([0-9]{1,3} ?- ?[0-9]{1})", re.IGNORECASE
    )
    ref_dict["CTA"] = re.compile(
        r"\b(?:CTA|Common ?Table ?of ?Allowances?) ?([[0-9]{1,2} ?- ?[0-9]{3})",
        re.IGNORECASE,
    )
    ref_dict["ATTP"] = re.compile(
        r"\b(?:ATTP|ARMY ?TACTICS,? ?TECHNIQUES ?AND ?PROCEDURES?) ?([0-9]{1} ?- ?[0-9]{2} ?\. ?[0-9]{2})",
        re.IGNORECASE,
    )
    ref_dict["TM"] = re.compile(
        r"\b(?:TM|Technical ?Manuals?) ?([0-9]{1,2} ?- ?[A-Z0-9]{1,4}(?:\.[0-9]{2})?(?: ?- ?[A-Z0-9&]{1,4})*)",
        re.IGNORECASE,
    )
    ref_dict["AFI"] = re.compile(
        r"\b(?:AFI|Air ?Force ?Instructions?) ?([0-9]{1,2} ?- ?[A-Z0-9-_]+)",
        re.IGNORECASE,
    )
    ref_dict["CFETP"] = re.compile(
        r"\b(?:CFETP|CAREER ?FIELD ?EDUCATION ?(?:AND|&) ?TRAINING ?PLAN) ?([A-Z0-9]*[0-9][A-Z0-9-_]+)",
        re.IGNORECASE,
    )
    ref_dict["AFMAN"] = re.compile(
        r"\b(?:AFMAN|AIR ?FORCE ?MANUAL) ?([0-9]{2} ?- ?[A-Z0-9-_]+)",
        re.IGNORECASE,
    )
    ref_dict["QTP"] = re.compile(
        r"\b(?:QTP|QUALIFICATION ?TRAINING ?PACKAGE) ?([0-9][0-9A-Z]{1,6}(?: ?- ?[0-9A-Z]{1,6}){0,2})",
        re.IGNORECASE,
    )
    ref_dict["AFPD"] = re.compile(
        r"\b(?:AFPD|AIR ?FORCE ?POLICY ?DIRECTIVE) ?(1|[0-9]{2} ?- ?[0-9]{1,2}(?: ?- ?[A-Z])?)",
        re.IGNORECASE,
    )
    ref_dict["AFTTP"] = re.compile(
        r"\b(?:AFTTP|Air ?Force ?Tactics?,? ?Techniques?,? ?(?:and|&)? ?Procedures?) ?([0-9] ?- ?[0-9]{1,2}(?:\.[0-9]{1,2})?(?:V[0-9]|_[A-Z]{2})?)",
        re.IGNORECASE,
    )
    ref_dict["AFVA"] = re.compile(
        r"\b(?:AFVA|Air ?Force ?Visual ?Aids?) ?([0-9]{1,2} ?- ?[0-9]{1,4})",
        re.IGNORECASE,
    )
    ref_dict["AFH"] = re.compile(
        r"\b(?:AFH|Air ?Force ?Handbook) ?(1|[0-9]{1,2} ?- ?[0-9]{3,4}(?: ?I ?| ?V ?[0-9]{1,2}|(?: ?, ? ?Vol(?:ume)? ?[0-9]{1,2}))?)",
        re.IGNORECASE,
    )
    ref_dict["HAFMD"] = re.compile(
        r"\b(?:HAFMD|HEADQUARTERS ?AIR ?FORCE ?MISSION ?DIRECTIVE) ?([0-9] ?- ?[0-9]{1,2}(?: ?ADDENDUM ?[A-Z])?)",
        re.IGNORECASE,
    )
    ref_dict["AFPAM"] = re.compile(
        r"\b(?:AFPAM|Air ?Force ?Pamphlet) ?((?: ?I ?)?[0-9]{2} ?- ?[0-9]{3,4}(?: ?V ?[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["AFMD"] = re.compile(
        r"\b(?:AFMD|Air ?Force ?MISSION ?DIRECTIVE) ?([0-9]{1,2})",
        re.IGNORECASE,
    )
    ref_dict["AFM"] = re.compile(
        r"\b(?:AFM|Air ?Force ?Manual) ?([0-9]{2} ?- ?[0-9]{2})",
        re.IGNORECASE,
    )
    ref_dict["HOI"] = re.compile(
        r"\b(?:HOI|HEADQUARTERS ?OPERATING ?INSTRUCTION) ?([0-9]{2} ?- ?[0-9]{1,2})",
        re.IGNORECASE,
    )
    ref_dict["AFJQS"] = re.compile(
        r"\b(?:AFJQS|Air ?Force ?Job ?Qualification ?Standard) ?([0-9][0-9A-Z]{4}(?: ?- ?[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["AFJI"] = re.compile(
        r"\b(?:AFJI|Air ?Force ?Joint ?Instruction) ?([0-9]{2} ?- ?[0-9]{3,4})",
        re.IGNORECASE,
    )
    ref_dict["AFGM"] = re.compile(
        r"\b(?:AFGM|Air ?Force ?Guidance ?Memorandum) ?([0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2}(?:[0-9] ?- ?[0-9]{2})?)",
        re.IGNORECASE,
    )
    ref_dict["DAFI"] = re.compile(
        r"\b(?:DAFI|Department ?of ?the ?Air ?Force ?Instruction) ?([0-9]{2} ?- ?[0-9]{3,4}(?: ?V ?[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["AF"] = re.compile(
        r"\b(?:AF|Air ?Force) ?(?:Form ?)?([0-9]{1,4}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["SF"] = re.compile(
        r"\bSF ?([0-9]{2,4}(?: ?- ?[0-9])?[A-Z]?)", re.IGNORECASE
    )
    ref_dict["AFPM"] = re.compile(
        r"\b(?:AFPM|Air ?Force ?Policy ?Memorandum) ?([0-9]{4} ?- ?[0-9]{2} ?- ?[0-9]{2})",
        re.IGNORECASE,
    )
    ref_dict["AFJMAN"] = re.compile(
        r"\b(?:AFJMAN|Air ?Force ?Joint Manual) ?([0-9]{2} ?- ?[0-9]{3})",
        re.IGNORECASE,
    )
    ref_dict["JTA"] = re.compile(
        r"\b(?:JTA|Joint ?Table ?of Allowances?) ?([0-9]{2} ?- ?[0-9]{1,3})",
        re.IGNORECASE,
    )
    ref_dict["DAFPD"] = re.compile(
        r"\b(?:DAFPD|Department ?of ?\the ?Air ?Force ?Policy ?Directive) ?([0-9]{2} ?- ?[0-9]{1,2})",
        re.IGNORECASE,
    )
    ref_dict["MCO"] = re.compile(
        r"\b(?:MCO|Marine ?Corps ?Orders?) ?(P?[0-9]{4,5}[A-Z]?\.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["MCBUL"] = re.compile(
        r"\b(?:MCBUL|MARINE ?CORPS ?BULLETIN) ?([0-9]{4,5})",
        re.IGNORECASE,
    )
    ref_dict["NAVMC"] = re.compile(
        r"\bNAVMC ?([0-9]{4}(?:\.[0-9]{1,3}[A-Z]?| ?- ?[A-Z])?)",
        re.IGNORECASE,
    )
    ref_dict["NAVMC DIR"] = re.compile(
        r"\b(?:NAVMC ?DIR|NAVMC ?Directive) ?([0-9]{4}.[0-9]{1,3}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["MCRP"] = re.compile(
        r"\b(?:MCRP|MARINE ?CORPS ?Reference ?Publication) ?([0-9]{1,2} ?- ?[0-9]{1,2}[A-Z]?(?:\.[0-9]{1-2}[A-Z]?)?)",
        re.IGNORECASE,
    )
    ref_dict["MCTP"] = re.compile(
        r"\b(?:MCTP|MARINE ?CORPS ?Tactical ?Publication) ?([0-9]{1,2} ?- ?[0-9]{2}[A-Z])",
        re.IGNORECASE,
    )

    # Marine Corps Warfighting Publication
    ref_dict["MCWP"] = re.compile(
        r"""
            (?:MCWP|Marine\s?Corps\s?Warfighting\s?Publication)
            \s?
            (
                (?:[0-9]{1,3}[-\.]){1,3}        # 1-3 iterations of: 1-3 digits, hyphen or period
                [0-9A-Z]{0,3}                   # 0-3 digits or letters
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )
    ref_dict["MCDP"] = re.compile(
        r"\b(?:MCDP|MARINE ?CORPS ?Doctrinal ?Publication) ?([0-9](?: ?- ?[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["MCIP"] = re.compile(
        r"\b(?:MCIP|MARINE ?CORPS ?Interim ?Publication) ?([0-9]{1,2} ?- ?[0-9]{2}(?:[A-Z]{1,2})?(?:\.?[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE,
    )
    ref_dict["FMFRP"] = re.compile(
        r"\b(?:FMFRP|Fleet ?Marine ?Force ?Reference ?Publication) ?([0-9]{1,2} ?- ?[0-9]{1,3}(?: ?- ?I+)?)",
        re.IGNORECASE,
    )
    ref_dict["FMFM"] = re.compile(
        r"\b(?:FMFM|Fleet ?Marine ?Force ?Manuals?) ?([0-9] ?- ?[0-9]{1,2}(?: ?- ?[0-9])?)",
        re.IGNORECASE,
    )
    ref_dict["IRM"] = re.compile(
        r"\b(?:IRM|Information ?Resource ?Management) ?((?:- ?)?[0-9]{4} ?- ?[0-9]{2}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["SECNAVINST"] = re.compile(
        r"\b(?:SECNAVINST|SECNAV ?INSTRUCTION) ?([0-9]{4}\.[0-9]{1,2}[A-Z]?)",
        re.IGNORECASE,
    )
    ref_dict["SECNAV"] = re.compile(
        r"\bSECNAV ?(M ?- ?[0-9]{4}\.[0-9]{1,2})", re.IGNORECASE
    )

    # Naval Supply Systems Command
    ref_dict["NAVSUP"] = re.compile(
        r"""
            NAVSUP
            \s
            P(?:ub(?:lication)?)?       # P or Pub or Publication
            \s?
            -?
            ([0-9]{1,4})
        """,
        re.VERBOSE | re.IGNORECASE
    )

    ref_dict["JAGINST"] = re.compile(
        r"\b(?:JAGINST|JAG ?Instruction) ?([0-9]{4,5}(?:\.[0-9]{1,2}[A-Z]?)?)",
        re.IGNORECASE,
    )
    ref_dict["OMBM"] = re.compile(r"(M-[0-9]{2}-[0-9]{2})", re.IGNORECASE)

    # Commandant Instruction (Coast Guard)
    ref_dict["COMDTINST"] = re.compile(
        r"""
            COMDTINST
            \s?
            (
                [A-Z]?
                [0-9]{3,6}
                (?:\.[0-9]{1,4}[A-Z]?)?     # optional group: period, 1-4 digits, letter (optional)
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Deputy Commandant for Mission Support (Coast Guard)
    ref_dict["DCMS"] = re.compile(
        r"""
            (?:
                Deputy\sCommandant\sfor\sMission\sSupport
                |DCMS                     
            )
            ,?
            \s?
            (?:Contingency\sSupport\sPlan,?\s?)?    # optional group
            (
                [0-9]{2,6}
                -
                [0-9]{1,4}
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Personnel Service Center Notice (Coast Guard)
    ref_dict["PSCNOTE"] = re.compile(
        r"""
            PSCNOTE
            \s?
            (
                [0-9]{1,6}
                (?:\.[0-9]{1,4})?                   # optional group: period, 1-4 digits
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Department of Defense Financial Management Regulation
    ref_dict["DoDFMR"] = re.compile(
        r"""
            (?:
                Department\sof\sDefense\sFinancial\sManagement\sRegulation
                |DoD\s?FMR                    
            )
            ,?
            \s?
            (
                Volume
                \s?
                [0-9]{1,3}
                [A-Z]?
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # TODO: find out what PSCINST stands for (Coast Guard)
    ref_dict["PSCINST"] = re.compile(
        r"""
            PSCINST
            \s?
            (
                [A-Z]?
                [0-9]{2,6}
                (?:\.?[0-9]{1,3})?                  # optional group: period, 1-3 digits
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Coast Guard Tactics, Techniques, and Procedures
    ref_dict["CGTTP"] = re.compile(
        r"""
            CGTTP
            \s?
            (
                (?:[0-9]{1,2}-[0-9]{1,2}){1,3}      # 1-3 iterations of: 1-2 digits, hyphen, 1-2 digits
                (?:-[0-9]{1,2})?                    # optional group: hyphen, 1-2 digits
                [A-Z]?
                (?:\.[0-9]{1,2}[A-Z]?)?             # optional group: period, 1-2 digits, letter (optional)
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Navy Tactics, Techniques, and Procedures
    ref_dict["NTTP"] = re.compile(
        r"""
            NTTP
            \s?
            (
                (?:[0-9]{1,2}-[0-9]{1,2}){1,3}      # 1-3 iterations of: 1-2 digits, hyphen, 1-2 digits
                (?:-[0-9]{1,2})?                    # optional group: hyphen, 1-2 digits
                [A-Z]?
                (?:\.[0-9]{1,2}[A-Z]?)?             # optional group: period, 1-2 digits, letter (optional)
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Department of Homeland Security Directive
    ref_dict["DHS Directive"] = re.compile(
        r"""
            DHS\sDirective
            (?:\sNo\.?)?
            \s?
            (
                [0-9]{1,3}
                -
                [0-9]{1,3}
            )
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Homeland Security Presidential Directive
    ref_dict["HSPD"] = re.compile(
        r"""
            (?:HSPD|Homeland\sSecurity\sPresidential\sDirective)
            [ -]?
            ([0-9]{1,3})
        """,
        re.VERBOSE | re.IGNORECASE,
    )

    # Office of the Chief of Naval Operations Instruction
    ref_dict["OPNAVINST"] = re.compile(
        r"""
        (?:OPNAVINST|OPNAV\sInstruction)
        \s?
        (
            [0-9]{1,6}
            \.
            [0-9]{1,3}
            [A-Z]?
        )
        """,
        re.VERBOSE | re.IGNORECASE
    )

    # Coast Guard Technical Order
    ref_dict["CGTO"] = re.compile(
        r"""
            CGTO
            \s
            (
                (?:PG)?                              # optional PG
                [- ]?                                # optional hyphen or space
                (?:[0-9]{1,4}[A-Z]{0,1}-){1,3}       # 1-3 iterations of: 1-4 digits, 0-1 letters, hyphen
                [0-9]{0,4}[A-Z]{0,1}                 # 0-4 digits, 0-1 letters
            )
        """,
        re.VERBOSE | re.IGNORECASE
    )

    # Code of Federal Regulations
    ref_dict["CFR"] = re.compile(
        r"""
            (?:title)?
            ([0-9]{1,3})
            (?:of\sthe)?
            [ ,]{1,2}
            (?:CFR|Code\sof\sFederal\sRegulations)
        """,
        re.VERBOSE | re.IGNORECASE
    )

    # Public Law
    ref_dict["PL"] = re.compile(
        r"""
            (?:                     
                P\.?                # P, optional period
                |Pub\.?             # or Pub, optional period
                |Public             # or Public
            )
            \s?
            (?:
                L\.?                # L, optional period
                |Law                # or Law
            )
            \s
            (?:No\.?)?               # optional group: No, optional period
            \s?
            (
                [0-9]{1,4}
                -
                [0-9]{1,4}
            )
        """,
        re.VERBOSE | re.IGNORECASE
    )

    # DHA Procedural Instruction
    ref_dict["DHA Procedural Instruction"] = pattern(
        r"""
            DHA\sProcedural\sInstruction
            \s
            (
                \d*\.\d*\b          # any number of digits with a dot between
            )
        """
    )

    # BUPERS
    ref_dict["BUPERSINST"] = pattern(
        r"""
            BUPERSINST
            \s{1,3}
            (
                \d*\.\d*\b
            )
        """
    )

    return ref_dict


