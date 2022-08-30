from typing import Union, List
from collections import Counter, defaultdict
from common.document_parser.ref_utils import make_dict, preprocess_text
from common.document_parser.lib.ref_list import look_for_general
import json
from common import PACKAGE_DOCUMENT_PARSER_PATH
import os

ref_regex = make_dict()


def check_ref_regex():
    doc_types_path = os.path.join(
        PACKAGE_DOCUMENT_PARSER_PATH, 'doc_types_list.json'
    )

    with open(doc_types_path) as f:
        doc_types = json.load(f)

    print("Listing regex keys that are not found in doc_types list")
    for key in ref_regex:
        if not key in doc_types:
            print(f"{key}")

    print()

    print("Listing doc_types from ES that are not handled in regex dict")
    for d in doc_types:
        if d not in ref_regex.keys():
            print(d)


if __name__ == "__main__":
    check_ref_regex()


def bookend(_):
    """Add complex surrounding text to emulate real docs environment
    For use if you know a doc name exists but don't have it used as a real reference
    Trying to make the regex robust
    """
    return f"fake text 1-2.3a-b.c {_} 7-8.9x.y-z blah blah"


def check_bookends(needs_bookend: List[str], ref_type: str, exp_result=None):
    # If exp_result is None, uses needs_bookend as exp_result

    if exp_result is None:
        exp_result = needs_bookend
    else:
        if len(needs_bookend) != len(exp_result):
            assert (
                False
            ), f"ERR: for ref type `{ref_type}`: exp_result len is {len(exp_result)} and needs_bookend len is {len(needs_bookend)}"

    for i in range(len(needs_bookend)):
        text = bookend(needs_bookend[i])
        check(text, ref_type, exp_result[i])


def check(check_str, ref_type, exp_result: Union[int, str, List[str]]):
    """Verify reference regex.

    Args:
        check_str (str): The string to extract references from.
        ref_type (str): Reference type. A key from ref_regex.
        exp_result (int or str or list of str): Use int to verify the expected
            number of results. Use str or list of str to verify the value(s) of
            the results.
    Returns:
        bool: True if the check passed, False otherwise.
    """
    check_str = preprocess_text(check_str)
    ref_dict = look_for_general(
        check_str, defaultdict(int), ref_regex[ref_type], ref_type
    )
    num_results = sum(ref_dict.values())

    if type(exp_result) == int:
        assert exp_result == num_results
    elif type(exp_result) == str:
        assert (
            num_results == 1
        ), f"num results isn't 1  : found {num_results}. expected result: {exp_result}"
        res = ref_dict.get(exp_result)
        assert res is not None, f"no ref_dict value for: {exp_result}"
    elif type(exp_result) == list and all(type(i) == str for i in exp_result):
        assert Counter(exp_result) == ref_dict
    else:
        assert (
            False
        ), f"ERR: Type of `exp_result` param <{type(exp_result)}> is not supported. Failing."


def test_dod():
    check_str = "reference DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoD"
    ref_type = "DoD"
    check(check_str, ref_type, 2)


def test_dodd():
    check_str = "reference DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoD Directive 5134.12 DoDD"
    ref_type = "DoDD"
    check(check_str, ref_type, 2)


def test_dodi():
    check_str = "reference DoD Instruction 3110.06 DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoDI"
    ref_type = "DoDI"
    check(check_str, ref_type, 3)


def test_dodm():
    check_str = "reference DoD 4160.28-M DoD Manual 4140.01 DoDD 5134.12 DoDI 4140.01 DoDM 4100.39 DoDM"
    ref_type = "DoDM"
    check(check_str, ref_type, 2)


def test_dtm():
    check_str = "reference DTM-07-024 DoD Manual 4140.01 DTM 04-021 DoDI 4140.01 DoDM 4100.39 DTM"
    ref_type = "DTM"
    check(check_str, ref_type, 2)


