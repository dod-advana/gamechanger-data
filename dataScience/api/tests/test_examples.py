class TestSet:
    qa_test_data = {"text": "How manysides does a pentagon have?"}
    qa_expect {"answers":["five"],"question":"How many sides does a pentagon have?"}[
    text_extract_test_data = {
        "text": "In a major policy revision intended to encourage more schools to welcome children back to in-person instruction, federal health officials on Friday relaxed the six-foot distancing rule for elementary school students, saying they need only remain three feet apart in classrooms as long as everyone is wearing a mask. The three-foot rule also now applies to students in middle schools and high schools, as long as community transmission is not high, officials said. When transmission is high, however, these students must be at least six feet apart, unless they are taught in cohorts, or small groups that are kept separate from others. The six-foot rule still applies in the community at large, officials emphasized, and for teachers and other adults who work in schools, who must maintain that distance from other adults and from students. Most schools are already operating at least partially in person, and evidence suggests they are doing so relatively safely. Research shows in-school spread can be mitigated with simple safety measures such as masking, distancing, hand-washing and open windows. EDUCATION BRIEFING: The pandemic is upending education. Get the latest news and tips."
    }
    summary_expect = {"extractType": "summary", "extracted": "In a major policy revision intended to encourage more schools to welcome children back to in-person instruction, federal health officials on Friday relaxed the six-foot distancing rule for elementary school students, saying they need only remain three feet apart in classrooms as long as everyone is wearing a mask."}
    topics_expect = {"extractType": "topics", "extracted": [[0.44866187988155737, "distancing"], [0.30738175379466876, "schools"], [
        0.3028274099264987, "upending"], [0.26273395468924415, "students"], [0.23815691706519543, "adults"]]}
    keywords_expect = {"extractType": "keywords",
                       "extracted": ["six-foot rule", "three-foot rule"]}
    sentence_test_data = {"text": "naval command"}
    sentence_search_expect = [
        {"score": 0.7741742730140686, "id": "OPNAVINST 1752.1C.pdf_1321",
            "text": "comusnaveur comusnavaf commander u s naval forces europe u s naval forces africa"},
        {"score": 0.31991302967071533, "id": "AAP 15.pdf_5768",
         "text": "rncs regional naval control of shipping nasg contrôle naval régional de la navigation commerciale nasg"},
        {"score": 0.2938539683818817, "id": "AAP 15.pdf_3147",
            "text": "l lsm lutte sous la mer mc undersea warfare usw mc"},
        {"score": 0.06577590107917786, "id": "OPNAVINST 3501.33F.pdf_698",
            "text": "i l battle messing only l f f f nco provide ships service facilities"},
        {"score": 0.01949344389140606, "id": "AAP 06.pdf_4340", "text": "bâtiment de défense aérienne air defence ship bâtiment assurant la responsabilité de la défense aérienne"}]
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
    transformer_list_expect = [
        "distilbart-mnli-12-3",
        "distilbert-base-uncased-distilled-squad",
        "distilroberta-base",
        "msmarco-distilbert-base-v2",
    ]
    
