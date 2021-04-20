--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.15
-- Dumped by pg_dump version 12.5

ALTER TABLE IF EXISTS ONLY public.gc_assists DROP CONSTRAINT IF EXISTS gc_assists_pkey;
ALTER TABLE IF EXISTS public.gc_assists ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.gc_assists_id_seq;
DROP TABLE IF EXISTS public.gc_assists;

--
-- Name: gc_assists; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.gc_assists (
    id integer NOT NULL,
    user_id text NOT NULL,
    user_score double precision,
    is_sme boolean,
    document_id text NOT NULL,
    paragraph_id integer NOT NULL,
    tokens_assumed text NOT NULL,
    entity_tag text NOT NULL,
    confidence_score double precision,
    tagged_correctly boolean NOT NULL,
    incorrect_reason integer NOT NULL,
    "createdAt" timestamp with time zone NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT now() NOT NULL,
    tag_unknown boolean
);


ALTER TABLE public.gc_assists OWNER TO postgres;

--
-- Name: gc_assists_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.gc_assists_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.gc_assists_id_seq OWNER TO postgres;

--
-- Name: gc_assists_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.gc_assists_id_seq OWNED BY public.gc_assists.id;


--
-- Name: gc_assists id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gc_assists ALTER COLUMN id SET DEFAULT nextval('public.gc_assists_id_seq'::regclass);


BEGIN;