def test_ai():
    check_str = (
        "reference Administrative Instruction 102 AI DoDD 5134.12 AI 86"
    )
    ref_type = "AI"
    check(check_str, ref_type, 2)


def test_icd():
    check_str = "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICD"
    ref_type = "ICD"
    check(check_str, ref_type, 2)


def test_icpg():
    check_str = "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICPG"
    ref_type = "ICPG"
    check(check_str, ref_type, 2)


def test_icpm():
    check_str = "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICPM"
    ref_type = "ICPM"
    check(check_str, ref_type, 1)


def test_cjcsi():
    string = "Chairman of the Joint Chiefs of Staff Instruction 1330.05A CHAIRMAN OF THE JOINT CHIEFS OF STAFF INSTRUCTION J-6 CJCSI 8010.01C (CJCSI) 3150.25"
    exp_result = [
        "CJCSI 1330.05A",
        "CJCSI J-6",
        "CJCSI 8010.01C",
        "CJCSI 3150.25",
    ]
    check(string, "CJCSI", exp_result)


def test_cjcsm():
    check_str = "reference CJCSM 3105.01 CJCSI 1001.01 CJCSI 1100.01D CJCSM 3150.05D CJCSM"
    ref_type = "CJCSM"
    check(check_str, ref_type, 2)


def test_cjcsg():
    check_str = "reference CJCSM 3105.01 CJCS GDE 3401D CJCSI 1100.01D CJCS GDE 5260 CJCSM"
    ref_type = "CJCS GDE"
    check(check_str, ref_type, 2)


def test_cjcsn():
    check_str = (
        "reference CJCSN 3112 CJCSI 1001.01 CJCSN 3130.01 CJCSM 3150.05D CJCSN"
    )
    ref_type = "CJCSN"
    check(check_str, ref_type, 2)


def test_jp():
    string = "JP 1-02 J P 1-02 Joint Publication 5-0 JP 1 JP 3-07.1 J.P. 3"
    exp_result = ["JP 1-02", "JP 1-02", "JP 5-0", "JP 1", "JP 3-07.1", "JP 3"]
    check(string, "JP", exp_result)


def test_dcid():
    check_str = "reference DCID 6/1 DoD DCID 1893 DoDD 5134.12 DoDI 4140.01 DCID 7/6 DCID"
    ref_type = "DCID"
    check(check_str, ref_type, 2)


def test_eo():
    check_str = "reference Executive Order 12996 DoD Executive Order 4140.01 Executive   Order 13340 "
    ref_type = "EO"
    check(check_str, ref_type, 2)


def test_ar():
    check_str = "AR 1-1 AR 1-15 AR 1-202 AR 10-89 AR 11-2 Army Regulations 11-18 AR 25-400-2 AR 380-67 AR 380-381 AR 381-47 AR 381-141 Army Regulation 525-21 Army Regulations (AR) 600-8-3 AR 600-8-10 AR 600-8-101 AR 600-9 AR 601-210 AR 5"
    exp_output = [
        "AR 1-1",
        "AR 1-15",
        "AR 1-202",
        "AR 10-89",
        "AR 11-2",
        "AR 11-18",
        "AR 25-400-2",
        "AR 380-67",
        "AR 380-381",
        "AR 381-47",
        "AR 381-141",
        "AR 525-21",
        "AR 600-8-3",
        "AR 600-8-10",
        "AR 600-8-101",
        "AR 600-9",
        "AR 601-210",
        "AR 5",
    ]
    check(check_str, "AR", exp_output)


def test_ago():
    check_str = "AGO 1958-27 AGO 2020 - 31 ARMY general orders (AGO) 2001- 18 ARMY general order 2000- 07 "
    ref_type = "AGO"
    check(check_str, ref_type, 4)


def test_adp():
    check_str = "ADP 1 ADP 3 -0 Army Doctrine Publication 7-0 ADP 1-01"
    ref_type = "ADP"
    check(check_str, ref_type, 4)


