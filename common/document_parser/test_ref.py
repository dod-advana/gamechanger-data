import logging
from common.document_parser.ref_utils import make_dict


logger = logging.getLogger(__name__)


ref_regex = make_dict()

def check(check_str, ref_type, exp_result):
    count = 0
    matches = ref_regex[ref_type][1].findall(check_str)
    for match in matches:
        num_match = ref_regex[ref_type][0].search(match[0])
        if not num_match:
            continue
        ref = (str(ref_type) + " " + str(num_match[0])).strip()
        count += 1
    return count==exp_result

def test_dod():
    check_str= "reference DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoD"
    ref_type = "DoD"
    assert check(check_str, ref_type, 2)

def test_dodd():
    check_str= "reference DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoD Directive 5134.12 DoDD"
    ref_type = "DoDD"
    assert check(check_str, ref_type, 2)

def test_dodi():
    check_str= "reference DoD Instruction 3110.06 DoD 4160.28-M DoD 7000.14-R DoDD 5134.12 DoDI 4140.01 DoDI 3110.06 DoDI"
    ref_type = "DoDI"
    assert check(check_str, ref_type, 3)

def test_dodm():
    check_str= "reference DoD 4160.28-M DoD Manual 4140.01 DoDD 5134.12 DoDI 4140.01 DoDM 4100.39 DoDM"
    ref_type = "DoDM"
    assert check(check_str, ref_type, 2)

def test_dtm():
    check_str= "reference DTM-07-024 DoD Manual 4140.01 DTM 04-021 DoDI 4140.01 DoDM 4100.39 DTM"
    ref_type = "DTM"
    assert check(check_str, ref_type, 2)

def test_ai():
    check_str= "reference Administrative Instruction 102 AI DoDD 5134.12 AI 86"
    ref_type = "AI"
    assert check(check_str, ref_type, 2)

def test_title():
    check_str= "reference Title 10 Title bla bla 12 Title 41"
    ref_type = "Title"
    assert check(check_str, ref_type, 2)

def test_icd():
    check_str= "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICD"
    ref_type = "ICD"
    assert check(check_str, ref_type, 2)

def test_icpg():
    check_str= "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICPG"
    ref_type = "ICPG"
    assert check(check_str, ref_type, 2)

def test_icpm():
    check_str= "reference ICPG 704.4 ICPM 2006-700-8 ICD 501 ICPG 710.1 Intelligence Community Directive 204 ICPM"
    ref_type = "ICPM"
    assert check(check_str, ref_type, 1)

def test_cjcsi():
    check_str= "reference CJCSI 1001.01  CJCSI 1100.01D DoDI 4140.01 CJCSI 12312321 CJCSM 3150.05D DoDM"
    ref_type = "CJCSI"
    assert check(check_str, ref_type, 2)

def test_cjcsm():
    check_str= "reference CJCSM 3105.01 CJCSI 1001.01 CJCSI 1100.01D CJCSM 3150.05D CJCSM"
    ref_type = "CJCSM"
    assert check(check_str, ref_type, 2)

def test_cjcsg():
    check_str= "reference CJCSM 3105.01 CJCS GDE 3401D CJCSI 1100.01D CJCS GDE 5260 CJCSM"
    ref_type = "CJCSG"
    assert check(check_str, ref_type, 2)

def test_cjcsn():
    check_str= "reference CJCSN 3112 CJCSI 1001.01 CJCSN 3130.01 CJCSM 3150.05D CJCSN"
    ref_type = "CJCSN"
    assert check(check_str, ref_type, 2)

def test_jp():
    check_str= "reference DoD 4160.28-M JP 1-02 DoDD 5134.12 JP 4140.01 JP   3-12 DoDM 4100.39 JP"
    ref_type = "JP"
    assert check(check_str, ref_type, 2)

def test_dcid():
    check_str= "reference DCID 6/1 DoD DCID 1893 DoDD 5134.12 DoDI 4140.01 DCID 7/6 DCID"
    ref_type = "DCID"
    assert check(check_str, ref_type, 2)

def test_eo():
    check_str= "reference Executive Order 12996 DoD Executive Order 4140.01 Executive   Order 13340 "
    ref_type = "EO"
    assert check(check_str, ref_type, 2)

def test_ar():
    check_str= "AR 1-1 AR 1-15 AR 1-202 AR 10-89 AR 11-2 Army Regulations 11-18 AR 25-400-2 AR 380-67 AR 380-381 AR 381-47 AR 381-141 Army Regulation 525-21 Army Regulations (AR) 600-8-3 AR 600-8-10 AR 600-8-101 AR 600-9 AR 601-210"
    ref_type = "AR"
    assert check(check_str, ref_type, 17)

def test_ago():
    check_str= "AGO 1958-27 AGO 2020 - 31 ARMY general orders (AGO) 2001- 18 ARMY general order 2000- 07 "
    ref_type = "AGO"
    assert check(check_str, ref_type, 4)

def test_adp():
    check_str= "ADP 1 ADP 3 -0 Army Doctrine Publication 7-0 ADP 1-01"
    ref_type = "ADP"
    assert check(check_str, ref_type, 4)

