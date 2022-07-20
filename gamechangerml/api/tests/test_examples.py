class TestSet:
    qa_test_data = {"text": "How manysides does a pentagon have?"}
    qa_expect = {
        "answers": ["five"],
        "question": "How many sides does a pentagon have?",
    }
    text_extract_test_data = {
        "text": "In a major policy revision intended to encourage more schools to welcome children back to in-person instruction, federal health officials on Friday relaxed the six-foot distancing rule for elementary school students, saying they need only remain three feet apart in classrooms as long as everyone is wearing a mask. The three-foot rule also now applies to students in middle schools and high schools, as long as community transmission is not high, officials said. When transmission is high, however, these students must be at least six feet apart, unless they are taught in cohorts, or small groups that are kept separate from others. The six-foot rule still applies in the community at large, officials emphasized, and for teachers and other adults who work in schools, who must maintain that distance from other adults and from students. Most schools are already operating at least partially in person, and evidence suggests they are doing so relatively safely. Research shows in-school spread can be mitigated with simple safety measures such as masking, distancing, hand-washing and open windows. EDUCATION BRIEFING: The pandemic is upending education. Get the latest news and tips."
    }
    summary_expect = {
        "extractType": "summary",
        "extracted": "In a major policy revision intended to encourage more schools to welcome children back to in-person instruction, federal health officials on Friday relaxed the six-foot distancing rule for elementary school students, saying they need only remain three feet apart in classrooms as long as everyone is wearing a mask.",
    }
    topics_expect = {
        "extractType": "topics",
        "extracted": [
            [0.44866187988155737, "distancing"],
            [0.30738175379466876, "schools"],
            [0.3028274099264987, "upending"],
            [0.26273395468924415, "students"],
            [0.23815691706519543, "adults"],
        ],
    }
    keywords_expect = {
        "extractType": "keywords",
        "extracted": ["six-foot rule", "three-foot rule"],
    }
    sentence_test_data = {"text": "naval command"}
    sentence_search_expect = [
        {
            "id": "OPNAVNOTE 5430.1032.pdf_36",
            "text": "naval forces central command comusnavcent commander u s naval forces southern command comnavso and commander u s naval forces europe commander u s naval forces africa comusnaveur comusnavaf",
            "text_length": 0.2,
            "score": 0.9124890685081481,
        },
        {
            "id": "OPNAVINST 3440.18.pdf_124",
            "text": "c commander u s naval forces europe africa for ports in the u s european command and the u s africa command area of responsibility",
            "text_length": 0.11060606060606061,
            "score": 0.7812968355236631,
        },
        {
            "id": "OPNAVINST 3006.1 w CH-2.pdf_178",
            "text": "enclosure naval forces africa commander u s naval forces central command commander u s naval forces southern command shall",
            "text_length": 0.09848484848484848,
            "score": 0.775530730233048,
        },
        {
            "id": "MILPERSMAN 1001-021.pdf_10",
            "text": "major shore commands e g office of the chief of naval operations navy personnel command commander navy reserve forces command etc",
            "text_length": 0.10909090909090909,
            "score": 0.7683667984875766,
        },
        {
            "id": "OPNAVINST 3440.18.pdf_125",
            "text": "d commander u s naval forces central command for ports in the u s central command area of responsibility and",
            "text_length": 0.07727272727272727,
            "score": 0.7664882681586526,
        },
        {
            "id": "OPNAVINST 8120.1A.pdf_64",
            "text": "j commander naval sea systems command comnavseasyscom comnavseasyscom is the echelon supporting flag officer to",
            "text_length": 0.08181818181818182,
            "score": 0.764475125616247,
        },
        {
            "id": "DoDD 4500.56 CH 5.pdf_157",
            "text": "m commander u s naval forces europe and commander u s naval forces africa",
            "text_length": 0.024242424242424242,
            "score": 0.7282583944725268,
        },
        {
            "id": "OPNAVINST 3111.17B.pdf_224",
            "text": "commander u s naval forces europe u s naval forces africa",
            "text_length": 0.0,
            "score": 0.716657280921936,
        },
        {
            "id": "MARINE CORPS MANUAL CH 1-3.pdf_690",
            "text": "navy personnel under the military command of the commandant of the marine corps",
            "text_length": 0.03333333333333333,
            "score": 0.6932793577512105,
        },
        {
            "id": "SECNAVINST 4200.36B.pdf_28",
            "text": "naval regional commanders and the commandant of the marine corps shall",
            "text_length": 0.019696969696969695,
            "score": 0.6766319462747284,
        },
    ]

    word_sim_data = {"text": "naval command"}
    word_sim_except = {"naval": ["navy", "maritime"], "command": []}

    recommender_data = {"filenames": ["Title 10"]}
    recommender_results = {
        "filenames": ["Title 10"],
        "results": [
            "Title 50",
            "AACP 02.1",
            "DoDD 5143.01 CH 2",
            "DoDD S-5230.28",
            "DoDI 5000.89",
        ],
    }

    # extraction_data = {"text": "Carbon emissions trading is poised to go global, and billions of dollars — maybe even trillions — could be at stake. That's thanks to last month's U.N. climate summit in Glasgow Scotland, which approved a new international trading system where companies pay for cuts in greenhouse gas emissions somewhere else, rather than doing it themselves."}
    # extraction_keywords_expect = {
    #     "extractType": "keywords",
    #     "extracted": [
    #         "climate summit",
    #         "glasgow scotland"
    #     ]
    # }
    # extraction_topic_except = {
    #     "extractType": "topics",
    #     "extracted": [
    #         [
    #             0.402564416275499,
    #             "trillions"
    #         ],
    #         [
    #             0.35468207783971445,
    #             "trading"
    #         ],
    #         [
    #             0.34311022758576537,
    #             "carbon_emissions"
    #         ],
    #         [
    #             0.2798555740973044,
    #             "greenhouse_emissions"
    #         ],
    #         [
    #             0.2722433559706402,
    #             "glasgow"
    #         ]
    #     ]
    # }
    transformer_test_data = {
        "query": "chemical agents",
        "documents": [
            {
                "text": "a . The Do D chemical agent facility commander or director and contractor laboratories that are provided Do D chemical agents will develop a reliable security system and process that provide the capability to detect , assess , deter , communicate , delay , and respond to unauthorized attempts to access chemical agents .",
                "id": "DoDI 5210.65 CH 2.pdf_2",
            },
            {
                "text": "b . Entities approved to receive ultra dilute chemical agents from Do D will assume liability , accountability , custody , and ownership upon accepting transfer of the agents .The entity will provide Do D with an authenticated list of officials and facilities authorized to accept shipment of ultra dilute chemical agents",
                "id": "DoDI 5210.65 CH 2.pdf_37",
            },
        ],
    }
    transformer_search_expect = {
        "query": "chemical agents",
        "answers": [
            {
                "answer": "Do D chemical agent facility commander",
                "context": "a . The Do D chemical agent facility commander or director and contractor laboratories that are provided Do D chemical agents will develop a reliable security system and process that provide the c",
                "id": "DoDI 5210.65 CH 2.pdf_2",
                "text": "a . The Do D chemical agent facility commander or director and contractor laboratories that are provided Do D chemical agents will develop a reliable security system and process that provide the capability to detect , assess , deter , communicate , delay , and respond to unauthorized attempts to access chemical agents .",
            },
            {
                "answer": "shipment of ultra dilute chemical agents",
                "context": "rship upon accepting transfer of the agents .The entity will provide Do D with an authenticated list of officials and facilities authorized to accept shipment of ultra dilute chemical agents",
                "id": "DoDI 5210.65 CH 2.pdf_37",
                "text": "b . Entities approved to receive ultra dilute chemical agents from Do D will assume liability , accountability , custody , and ownership upon accepting transfer of the agents .The entity will provide Do D with an authenticated list of officials and facilities authorized to accept shipment of ultra dilute chemical agents",
            },
        ],
    }
    transformer_list_expect = {
        "bert-base-cased-squad2",
        "distilbart-mnli-12-3",
        "distilbert-base-uncased-distilled-squad",
        "distilroberta-base",
        "msmarco-distilbert-base-v2",
        "msmarco-distilbert-base-v2_20220105"
        # 'msmarco-distilbert-base-v2_2021-10-17',
        # 'msmarco-distilbert-base-v2_20211210',
    }

    sent_index_processing_pars = {
        "good": "6. U.S. Army Corps of Engineers (USACE). USACE is involved with waterways dredging, flood prevention, permitting obstructions within U.S. waters, and the construction, maintenance, and operation of waterway projects, such as locks, dams, and reservoirs, etc. USACE also enforces the Refuse Act (33 U.S.C. 407). The Coast Guard has been designated to assist in the enforcement of certain specific provisions of law and regulations administered by USACE. Comman...",
        "bad_acronyms": "EPA/625/11-91/002, 1992 (ar) 40 CFR 268 (as) 40 CFR 240 (at) 42 U.S.C. 7401 (au) 40 CFR 61 (av) 40 CFR 230 (aw) 33 CFR 320 (ax) 33 CFR 321 (ay) 33 CFR 322 (az) 33 CFR 323 (ba) 33 CFR 325 (bb) 33 CFR 330 (bc) 40 CFR 233 (bd) 16 U.S.C. §§1451-1464 (be) 42 U.S.C. 4321 (bf) 40 CFR 220 (bg) 40 CFR 221 (bh) 40 CFR 222 (bi) 40 CFR 227 (bj) 40 CFR 224 (bk) 40 CFR 228 (bl) 40 CFR 223 (bm) 40 CFR 225 (bn) 40 CFR 226 (bo) 40 CFR 229 (bp) 33 U.S.C. 1401 (bq) 40 CFR 255 (br) 33 CFR 324 (bs) 15 CFR 930",
        "bad_pages": "Page D4-1 – D4-6 Page D4-1 – D4-6 Page D4-9 – D4-10 Page D4-9 – D4-10 Page D4-13 – D4-16 Page D4-13 – D4-16 Page D4-19 – D4-20 Page D4-18a – D4-20 Page E3-1 – E3-25 Page E3-1 – E3-36",
        "bad_long_tokens": "OPLANOPORDPAPACEPCCPCIPDSPHAPMCSPMIPOIPSGPZRTDSBSPOSQDLDRSSASTANAGTACEVACTACSOPTAPTASKORGTB MEDTCTCCCTEWLSTFCTLTLPTMTOETTPUAoperation planoperation orderphysician assistantprimary, alternate, contingency, and emergencypre-combat checkpre-combat inspectionpatient decontamination siteperiodic health assessmentpreventive maintainence checks and servicepatient movement itempoint of injuryplatoon sergeantpickup zonereturn to dutysupply bulletinsupport ope",
        "bad_toc": "DoDM 4140.68 March 5 2020 TABLE OF CONTENTS 2 TABLE OF CONTENTS SECTION 1 GENERAL ISSUANCE INFORMATION .............................................................................. 4 1.1. Applicability. .................................................................................................................... 4 SECTION 2 RESPONSIBILITIES ......................................................................................................... 5 2.1. Assistant Secretary of Defense for Sustainment. .............................................................. 5 2.2. DLA. ................................................................................................................................. 5 2.3. DoD Component Heads. ................................................................................................... 5 2.4. Secretaries of the Military Departments. .......................................................................... 6 2.5. Commander United States Special Operations Command USSOCOM. ...................... 7 2.6. Administrators of Participating U.S. Government Civil Agencies. .................................. 7 SECTION 3 GENERAL PROCEDURES ................................................................................................ 8 3.1. NIMSCs. ........................................................................................................................... 8 3.2. PICA. .............................................................................................................................. 17 3.3. SICA. .............................................................................................................................. 18 3.4. Exceptions for SOP Items.............................................................................................. 19 3.5. NIMSC Designation........................................................................................................ 20 SECTION 4 SUPPLY AND DEPOT MAINTENANCE OPERATIONS PROCEDURES ................................ 24 4.1. Procedures for NIMSC 1 2 3 4 5 6 7 8 or 0 items. ................................................. 24 4.2. Provisioning. ................................................................................................................... 24 4.3. PICA Assignment. .......................................................................................................... 25 4.4. IMC Changes and PICA or SICA Reassignment Requests. ........................................... 26 4.5. Item Adoption. ................................................................................................................ 28 4.6. Procurement. ................................................................................................................... 28 4.7. Cataloging. ...................................................................................................................... 29 4.8. Depot Maintenance. ........................................................................................................ 31 4.9. Disposition. ..................................................................................................................... 31 4.10. Inactive Items. ............................................................................................................... 32 4.11. Standardization. ............................................................................................................ 33 SECTION 5 ITEM REVIEW PROCEDURES FOR MIGRATION TO NIMSC 5 OR NIMSC 6 .................. 34 5.1. Review Items for Migration to NIMSC 5 or NIMSC 6. ................................................. 34 5.2. Single Submitter of Procurement Specifications and Depotlevel Repair Specifications. ................................................................................................................... 35 SECTION 6 NIMSC MIGRATION PROCEDURES ............................................................................. 37 6.1. Migration to NIMSC 5 or NIMSC 6. .............................................................................. 37 6.2. NIMSC Migration or PICA Reassignment. .................................................................... 37 6.3. PreETD TimePeriod. .................................................................................................... 40 6.4. ETD TimePeriod............................................................................................................ 42 6.5. PostETD Timeperiod.................................................................................................... 42 SECTION 7 SUPPLY OPERATIONS PROCEDURES FOR NIMSC 5 AND NIMSC 6 ITEMS ................. 44 7.1. Item Stockage.................................................................................................................. 44 7.2. Requirements Computation and Methodology. .............................................................. 44 7.3. Item Distribution. ............................................................................................................ 44 a. Item Transfer Actions. ................................................................................................. 44 b. Requisition Processing. ................................................................................................ 45 ",
    }
    sent_index_processing_results = {
        "has_many_short_tokens": [False, True, True, False, False],
        "has_many_repeating": [False, True, True, False, True],
        "has_extralong_tokens": [False, False, False, True, True],
        "is_a_toc": [False, False, False, False, True],
        "check_quality": [True, False, False, False, False],
    }