def test_pam():
    check_str = "PAM 600-8-101 DA Pamphlet 5-11 PAM 40-507 "
    ref_type = "PAM"
    check(check_str, ref_type, 3)


def test_atp():
    check_str = (
        "ATP 1-0.1 ATP 1-20 ATP 2-22.9-2 Army Techniques Publication 1-05.03 "
    )
    ref_type = "ATP"
    check(check_str, ref_type, 4)


def test_army_dir():
    check_str = "army DIR 2020-08 army directive 2019 - 27 army dir"
    ref_type = "ARMY"
    check(check_str, ref_type, 2)


def test_tc():
    check_str = "TC 2-91.5A (TC) 3-4 Training circular 3-34.500 TC"
    ref_type = "TC"
    check(check_str, ref_type, 3)


def test_stp():
    check_str = "STP 6-13B24-SM -TG STP 3-CIED - SM-TG STP 6-13II-MQS STP 10-92L14-SM-TG STP 1AB-1948 "
    ref_type = "STP"
    check(check_str, ref_type, 4)


def test_tb():
    check_str = "TB 8-6500-MPL TB 8-6515-001-35 TB 38-750-2 TB MED 1 TB MED 284 TB MED 750-1 TB 420-1 TB 420-33 TB ENG 146 TB ENG 62"
    ref_type = "TB"
    check(check_str, ref_type, 10)


def test_da_memo():
    check_str = "DA MEMO 600-8-22 DA MEMO 5-5, DA Memorandum 25-53 da memo"
    ref_type = "DA"
    check(check_str, ref_type, 3)


def test_fm():
    check_str = "FM 3-01.13 FM 3-13 Field Manual 1-0 FM 3-55.93 FM 3-90-1 FM 101-51-3-CD FM 7-100.1"
    ref_type = "FM"
    check(check_str, ref_type, 7)


def test_gta():
    check_str = "GTA 03-04-001A GTA 90-01-028 Graphic Training aid 43-01-103 "
    ref_type = "GTA"
    check(check_str, ref_type, 3)


def test_hqda_policy():
    check_str = "HQDA POLICY NOTICE 1-1 HQDA POLICY NOTICE 600-4 "
    ref_type = "HQDA"
    check(check_str, ref_type, 2)


def test_cta():
    check_str = "CTA 8-100 CTA 50-909 Common Table of Allowances 50-970 "
    ref_type = "CTA"
    check(check_str, ref_type, 3)


def test_attp():
    check_str = "reference ATTP 3-06.11	 ATTP 4140.01 "
    ref_type = "ATTP"
    check(check_str, ref_type, 1)


def test_tm():
    check_str = "TM 43-0001-26-2 TM 5-3895-332-23P TM 5-3820-255-12&P TM 3-11.42 TM 3-34.48-2 TM 1-5895-308-SUM TM 1-1680-377-13&P-4"
    ref_type = "TM"
    check(check_str, ref_type, 7)


def test_afi():
    check_str = "AFI 1-1 AFI 11-2E-3V3 AFI10-2611-O AFI 13-101 AFI 17-2CDAV3"
    ref_type = "AFI"
    check(check_str, ref_type, 5)


def test_cfetp():
    check_str = "CFETP 15WXC1 CFETP 1N2X1X-CC2 CFETP 3E4X1WG"
    ref_type = "CFETP"
    check(check_str, ref_type, 3)


def test_afman():
    check_str = "AFMAN 11-2AEV3ADDENDA-A Air Force Manual 11-2C-32BV2 AFMAN10-1004 AFMAN11-2KC-10V3_ADDENDA-A"
    ref_type = "AFMAN"
    check(check_str, ref_type, 4)


def test_qtp():
    check_str = "QTP 24-3-HAZMAT QTP 43AX-1 (QTP) 24-3-D549"
    ref_type = "QTP"
    check(check_str, ref_type, 3)


def test_afpd():
    check_str = "AFPD 1 AFPD 4 AFPD 10-10 AFPD 91-1"
    ref_type = "AFPD"
    check(check_str, ref_type, 3)