def test_pam():
    check_str= "PAM 600-8-101 DA Pamphlet 5-11 PAM 40-507 "
    ref_type = "PAM"
    assert check(check_str, ref_type, 3)

def test_atp():
    check_str= "ATP 1-0.1 ATP 1-20 ATP 2-22.9-2 Army Techniques Publication 1-05.03 "
    ref_type = "ATP"
    assert check(check_str, ref_type, 4)

def test_army_dir():
    check_str= "army DIR 2020-08 army directive 2019 - 27 army dir"
    ref_type = "ARMY"
    assert check(check_str, ref_type, 2)

def test_tc():
    check_str= "TC 2-91.5A (TC) 3-4 Training circular 3-34.500 TC"
    ref_type = "TC"
    assert check(check_str, ref_type, 3)

def test_stp():
    check_str= "STP 6-13B24-SM -TG STP 3-CIED - SM-TG STP 6-13II-MQS STP 10-92L14-SM-TG STP 1AB-1948 "
    ref_type = "STP"
    assert check(check_str, ref_type, 4)

def test_tb():
    check_str= "TB 8-6500-MPL TB 8-6515-001-35 TB 38-750-2 TB MED 1 TB MED 284 TB MED 750-1 TB 420-1 TB 420-33 TB ENG 146 TB ENG 62"
    ref_type = "TB"
    assert check(check_str, ref_type, 10)

def test_da_memo():
    check_str= "DA MEMO 600-8-22 DA MEMO 5-5, DA Memorandum 25-53 da memo"
    ref_type = "DA"
    assert check(check_str, ref_type, 3)

def test_fm():
    check_str= "FM 3-01.13 FM 3-13 Field Manual 1-0 FM 3-55.93 FM 3-90-1 FM 101-51-3-CD FM 7-100.1"
    ref_type = "FM"
    assert check(check_str, ref_type, 7)

def test_gta():
    check_str= "GTA 03-04-001A GTA 90-01-028 Graphic Training aid 43-01-103 "
    ref_type = "GTA"
    assert check(check_str, ref_type, 3)

def test_hqda_policy():
    check_str= "HQDA POLICY NOTICE 1-1 HQDA POLICY NOTICE 600-4 "
    ref_type = "HQDA"
    assert check(check_str, ref_type, 2)

def test_cta():
    check_str= "CTA 8-100 CTA 50-909 Common Table of Allowances 50-970 "
    ref_type = "CTA"
    assert check(check_str, ref_type, 3)

def test_attp():
    check_str= "reference ATTP 3-06.11	 ATTP 4140.01 "
    ref_type = "ATTP"
    assert check(check_str, ref_type, 1)

def test_tm():
    check_str= "TM 43-0001-26-2 TM 5-3895-332-23P TM 5-3820-255-12&P TM 3-11.42 TM 3-34.48-2 TM 1-5895-308-SUM TM 1-1680-377-13&P-4"
    ref_type = "TM"
    assert check(check_str, ref_type, 7)

def test_afi():
    check_str = "AFI 1-1 AFI 11-2E-3V3 AFI10-2611-O AFI 13-101 AFI 17-2CDAV3"
    ref_type = "AFI"
    assert check(check_str, ref_type, 5)

def test_cfetp():
    check_str = "CFETP 15WXC1 CFETP 1N2X1X-CC2 CFETP 3E4X1WG"
    ref_type = "CFETP"
    assert check(check_str, ref_type, 3)

def test_afman():
    check_str = "AFMAN 11-2AEV3ADDENDA-A Air Force Manual 11-2C-32BV2 AFMAN10-1004 AFMAN11-2KC-10V3_ADDENDA-A"
    ref_type = "AFMAN"
    assert check(check_str, ref_type, 4)

def test_qtp():
    check_str = "QTP 24-3-HAZMAT QTP 43AX-1 (QTP) 24-3-D549"
    ref_type = "QTP"
    assert check(check_str, ref_type, 3)

def test_afpd():
    check_str = "AFPD 1 AFPD 4 AFPD 10-10 AFPD 91-1"
    ref_type = "AFPD"
    assert check(check_str, ref_type, 3)

def test_afttp():
    check_str = "Air Force Tactics, Techniques, and Procedures (AFTTP) 3-42.32 AFTTP3-4.6_AS AFTTP 3-32.33V1"
    ref_type = "AFTTP"
    assert check(check_str, ref_type, 3)

def test_afva():
    check_str = "AFVA 10-241 AFVA 51-1"
    ref_type = "AFVA"
    assert check(check_str, ref_type, 2)

def test_afh():
    check_str = "AFH 10-222V1 AFH 1 AFH32-7084"
    ref_type = "AFH"
    assert check(check_str, ref_type, 3)

def test_hafmd():
    check_str = "HAFMD 1-2 HAFMD 1-24 Addendum B"
    ref_type = "HAFMD"
    assert check(check_str, ref_type, 2)

def test_afpam():
    check_str = "AFPAM 36-2801V1 AFPAM ( I ) 24-237"
    ref_type = "AFPAM"
    assert check(check_str, ref_type, 2)