--
-- Data for Name: gc_assists; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.gc_assists VALUES (1, 'steve', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_0_0', 0, 'Functional Managers', 'ORG', NULL, true, 0, '2020-09-22 19:52:02.515+00', '2020-09-22 19:52:02.515+00', NULL);
INSERT INTO public.gc_assists VALUES (2, 'Designer', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_2_0', 0, 'ICD 207', 'ORG', NULL, true, 0, '2020-09-22 19:54:29.375+00', '2020-09-22 19:54:29.375+00', NULL);
INSERT INTO public.gc_assists VALUES (3, 'Designer', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_2_0', 0, 'Functional Managers', 'ORG', NULL, true, 0, '2020-09-22 19:54:29.375+00', '2020-09-22 19:54:29.375+00', NULL);
INSERT INTO public.gc_assists VALUES (4, 'Designer', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_2_0', 0, 'Integrated Mission Management', 'ORG', NULL, true, 0, '2020-09-22 19:54:29.375+00', '2020-09-22 19:54:29.375+00', NULL);
INSERT INTO public.gc_assists VALUES (5, 'Designer', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_2_0', 0, 'The National Intelligence Council', 'ORG', NULL, true, 0, '2020-09-22 19:54:29.375+00', '2020-09-22 19:54:29.375+00', NULL);
INSERT INTO public.gc_assists VALUES (6, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'EMSO', 'ORG', NULL, false, 3, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (7, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'Shanahan', 'ORG', NULL, false, 3, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (8, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'SDO', 'ORG', NULL, false, 3, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (9, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'CFT', 'ORG', NULL, true, 0, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (10, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'bl U', 'PERSON', NULL, true, 0, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (11, 'Designer', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'Patrick M', 'PERSON', NULL, true, 0, '2020-09-22 20:23:04.9+00', '2020-09-22 20:23:04.9+00', NULL);
INSERT INTO public.gc_assists VALUES (12, 'gc_beta', NULL, NULL, 'DoDD 3025.13, 10 8 2010, Ch 1, 5 4 2017 OCR.pdf_1_3', 3, 'U.S.C', 'ORG', NULL, true, 0, '2020-09-23 16:49:43.853+00', '2020-09-23 16:49:43.853+00', NULL);
INSERT INTO public.gc_assists VALUES (13, 'steve', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_4_0', 0, 'EMSO', 'ORG', NULL, false, 2, '2020-09-25 13:29:10.157+00', '2020-09-25 13:29:10.157+00', NULL);
INSERT INTO public.gc_assists VALUES (14, 'steve', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_4_0', 0, 'the EMSO CFT', 'ORG', NULL, true, 0, '2020-09-25 13:29:10.157+00', '2020-09-25 13:29:10.157+00', NULL);
INSERT INTO public.gc_assists VALUES (15, 'steve', NULL, NULL, 'DoDD 3025.13, 10 8 2010, Ch 1, 5 4 2017 OCR.pdf_4_4', 4, 'THE DEPARTMENT OF DEFENSE', 'ORG', NULL, true, 0, '2020-10-07 17:58:56.772+00', '2020-10-07 17:58:56.772+00', NULL);
INSERT INTO public.gc_assists VALUES (16, 'gc_user', NULL, NULL, 'ICPG 900.2, 12 23 2016 OCR.pdf_0_0', 0, 'Functional Managers', 'ORG', NULL, false, 3, '2020-10-08 15:10:59.549+00', '2020-10-08 15:10:59.549+00', NULL);
INSERT INTO public.gc_assists VALUES (17, 'gc_beta', NULL, NULL, 'DoDD 3025.13, 10 8 2010, Ch 1, 5 4 2017 OCR.pdf_6_6', 6, 'OSD Components', 'ORG', NULL, true, 0, '2020-10-14 19:27:14.861+00', '2020-10-14 19:27:14.861+00', NULL);
INSERT INTO public.gc_assists VALUES (18, 'steve', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_6_0', 0, 'NDAA', 'ORG', NULL, true, 0, '2020-10-15 18:47:10.454+00', '2020-10-15 18:47:10.454+00', NULL);
INSERT INTO public.gc_assists VALUES (19, 'steve', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'EMSO', 'ORG', NULL, true, 0, '2020-10-15 19:10:44.193+00', '2020-10-15 19:10:44.193+00', NULL);
INSERT INTO public.gc_assists VALUES (20, 'steve', NULL, NULL, 'SEC DEF Memo, Establishment of the Electromagnetic Spectrum Operations Cross Functional Team, 2 2 2019 OCR.pdf_1_0', 0, 'Shanahan', 'ORG', NULL, false, 1, '2020-10-15 19:10:44.194+00', '2020-10-15 19:10:44.194+00', NULL);
INSERT INTO public.gc_assists VALUES (21, 'steve', NULL, NULL, 'CJCSI 5711.02C.pdf_18', 7, 'Federal Agencies', 'ORG', NULL, false, 3, '2020-10-20 17:02:40.243+00', '2020-10-20 17:02:40.243+00', NULL);
INSERT INTO public.gc_assists VALUES (22, 'steve', NULL, NULL, 'CJCSN 5768.pdf_21', 8, 'the Department of Defense', 'ORG', NULL, true, 0, '2020-10-21 19:44:50.764+00', '2020-10-21 19:44:50.764+00', false);
INSERT INTO public.gc_assists VALUES (23, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Defense', 'ORG', NULL, false, 2, '2020-10-21 20:05:21.041+00', '2020-10-21 20:05:21.041+00', false);
INSERT INTO public.gc_assists VALUES (24, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'NATO', 'ORG', NULL, true, 0, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (25, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'State', 'ORG', NULL, false, 2, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (26, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'COMSEC', 'ORG', NULL, false, 1, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (27, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Japan', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (28, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Malaysia', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (30, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'New Zealand', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (31, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Singapore', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.043+00', '2020-10-21 20:05:21.043+00', false);
INSERT INTO public.gc_assists VALUES (29, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'the Republic of Korea', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.043+00', '2020-10-21 20:05:21.043+00', false);
INSERT INTO public.gc_assists VALUES (32, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Australia', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.042+00', '2020-10-21 20:05:21.042+00', false);
INSERT INTO public.gc_assists VALUES (33, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Philippines', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.043+00', '2020-10-21 20:05:21.043+00', false);
INSERT INTO public.gc_assists VALUES (34, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_233', 4, 'Thailand', 'GPE', NULL, true, 0, '2020-10-21 20:05:21.043+00', '2020-10-21 20:05:21.043+00', false);
INSERT INTO public.gc_assists VALUES (35, 'steve', NULL, NULL, 'CJCSI 3500.01J.pdf_584', 4, 'bk', 'ORG', NULL, false, 3, '2020-10-21 20:06:11.264+00', '2020-10-21 20:06:11.264+00', false);
INSERT INTO public.gc_assists VALUES (36, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'CJCS', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.387+00', '2020-10-21 20:09:58.387+00', false);
INSERT INTO public.gc_assists VALUES (37, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'the Federal Government', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.387+00', '2020-10-21 20:09:58.387+00', false);
INSERT INTO public.gc_assists VALUES (38, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'Human Resources Office', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.387+00', '2020-10-21 20:09:58.387+00', false);
INSERT INTO public.gc_assists VALUES (39, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'JCSCA', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (40, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'DPSA', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.387+00', '2020-10-21 20:09:58.387+00', false);
INSERT INTO public.gc_assists VALUES (41, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'JCSAA', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.387+00', '2020-10-21 20:09:58.387+00', false);
INSERT INTO public.gc_assists VALUES (42, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'the Length of Service', 'ORG', NULL, false, 3, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (43, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'CPB', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (44, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'Department of State', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (45, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'DJS', 'NORP', NULL, false, 1, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (46, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'Federal Government', 'ORG', NULL, true, 0, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (47, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_30', 0, 'OPSA', 'GPE', NULL, false, 1, '2020-10-21 20:09:58.388+00', '2020-10-21 20:09:58.388+00', false);
INSERT INTO public.gc_assists VALUES (48, 'steve', NULL, NULL, 'AI 68 CH 1.pdf_12', 12, 'NCR', 'ORG', NULL, false, 1, '2020-10-21 20:14:14.522+00', '2020-10-21 20:14:14.522+00', false);
INSERT INTO public.gc_assists VALUES (49, 'steve', NULL, NULL, 'AI 68 CH 1.pdf_12', 12, 'Washington Headquarters Services', 'ORG', NULL, true, 0, '2020-10-21 20:14:14.523+00', '2020-10-21 20:14:14.523+00', false);
INSERT INTO public.gc_assists VALUES (50, 'steve', NULL, NULL, 'AI 68 CH 1.pdf_12', 12, 'WHS', 'ORG', NULL, true, 0, '2020-10-21 20:14:14.523+00', '2020-10-21 20:14:14.523+00', false);
INSERT INTO public.gc_assists VALUES (51, 'steve', NULL, NULL, 'AI 68 CH 1.pdf_12', 12, 'the National Capital Region', 'LOC', NULL, true, 0, '2020-10-21 20:14:14.523+00', '2020-10-21 20:14:14.523+00', false);
INSERT INTO public.gc_assists VALUES (52, 'steve', NULL, NULL, 'AI 68 CH 1.pdf_12', 12, 'This Administrative Instruction', 'LAW', NULL, true, 0, '2020-10-21 20:14:14.523+00', '2020-10-21 20:14:14.523+00', false);
INSERT INTO public.gc_assists VALUES (53, 'steve', NULL, NULL, 'CJCSN 5768.pdf_2', 2, 'Notice 5768', 'LAW', NULL, false, 2, '2020-10-21 20:15:20.44+00', '2020-10-21 20:15:20.44+00', false);
INSERT INTO public.gc_assists VALUES (54, 'steve', NULL, NULL, 'CJCSI 5123.01H.pdf_980', 11, 'IAW', 'ORG', NULL, true, 0, '2020-10-21 20:15:51.28+00', '2020-10-21 20:15:51.28+00', false);
INSERT INTO public.gc_assists VALUES (55, 'steve', NULL, NULL, 'CJCSI 5123.01H.pdf_980', 11, 'gg', 'ORG', NULL, false, 3, '2020-10-21 20:15:51.281+00', '2020-10-21 20:15:51.281+00', false);
INSERT INTO public.gc_assists VALUES (56, 'steve', NULL, NULL, 'CJCSI 5123.01H.pdf_980', 11, 'ff', 'ORG', NULL, false, 3, '2020-10-21 20:15:51.281+00', '2020-10-21 20:15:51.281+00', false);
INSERT INTO public.gc_assists VALUES (57, 'steve', NULL, NULL, 'CJCSI 5140.01B.pdf_409', 9, 'MAP', 'ORG', NULL, false, 0, '2020-10-21 20:19:53.921+00', '2020-10-21 20:19:53.921+00', true);
INSERT INTO public.gc_assists VALUES (58, 'steve', NULL, NULL, 'CJCSI 5711.02C.pdf_53', 0, 'CJCSI', 'ORG', NULL, true, 0, '2020-10-21 20:21:06.122+00', '2020-10-21 20:21:06.122+00', false);
INSERT INTO public.gc_assists VALUES (59, 'steve', NULL, NULL, 'CJCSI 6731.01C.pdf_380', 9, 'United States', 'ORG', NULL, false, 2, '2020-10-21 20:23:43.196+00', '2020-10-21 20:23:43.196+00', false);
INSERT INTO public.gc_assists VALUES (60, 'steve', NULL, NULL, 'CJCSI 6731.01C.pdf_380', 9, 'United States', 'GPE', NULL, false, 2, '2020-10-21 20:23:43.196+00', '2020-10-21 20:23:43.196+00', false);
INSERT INTO public.gc_assists VALUES (61, 'steve', NULL, NULL, 'CJCSI 5140.01B.pdf_322', 13, 'Target Coordination Mensuration Certification and Program Accreditation', 'ORG', NULL, false, 0, '2020-10-21 20:24:33.206+00', '2020-10-21 20:24:33.206+00', true);
INSERT INTO public.gc_assists VALUES (62, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_264', 5, 'Policy for Department of Defense', 'ORG', NULL, false, 3, '2020-10-21 20:27:11.812+00', '2020-10-21 20:27:11.812+00', false);
INSERT INTO public.gc_assists VALUES (63, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_264', 5, 'CJCSI', 'ORG', NULL, true, 0, '2020-10-21 20:27:11.812+00', '2020-10-21 20:27:11.812+00', false);
INSERT INTO public.gc_assists VALUES (64, 'steve', NULL, NULL, 'CJCSI 6740.01C.pdf_264', 5, 'DOD', 'ORG', NULL, true, 0, '2020-10-21 20:27:11.812+00', '2020-10-21 20:27:11.812+00', false);
INSERT INTO public.gc_assists VALUES (65, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_14', 0, 'PSD Awards Office', 'ORG', NULL, true, 0, '2020-10-21 20:28:03.179+00', '2020-10-21 20:28:03.179+00', false);
INSERT INTO public.gc_assists VALUES (66, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_14', 0, 'JS', 'ORG', NULL, true, 0, '2020-10-21 20:28:03.179+00', '2020-10-21 20:28:03.179+00', false);
INSERT INTO public.gc_assists VALUES (67, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_14', 0, 'the Editorial and Actions Processing Branch', 'ORG', NULL, true, 0, '2020-10-21 20:28:03.179+00', '2020-10-21 20:28:03.179+00', false);
INSERT INTO public.gc_assists VALUES (68, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_14', 0, 'Times New Roman', 'ORG', NULL, false, 1, '2020-10-21 20:28:03.179+00', '2020-10-21 20:28:03.179+00', false);
INSERT INTO public.gc_assists VALUES (69, 'steve', NULL, NULL, 'CJCSI 1100.01D.pdf_14', 0, 'JS', 'LAW', NULL, false, 0, '2020-10-21 20:28:03.179+00', '2020-10-21 20:28:03.179+00', true);
INSERT INTO public.gc_assists VALUES (70, 'steve', NULL, NULL, 'CJCSI 6245.01A.pdf_123', 19, 'JPME Ph 1 & 2', 'ORG', NULL, false, 0, '2020-10-22 17:24:38.556+00', '2020-10-22 17:24:38.556+00', true);
INSERT INTO public.gc_assists VALUES (73, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'the Department of the Army', 'ORG', NULL, true, 0, '2020-10-27 16:46:50.317+00', '2020-10-27 16:46:50.317+00', false);
INSERT INTO public.gc_assists VALUES (74, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'WD Bul', 'ORG', NULL, false, 0, '2020-10-27 16:46:50.317+00', '2020-10-27 16:46:50.317+00', true);
INSERT INTO public.gc_assists VALUES (75, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Infantry', 'ORG', NULL, false, 1, '2020-10-27 16:46:50.317+00', '2020-10-27 16:46:50.317+00', false);
INSERT INTO public.gc_assists VALUES (76, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'the United States Army', 'ORG', NULL, true, 0, '2020-10-27 16:46:50.317+00', '2020-10-27 16:46:50.317+00', false);
INSERT INTO public.gc_assists VALUES (78, 'gc_beta', NULL, NULL, 'AGO 1958-40.pdf_4', 0, 'unita', 'ORG', NULL, false, 3, '2020-11-02 14:56:09.856+00', '2020-11-02 14:56:09.856+00', false);
INSERT INTO public.gc_assists VALUES (77, 'gc_beta', NULL, NULL, 'AGO 1958-40.pdf_4', 0, 'battalfos', 'ORG', NULL, true, 0, '2020-11-02 14:56:09.856+00', '2020-11-02 14:56:09.856+00', false);
INSERT INTO public.gc_assists VALUES (79, 'gc_beta', NULL, NULL, 'AGO 1958-40.pdf_4', 0, 'THGO', 'ORG', NULL, true, 0, '2020-11-02 14:56:09.856+00', '2020-11-02 14:56:09.856+00', false);
INSERT INTO public.gc_assists VALUES (80, 'steve', NULL, NULL, 'AR 15-6.pdf_37', 0, 'UCMJ', 'ORG', NULL, true, 0, '2020-11-02 16:52:26.835+00', '2020-11-02 16:52:26.835+00', false);
INSERT INTO public.gc_assists VALUES (81, 'steve', NULL, NULL, 'AR 15-6.pdf_37', 0, 'AR 156', 'ORG', NULL, false, 3, '2020-11-02 16:52:26.836+00', '2020-11-02 16:52:26.836+00', false);
INSERT INTO public.gc_assists VALUES (83, 'steve', NULL, NULL, 'AGO 1960-10.pdf_0', 0, 'Iilbbon with Mcbl', 'ORG', NULL, false, 3, '2020-11-05 18:17:59.732+00', '2020-11-05 18:17:59.732+00', false);
INSERT INTO public.gc_assists VALUES (82, 'steve', NULL, NULL, 'AGO 1960-10.pdf_0', 0, 'HBADQUARTI3RS', 'ORG', NULL, false, 3, '2020-11-05 18:17:59.732+00', '2020-11-05 18:17:59.732+00', false);
INSERT INTO public.gc_assists VALUES (84, 'steve', NULL, NULL, 'AR 145-1.pdf_8', 0, 'The Commanding General', 'ORG', NULL, false, 3, '2020-11-10 19:33:51.194+00', '2020-11-10 19:33:51.194+00', false);
INSERT INTO public.gc_assists VALUES (85, 'steve', NULL, NULL, 'AR 145-1.pdf_8', 0, 'Fourth ROTC Region', 'ORG', NULL, false, 0, '2020-11-10 19:33:51.194+00', '2020-11-10 19:33:51.194+00', true);
INSERT INTO public.gc_assists VALUES (86, 'steve', NULL, NULL, 'AR 145-1.pdf_8', 0, 'PERSCOM', 'ORG', NULL, true, 0, '2020-11-10 19:33:51.193+00', '2020-11-10 19:33:51.193+00', false);
INSERT INTO public.gc_assists VALUES (87, 'steve', NULL, NULL, 'AR 145-1.pdf_8', 0, 'TRADOC', 'ORG', NULL, true, 0, '2020-11-10 19:33:51.194+00', '2020-11-10 19:33:51.194+00', false);
INSERT INTO public.gc_assists VALUES (88, 'steve', NULL, NULL, 'AGO 1952-16.pdf_1', 0, 'USA Theddjufant Ueneral', 'ORG', NULL, false, 0, '2020-11-10 19:34:57.59+00', '2020-11-10 19:34:57.59+00', true);
INSERT INTO public.gc_assists VALUES (89, 'steve', NULL, NULL, 'AGO 1952-16.pdf_1', 0, 'OE', 'ORG', NULL, false, 0, '2020-11-10 19:34:57.59+00', '2020-11-10 19:34:57.59+00', true);
INSERT INTO public.gc_assists VALUES (90, 'steve', NULL, NULL, 'AR 11-35.pdf_8', 0, 'OEH', 'ORG', NULL, false, 0, '2020-11-18 17:45:08.09+00', '2020-11-18 17:45:08.09+00', true);
INSERT INTO public.gc_assists VALUES (91, 'steve', NULL, NULL, 'AR 11-35.pdf_8', 0, 'Army', 'ORG', NULL, false, 3, '2020-11-18 17:45:08.09+00', '2020-11-18 17:45:08.09+00', false);
INSERT INTO public.gc_assists VALUES (92, 'steve', NULL, NULL, 'AR 11-35.pdf_8', 0, 'TTP', 'ORG', NULL, false, 0, '2020-11-18 17:45:08.09+00', '2020-11-18 17:45:08.09+00', true);
INSERT INTO public.gc_assists VALUES (93, 'steve', NULL, NULL, 'AGO 1952-22.pdf_1', 0, 'oxper', 'ORG', NULL, false, 0, '2020-11-18 17:45:31.058+00', '2020-11-18 17:45:31.058+00', true);
INSERT INTO public.gc_assists VALUES (94, 'steve', NULL, NULL, 'AGO 1952-22.pdf_1', 0, 'United States Army Mafor General', 'ORG', NULL, true, 0, '2020-11-18 17:45:31.058+00', '2020-11-18 17:45:31.058+00', false);
INSERT INTO public.gc_assists VALUES (95, 'steve', NULL, NULL, 'AGO 1959-30.pdf_5', 0, 'Chemical Corps', 'ORG', NULL, true, 0, '2020-11-18 21:03:29.644+00', '2020-11-18 21:03:29.644+00', false);
INSERT INTO public.gc_assists VALUES (96, 'steve', NULL, NULL, 'AGO 1959-30.pdf_5', 0, 'Transportation Corps', 'ORG', NULL, true, 0, '2020-11-18 21:03:29.644+00', '2020-11-18 21:03:29.644+00', false);
INSERT INTO public.gc_assists VALUES (97, 'steve', NULL, NULL, 'AGO 1959-30.pdf_5', 0, 'Military Pollce Corps', 'ORG', NULL, true, 0, '2020-11-18 21:03:29.644+00', '2020-11-18 21:03:29.644+00', false);
INSERT INTO public.gc_assists VALUES (98, 'steve', NULL, NULL, 'AGO 1959-30.pdf_5', 0, 'Army', 'ORG', NULL, false, 2, '2020-11-18 21:03:29.645+00', '2020-11-18 21:03:29.645+00', false);
INSERT INTO public.gc_assists VALUES (99, 'steve', NULL, NULL, 'AGO 1959-30.pdf_5', 0, 'Tdeutenant', 'ORG', NULL, false, 0, '2020-11-18 21:03:29.645+00', '2020-11-18 21:03:29.645+00', true);
INSERT INTO public.gc_assists VALUES (100, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'the Department of the Army', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (102, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'WD Bul', 'ORG', NULL, false, 3, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (103, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Infantry', 'ORG', NULL, false, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', true);
INSERT INTO public.gc_assists VALUES (104, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'grogsly', 'ORG', NULL, false, 3, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (101, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'the United States Army', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (105, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'United States Army', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (106, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'ww w ww AGO', 'ORG', NULL, false, 3, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (107, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, '8d Infantry Division', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (108, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Congress', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (109, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, '7th Infantry Regiment', 'ORG', NULL, true, 0, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (110, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'shelis', 'PERSON', NULL, false, 3, '2020-11-19 17:17:56.999+00', '2020-11-19 17:17:56.999+00', false);
INSERT INTO public.gc_assists VALUES (111, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'John Essebagger', 'PERSON', NULL, false, 2, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (112, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'banzaj charze', 'PERSON', NULL, false, 3, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (113, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Kasebagger', 'PERSON', NULL, true, 0, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (114, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Corporal Esasebagger', 'PERSON', NULL, true, 0, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (115, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'Korea', 'GPE', NULL, true, 0, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (116, 'steve', NULL, NULL, 'AGO 1952-61.pdf_0', 0, 'tinued', 'GPE', NULL, false, 3, '2020-11-19 17:17:57+00', '2020-11-19 17:17:57+00', false);
INSERT INTO public.gc_assists VALUES (117, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'OGDEN ORDNANCE PLANT', 'ORG', NULL, false, 0, '2020-12-02 18:29:37.186+00', '2020-12-02 18:29:37.186+00', true);
INSERT INTO public.gc_assists VALUES (119, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'Ordera 88', 'PERSON', NULL, false, 3, '2020-12-02 18:29:37.186+00', '2020-12-02 18:29:37.186+00', false);
INSERT INTO public.gc_assists VALUES (118, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'Section OGDEN ORDNANCE PLANT', 'ORG', NULL, false, 0, '2020-12-02 18:29:37.186+00', '2020-12-02 18:29:37.186+00', true);
INSERT INTO public.gc_assists VALUES (120, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'FORT SLOCUM', 'GPE', NULL, false, 1, '2020-12-02 18:29:37.186+00', '2020-12-02 18:29:37.186+00', false);
INSERT INTO public.gc_assists VALUES (121, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'NEW YORK', 'GPE', NULL, true, 0, '2020-12-02 18:29:37.186+00', '2020-12-02 18:29:37.186+00', false);
INSERT INTO public.gc_assists VALUES (122, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1955-01.pdf_0', 0, 'Onoens', 'GPE', NULL, false, 0, '2020-12-02 18:29:37.187+00', '2020-12-02 18:29:37.187+00', true);
INSERT INTO public.gc_assists VALUES (123, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1960-10.pdf_0', 0, 'HBADQUARTI3RS', 'ORG', NULL, true, 0, '2020-12-02 21:37:57.067+00', '2020-12-02 21:37:57.067+00', false);
INSERT INTO public.gc_assists VALUES (124, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'AGO 1954-56.pdf_19', 1, 'the United Stettes', 'ORG', NULL, false, 0, '2020-12-02 21:43:30.037+00', '2020-12-02 21:43:30.037+00', true);
INSERT INTO public.gc_assists VALUES (125, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'the United States Army', 'ORG', NULL, true, 0, '2020-12-03 15:11:11.217+00', '2020-12-03 15:11:11.217+00', false);
INSERT INTO public.gc_assists VALUES (126, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'Armed Forces', 'ORG', NULL, true, 0, '2020-12-03 15:11:11.218+00', '2020-12-03 15:11:11.218+00', false);
INSERT INTO public.gc_assists VALUES (130, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'GEZFXAL', 'ORG', NULL, false, 0, '2020-12-03 15:11:11.218+00', '2020-12-03 15:11:11.218+00', true);
INSERT INTO public.gc_assists VALUES (128, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'New York Xanchester', 'ORG', NULL, false, 0, '2020-12-03 15:11:11.218+00', '2020-12-03 15:11:11.218+00', true);
INSERT INTO public.gc_assists VALUES (129, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'Bncand Army', 'ORG', NULL, false, 0, '2020-12-03 15:11:11.218+00', '2020-12-03 15:11:11.218+00', true);
INSERT INTO public.gc_assists VALUES (132, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'Pennsylvania Fafrmont', 'ORG', NULL, false, 3, '2020-12-03 15:11:11.219+00', '2020-12-03 15:11:11.219+00', false);
INSERT INTO public.gc_assists VALUES (133, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, 'Data Loggers', 'ORG', NULL, true, 0, '2020-12-29 22:20:16.129+00', '2020-12-29 22:20:16.129+00', false);
INSERT INTO public.gc_assists VALUES (140, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'A BRIEF HISTORY OF THE 4TH MARINES.pdf_2', 0, 'MARINE CORPS', 'ORG', NULL, true, 0, '2021-01-11 21:31:22.332+00', '2021-01-11 21:31:22.332+00', false);
INSERT INTO public.gc_assists VALUES (141, '845de8d3c0527e4c612de9fd66ae0668', NULL, NULL, 'AFH 32-1290_I.pdf_28', 0, 'AFH', 'ORG', NULL, false, 0, '2021-01-22 14:24:31.472+00', '2021-01-22 14:24:31.472+00', true);
INSERT INTO public.gc_assists VALUES (142, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'A BRIEF HISTORY OF THE 10TH MARINES.pdf_58', 0, 'Francisco Franco', 'ORG', NULL, false, 1, '2021-01-22 21:27:14.651+00', '2021-01-22 21:27:14.651+00', false);
INSERT INTO public.gc_assists VALUES (135, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, 'AFH', 'ORG', NULL, true, 0, '2020-12-29 22:20:16.129+00', '2020-12-29 22:20:16.129+00', false);
INSERT INTO public.gc_assists VALUES (138, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, '1.8.5', 'PERSON', NULL, true, 0, '2020-12-29 22:20:16.13+00', '2020-12-29 22:20:16.13+00', false);
INSERT INTO public.gc_assists VALUES (143, 'd69403e2673e611d4cbd3fad6fd1788e', NULL, NULL, 'A BRIEF HISTORY OF THE 10TH MARINES.pdf_58', 0, 'The 3d Battalion', 'ORG', NULL, false, 1, '2021-01-22 21:27:14.651+00', '2021-01-22 21:27:14.651+00', false);
INSERT INTO public.gc_assists VALUES (136, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, '1.8.4', 'PERSON', NULL, true, 0, '2020-12-29 22:20:16.129+00', '2020-12-29 22:20:16.129+00', false);
INSERT INTO public.gc_assists VALUES (134, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, 'ohms', 'PERSON', NULL, true, 0, '2020-12-29 22:20:16.13+00', '2020-12-29 22:20:16.13+00', false);
INSERT INTO public.gc_assists VALUES (137, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, 'AC', 'ORG', NULL, true, 0, '2020-12-29 22:20:16.129+00', '2020-12-29 22:20:16.129+00', false);
INSERT INTO public.gc_assists VALUES (139, '0aad40f415c9173fcc83acd984c0c83c', NULL, NULL, 'AFH 32-1290_I.pdf_20', 0, 'DC', 'GPE', NULL, true, 0, '2020-12-29 22:20:16.13+00', '2020-12-29 22:20:16.13+00', false);
INSERT INTO public.gc_assists VALUES (127, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'DA General Orders No', 'ORG', NULL, false, 3, '2020-12-03 15:11:11.218+00', '2020-12-03 15:11:11.218+00', false);
INSERT INTO public.gc_assists VALUES (131, '475377006295ab95937c7188a09cfcd6', NULL, NULL, 'AGO 1954-51.pdf_0', 0, 'DA', 'ORG', NULL, false, 0, '2020-12-03 15:11:11.219+00', '2020-12-03 15:11:11.219+00', true);


COMMIT;

--
-- Name: gc_assists_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.gc_assists_id_seq', 143, true);


--
-- Name: gc_assists gc_assists_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.gc_assists
    ADD CONSTRAINT gc_assists_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