def test_afttp():
    check_str = "Air Force Tactics, Techniques, and Procedures (AFTTP) 3-42.32 AFTTP3-4.6_AS AFTTP 3-32.33V1"
    ref_type = "AFTTP"
    check(check_str, ref_type, 3)


def test_afva():
    check_str = "AFVA 10-241 AFVA 51-1"
    ref_type = "AFVA"
    check(check_str, ref_type, 2)


def test_afh():
    check_str = "AFH 10-222V1 AFH 1 AFH32-7084"
    ref_type = "AFH"
    check(check_str, ref_type, 3)


def test_hafmd():
    check_str = "HAFMD 1-2 HAFMD 1-24 Addendum B"
    ref_type = "HAFMD"
    check(check_str, ref_type, 2)


def test_afpam():
    check_str = "AFPAM 36-2801V1 AFPAM ( I ) 24-237"
    ref_type = "AFPAM"
    check(check_str, ref_type, 2)


def test_afmd():
    check_str = "AFMD 1 AFMD 28"
    ref_type = "AFMD"
    check(check_str, ref_type, 2)


def test_afm():
    check_str = "AFM 19-10"
    ref_type = "AFM"
    check(check_str, ref_type, 1)


def test_HOI():
    check_str = "HOI 10-1 HOI 36-28"
    ref_type = "HOI"
    check(check_str, ref_type, 2)


def test_afjqs():
    check_str = "AFJQS 5J0X1-2 AFJQS 2XXXX"
    ref_type = "AFJQS"
    check(check_str, ref_type, 2)


def test_afji():
    check_str = "AFJI 10-411 Air Force Joint Instruction (AFJI) 32-9006"
    ref_type = "AFJI"
    check(check_str, ref_type, 2)


def test_afgm():
    check_str = "AFGM 2020-36-04 AFGM 2020-63-148-01"
    ref_type = "AFGM"
    check(check_str, ref_type, 2)


def test_dafi():
    check_str = "DAFI 33-360 DAFI 90-2002 DAFI 48-107V1"
    ref_type = "DAFI"
    check(check_str, ref_type, 3)


def test_af():
    check_str = "AF 100 AF form 1005"
    ref_type = "AF"
    check(check_str, ref_type, 2)


def test_sf():
    check_str = "SF 87 SF 708"
    ref_type = "SF"
    check(check_str, ref_type, 2)


def test_afpm():
    check_str = "AFPM 2019-36-02"
    ref_type = "AFPM"
    check(check_str, ref_type, 1)


def test_afjman():
    check_str = "AFJMAN 23-209"
    ref_type = "AFJMAN"
    check(check_str, ref_type, 1)


def test_jta():
    check_str = "JTA 08-02 JTA 74-1"
    ref_type = "JTA"
    check(check_str, ref_type, 2)


def test_dafpd():
    check_str = "DAFPD 10-36 DAFPD 90-1"
    ref_type = "DAFPD"
    check(check_str, ref_type, 2)


def test_mco():
    check_str = "MCO 4200.34 MCO P12000.11A MCO 7220R.39"
    ref_type = "MCO"
    check(check_str, ref_type, 3)


def test_mcbul():
    check_str = "MCBUL 1300 MCBUL 10120"
    ref_type = "MCBUL"
    check(check_str, ref_type, 2)


def test_navmc():
    check_str = "NAVMC 4500.36B NAVMC 2915"
    ref_type = "NAVMC"
    check(check_str, ref_type, 2)


def test_navmcdir():
    check_str = "NAVMC DIR 1650.48 NAVMC Directive 5100.8"
    ref_type = "NAVMC DIR"
    check(check_str, ref_type, 2)


def test_mcrp():
    check_str = "MCRP 1-10.1 MCRP 3-40B.5 MCRP 4-11.3M"
    ref_type = "MCRP"
    check(check_str, ref_type, 3)