def test_afmd():
    check_str = "AFMD 1 AFMD 28"
    ref_type = "AFMD"
    assert check(check_str, ref_type, 2)

def test_afm():
    check_str = "AFM 19-10"
    ref_type = "AFM"
    assert check(check_str, ref_type, 1)

def test_HOI():
    check_str = "HOI 10-1 HOI 36-28"
    ref_type = "HOI"
    assert check(check_str, ref_type, 2)

def test_afjqs():
    check_str = "AFJQS 5J0X1-2 AFJQS 2XXXX"
    ref_type = "AFJQS"
    assert check(check_str, ref_type, 2)

def test_afji():
    check_str = "AFJI 10-411 Air Force Joint Instruction (AFJI) 32-9006"
    ref_type = "AFJI"
    assert check(check_str, ref_type, 2)

def test_afgm():
    check_str = "AFGM 2020-36-04 AFGM 2020-63-148-01"
    ref_type = "AFGM"
    assert check(check_str, ref_type, 2)

def test_dafi():
    check_str = "DAFI 33-360 DAFI 90-2002 DAFI 48-107V1"
    ref_type = "DAFI"
    assert check(check_str, ref_type, 3)

def test_af():
    check_str = "AF 100 AF form 1005"
    ref_type = "AF"
    assert check(check_str, ref_type, 2)

def test_sf():
    check_str = "SF 87 SF 708"
    ref_type = "SF"
    assert check(check_str, ref_type, 2)

def test_afpm():
    check_str = "AFPM 2019-36-02"
    ref_type = "AFPM"
    assert check(check_str, ref_type, 1)

def test_afjman():
    check_str = "AFJMAN 23-209"
    ref_type = "AFJMAN"
    assert check(check_str, ref_type, 1)

def test_jta():
    check_str = "JTA 08-02 JTA 74-1"
    ref_type = "JTA"
    assert check(check_str, ref_type, 2)

def test_dafpd():
    check_str = "DAFPD 10-36 DAFPD 90-1"
    ref_type = "DAFPD"
    assert check(check_str, ref_type, 2)

def test_mco():
    check_str = "MCO 4200.34 MCO P12000.11A MCO 7220R.39"
    ref_type = "MCO"
    assert check(check_str, ref_type, 3)

def test_mcbul():
    check_str = "MCBUL 1300 MCBUL 10120"
    ref_type = "MCBUL"
    assert check(check_str, ref_type, 2)

def test_navmc():
    check_str = "NAVMC 4500.36B NAVMC 2915"
    ref_type = "NAVMC"
    assert check(check_str, ref_type, 2)

def test_navmcdir():
    check_str = "NAVMC DIR 1650.48 NAVMC Directive 5100.8"
    ref_type = "NAVMC DIR"
    assert check(check_str, ref_type, 2)

def test_mcrp():
    check_str = "MCRP 1-10.1 MCRP 3-40B.5 MCRP 4-11.3M"
    ref_type = "MCRP"
    assert check(check_str, ref_type, 3)

def test_mcwp():
    check_str = "MCWP 3-15.7 MCWP 11-10"
    ref_type = "MCWP"
    assert check(check_str, ref_type, 2)

def test_mctp():
    check_str = "MCTP 12-10A MCTP 3-20G"
    ref_type = "MCTP"
    assert check(check_str, ref_type, 2)

def test_mcip():
    check_str = "MCIP 3-03DI MCIP 3-03.1i MCIP 3-40G.21"
    ref_type = "MCIP"
    assert check(check_str, ref_type, 3)

def test_mcdp():
    check_str = "MCDP 1-1 MCDP 7"
    ref_type = "MCDP"
    assert check(check_str, ref_type, 2)

def test_fmfrp():
    check_str = "FMFRP 12-109-II FMFRP 0-53"
    ref_type = "FMFRP"
    assert check(check_str, ref_type, 2)

def test_fmfm():
    check_str = "FMFM 6-1"
    ref_type = "FMFM"
    assert check(check_str, ref_type, 1)

def test_irm():
    check_str = "IRM-2300-05B IRM 5236-06A IRM-5231-03"
    ref_type = "IRM"
    assert check(check_str, ref_type, 3)

def test_secnavinst():
    check_str = "SECNAV Instruction 1640.9C SECNAVINST 5210.60"
    ref_type = "SECNAVINST"
    assert check(check_str, ref_type, 2)

def test_secnav():
    check_str = "SECNAV M-1650.1 SECNAV M-5210.2"
    ref_type = "SECNAV"
    assert check(check_str, ref_type, 2)

def test_navsup():
    check_str = "NAVSUP P-486 NAVSUP Publication 727"
    ref_type = "NAVSUP"
    assert check(check_str, ref_type, 2)

def test_jaginst():
    check_str = "JAGINST 5800.7F JAG INSTRUCTION 1440.1E"
    ref_type = "JAGINST"
    assert check(check_str, ref_type, 2)

def test_ombm():
    check_str = "M-00-02 M-07-16 m 18  19"
    ref_type = "OMBM"
    assert check(check_str, ref_type, 2)