def test_mcwp():
    check_str = "MCWP 3-15.7 MCWP 11-10 MCWP 3-41.1A MCWP 0-1"
    exp_result = ["MCWP 3-15.7", "MCWP 11-10", "MCWP 3-41.1A", "MCWP 0-1"]
    check(check_str, "MCWP", exp_result)


def test_mctp():
    check_str = "MCTP 12-10A MCTP 3-20G"
    ref_type = "MCTP"
    check(check_str, ref_type, 2)


def test_mcip():
    check_str = "MCIP 3-03DI MCIP 3-03.1i MCIP 3-40G.21"
    ref_type = "MCIP"
    check(check_str, ref_type, 3)


def test_mcdp():
    check_str = "MCDP 1-1 MCDP 7"
    ref_type = "MCDP"
    check(check_str, ref_type, 2)


def test_fmfrp():
    check_str = "FMFRP 12-109-II FMFRP 0-53"
    ref_type = "FMFRP"
    check(check_str, ref_type, 2)


def test_fmfm():
    check_str = "FMFM 6-1"
    ref_type = "FMFM"
    check(check_str, ref_type, 1)


def test_irm():
    check_str = "IRM-2300-05B IRM 5236-06A IRM-5231-03"
    ref_type = "IRM"
    check(check_str, ref_type, 3)


def test_secnavinst():
    check_str = "SECNAV Instruction 1640.9C SECNAVINST 5210.60"
    ref_type = "SECNAVINST"
    check(check_str, ref_type, 2)

    text = "436 SECNAVINST 5430.27C, supra note 15, ¶ 8.f., at 6."
    exp = "SECNAVINST 5430.27C"
    check(text, ref_type, exp)


def test_secnav():
    check_str = "SECNAV M-1650.1 SECNAV M-5210.2"
    ref_type = "SECNAV"
    check(check_str, ref_type, 2)


def test_navsup():
    check_str = (
        "NAVSUP P-486 NAVSUP Publication 727 NAVSUP PUB 572 NAVSUP P 486"
    )
    exp_result = [
        "NAVSUP 486",
        "NAVSUP 727",
        "NAVSUP 572",
        "NAVSUP 486",
    ]
    check(check_str, "NAVSUP", exp_result)


def test_jaginst():
    check_str = "JAGINST 5800.7F JAG INSTRUCTION 1440.1E"
    ref_type = "JAGINST"
    check(check_str, ref_type, 2)


def test_comdtinst():
    string = "COMDTINST M1100.2 COMDTINST M10550.25 COMDTINST M7220.29 COMDTINST M1000.3A COMDTINST 1560.3 COMDTINST 7220.39 COMDTINST 12430.6B"
    exp_result = [
        "COMDTINST M1100.2",
        "COMDTINST M10550.25",
        "COMDTINST M7220.29",
        "COMDTINST M1000.3A",
        "COMDTINST 1560.3",
        "COMDTINST 7220.39",
        "COMDTINST 12430.6B",
    ]
    check(string, "COMDTINST", exp_result)


def test_dcms():
    string = "(DCMS), Contingency Support Plan, 9930-17 U. S. Coast Guard Deputy Commandant for Mission Support (DCMS) Contingency Support Plan 9930-17"
    exp_result = ["DCMS 9930-17", "DCMS 9930-17"]
    check(string, "DCMS", exp_result)


def test_pscnote():
    string = "PSCNOTE 1401.5"
    exp_result = ["PSCNOTE 1401.5"]
    check(string, "PSCNOTE", exp_result)


def test_dodfmr():
    string = "Department of Defense Financial Management Regulation (DoD FMR), Volume 7A"
    exp_result = ["DoDFMR Volume 7A"]
    check(string, "DoDFMR", exp_result)


def test_pscinst():
    string = "PSCINST M1000.2 PSCINST 1401.2 PSCINST M1910.1"
    exp_result = [
        "PSCINST M1000.2",
        "PSCINST 1401.2",
        "PSCINST M1910.1",
    ]
    check(string, "PSCINST", exp_result)


def test_cgttp():
    string = "CGTTP 1-16.5 CGTTP 4-11.14 CGTTP 4-11-15"
    exp_result = ["CGTTP 1-16.5", "CGTTP 4-11.14", "CGTTP 4-11-15"]
    check(string, "CGTTP", exp_result)


def test_nttp():
    string = "NTTP 4-01.4 NTTP 3-04.11 NTTP 3-13.3M NTTP 3-54M"
    exp_result = ["NTTP 4-01.4", "NTTP 3-04.11", "NTTP 3-13.3M", "NTTP 3-54M"]
    check(string, "NTTP", exp_result)


def test_dhs_directive():
    string = "DHS Directive No. 066-05 DHS Directive 254-02"
    exp_result = ["DHS Directive 066-05", "DHS Directive 254-02"]
    check(string, "DHS Directive", exp_result)


def test_hspd():
    string = "HSPD-5 Homeland Security Presidential Directive-9 Homeland Security Presidential Directive 12"
    exp_result = ["HSPD 5", "HSPD 9", "HSPD 12"]
    check(string, "HSPD", exp_result)


def test_opnavinst():
    string = "OPNAVINST 1100.4B OPNAVINST 3500.38B"
    exp_result = ["OPNAVINST 1100.4B", "OPNAVINST 3500.38B"]
    check(string, "OPNAVINST", exp_result)


def test_cgto():
    string = "CGTO 1-1B-50 CGTO PG85-00-1490-A CGTO PG 85-00-70-A CGTO PG-85-00-110 CGTO 1H-60T-1 CGTO PG-85-00-310 CGTO PG-85-00-290-A CGTO 33-1"
    exp_result = [
        "CGTO 1-1B-50",
        "CGTO PG85-00-1490-A",
        "CGTO PG 85-00-70-A",
        "CGTO PG-85-00-110",
        "CGTO 1H-60T-1",
        "CGTO PG-85-00-310",
        "CGTO PG-85-00-290-A",
        "CGTO 33-1",
    ]
    check(string, "CGTO", exp_result)


def test_cfr_title():
    string = "title 50, Code of Federal Regulations 5 CFR Title 46 CFR"
    exp_result = ["CFR Title 50", "CFR Title 5", "CFR Title 46"]
    check(string, "CFR Title", exp_result)


def test_pl():
    string = (
        "Public Law 98-615 Pub. L. No. 107-296 Pub. L. No 11-845 P.L. 109-13"
    )
    exp_result = ["PL 98-615", "PL 107-296", "PL 11-845", "PL 109-13"]

    check(string, "PL", exp_result)


def test_dha_procedural_inst():
    # note the crawlers have it pluralized, so the key should be plural so it can be found
    kind = "DHA Procedural Instructions"
    string = "(c)      DHA Procedural Instruction 5025.01, “Publication System,” August 21, 2015 "
    exp_result = "DHA Procedural Instructions 5025.01"

    check(string, kind, exp_result)


def test_dha_procedures_manual():
    kind = "DHA Procedures Manuals"
    needs_bookend = [
        "DHA Procedures Manuals 1025.01",
        "DHA Procedures Manuals 6025.13, Volume 5",
        "DHA Procedures Manuals 6025.13,  Volumes 1-7",
    ]
    check_bookends(
        needs_bookend, kind, [" ".join(x.split()) for x in needs_bookend]
    )


def test_dha_tech_manual():
    kind = "DHA Technical Manuals"
    needs_bookend = [
        "DHA Technical Manuals 4165.01, Volume 7",
        "DHA Technical Manuals 4165.01 Volume, 7",  # 🥴
        "DHA Technical Manuals 3200.02",
    ]
    check_bookends(needs_bookend, kind)


def test_dha_admin_inst():
    kind = "DHA Administrative Instructions"
    needs_bookend = [
        "DHA Administrative Instructions 3020.01, Change 1",
        "DHA Administrative Instructions 4000.01",
        "DHA Administrative Instructions 034",
    ]
    check_bookends(needs_bookend, kind)


def test_bupers_inst():
    kind = "BUPERSINST"

    text = "BUPERSINST  1750.10 Compliance  with  this  Publication  is  Mandatory"
    expected = "BUPERSINST 1750.10"
    check(text, kind, expected)

    needs_bookend = [
        "BUPERSINST BUPERSNOTE 5215",
        "BUPERSINST 1750.10D Vol 2",
        "BUPERSINST 5230.11A CH1",
        "BUPERSINST 12600.4CH1",
    ]

    check_bookends(needs_bookend, kind)


def test_usc_title():
    string = "Title 1, U. S. Code - Title 2 U.S.C. - Title 3, United States Code - 4 United States Code - 5 U.S.C. - U.S.C. Title 6 - United States Code Title 7"
    exp_result = [
        "Title 1",
        "Title 2",
        "Title 3",
        "Title 4",
        "Title 5",
        "Title 6",
        "Title 7",
    ]
    check(string, "Title", exp_result)


def test_navair():
    exp_result = [
        "NAVAIR 01-1B-50",
        "NAVAIR 00-80T-106",
        "NAVAIR 01-75GAJ-1",
        "NAVAIR 01-1a-505-1",
        "NAVAIR 16-1-529",
        "NAVAIR 01-75GAA-9",
    ]
    check_bookends(exp_result, "NAVAIR")


def test_comdtpub():
    exp_result = [
        "COMDTPUB P5090.1",
        "COMDTPUB P16700.4",
        "COMDTPUB P3120.17",
        "COMDTPUB 5800.7A",
        "COMDTPUB 16502.5",
    ]
    check_bookends(exp_result, "COMDTPUB")


def test_nfpa():
    needs_bookend = ["NFPA 70", "NFPA 493"]
    check_bookends(needs_bookend, "NFPA")

    string = "National Fire Protection Association (NFPA) 496"
    check(string, "NFPA", "NFPA 496")


def test_ombc():
    string = "OMB Circular A-4 OMB Circular A-130 OMB Circular No. A-123"
    exp_result = ["OMBC A-4", "OMBC A-130", "OMBC A-123"]
    check(string, "OMBC", exp_result)


def test_milstd():
    needs_bookend = [
        "(DOD) Military Standard (MIL-STD) 2525D",
        "DoD Military Standard 882D",
        "DOD Military Standard 1472F",
        "MIL-STD-235(D)",
    ]
    exp_result = [
        "MIL-STD 2525D",
        "MIL-STD 882D",
        "MIL-STD 1472F",
        "MIL-STD 235D",
    ]
    check_bookends(needs_bookend, "MIL-STD", exp_result)


def test_navedtra():
    exp_result = [
        "NAVEDTRA 10076A",
        "NAVEDTRA 14043",
        "NAVEDTRA 43100-1M",
        "NAVEDTRA 14167F",
        "NAVEDTRA 130-140",
        "NAVEDTRA 14295B2",
    ]
    check_bookends(exp_result, "NAVEDTRA")


def test_navmed():
    exp_result = [
        "NAVMED P-5010-4",
        "NAVMED P-117",
        "NAVMED 1300/1",
        "NAVMED 6150/50",
    ]
    check_bookends(exp_result, "NAVMED")


def test_nehc_technical_manual():
    needs_bookend = [
        "NEHC Technical Manual 601",
        "NEHC Technical Manual OM 500",
        "NEHC-TM IH 6290.91-2B",
        "NEHC TM OM 6260",
        "(NEHC) TM 6290.91-2",
        "NEHC TM96-2",
    ]
    exp_result = [
        "NEHC Technical Manual 601",
        "NEHC Technical Manual OM 500",
        "NEHC Technical Manual IH 6290.91-2B",
        "NEHC Technical Manual OM 6260",
        "NEHC Technical Manual 6290.91-2",
        "NEHC Technical Manual 96-2",
    ]
    check_bookends(needs_bookend, "NEHC Technical Manual", exp_result)


def test_navsea():
    needs_bookend = [
        "NAVSEA SS400-ABMMO-010",
        "NAVSEA SS400-AB-MMO-010 REV 1",
        "NAVSEA SS400-AD-MMO-010",
        "NAVSEA 389-0288",
        "NAVSEA SS521-AG-PRO-010",
    ]
    check_bookends(needs_bookend, "NAVSEA")


def test_maradmin():
    kind = "MARADMIN"
    text = "(n) MARADMIN 488/11 FY12 Commandant's Career-Level Education Board"
    exp = "MARADMIN 488/11"
    check(text, kind, exp)

    text = "435 Message 142126Z MAY 10, MARADMIN 276/10, Subj: Implementation of Command Inspections of SJA Offices, Law Centers and Legal Service Support Section (stating that SJA offices, Law Centers, and LSSSs had not previously been subject to inspection within the CGIP). "
    exp = "MARADMIN 276/10"
    check(text, kind, exp)

    needs_bookend = ["MARADMIN 391/07", "MARADMIN 213-16"]
    check_bookends(needs_bookend, "MARADMIN")


def test_hr():
    kind = "H.R."
    text = "32 H.R. 12910, 90th Cong. (1st Sess. 1967) at 113 Cong. Rec. 27483, 27485 (daily ed. Oct. 2, 1967) (statements of Rep. Philbin and Rep. Bennett)."
    exp = "H.R. 12910"
    check(text, kind, exp)

    needs_bookend = ["H.R. 1234", "HR 567", "H. R. 78"]
    exp_result = ["H.R. 1234", "H.R. 567", "H.R. 78"]
    check_bookends(needs_bookend, "H.R.", exp_result)


def test_navadmin():
    needs_bookend = ["NAVADMIN 367/10", "NAVADMIN 17117"]
    check_bookends(needs_bookend, "NAVADMIN")


def test_milpersman():
    needs_bookend = ["MILPERSMAN 1220-410", "MILPERSMAN 1306-3000"]
    check_bookends(needs_bookend, "MILPERSMAN")


def test_ombm():
    needs_bookend = ["OMBM M-09-15", "OMB M-06-19"]
    exp_result = ["OMBM M-09-15", "OMBM M-06-19"]
    check_bookends(needs_bookend, "OMBM", exp_result)


def test_alnav():
    needs_bookend = ["ALNAV 044/20"]
    check_bookends(needs_bookend, "ALNAV")


def test_bumedinst():
    needs_bookend = [
        "BUMEDINST 3440.10B",
        "BUMEDINST 5510.10",
        "BUMEDINST 12550.1C",
        "BUMEDINST 12550.1",
    ]
    check_bookends(needs_bookend, "BUMEDINST")


def test_cfetp():
    needs_bookend = [
        "CFETP 2A6X4",
        "CFETP 2A6X4",
        "CFETP 3E9X1",
        "CFETP 2M0X2",
    ]
    check_bookends(needs_bookend, "CFETP")


def test_stanag():
    needs_bookend = ["STANAG 4170", "[STANAG 4554]"]
    exp_result = ["STANAG 4170", "STANAG 4554"]
    check_bookends(needs_bookend, "STANAG", exp_result)


def test_comnavresforcominst():
    needs_bookend = [
        "COMNAVRESFORCOMINST 1700.1F CH-1",
        "COMNAVRESFORCOMINST 3440.1E",
    ]
    check_bookends(needs_bookend, "COMNAVRESFORCOMINST")


def test_opnavnote():
    needs_bookend = ["OPNAVNOTE 5450", "OPNAV notice (OPNAVNOTE) 9201"]
    exp_result = ["OPNAVNOTE 5450", "OPNAVNOTE 9201"]
    check_bookends(needs_bookend, "OPNAVNOTE", exp_result)
