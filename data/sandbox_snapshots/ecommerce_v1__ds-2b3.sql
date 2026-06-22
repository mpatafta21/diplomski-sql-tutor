pg_dump: warning: there are circular foreign-key constraints on this table:
pg_dump: detail: employees
pg_dump: hint: You might not be able to restore the dump without using --disable-triggers or temporarily dropping the constraints.
pg_dump: hint: Consider using a full dump instead of a --data-only dump to avoid this problem.
--
-- PostgreSQL database dump
--

\restrict o9RxaIZY2WfhMqrTIs7hwrQ9tIePHsSKoIXUtHv5PaIgeo8OLSyfCBeEPjzPUai

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: categories; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.categories (id, name, description) FROM stdin;
1	Electronics	Agent every development say quality.
2	Books	Beautiful instead ahead despite measure ago current practice nation determine.
3	Sports	Everything thank serve civil institution everyone democratic shake bill here.
4	Home	Suggest page southern role movie win her need.
5	Garden	Peace technology officer relate animal direction eye bag do big everyone.
6	Toys	Class great prove reduce raise author play move.
7	Clothing	Clear here writer policy news range successful.
8	Beauty	Director allow firm environment decision.
9	Automotive	Then fire pretty how trip learn enter east no enjoy.
10	Music	Investment on gun young catch management sense technology check civil.
11	Movies	Others his other life edge network wall quite boy.
12	Office	Seem shoulder future fall citizen about reveal rest will seven.
13	Pet Supplies	Tree that fear police participant check several much single.
14	Tools	Truth out major born guy world southern dream drive note.
15	Health	Beat magazine attorney set she.
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.customers (id, first_name, last_name, email, country, city, registered_at) FROM stdin;
1	Leon	Car	skodamartina@example.org	Croatia	Drniš	2025-08-15 01:44:07.03092+00
2	Matej	Škara	severdjurdjica@example.org	Croatia	Čakovec	2024-01-25 16:07:46.551356+00
3	David	Sokić	rasickristina@example.net	Croatia	Hvar	2024-10-04 07:31:17.847174+00
4	Matea	Amidžić	mijomikic@example.com	Croatia	Duga Resa	2024-01-22 00:42:42.643988+00
5	Romano	Ladavac	brckosuzana@example.org	Croatia	Valpovo	2024-06-10 23:38:43.789875+00
6	Marijana	Bebić	hpuharic@example.com	Croatia	Oroslavje	2024-04-16 08:20:12.881892+00
7	Jure	Stošić	hrvoje31@example.org	Croatia	Solin	2024-04-12 04:39:42.706908+00
8	Christopher	Hall	jamesshawn@example.com	Central African Republic	Michaelview	2025-07-08 02:30:39.053746+00
9	Frances	Jones	amandasanchez@example.com	Hong Kong	Veronicaside	2024-01-26 17:49:38.199722+00
10	Mark	Tate	perezantonio@example.com	Iran	Carlshire	2026-01-15 08:37:49.482634+00
11	Nada	Herceg	pmatahlija@example.com	Croatia	Jastrebarsko	2023-10-31 02:26:35.392586+00
12	Pavao	Rašić	pero96@example.net	Croatia	Kutina	2024-01-26 10:05:05.888138+00
13	Ivka	Pešić	wbracun@example.org	Croatia	Duga Resa	2025-04-17 14:40:11.276808+00
14	Tomo	Vrhovec	esladonja@example.com	Croatia	Pakrac	2026-05-26 13:49:42.260577+00
15	Dominik	Jemrić	vrhovecmladen@example.org	Croatia	Solin	2025-05-02 10:05:50.791605+00
16	Fuma	Knežević	derceg@example.org	Croatia	Zagreb	2024-11-29 14:35:55.444383+00
17	Karla	Pečur	terlevicmilica@example.net	Croatia	Duga Resa	2024-07-13 19:27:46.198885+00
18	Evan	Ashley	georgetracy@example.org	Vanuatu	Natashaport	2024-02-17 11:29:24.025784+00
19	John	Bradley	millertodd@example.org	Senegal	East Donna	2026-04-02 14:05:25.452197+00
20	Frederick	Rose	ibrandt@example.net	Portugal	Lake Larry	2026-05-25 12:16:00.586153+00
21	Luka	Maras	cpokas@example.org	Croatia	Hvar	2023-08-09 06:15:08.922601+00
22	Anita	Seničić	ivanhorvatinec@example.org	Croatia	Samobor	2025-04-21 14:50:12.234175+00
23	Lorena	Bogdan	kuvezdicbranka@example.net	Croatia	Kastav	2025-06-02 02:50:29.418687+00
24	Lea	Puškarić	nenadritosa@example.net	Croatia	Ivanec	2025-10-06 19:54:08.098446+00
25	Viktor	Matošević	elizabetabrletic@example.net	Croatia	Krk	2024-09-06 05:30:40.345649+00
26	Antun	Šestak	volaricmarijan@example.net	Croatia	Buzet	2024-08-14 06:23:24.521848+00
27	Petra	Bučar	katicagracin@example.net	Croatia	Drniš	2024-09-04 08:53:06.594504+00
28	Joshua	Wright	ramosmichelle@example.net	Bolivia	Lake Yvettetown	2026-04-26 20:30:41.228369+00
29	Sara	Allison	richardolson@example.com	United Kingdom	East Nicholasfurt	2024-03-16 16:39:52.679394+00
30	Kristen	Gibson	uhorton@example.net	Panama	Mooreport	2024-01-24 15:29:13.334657+00
31	Biljana	Rukavina	sokcevicnada@example.org	Croatia	Ozalj	2024-11-03 12:47:12.086715+00
32	Dominik	Erceg	pesadanijela@example.org	Croatia	Pakrac	2023-08-13 13:43:53.071643+00
33	Maja	Matković	risekmare@example.net	Croatia	Pleternica	2023-08-28 22:29:10.050748+00
34	Marin	Sakač	marija35@example.org	Croatia	Lipik	2023-10-21 12:17:18.191689+00
35	Lovro	Komar	wkraljevic@example.org	Croatia	Nova Gradiška	2025-04-10 17:20:39.918656+00
36	Fran	Bungić	puljizlea@example.net	Croatia	Donji Miholjac	2026-03-18 16:43:43.432615+00
37	Božica	Jaković	mateja27@example.net	Croatia	Petrinja	2026-05-13 03:12:41.522996+00
38	Lindsay	Rice	sarah12@example.com	Brazil	Lake Angelaview	2024-04-03 19:58:08.824223+00
39	Jason	Cooper	william40@example.org	North Macedonia	Calderonton	2023-06-03 23:47:15.123444+00
40	Kellie	Walsh	evan78@example.net	Japan	North Charlesberg	2025-01-17 22:05:10.161867+00
41	Zvonko	Malnar	steficacvrtila@example.org	Croatia	Kutina	2026-02-09 03:18:48.527411+00
42	Toni	Bačak	laura31@example.com	Croatia	Zagreb	2025-04-10 04:15:18.263562+00
43	Jasminka	Ivanović	valtergalesic@example.com	Croatia	Đurđevac	2025-08-15 04:11:15.746464+00
44	Nina	Medač	marinaergotic@example.net	Croatia	Labin	2026-01-10 18:09:34.74841+00
45	Boris	Hrabar	vladonikolic@example.com	Croatia	Trilj	2025-10-18 13:58:07.836665+00
46	Lorena	Hranić	veickatica@example.com	Croatia	Kastav	2026-01-02 04:40:36.807419+00
47	Saša	Katić	lovre86@example.net	Croatia	Vrlika	2023-06-30 08:21:52.400687+00
48	Natalie	Green	benjamin96@example.com	Saint Lucia	Samuelhaven	2023-10-04 19:42:54.42838+00
49	Rachel	Lee	fletcheraaron@example.net	Poland	West Ryan	2026-04-04 19:21:48.952797+00
50	Samantha	Hanson	cortezkevin@example.com	Papua New Guinea	Nguyenport	2025-01-27 14:05:08.578511+00
51	Katica	Mihelčić	vvranic@example.org	Croatia	Ludbreg	2025-01-20 11:48:13.938497+00
52	Albina	Kosanović	laura69@example.net	Croatia	Novalja	2024-09-26 04:18:58.105541+00
53	Mate	Herout	ksimunovic@example.net	Croatia	Kaštela	2024-12-15 21:31:52.992692+00
54	Kristijan	Stražičić	dragica34@example.org	Croatia	Dubrovnik	2023-06-26 20:52:00.536579+00
55	Mara	Oršoš	muzinazora@example.net	Croatia	Senj	2025-07-02 02:46:05.73562+00
56	Danijel	Matijaš	janavaci@example.net	Croatia	Vis	2025-08-30 22:52:07.202082+00
57	Saša	Buzov	lhorvatek@example.net	Croatia	Buje	2025-01-30 20:48:06.461547+00
58	Samantha	Martinez	lauriecontreras@example.net	Nepal	Stephaniemouth	2025-04-01 09:38:06.827539+00
59	Jennifer	Wagner	vmerritt@example.com	Korea	Karenview	2025-09-16 05:21:44.781659+00
60	Adrienne	Sims	scott43@example.com	Grenada	Patricialand	2023-10-29 17:24:25.185539+00
61	Lucija	Maričević	milehecimovic@example.org	Croatia	Makarska	2024-05-27 15:49:34.112905+00
62	Antun	Merkaš	hadziczvonko@example.com	Croatia	Vodice	2025-09-20 14:04:49.88255+00
63	Mijo	Baljak	aozimec@example.com	Croatia	Slavonski Brod	2024-07-31 10:08:01.089415+00
64	Zvonko	Mihaljević	daliborhorvatek@example.com	Croatia	Novigrad	2023-07-01 21:49:09.741518+00
65	Petra	Vižintin	ksaric@example.com	Croatia	Zaprešić	2025-04-11 22:12:39.924863+00
66	Anka	Maršić	boziclovre@example.com	Croatia	Varaždinske Toplice	2024-10-17 23:57:31.731633+00
67	Barbara	Jukić	nkunac@example.com	Croatia	Krapina	2025-09-11 04:48:58.782107+00
68	Nicholas	Walton	fking@example.com	Andorra	West Jeffreyland	2025-10-03 02:50:59.303138+00
69	Denise	Webster	jamessmith@example.org	Dominican Republic	South Elizabeth	2025-02-07 01:24:41.626988+00
70	Jeffery	Lyons	gary91@example.org	Georgia	New Anthonyport	2025-02-20 00:26:00.044523+00
71	Stana	Matana	danicasimic@example.net	Croatia	Daruvar	2025-07-03 00:49:30.562419+00
72	Milka	Vukman	ribaricstjepan@example.org	Croatia	Opuzen	2024-09-11 11:43:19.61556+00
73	Slavica	Bogović	ane67@example.org	Croatia	Zabok	2024-06-30 23:06:20.93944+00
74	Zoran	Nedić	zeljkagabud@example.net	Croatia	Petrinja	2025-11-01 15:59:12.149873+00
75	Dragutin	Žufika	bnovak@example.net	Croatia	Korčula	2025-12-19 08:17:06.015368+00
76	Zoran	Bradić	ante37@example.net	Croatia	Krapina	2023-07-01 13:16:38.758494+00
77	Nika	Glasnović	wherceg@example.com	Croatia	Kastav	2026-01-19 16:33:59.590267+00
78	Jacqueline	Hill	blackjames@example.org	Saint Helena	Freemanbury	2025-06-25 19:41:33.812145+00
79	Debbie	Henry	davisjeffrey@example.net	Ecuador	Elizabethstad	2024-10-30 16:00:32.909046+00
80	Alyssa	Coleman	michael74@example.com	El Salvador	North Jennifer	2024-05-10 20:35:53.493019+00
81	Pavao	Prtenjača	katicahodak@example.net	Croatia	Kastav	2025-08-02 01:09:36.767159+00
82	Roko	Poropat	ema34@example.org	Croatia	Đurđevac	2024-04-26 07:21:39.501502+00
83	Mirko	Prpić	martinabeletic@example.org	Croatia	Rovinj	2026-03-30 13:32:04.203353+00
84	Leon	Špoljarić	aburic@example.net	Croatia	Novi Marof	2024-11-05 15:25:37.701323+00
85	Renata	Glavor	jerkovicbranko@example.org	Croatia	Ludbreg	2024-11-19 22:08:33.14604+00
86	Hrvoje	Toić	dubovecakjanja@example.net	Croatia	Čabar	2026-05-24 03:53:19.411946+00
87	Hana	Rastija	msoric@example.net	Croatia	Split	2024-12-23 16:46:54.595865+00
88	Shannon	Ramos	ntorres@example.org	New Zealand	Port Jaredborough	2024-03-16 02:01:07.727599+00
89	Christopher	Allen	moorericky@example.net	Nepal	Carterbury	2024-04-10 18:55:13.823652+00
90	Justin	Heath	mcdanielsandra@example.net	Namibia	South Danny	2024-02-01 10:25:21.41705+00
91	Janja	Jurković	brankabjelis@example.org	Croatia	Pakrac	2025-08-28 18:05:47.331537+00
92	Franjo	Klarin	dcvetkovic@example.net	Croatia	Rovinj	2024-08-14 03:25:29.230915+00
93	Marta	Peruško	fmirosavljevic@example.net	Croatia	Virovitica	2024-09-15 11:43:27.498062+00
94	Nevenka	Soldo	anka13@example.net	Croatia	Slunj	2025-06-05 17:43:21.420557+00
95	Marina	Roso	suranrobert@example.org	Croatia	Omiš	2025-05-13 23:28:22.878661+00
96	Matea	Gelemanović	ftopic@example.org	Croatia	Križevci	2024-08-20 12:59:22.941423+00
97	Nevenka	Vlašić	erseknikolina@example.com	Croatia	Kaštela	2025-05-26 02:41:25.264354+00
98	Richard	Hodges	gibsonleonard@example.com	Brazil	Hancocktown	2025-05-20 17:13:29.581718+00
99	Amy	Gutierrez	aprildean@example.com	Niue	Wolfborough	2024-03-18 17:23:53.624996+00
100	David	Roberts	omartinez@example.net	South Georgia and the South Sandwich Islands	Lake Eric	2025-01-23 16:06:47.367456+00
101	Elvis	Matulin	hrastinskisime@example.org	Croatia	Vukovar	2023-10-06 19:35:08.767267+00
102	Zvonko	Dukić	sculjak@example.net	Croatia	Mali Lošinj	2025-11-30 17:30:53.550326+00
103	Boris	Jakovac	jrahija@example.com	Croatia	Vrbovec	2025-03-17 20:32:45.937093+00
104	Pero	Deže	karlovicsasa@example.com	Croatia	Vrgorac	2025-10-10 05:22:14.648926+00
105	Marina	Adžijević	nenad49@example.net	Croatia	Varaždinske Toplice	2023-11-09 22:12:03.166146+00
106	Dragutin	Paradi	nina88@example.com	Croatia	Vrgorac	2024-05-17 16:24:52.675872+00
107	Kate	Zmaić	goranmaricevic@example.org	Croatia	Bjelovar	2024-05-13 17:43:03.0799+00
108	Thomas	Mcintyre	qhughes@example.net	Canada	Hannaberg	2024-12-01 11:26:11.659647+00
109	Brittany	Kane	dgarcia@example.org	Saint Helena	South Monica	2026-04-27 21:46:15.442885+00
110	Charles	Harrington	matthew61@example.com	Timor-Leste	Finleyfort	2026-01-10 23:50:45.712787+00
111	Anđa	Stolnik	ilickarlo@example.net	Croatia	Ilok	2025-08-26 08:28:11.266484+00
112	Željka	Bukvić	modricjelena@example.net	Croatia	Vodice	2023-07-01 19:46:46.121496+00
113	Nika	Birtić	sandra56@example.org	Croatia	Opatija	2024-08-24 14:23:08.782281+00
114	Mateo	Gegić	julijanabosnjak@example.net	Croatia	Pleternica	2025-06-17 15:07:36.777063+00
115	Dario	Sakač	lucijanimac@example.net	Croatia	Nova Gradiška	2024-03-05 20:56:36.569382+00
116	Andrea	Novak	matej82@example.org	Croatia	Vrlika	2024-06-12 17:58:53.543676+00
117	Ivan	Kolić	qvucin@example.com	Croatia	Gospić	2026-05-30 03:21:07.315603+00
118	Melissa	Rodriguez	karmstrong@example.com	Reunion	Andrewfurt	2024-03-26 20:37:58.683392+00
119	Ashlee	Jennings	lozanojulie@example.com	Singapore	New Laurie	2024-01-26 01:46:09.253268+00
120	James	King	courtneyberger@example.net	Armenia	Kristinaton	2025-02-24 03:45:36.705578+00
121	Nikola	Darojković	kokanovicnika@example.net	Croatia	Đurđevac	2024-01-06 02:54:08.97484+00
122	Tomislav	Puškarić	dominik84@example.org	Croatia	Vodnjan	2025-11-19 17:38:40.088871+00
123	Bruno	Kokanović	vedran17@example.org	Croatia	Slavonski Brod	2026-04-24 02:52:19.861882+00
124	Matej	Šarić	xraspor@example.org	Croatia	Beli Manastir	2024-03-15 21:05:12.620008+00
125	Ika	Mušćet	mate49@example.com	Croatia	Daruvar	2025-06-08 12:54:41.063385+00
126	Boris	Barac	joso31@example.net	Croatia	Vodnjan	2025-07-07 06:58:05.079185+00
127	Luka	Matulić	dolinarbara@example.org	Croatia	Novska	2023-10-05 08:11:54.063306+00
128	Jimmy	Medina	qchavez@example.net	Qatar	Matthewsberg	2026-01-25 06:31:11.08784+00
129	Diana	Bass	rcrosby@example.org	Portugal	Jeffmouth	2026-04-06 15:33:39.64531+00
130	Melissa	Garcia	amy50@example.com	Falkland Islands (Malvinas)	North Stacy	2025-11-19 04:31:45.158207+00
131	Dragica	Vidas	lovretriplat@example.net	Croatia	Buje	2025-10-09 05:06:11.531613+00
132	Mara	Cvetnić	bozicasurina@example.net	Croatia	Pag	2024-01-22 17:28:43.404022+00
133	Lucija	Kupsjak	tomislavsladonja@example.org	Croatia	Varaždin	2026-05-13 07:48:31.919877+00
134	Ivana	Radelić	valter21@example.net	Croatia	Donji Miholjac	2023-06-16 09:19:54.269879+00
135	Tomo	Ivančan	anica24@example.org	Croatia	Skradin	2024-09-03 08:39:47.482473+00
136	Gordana	Škugor	orsulicandrija@example.com	Croatia	Nin	2024-12-03 04:07:57.560471+00
137	Jozo	Bebić	anton00@example.com	Croatia	Metković	2025-06-20 21:02:36.660491+00
138	Tracy	Browning	lammarc@example.org	Bahrain	West Claudia	2025-03-02 12:02:40.820706+00
139	Jennifer	James	shawn96@example.org	South Africa	Port Dianaside	2025-07-28 22:40:28.844678+00
140	Jason	Hayes	robertwilcox@example.com	Israel	West Ronaldview	2024-07-14 05:38:39.743255+00
141	Jasminka	Vukušić	fbogadi@example.org	Croatia	Mursko Središće	2023-09-13 21:55:38.916405+00
142	Patrik	Mamula	erikbjelis@example.net	Croatia	Prelog	2023-10-12 00:53:45.208623+00
143	Ružica	Viljevac	dsalic@example.com	Croatia	Krk	2023-09-21 14:57:31.125003+00
144	David	Herceg	marinpapak@example.org	Croatia	Križevci	2025-12-12 09:34:01.37666+00
145	Slavica	Ciganović	goran36@example.net	Croatia	Pazin	2026-03-14 02:56:07.078023+00
146	Zoran	Zeba	ankica24@example.net	Croatia	Vrbovec	2024-06-06 11:00:34.940632+00
147	Ana	Gelemanović	franvaljetic@example.com	Croatia	Dubrovnik	2025-08-20 00:00:58.948305+00
148	Teresa	Davis	nicholaschavez@example.org	Heard Island and McDonald Islands	Jennifershire	2025-03-14 09:36:32.529201+00
149	Nicole	Moore	craigjoseph@example.net	Jamaica	Lawsonchester	2024-03-25 10:05:25.974716+00
150	Kari	Wilson	rrodriguez@example.net	Nauru	Roseport	2023-07-19 20:53:55.164572+00
151	Valentina	Smolić	andraseklara@example.com	Croatia	Solin	2023-10-28 11:26:51.558551+00
152	Marica	Klarić	hana07@example.net	Croatia	Đurđevac	2023-10-19 15:46:41.256171+00
153	Dragan	Ćurić	darkoradjenovic@example.net	Croatia	Crikvenica	2024-08-08 04:26:14.656796+00
154	Patrik	Bašnec	dbalic@example.org	Croatia	Otok	2024-09-12 11:33:16.675232+00
155	Veronika	Čop	hklaric@example.com	Croatia	Zadar	2024-05-20 23:03:55.099888+00
156	Vedran	Stolnik	xvucin@example.org	Croatia	Valpovo	2023-09-24 02:27:28.858092+00
157	Željka	Seršić	fpopovic@example.com	Croatia	Slatina	2024-06-06 02:49:16.945088+00
158	Mason	Jackson	schmidtjames@example.com	Guernsey	East Curtis	2024-03-06 13:48:48.818294+00
159	Glenn	Hernandez	thompsonkendra@example.com	Kyrgyz Republic	Maldonadoshire	2025-05-04 15:28:54.351978+00
160	Valerie	Morris	edward17@example.com	Norfolk Island	Laurashire	2023-07-31 15:43:10.304373+00
161	David	Borojević	antonio70@example.org	Croatia	Trogir	2024-04-09 15:53:26.38839+00
162	Lovro	Branković	lnisevic@example.net	Croatia	Nin	2026-02-20 04:05:12.47122+00
163	Goran	Ugrinić	nevenkasolomun@example.com	Croatia	Zabok	2023-08-06 21:39:20.058301+00
164	Eva	Lešić	petriclovro@example.org	Croatia	Ivanec	2025-07-14 11:04:17.933599+00
165	Aldo	Popović	saramamula@example.com	Croatia	Makarska	2025-09-25 16:51:46.622952+00
166	Matej	Smoković	tomiclovro@example.com	Croatia	Kraljevica	2023-09-11 15:47:41.708491+00
167	Matej	Markovac	maria92@example.com	Croatia	Ozalj	2025-05-27 05:44:20.106912+00
168	Sabrina	Collins	tanderson@example.org	Georgia	Schneidermouth	2025-11-07 03:05:36.626182+00
169	Elizabeth	Calderon	lucasrodney@example.com	Andorra	Kyleborough	2024-06-08 13:10:36.193931+00
170	Katie	Lee	ericphillips@example.org	Madagascar	Lake Matthewberg	2025-03-15 12:30:08.803511+00
171	Jasminka	Fabijanić	zoranzanoski@example.net	Croatia	Sinj	2024-09-21 16:09:56.300516+00
172	Zdenka	Mahnet	alenstancin@example.com	Croatia	Ilok	2025-01-05 05:35:10.616254+00
173	Mirjana	Odobašić	slavicavrban@example.net	Croatia	Novalja	2025-09-20 04:41:11.758747+00
174	Slavko	Marić	meterovic@example.net	Croatia	Velika Gorica	2024-02-29 00:57:00.041799+00
175	Lovre	Pandurić	elvis18@example.org	Croatia	Čabar	2025-09-13 06:26:33.052015+00
176	Marta	Mraović	zoranmiocic@example.org	Croatia	Šibenik	2024-10-06 09:59:04.668817+00
177	Ruža	Barbieri	zbijelic@example.net	Croatia	Imotski	2024-07-27 05:39:50.717834+00
178	Christopher	Walker	sarah52@example.org	Argentina	Samanthafort	2025-07-01 19:20:43.941462+00
179	Dominic	Thornton	fgilbert@example.org	Equatorial Guinea	Port Edward	2026-03-26 07:55:50.19114+00
180	Chelsea	Henderson	john10@example.org	Italy	Brownfort	2025-03-14 23:09:33.305391+00
181	Anica	Tomičić	mislavdoncevic@example.com	Croatia	Bakar	2025-04-03 18:21:55.081792+00
182	Manda	Ritoša	qgolubic@example.net	Croatia	Opatija	2026-05-03 01:18:27.386581+00
183	Božica	Poslon	martinovicboris@example.org	Croatia	Zaprešić	2024-07-13 03:22:58.633732+00
184	Pero	Baksa	tomislav15@example.org	Croatia	Solin	2025-02-26 17:01:12.4878+00
185	Robert	Kučić	baraljubicic@example.net	Croatia	Šibenik	2025-05-04 10:19:18.6874+00
186	Zoran	Žuvela	ezelic@example.net	Croatia	Sveti Ivan Zelina	2023-10-25 20:48:05.911189+00
187	Mislav	Žugec	sbatrac@example.org	Croatia	Supetar	2024-01-04 16:03:34.647542+00
188	Bobby	Mahoney	ihays@example.com	El Salvador	Port Deborahport	2024-06-25 05:59:43.495897+00
189	Kimberly	Glenn	joshua56@example.com	Samoa	Klinefurt	2024-06-05 14:17:12.131019+00
190	Jacob	Holt	sandra84@example.org	Saint Lucia	Millerburgh	2025-01-17 19:02:18.655291+00
191	Nevenka	Burić	kunacmario@example.com	Croatia	Nin	2025-03-21 09:51:18.842555+00
192	Štefanija	Filipčić	cljubic@example.org	Croatia	Petrinja	2026-05-28 19:11:28.706499+00
193	Martina	Triplat	borosakmartin@example.net	Croatia	Kutina	2024-12-13 07:18:44.184601+00
194	Pero	Vretenar	ankicadominkovic@example.net	Croatia	Biograd na Moru	2023-10-16 10:03:06.656539+00
195	Maja	Žuvela	sanja69@example.org	Croatia	Pula	2024-10-05 02:17:07.164124+00
196	Slavica	Mamić	esuran@example.net	Croatia	Opatija	2024-07-06 04:19:51.964648+00
197	Nada	Tušek	mare10@example.net	Croatia	Novska	2024-12-18 09:50:16.800325+00
198	Robin	Wilson	jane39@example.com	Puerto Rico	Gonzalezberg	2025-12-20 13:33:26.298552+00
199	Shannon	Roach	zosborn@example.net	Tanzania	Elizabethland	2025-01-22 17:58:28.351991+00
200	Kelly	Evans	jenniferho@example.net	China	Williamville	2026-05-14 12:51:07.106517+00
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.employees (id, first_name, last_name, email, manager_id, department, salary, hired_at) FROM stdin;
1	Laura	Young	ceo@tutor.example	\N	Executive	24028.06	2013-11-17
2	Michael	Armstrong	vp0@tutor.example	1	Operations	11414.63	2017-10-23
3	Tonya	Anderson	vp1@tutor.example	1	Marketing	11287.62	2019-01-23
4	Cameron	Sanders	vp2@tutor.example	1	Sales	9823.25	2018-07-23
5	Timothy	Jenkins	vp3@tutor.example	1	Engineering	10579.33	2017-08-20
6	Bailey	Martinez	mgr0@tutor.example	4	Marketing	5546.25	2020-09-04
7	Charles	Owens	mgr1@tutor.example	3	Operations	5656.15	2021-06-23
8	David	Calderon	mgr2@tutor.example	3	Sales	4993.25	2021-08-12
9	Briana	Saunders	mgr3@tutor.example	4	Sales	6864.48	2019-12-04
10	Wesley	Oneill	mgr4@tutor.example	3	Support	4786.24	2022-09-25
11	April	Torres	mgr5@tutor.example	3	Engineering	4085.49	2020-01-21
12	Sarah	Perez	mgr6@tutor.example	3	Marketing	6139.46	2023-03-14
13	April	Campbell	mgr7@tutor.example	2	Marketing	5450.54	2019-09-22
14	James	Huber	mgr8@tutor.example	3	Marketing	5730.32	2020-07-03
15	Colleen	Mendez	mgr9@tutor.example	3	Engineering	6296.20	2019-10-13
16	Danielle	Vargas	rep0@tutor.example	6	Sales	3056.84	2023-09-24
17	George	Weber	rep1@tutor.example	9	Engineering	3108.22	2025-01-05
18	Matthew	Bradshaw	rep2@tutor.example	14	Marketing	1600.44	2021-07-28
19	Michelle	Miller	rep3@tutor.example	9	Sales	2412.92	2025-03-14
20	Kelli	Baker	rep4@tutor.example	13	Operations	3475.78	2022-04-01
21	Ashley	Montgomery	rep5@tutor.example	15	Support	3400.08	2021-07-12
22	Pamela	Gardner	rep6@tutor.example	13	Operations	3130.01	2023-12-22
23	Kevin	Sanchez	rep7@tutor.example	14	Marketing	3161.14	2024-08-20
24	Richard	Chavez	rep8@tutor.example	14	Marketing	3294.42	2024-02-29
25	Eric	Perry	rep9@tutor.example	13	Marketing	2018.38	2023-04-07
26	Matthew	Thomas	rep10@tutor.example	9	Support	3031.63	2024-11-07
27	Luis	Travis	rep11@tutor.example	14	Marketing	2753.50	2022-10-15
28	Raymond	Hodges	rep12@tutor.example	10	Marketing	1654.97	2023-06-20
29	Daniel	Allen	rep13@tutor.example	10	Engineering	2043.43	2021-11-24
30	Shannon	Thomas	rep14@tutor.example	11	Operations	1661.16	2021-08-10
31	Sonia	Lin	rep15@tutor.example	8	Engineering	2266.07	2023-01-29
32	Sydney	Barrera	rep16@tutor.example	8	Engineering	1628.46	2024-08-29
33	Sarah	Griffith	rep17@tutor.example	12	Support	2585.22	2022-03-02
34	Erik	Ferrell	rep18@tutor.example	12	Sales	1913.67	2023-04-11
35	Natasha	Jimenez	rep19@tutor.example	12	Marketing	3309.68	2021-10-07
36	Phillip	Bryant	rep20@tutor.example	15	Sales	3213.46	2022-05-15
37	Brandy	Williams	rep21@tutor.example	15	Marketing	2453.96	2022-07-14
38	Carla	Cameron	rep22@tutor.example	11	Support	3006.95	2024-02-05
39	Justin	Smith	rep23@tutor.example	12	Operations	2995.03	2021-11-02
40	Dennis	Baker	rep24@tutor.example	14	Operations	3295.62	2022-11-14
41	Richard	Williams	rep25@tutor.example	13	Engineering	2045.87	2021-08-11
42	Anna	Cox	rep26@tutor.example	13	Sales	2277.71	2022-07-24
43	Paul	Cole	rep27@tutor.example	12	Engineering	3181.01	2023-08-10
44	Marcia	Hanson	rep28@tutor.example	8	Operations	2568.25	2023-11-07
45	David	Davis	rep29@tutor.example	12	Operations	2628.78	2022-11-25
46	Valerie	Grant	rep30@tutor.example	6	Sales	2785.50	2022-11-14
47	Drew	Morrison	rep31@tutor.example	8	Marketing	1863.46	2023-01-05
48	Billy	Williams	rep32@tutor.example	10	Marketing	2154.71	2024-04-05
49	Linda	Stone	rep33@tutor.example	13	Support	2175.00	2022-01-01
50	Patricia	Taylor	rep34@tutor.example	12	Support	3004.02	2025-02-17
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.orders (id, customer_id, employee_id, order_date, status, total_amount) FROM stdin;
1	108	\N	2025-09-23 22:13:24.1203+00	delivered	3832.15
2	5	4	2025-10-21 02:36:40.189291+00	cancelled	4806.92
3	90	\N	2026-01-10 18:09:39.12701+00	delivered	3160.68
4	167	\N	2026-04-03 08:06:42.574921+00	delivered	4523.92
5	64	\N	2026-01-02 10:30:48.214438+00	delivered	2413.08
6	40	\N	2025-12-01 21:04:01.088398+00	delivered	4499.46
7	30	14	2025-12-02 18:05:49.312871+00	delivered	2613.81
8	66	11	2025-11-25 11:56:37.479739+00	shipped	2523.17
9	30	11	2025-12-22 04:31:28.281155+00	cancelled	6179.89
10	28	20	2025-11-20 00:51:36.406492+00	shipped	7410.14
11	97	46	2025-06-05 15:54:04.01263+00	delivered	9078.93
12	152	41	2025-09-28 13:37:56.407317+00	delivered	2471.18
13	78	39	2025-07-09 14:49:59.094966+00	processing	2185.25
14	145	23	2025-10-29 17:21:27.315842+00	shipped	4726.89
15	170	33	2025-09-19 23:05:44.171494+00	shipped	2390.53
16	4	32	2026-04-23 20:26:32.232362+00	delivered	5922.56
17	93	30	2026-04-14 02:40:37.510129+00	processing	4803.06
18	112	\N	2026-01-15 10:00:42.861604+00	shipped	88.68
19	167	\N	2026-01-03 14:25:55.166496+00	processing	1548.66
20	138	30	2025-09-04 13:38:29.899923+00	delivered	11081.62
21	152	\N	2026-01-25 00:49:07.232972+00	pending	773.23
22	23	\N	2026-05-20 14:52:57.835006+00	delivered	8282.38
23	119	43	2025-12-27 20:49:57.784819+00	delivered	4312.33
24	8	21	2025-08-21 16:39:17.489343+00	delivered	7354.33
25	55	17	2025-06-18 08:13:57.38794+00	delivered	5953.04
26	153	18	2025-11-22 01:33:51.429197+00	shipped	1158.91
27	133	6	2025-12-08 01:21:37.323301+00	delivered	5810.89
28	105	49	2026-02-17 23:46:52.339688+00	delivered	57.22
29	122	32	2026-03-09 12:04:37.143147+00	delivered	6051.73
30	5	\N	2025-10-16 10:43:22.072849+00	delivered	467.40
31	63	38	2026-03-26 16:33:04.445541+00	delivered	521.65
32	142	28	2025-08-27 01:06:08.908485+00	cancelled	1230.57
33	141	45	2025-12-25 17:04:44.896148+00	delivered	7796.15
34	79	\N	2026-02-10 10:39:49.45537+00	delivered	8653.71
35	50	48	2025-08-08 06:26:06.666172+00	shipped	642.57
36	48	\N	2025-11-07 16:06:13.59891+00	processing	1447.96
37	71	49	2025-10-30 12:59:35.311327+00	shipped	5477.53
38	73	13	2025-10-28 09:58:29.16314+00	delivered	9399.46
39	93	\N	2025-08-13 01:19:52.003627+00	delivered	7299.61
40	137	\N	2025-11-29 20:53:41.62666+00	delivered	2000.96
41	14	45	2026-01-08 22:08:07.705797+00	pending	1536.52
42	164	32	2025-11-18 20:02:45.119456+00	delivered	3334.15
43	4	31	2026-04-05 10:44:04.854861+00	delivered	1147.02
44	88	\N	2026-02-20 06:17:52.002125+00	delivered	5346.49
45	123	\N	2026-02-12 08:43:18.676352+00	delivered	1443.94
46	126	\N	2025-12-06 00:43:05.174835+00	shipped	3622.10
47	14	\N	2025-12-21 10:39:51.81857+00	processing	9276.82
48	78	\N	2026-05-30 03:22:15.853835+00	delivered	5078.84
49	143	39	2025-11-21 07:21:02.831428+00	shipped	7876.14
50	159	\N	2025-10-15 05:13:15.980351+00	shipped	7862.50
51	116	20	2026-05-15 00:08:27.512276+00	pending	1376.27
52	110	40	2025-11-14 11:21:56.72877+00	delivered	733.00
53	26	14	2025-12-11 07:19:46.031192+00	shipped	3213.56
54	68	11	2025-12-16 02:33:55.763579+00	delivered	6278.94
55	142	\N	2026-02-01 10:34:02.241085+00	delivered	7943.16
56	116	31	2026-04-12 11:42:56.949067+00	delivered	9447.18
57	60	\N	2026-02-03 05:19:14.320219+00	delivered	2651.75
58	117	\N	2026-03-20 02:41:26.72853+00	delivered	2194.51
59	68	41	2025-09-04 03:24:03.626413+00	shipped	6552.64
60	51	35	2025-11-23 10:16:19.645631+00	delivered	5256.50
61	39	10	2026-05-15 05:51:19.474604+00	delivered	1808.76
62	43	39	2025-09-09 11:46:07.178414+00	processing	3136.09
63	146	29	2025-09-16 14:38:15.225904+00	delivered	4619.79
64	78	18	2026-05-09 10:54:06.833272+00	shipped	2387.56
65	127	39	2026-05-24 08:19:24.859175+00	delivered	3639.44
66	111	39	2026-03-08 05:59:38.819592+00	delivered	690.52
67	24	\N	2026-02-12 01:03:28.769905+00	shipped	4951.18
68	148	2	2026-02-06 16:32:34.665876+00	cancelled	3606.06
69	173	37	2025-11-25 04:32:57.083332+00	delivered	10624.78
70	45	42	2025-11-21 19:54:25.957884+00	delivered	9109.97
71	72	\N	2025-12-21 07:09:54.916361+00	shipped	2139.99
72	163	6	2026-05-06 21:32:24.724672+00	delivered	3148.90
73	105	43	2026-02-18 04:00:08.275904+00	delivered	6246.22
74	42	45	2025-09-12 16:45:29.346194+00	delivered	1549.00
75	170	49	2025-12-26 01:01:32.101964+00	shipped	2924.75
76	117	\N	2025-12-14 23:32:47.102728+00	delivered	5839.96
77	30	26	2026-04-22 18:05:12.404063+00	pending	2254.70
78	1	35	2025-10-21 16:26:32.54609+00	delivered	1811.74
79	14	\N	2025-10-03 15:25:59.828615+00	delivered	4071.99
80	128	49	2026-03-08 22:33:42.933838+00	delivered	2619.92
81	69	19	2025-07-23 02:02:24.309757+00	delivered	5872.48
82	125	\N	2025-06-14 22:48:37.019428+00	cancelled	4009.24
83	156	46	2026-05-14 12:06:58.785982+00	delivered	933.82
84	142	\N	2025-06-28 10:49:07.048392+00	delivered	2999.46
85	58	8	2026-05-03 01:42:44.015006+00	delivered	1320.63
86	31	10	2026-01-25 04:09:32.822614+00	delivered	7310.72
87	75	18	2026-02-27 13:03:19.738237+00	delivered	9599.40
88	124	16	2025-08-16 17:49:21.209969+00	delivered	3582.40
89	38	39	2026-03-28 23:41:29.328353+00	shipped	3754.16
90	35	18	2025-09-06 14:44:59.729052+00	processing	4645.18
91	107	33	2025-12-21 20:34:50.274205+00	delivered	2732.88
92	1	\N	2025-09-06 19:02:02.916766+00	delivered	3523.92
93	151	43	2025-07-09 11:31:10.398821+00	delivered	4540.26
94	39	31	2026-02-25 04:32:16.956141+00	delivered	588.20
95	142	25	2025-08-25 23:33:16.984602+00	delivered	3706.45
96	83	45	2025-06-18 03:03:47.271094+00	delivered	10370.15
97	99	\N	2026-04-26 04:41:34.545233+00	processing	11788.72
98	12	31	2025-08-21 00:14:56.564396+00	processing	9824.95
99	98	43	2025-08-23 15:03:17.848945+00	processing	9956.44
100	167	32	2025-07-06 04:22:36.541332+00	cancelled	8459.03
101	33	38	2025-09-28 05:20:24.678873+00	delivered	2042.05
102	26	29	2025-11-19 03:02:41.379668+00	delivered	3813.78
103	117	\N	2026-02-03 09:13:51.685866+00	delivered	2704.35
104	168	5	2025-07-19 19:04:06.906943+00	delivered	6632.65
105	68	45	2026-05-17 20:48:20.104377+00	delivered	3223.10
106	21	44	2026-05-22 18:11:46.164889+00	pending	7125.24
220	28	\N	2025-10-29 07:34:39.604728+00	shipped	3848.90
107	98	41	2025-07-27 06:32:20.845545+00	processing	4497.85
108	125	3	2026-01-24 01:10:01.653361+00	shipped	7151.06
109	61	19	2026-04-17 05:36:35.316881+00	cancelled	875.28
110	24	7	2025-11-20 07:56:04.092607+00	processing	3798.99
111	26	45	2026-01-23 04:31:53.757262+00	delivered	1897.02
112	8	\N	2026-03-02 16:12:01.741242+00	processing	1797.57
113	76	28	2025-09-12 11:59:11.81773+00	delivered	10070.84
114	136	44	2025-09-11 19:56:52.575817+00	processing	5474.95
115	44	\N	2025-06-21 04:40:14.1151+00	shipped	6706.87
116	98	16	2026-03-07 08:31:27.677675+00	delivered	6621.97
117	150	\N	2026-01-23 19:57:34.82897+00	delivered	878.24
118	66	43	2025-08-23 09:39:07.520685+00	delivered	4900.45
119	120	44	2026-02-24 09:12:51.569989+00	shipped	7150.64
120	19	23	2026-04-06 03:52:53.198482+00	cancelled	3645.79
121	77	28	2025-06-13 05:00:46.920324+00	shipped	9082.15
122	117	13	2026-05-02 03:27:29.349052+00	cancelled	2144.15
123	124	\N	2025-10-30 05:08:42.06307+00	delivered	515.16
124	92	45	2026-04-01 12:18:32.357425+00	delivered	3806.16
125	169	1	2026-05-06 16:36:25.266447+00	shipped	3798.85
126	13	48	2025-06-12 20:36:43.02788+00	delivered	2818.72
127	74	15	2026-04-01 00:01:19.565192+00	shipped	6757.40
128	91	\N	2026-03-14 09:08:21.575386+00	delivered	5000.22
129	65	47	2025-08-06 15:13:42.982307+00	processing	385.72
130	175	41	2026-02-28 03:38:52.291027+00	delivered	2473.85
131	161	20	2026-04-14 04:21:22.868805+00	processing	10340.55
132	9	47	2025-09-13 07:27:48.948697+00	delivered	3062.19
133	76	27	2025-06-13 06:29:06.22254+00	delivered	4567.00
134	34	24	2025-09-16 13:42:00.21632+00	shipped	5226.12
135	70	17	2026-01-05 17:54:58.907766+00	pending	5026.76
136	124	19	2026-05-04 16:40:40.46368+00	processing	2349.30
137	87	30	2025-09-29 22:57:51.530779+00	cancelled	2904.29
138	37	15	2025-11-12 12:46:49.911237+00	pending	3094.65
139	173	36	2026-01-19 19:39:22.400587+00	delivered	1437.84
140	102	\N	2025-12-08 02:06:57.583711+00	shipped	3847.61
141	117	48	2026-04-20 09:06:17.912057+00	shipped	2144.58
142	150	41	2025-07-18 14:25:48.267422+00	pending	677.48
143	28	31	2025-11-30 17:52:22.225975+00	delivered	60.75
144	144	40	2025-09-07 05:41:23.751843+00	delivered	3828.93
145	17	30	2026-03-21 23:56:02.028851+00	pending	6190.07
146	78	8	2025-09-28 08:45:46.743119+00	delivered	2610.68
147	10	32	2026-02-21 14:52:52.645826+00	delivered	3709.93
148	61	9	2026-01-22 08:46:45.286318+00	delivered	4439.69
149	95	48	2026-02-17 01:07:28.84983+00	shipped	3021.76
150	139	48	2025-06-04 17:31:27.242904+00	processing	8450.15
151	107	32	2025-09-30 17:06:36.045494+00	shipped	6924.36
152	72	\N	2025-09-15 08:10:38.612518+00	delivered	5058.22
153	114	16	2026-01-31 21:42:14.729758+00	pending	2226.41
154	26	24	2025-08-09 03:16:15.762038+00	shipped	6947.77
155	166	26	2026-01-08 17:32:45.853878+00	delivered	748.33
156	32	30	2026-01-18 20:58:57.260321+00	delivered	5755.81
157	55	39	2025-10-25 16:29:48.707038+00	cancelled	4024.24
158	13	16	2025-11-02 19:12:34.556482+00	cancelled	11290.86
159	145	\N	2025-09-27 08:35:30.997226+00	processing	1402.84
160	142	\N	2025-10-23 23:40:24.943858+00	delivered	1410.09
161	60	10	2025-07-04 10:11:18.60189+00	processing	10259.34
162	153	\N	2026-05-24 03:16:56.452955+00	pending	3640.10
163	38	35	2025-11-20 23:18:48.938164+00	delivered	5393.83
164	45	\N	2026-05-07 09:17:10.679701+00	pending	5767.98
165	34	\N	2025-06-02 01:56:12.310715+00	processing	12006.25
166	61	2	2025-10-17 16:23:11.782924+00	delivered	310.60
167	14	\N	2025-11-09 18:02:30.923469+00	delivered	1282.90
168	30	31	2025-09-05 02:28:25.48951+00	delivered	2154.70
169	93	7	2025-09-27 23:28:54.67556+00	delivered	3389.76
170	57	3	2025-12-29 07:46:36.167182+00	processing	3222.06
171	169	30	2025-12-25 19:46:15.217159+00	shipped	8788.32
172	8	\N	2025-09-03 02:46:39.73025+00	delivered	362.58
173	103	7	2025-10-08 21:48:46.400086+00	delivered	17495.07
174	114	\N	2025-08-24 21:26:14.051826+00	delivered	11401.94
175	156	\N	2026-01-29 11:43:06.129167+00	delivered	2227.52
176	160	36	2025-11-16 13:36:22.864877+00	processing	3676.55
177	98	34	2025-07-27 22:06:17.688464+00	delivered	918.66
178	130	7	2026-02-05 04:01:20.099468+00	processing	3769.45
179	30	42	2026-05-02 17:47:28.782141+00	pending	1755.05
180	142	14	2026-04-19 20:19:10.842328+00	delivered	3733.57
181	59	30	2026-03-07 18:18:26.696601+00	delivered	3716.56
182	25	21	2026-02-06 16:59:07.203546+00	shipped	840.58
183	96	44	2026-01-18 20:51:20.669527+00	pending	928.75
184	18	\N	2026-05-09 03:27:06.050745+00	delivered	4469.81
185	111	\N	2025-10-11 19:52:01.918605+00	processing	5029.53
186	34	38	2025-08-19 05:58:37.161494+00	cancelled	4863.12
187	144	8	2026-05-15 06:03:29.718359+00	delivered	4738.02
188	171	28	2025-11-21 05:41:35.969923+00	pending	1515.86
189	14	39	2025-11-12 18:17:57.862254+00	delivered	10527.39
190	27	14	2026-05-26 17:58:54.510308+00	delivered	3822.49
191	124	\N	2025-10-14 01:10:16.501623+00	delivered	3900.11
192	143	49	2026-02-10 23:06:34.205032+00	delivered	4812.99
193	58	36	2026-04-28 23:25:26.425171+00	cancelled	6134.44
194	160	42	2026-03-03 04:49:06.523376+00	shipped	3234.43
195	156	45	2026-03-19 12:09:40.228925+00	delivered	3989.56
196	47	\N	2026-03-28 03:06:27.976915+00	processing	556.22
197	87	12	2026-03-04 20:20:38.896489+00	pending	2679.64
198	145	5	2026-02-03 01:46:46.35663+00	delivered	1362.30
199	163	6	2026-01-03 04:49:55.79375+00	processing	3582.53
200	56	30	2026-03-14 03:58:04.99289+00	delivered	6240.68
201	95	21	2025-12-08 12:31:50.816583+00	processing	3423.57
202	146	4	2025-12-09 11:54:15.838673+00	delivered	6383.20
203	159	\N	2025-10-09 17:23:05.584814+00	delivered	124.16
204	114	32	2026-04-30 14:24:45.059285+00	shipped	6013.33
205	107	\N	2025-07-10 13:39:39.211421+00	processing	8175.68
206	30	8	2026-03-29 06:54:00.024416+00	delivered	2802.90
207	174	34	2026-04-25 08:33:59.310213+00	shipped	7144.68
208	12	\N	2025-08-12 10:07:24.104461+00	cancelled	2861.07
209	15	\N	2025-12-12 14:17:58.935947+00	delivered	4346.55
210	55	49	2025-07-29 16:21:31.612473+00	delivered	780.44
211	84	\N	2026-04-07 16:17:05.351057+00	delivered	5864.85
212	111	\N	2025-11-07 23:08:01.674374+00	delivered	504.46
213	59	43	2026-02-03 01:22:13.2257+00	processing	1103.48
214	19	48	2026-02-16 10:23:46.99242+00	delivered	2311.55
215	5	5	2025-11-25 03:00:51.098709+00	pending	4283.23
216	148	26	2026-04-23 21:30:49.965233+00	processing	9873.08
217	107	\N	2025-11-09 07:03:35.709921+00	delivered	7644.68
218	84	\N	2025-06-19 21:45:20.436602+00	pending	1100.54
219	118	24	2025-07-17 18:39:28.698429+00	delivered	3336.88
221	135	\N	2025-12-22 13:10:32.395607+00	pending	1449.24
222	87	\N	2025-12-20 16:20:51.686343+00	processing	1945.86
223	20	8	2026-01-31 07:23:09.084083+00	shipped	2425.75
224	50	23	2025-09-20 03:24:21.575429+00	delivered	2135.90
225	166	16	2025-06-07 12:54:00.592336+00	delivered	2482.29
226	66	\N	2025-08-31 12:34:35.285411+00	shipped	4074.30
227	168	\N	2025-05-31 16:29:54.440916+00	cancelled	7290.64
228	161	49	2025-08-18 04:08:10.071847+00	shipped	1600.48
229	149	37	2025-06-26 06:13:29.469519+00	shipped	2847.04
230	160	41	2025-11-01 08:05:42.515349+00	delivered	8585.77
231	113	\N	2026-02-10 09:28:16.696505+00	delivered	4319.05
232	78	38	2025-12-14 05:46:29.831084+00	delivered	3963.52
233	130	\N	2025-06-21 14:15:07.049986+00	delivered	262.10
234	10	\N	2026-04-22 04:34:11.405876+00	processing	6556.81
235	20	6	2026-05-25 18:18:28.797499+00	shipped	4392.77
236	130	38	2025-11-19 00:07:42.258289+00	shipped	2980.52
237	11	37	2025-09-12 10:38:01.645423+00	shipped	1089.42
238	83	33	2025-08-04 07:44:19.215569+00	delivered	3675.53
239	16	22	2025-07-19 01:12:08.986586+00	cancelled	353.98
240	22	12	2026-01-19 21:31:11.067839+00	delivered	3488.33
241	113	34	2026-02-20 22:50:32.195942+00	shipped	3372.46
242	41	19	2026-05-17 14:21:08.02625+00	delivered	7537.46
243	87	4	2025-10-14 08:30:00.414899+00	processing	7267.92
244	166	22	2026-04-21 03:16:55.267809+00	delivered	3557.16
245	174	17	2025-11-10 09:50:03.881633+00	processing	1449.00
246	169	39	2026-04-30 13:16:34.356465+00	pending	2889.82
247	86	\N	2025-10-15 11:06:28.646241+00	shipped	1621.69
248	90	42	2025-06-28 21:31:03.831407+00	shipped	7392.30
249	101	\N	2026-05-17 17:31:25.55133+00	processing	1086.97
250	22	25	2026-04-15 00:11:36.913218+00	shipped	2766.96
251	85	43	2025-07-18 03:49:20.209226+00	processing	3269.29
252	135	\N	2026-04-09 19:07:52.524971+00	shipped	4835.78
253	131	24	2025-07-12 21:58:31.540865+00	delivered	2430.89
254	55	50	2026-05-28 05:07:19.601131+00	delivered	4480.11
255	58	10	2025-10-21 03:31:23.47573+00	delivered	129.29
256	26	35	2025-07-16 02:21:34.415009+00	processing	7448.32
257	135	\N	2026-05-23 01:19:42.782585+00	delivered	3375.91
258	159	\N	2026-03-31 11:54:41.206524+00	delivered	957.38
259	42	\N	2026-03-02 18:33:10.163338+00	shipped	4766.39
260	160	11	2026-05-22 23:16:48.151765+00	processing	3243.06
261	12	44	2025-11-15 16:38:47.876974+00	processing	4024.12
262	114	49	2026-02-17 05:28:14.728608+00	processing	5917.05
263	115	\N	2025-11-01 11:52:12.264497+00	delivered	788.04
264	121	13	2025-10-16 02:42:43.372755+00	delivered	7902.51
265	147	30	2025-08-22 11:14:44.324312+00	processing	1846.10
266	98	27	2025-11-14 19:47:46.310085+00	cancelled	5396.39
267	52	9	2025-07-26 05:49:20.222149+00	pending	6679.23
268	14	24	2025-08-07 10:14:23.840839+00	shipped	7100.11
269	27	34	2026-04-15 05:55:49.311643+00	pending	639.12
270	73	\N	2026-03-06 04:09:59.608478+00	delivered	9701.88
271	116	10	2025-06-11 08:28:29.301243+00	processing	2529.04
272	24	15	2026-01-26 17:12:00.078674+00	processing	6783.60
273	90	27	2026-01-10 04:20:05.310165+00	delivered	2230.33
274	129	25	2026-05-07 12:54:09.20236+00	cancelled	4213.72
275	96	\N	2026-04-20 07:11:18.921248+00	delivered	1244.08
276	26	42	2025-08-26 11:41:18.708376+00	delivered	3760.67
277	38	\N	2025-06-24 03:55:17.257685+00	delivered	4169.43
278	121	9	2026-01-02 12:26:14.660751+00	processing	693.64
279	121	1	2025-11-09 15:27:38.867166+00	pending	1967.80
280	5	\N	2026-01-31 00:51:48.494536+00	processing	1526.93
281	141	39	2026-04-14 03:40:13.004007+00	shipped	6882.31
282	29	16	2025-08-27 23:20:47.000183+00	delivered	8122.44
283	13	\N	2025-06-15 17:50:02.81188+00	shipped	2003.58
284	160	8	2025-11-06 21:54:29.555928+00	processing	1589.52
285	128	2	2025-12-13 17:28:13.793102+00	shipped	10000.91
286	148	\N	2026-03-02 02:49:46.653111+00	delivered	5311.96
287	110	\N	2026-03-10 00:51:10.821765+00	delivered	2105.77
288	147	43	2025-07-20 18:27:37.348109+00	shipped	1133.97
289	135	5	2026-05-28 10:42:10.675678+00	cancelled	8908.08
290	140	33	2025-08-24 02:40:09.177799+00	shipped	8184.40
291	100	3	2026-04-30 06:58:55.2454+00	shipped	6310.82
292	96	\N	2025-12-27 00:06:37.766778+00	delivered	6011.78
293	18	47	2025-12-27 12:04:16.272177+00	shipped	2988.24
294	27	48	2026-03-08 17:57:00.42121+00	processing	430.71
295	35	\N	2026-03-25 11:48:36.155241+00	shipped	189.82
296	165	\N	2025-08-25 02:42:34.082784+00	processing	2577.52
297	119	31	2026-04-15 15:08:08.540642+00	shipped	6685.50
298	35	\N	2026-05-25 14:26:10.586175+00	processing	1773.54
299	118	\N	2025-12-06 23:13:37.90916+00	delivered	3933.87
300	52	21	2025-10-28 15:14:06.254947+00	pending	5901.74
301	132	35	2025-09-08 01:59:55.628855+00	delivered	8285.89
302	10	13	2025-12-19 22:07:22.679464+00	delivered	2863.25
303	13	22	2026-01-01 16:28:39.176493+00	delivered	1375.68
304	95	26	2026-02-23 02:45:30.437946+00	processing	4371.16
305	99	12	2025-08-02 13:14:27.786839+00	delivered	8238.43
306	128	34	2026-02-02 11:49:34.450512+00	delivered	1975.95
307	22	6	2025-12-19 14:31:08.721872+00	delivered	6748.53
308	47	21	2025-06-16 17:02:25.070127+00	delivered	3908.47
309	84	20	2025-10-03 09:07:23.857619+00	delivered	2089.10
310	110	\N	2026-01-20 13:13:11.237437+00	delivered	1909.71
311	115	\N	2025-10-16 19:10:32.111799+00	pending	7244.43
312	91	28	2025-12-08 03:22:58.322788+00	delivered	2412.24
313	15	\N	2026-02-08 21:44:16.584033+00	shipped	2702.25
314	94	48	2025-10-26 16:46:03.062789+00	shipped	4895.42
315	8	\N	2025-09-17 02:48:58.048335+00	shipped	7524.25
316	113	\N	2025-08-05 17:54:16.388277+00	delivered	1909.90
317	166	25	2025-12-13 01:24:56.226319+00	pending	4254.32
318	9	44	2025-08-26 14:20:05.525021+00	delivered	6867.84
319	95	49	2025-08-20 21:22:54.422264+00	delivered	6580.29
320	36	26	2026-04-08 19:03:58.474762+00	delivered	2623.31
321	72	\N	2025-07-22 07:25:06.039544+00	delivered	10497.05
322	48	25	2025-11-15 16:49:58.719656+00	pending	1505.01
323	31	\N	2025-06-20 15:10:59.28721+00	delivered	6794.50
324	115	\N	2025-10-28 07:29:50.572919+00	shipped	1675.48
325	126	\N	2025-10-29 17:04:24.790126+00	delivered	2044.76
326	19	46	2025-12-10 03:50:47.756656+00	delivered	6375.98
327	23	21	2025-10-19 10:51:13.380588+00	shipped	4944.17
328	17	19	2025-08-31 17:17:46.269587+00	pending	161.16
329	41	45	2025-09-28 05:04:18.100366+00	shipped	3696.59
330	93	8	2025-06-28 11:10:40.792045+00	cancelled	487.39
331	36	\N	2025-11-10 20:47:20.118972+00	delivered	8876.49
332	93	24	2025-10-13 02:50:30.498617+00	delivered	774.56
333	142	\N	2025-12-12 05:19:05.212728+00	pending	3757.85
334	17	46	2026-03-29 12:26:31.179271+00	processing	5156.30
335	135	27	2025-06-18 09:49:23.799281+00	processing	8195.54
336	19	\N	2025-10-15 08:13:46.21351+00	delivered	4719.43
337	19	44	2026-01-06 13:04:57.107569+00	shipped	7217.06
338	33	50	2025-06-14 00:43:47.727556+00	shipped	8113.17
339	151	\N	2025-06-26 04:04:31.835388+00	cancelled	2600.32
340	111	4	2026-03-20 11:26:23.119746+00	processing	1952.78
341	133	\N	2025-12-31 04:40:59.34624+00	delivered	759.16
342	83	15	2026-01-30 19:50:22.867245+00	delivered	9183.04
343	133	6	2025-08-17 20:22:49.082539+00	delivered	6318.48
344	163	18	2025-08-14 21:08:13.820724+00	delivered	1432.15
345	78	6	2026-04-26 20:53:51.481809+00	shipped	2013.63
346	44	38	2025-09-18 07:44:20.483204+00	delivered	4617.23
347	169	39	2026-04-27 14:05:24.754966+00	delivered	3616.09
348	145	\N	2025-08-15 22:43:17.945299+00	pending	2442.62
349	21	\N	2025-08-07 23:46:03.659858+00	shipped	8478.71
350	148	\N	2026-02-25 09:39:33.232162+00	delivered	6874.54
351	147	41	2026-02-27 09:01:46.604721+00	delivered	3823.57
352	161	42	2026-03-02 02:20:52.111868+00	cancelled	1214.64
353	124	\N	2026-04-29 13:50:18.589845+00	processing	929.63
354	104	\N	2026-02-08 15:45:31.052653+00	delivered	6055.27
355	16	\N	2026-02-11 15:07:55.368591+00	delivered	7362.56
356	119	\N	2025-10-22 10:50:49.199495+00	shipped	9788.59
357	81	21	2025-08-25 23:58:59.888623+00	processing	10307.74
358	89	9	2025-09-25 01:15:55.927204+00	processing	1941.96
359	132	21	2025-09-10 23:17:40.368516+00	delivered	4166.10
360	32	\N	2025-11-16 21:06:18.702783+00	delivered	3912.93
361	25	\N	2026-01-22 12:36:04.063792+00	pending	5783.53
362	158	11	2025-09-20 05:37:16.601759+00	processing	5250.44
363	148	13	2025-10-08 22:37:26.263442+00	processing	4937.74
364	128	30	2026-04-18 00:34:59.718333+00	delivered	7480.37
365	79	6	2025-11-16 18:56:43.314214+00	pending	766.69
366	130	16	2026-03-19 19:21:48.191186+00	delivered	8126.07
367	91	\N	2026-02-18 10:34:10.411872+00	delivered	4783.04
368	153	42	2026-03-04 18:19:20.314459+00	shipped	1103.34
369	74	7	2025-09-24 13:09:13.226493+00	delivered	3044.82
370	68	49	2025-08-12 18:37:56.615904+00	delivered	6915.44
371	12	37	2025-09-21 21:03:53.538074+00	shipped	7727.02
372	93	5	2025-06-16 06:47:46.323061+00	delivered	1343.25
373	116	18	2026-04-11 04:25:33.223854+00	processing	7088.08
374	160	8	2026-02-25 07:42:21.624528+00	delivered	2264.66
375	25	22	2025-06-05 12:14:43.133843+00	shipped	1004.20
376	94	13	2025-12-18 16:15:42.936448+00	shipped	1088.55
377	103	3	2025-12-29 21:32:56.456045+00	delivered	4482.81
378	86	34	2026-02-17 13:31:02.636401+00	delivered	3947.04
379	156	9	2025-09-15 09:39:01.086118+00	delivered	7514.16
380	157	26	2025-08-10 05:50:08.29288+00	cancelled	665.90
381	77	33	2025-08-22 14:21:13.055868+00	processing	2352.49
382	137	37	2025-12-24 16:42:13.22797+00	delivered	4636.82
383	5	44	2025-08-28 08:04:33.254032+00	delivered	11437.03
384	107	47	2025-12-17 16:51:57.029013+00	pending	5732.29
385	162	\N	2026-05-10 04:14:57.573428+00	delivered	10537.39
386	168	50	2025-09-30 21:04:22.994369+00	shipped	3205.25
387	59	38	2026-03-05 09:30:05.736947+00	delivered	8073.96
388	135	40	2025-11-25 01:12:03.073575+00	processing	2313.18
389	98	\N	2026-02-18 20:36:03.095139+00	shipped	7236.29
390	9	45	2026-02-24 17:10:11.466114+00	delivered	2379.45
391	5	27	2025-11-14 21:34:55.045174+00	delivered	4757.24
392	53	50	2026-02-22 05:22:16.031928+00	shipped	14034.69
393	121	48	2025-10-06 05:09:26.369544+00	processing	4354.48
394	36	36	2025-07-20 16:54:30.337367+00	delivered	7760.50
395	170	25	2025-12-16 04:57:34.207369+00	delivered	5297.79
396	45	35	2025-08-05 19:23:02.979571+00	delivered	3563.77
397	91	47	2026-04-20 10:01:17.671981+00	shipped	3718.64
398	68	13	2026-05-27 07:00:14.534131+00	cancelled	1496.38
399	72	15	2026-05-15 04:58:27.950661+00	pending	722.53
400	77	46	2025-12-07 22:50:11.595581+00	delivered	6392.69
401	126	23	2026-04-02 01:08:18.938294+00	shipped	3550.25
402	71	\N	2025-06-26 17:37:41.170679+00	shipped	659.74
403	140	26	2026-03-25 08:25:17.007923+00	processing	7850.92
404	38	\N	2025-06-17 07:19:51.929856+00	delivered	4231.06
405	21	29	2025-06-01 22:01:28.662548+00	shipped	8598.07
406	123	\N	2025-07-19 19:16:59.930129+00	processing	3551.09
407	70	45	2026-01-15 22:38:41.398589+00	delivered	3670.18
408	28	38	2025-06-24 09:51:22.391599+00	delivered	4939.14
409	13	34	2025-07-24 17:57:18.681661+00	delivered	4015.72
410	60	\N	2025-08-18 11:18:34.96165+00	delivered	3635.69
411	121	\N	2025-11-13 03:20:12.421612+00	processing	1692.96
412	2	11	2025-06-21 15:57:24.443707+00	delivered	5985.66
413	122	13	2026-01-18 12:14:28.809843+00	processing	1249.36
414	74	42	2026-05-06 16:26:29.176107+00	delivered	3048.10
415	23	15	2026-04-28 23:01:32.690683+00	shipped	2975.55
416	10	12	2026-01-26 09:11:37.929108+00	delivered	1440.50
417	46	3	2025-06-05 07:57:59.213906+00	cancelled	2486.36
418	102	12	2025-12-10 23:18:44.885451+00	pending	7566.22
419	75	1	2025-10-27 19:45:36.710451+00	delivered	1157.58
420	155	\N	2025-06-05 16:40:58.624193+00	cancelled	16451.24
421	73	42	2026-02-18 08:38:01.057464+00	shipped	7913.37
422	127	9	2025-12-12 06:13:01.879111+00	pending	406.98
423	120	\N	2025-09-12 07:06:30.461607+00	processing	9554.48
424	85	\N	2025-11-30 00:22:14.744537+00	delivered	1167.31
425	66	1	2026-02-09 11:19:50.633386+00	processing	10260.45
426	76	49	2025-11-03 20:22:01.074863+00	delivered	1652.49
427	157	26	2026-05-08 19:21:16.748102+00	processing	1357.08
428	132	26	2025-08-04 01:28:32.375522+00	shipped	2785.77
429	48	31	2026-04-30 21:27:41.019698+00	delivered	1934.16
430	64	\N	2025-12-08 02:42:07.668737+00	delivered	16099.00
431	115	22	2025-08-26 14:20:25.825546+00	delivered	2005.03
432	147	\N	2026-01-11 22:54:56.421851+00	shipped	4872.42
433	61	\N	2025-08-30 18:42:10.382699+00	delivered	241.10
434	79	\N	2025-10-07 01:00:40.247406+00	shipped	2613.79
435	80	41	2026-03-16 22:17:11.968366+00	pending	6009.56
436	76	15	2025-06-28 10:43:45.415972+00	delivered	1041.69
437	35	30	2026-05-15 23:02:23.235327+00	processing	5422.68
438	156	45	2025-11-14 05:31:46.680954+00	shipped	11737.00
439	121	43	2025-08-27 09:58:03.310161+00	processing	4278.73
440	64	39	2026-02-09 05:52:18.356739+00	pending	6160.26
441	21	34	2025-09-17 03:34:16.531902+00	processing	7083.75
442	20	8	2026-03-29 00:39:32.409569+00	delivered	7691.48
443	141	13	2025-06-29 00:44:02.817601+00	shipped	736.47
444	39	\N	2026-05-27 18:50:52.872509+00	pending	6469.33
445	114	\N	2026-01-22 22:53:03.643126+00	delivered	1007.74
446	150	33	2025-06-11 03:48:15.51716+00	delivered	1555.53
447	15	33	2025-10-25 14:38:16.259806+00	delivered	1990.91
448	145	\N	2025-10-15 08:14:36.499892+00	delivered	3471.15
449	79	26	2025-11-20 10:36:43.279516+00	delivered	3907.14
450	1	38	2026-01-18 03:38:46.918817+00	delivered	6024.59
451	109	5	2026-02-11 07:02:14.848033+00	shipped	10486.49
452	16	5	2025-06-29 18:52:20.138779+00	cancelled	7795.80
453	121	\N	2026-04-04 08:01:25.159243+00	delivered	2206.85
454	35	47	2026-01-21 03:10:03.578493+00	shipped	184.54
455	108	25	2025-09-28 13:54:15.404981+00	delivered	9687.05
456	97	44	2026-05-22 13:05:56.284441+00	cancelled	4859.04
457	139	\N	2026-05-21 06:30:39.759342+00	pending	7660.67
458	31	\N	2026-04-22 09:35:26.056707+00	shipped	3842.14
459	136	\N	2026-05-01 07:07:59.806462+00	cancelled	421.04
460	1	20	2025-08-22 12:08:36.690661+00	delivered	4407.87
461	140	25	2026-04-24 18:24:28.831878+00	processing	1571.98
462	64	10	2026-02-07 10:29:36.577875+00	delivered	8504.93
463	29	\N	2025-12-23 14:21:33.695569+00	shipped	1314.58
464	158	2	2025-09-06 14:25:11.009225+00	delivered	8456.40
465	18	\N	2026-05-03 03:01:25.99832+00	delivered	9027.40
466	154	4	2026-02-04 13:36:13.168294+00	delivered	641.38
467	12	15	2025-09-09 23:44:53.176733+00	shipped	765.84
468	15	\N	2025-12-14 22:08:32.386955+00	cancelled	1226.12
469	60	47	2026-01-25 22:53:35.560957+00	shipped	4783.60
470	148	44	2025-08-04 02:14:38.708527+00	processing	1604.94
471	61	10	2026-04-06 04:42:35.263603+00	cancelled	5706.61
472	134	\N	2025-06-05 07:19:14.376235+00	delivered	4298.70
473	16	38	2025-08-14 05:57:49.958238+00	pending	625.36
474	45	28	2025-07-22 06:00:51.032854+00	shipped	4601.84
475	13	42	2026-03-26 08:02:37.066677+00	shipped	4314.14
476	135	27	2026-03-26 09:53:55.933105+00	delivered	2976.82
477	77	49	2026-05-04 20:21:37.26659+00	shipped	4888.11
478	62	20	2025-09-16 21:27:17.795404+00	pending	2498.91
479	37	4	2025-12-22 13:35:16.020562+00	shipped	5387.06
480	107	9	2025-12-23 13:35:09.53628+00	delivered	8372.77
481	66	\N	2026-04-05 20:04:26.362058+00	shipped	5058.35
482	116	6	2026-02-01 20:47:29.680939+00	shipped	4230.29
483	49	\N	2025-12-14 00:30:21.926762+00	delivered	2460.00
484	155	5	2025-10-17 18:46:09.642414+00	delivered	5230.00
485	151	36	2026-02-24 18:29:39.06602+00	delivered	14751.94
486	54	22	2026-03-15 07:22:55.38424+00	delivered	2883.52
487	4	\N	2026-02-06 08:23:46.77016+00	delivered	9336.43
488	31	49	2025-06-28 05:32:37.940561+00	delivered	6459.46
489	63	46	2026-02-26 20:33:31.902988+00	delivered	1705.20
490	62	50	2025-10-03 21:47:12.877337+00	delivered	3308.20
491	120	23	2025-07-05 06:21:20.60261+00	delivered	1041.18
492	93	32	2025-08-23 08:59:03.060665+00	delivered	5019.55
493	121	21	2025-06-27 08:25:23.738057+00	pending	1204.11
494	95	3	2026-01-06 14:49:46.264634+00	shipped	7474.82
495	57	2	2026-01-09 19:03:39.11697+00	delivered	8426.18
496	150	27	2026-01-03 03:01:41.307445+00	delivered	3049.66
497	51	25	2026-05-19 11:23:25.28188+00	shipped	4530.70
498	63	42	2025-09-26 19:00:17.685245+00	pending	6491.00
499	87	\N	2026-01-17 04:38:06.442793+00	processing	183.69
500	165	30	2026-03-12 18:27:37.765098+00	delivered	2990.35
501	91	\N	2025-11-11 03:28:49.55078+00	processing	7762.10
502	126	\N	2025-08-21 21:52:18.940094+00	pending	6122.59
503	165	34	2025-12-18 13:51:41.484303+00	delivered	9086.07
504	20	43	2025-10-14 16:58:06.599778+00	delivered	7549.42
505	2	41	2025-08-06 10:11:56.16813+00	delivered	6250.68
506	39	\N	2025-12-30 13:42:22.529025+00	shipped	1534.16
507	96	\N	2025-10-16 09:41:30.281882+00	shipped	7215.91
508	158	43	2026-03-08 14:41:58.920084+00	delivered	7145.75
509	2	27	2025-09-15 11:17:28.292427+00	delivered	6048.16
510	136	35	2025-08-28 14:23:06.68596+00	cancelled	1916.60
511	5	45	2025-06-26 10:24:27.012464+00	shipped	3313.48
512	46	\N	2025-09-05 11:02:38.634325+00	delivered	7213.06
513	39	\N	2025-10-16 09:03:15.461736+00	shipped	7716.40
514	65	18	2026-03-12 21:27:34.677944+00	processing	1244.84
515	21	26	2025-07-25 22:25:11.107664+00	delivered	1680.09
516	63	15	2025-10-19 21:23:53.817407+00	delivered	4345.64
517	21	42	2025-10-09 07:52:37.873735+00	processing	3772.38
518	24	25	2025-07-03 00:18:42.006974+00	shipped	1543.70
519	15	45	2026-05-09 23:49:42.952746+00	delivered	5308.10
520	128	42	2025-11-09 00:30:48.28142+00	processing	7686.75
521	145	7	2026-03-04 15:50:46.227355+00	pending	7689.93
522	11	\N	2025-07-06 22:12:05.746078+00	pending	1873.05
523	146	3	2025-07-01 11:17:31.714961+00	pending	2988.51
524	72	37	2025-11-03 23:55:42.807064+00	shipped	3149.30
525	46	21	2025-12-20 00:27:45.617757+00	delivered	3615.91
526	54	49	2025-12-03 17:59:56.568905+00	processing	124.50
527	102	20	2025-07-07 07:30:23.638787+00	delivered	7602.27
528	62	25	2025-07-02 07:38:34.13637+00	shipped	8002.15
529	139	49	2025-12-19 00:13:24.084903+00	processing	7914.76
530	21	23	2026-01-03 14:33:46.603112+00	delivered	2229.62
531	112	\N	2026-03-13 02:16:01.729423+00	delivered	2869.25
532	155	39	2026-04-11 01:12:42.498454+00	delivered	3751.70
533	84	\N	2025-06-04 02:14:25.525971+00	delivered	5804.78
534	116	23	2025-10-28 17:25:31.125814+00	shipped	1961.58
535	97	44	2026-03-11 04:04:29.765545+00	shipped	9927.88
536	98	\N	2026-02-19 07:52:21.827431+00	shipped	8979.06
537	64	6	2025-12-20 22:49:43.056978+00	delivered	1589.90
538	98	41	2026-05-28 04:06:00.844668+00	delivered	2844.56
539	100	7	2025-08-27 05:53:17.631033+00	delivered	1067.95
540	79	49	2025-12-06 21:56:34.105708+00	delivered	918.87
541	34	\N	2026-02-04 21:22:51.829639+00	delivered	9344.60
542	143	27	2025-07-31 11:52:37.826241+00	delivered	6076.57
543	23	6	2025-09-05 19:20:40.737514+00	shipped	4799.47
544	84	1	2025-09-05 14:51:18.438243+00	delivered	2435.64
545	100	47	2025-07-22 21:17:42.608351+00	pending	2779.62
546	63	11	2025-07-30 15:45:55.803002+00	shipped	7534.70
547	44	\N	2025-09-08 09:04:51.928223+00	delivered	5306.71
548	127	\N	2025-09-17 01:37:18.742408+00	delivered	1871.41
549	71	31	2026-03-12 10:44:00.034801+00	processing	3528.68
550	93	\N	2025-10-09 11:35:59.520144+00	delivered	2781.04
551	161	40	2026-05-10 10:53:29.708554+00	delivered	3010.48
552	28	\N	2026-02-17 21:17:49.703686+00	delivered	2299.54
553	102	40	2025-11-27 16:09:02.60382+00	delivered	8180.75
554	85	28	2026-01-10 19:38:10.269712+00	processing	1788.16
555	167	9	2025-11-13 19:34:14.674134+00	delivered	3359.91
556	155	13	2025-07-19 01:44:03.19267+00	delivered	910.44
557	46	21	2025-06-02 01:23:12.090374+00	delivered	4227.84
558	163	37	2025-10-22 02:36:23.30052+00	processing	2345.27
559	84	26	2026-04-02 23:26:47.458847+00	delivered	3685.06
560	145	\N	2025-10-16 08:05:23.055184+00	cancelled	979.98
561	47	36	2026-04-10 11:53:20.466162+00	delivered	4532.88
562	119	14	2025-11-07 08:57:14.514333+00	delivered	4033.98
563	75	5	2025-11-03 20:44:38.401748+00	processing	6244.69
564	105	9	2026-03-27 08:58:40.159791+00	shipped	1394.10
565	62	\N	2026-01-23 08:53:54.265745+00	delivered	3200.95
566	109	5	2026-01-02 16:22:16.427188+00	delivered	8712.05
567	154	26	2025-09-17 07:36:32.963704+00	shipped	7759.34
568	108	24	2026-01-05 21:40:14.748802+00	processing	3921.47
569	138	6	2026-02-08 12:49:51.412618+00	delivered	968.80
570	64	23	2025-11-21 12:56:59.982201+00	delivered	979.62
571	157	\N	2025-08-03 11:11:28.474778+00	cancelled	5918.33
572	174	49	2025-10-23 00:56:17.371091+00	delivered	2909.64
573	111	\N	2025-09-24 03:32:59.036401+00	delivered	5709.27
574	57	34	2026-02-22 23:47:52.343395+00	shipped	4427.09
575	148	\N	2026-01-16 17:56:11.906087+00	delivered	7217.78
576	119	38	2026-05-19 01:14:40.199152+00	shipped	4115.20
577	39	2	2026-03-12 04:39:54.740346+00	delivered	4398.52
578	76	6	2025-09-26 14:42:21.961019+00	delivered	5014.96
579	37	22	2025-09-09 23:06:33.722733+00	delivered	1295.37
580	53	23	2026-03-13 14:46:58.671369+00	delivered	5622.43
581	113	29	2025-10-10 21:42:14.94948+00	delivered	556.23
582	77	\N	2026-05-06 00:20:33.068505+00	processing	2753.30
583	6	42	2025-08-11 13:27:53.389948+00	delivered	8337.50
584	43	48	2026-05-29 19:51:01.983335+00	delivered	3522.89
585	45	22	2025-08-04 07:15:51.547509+00	shipped	6100.76
586	119	\N	2026-03-06 22:49:11.663687+00	delivered	2904.89
587	48	\N	2025-06-09 10:00:20.535615+00	shipped	5567.81
588	102	\N	2026-02-20 04:38:36.137379+00	shipped	9.09
589	51	28	2026-05-09 23:57:26.460461+00	delivered	9108.75
590	55	\N	2025-08-15 03:47:35.096796+00	processing	8502.68
591	17	35	2026-03-17 22:23:07.398211+00	delivered	5224.77
592	84	\N	2026-03-30 04:52:56.579075+00	delivered	3572.08
593	172	34	2025-06-24 20:17:37.952446+00	cancelled	2142.37
594	81	40	2026-04-05 05:34:15.892227+00	delivered	7421.11
595	30	30	2026-03-16 23:14:40.887922+00	shipped	3717.36
596	173	20	2026-01-31 09:13:34.110546+00	pending	2688.40
597	152	\N	2025-07-20 10:04:34.83164+00	delivered	323.10
598	31	\N	2025-09-18 04:37:25.751892+00	delivered	957.55
599	96	33	2025-08-30 21:00:45.223406+00	delivered	10411.76
600	153	\N	2025-07-25 21:14:53.35591+00	delivered	1653.21
601	48	35	2025-11-01 03:06:13.173844+00	shipped	7987.41
602	166	12	2025-10-15 06:40:35.71926+00	shipped	4304.50
603	126	\N	2025-11-10 14:28:35.955733+00	delivered	10063.13
604	116	23	2026-01-03 23:24:36.799904+00	cancelled	7530.76
605	125	\N	2025-12-29 05:52:36.801989+00	processing	946.46
606	144	32	2025-12-11 18:12:07.006741+00	delivered	1202.43
607	126	29	2026-05-02 21:12:27.706302+00	delivered	1787.57
608	22	49	2026-04-13 05:03:57.860071+00	delivered	7112.00
609	9	\N	2025-10-30 08:47:20.516072+00	shipped	2774.76
610	44	37	2025-06-13 00:20:24.576483+00	processing	4643.92
611	127	8	2026-05-19 07:04:24.016609+00	shipped	561.33
612	69	24	2026-02-10 20:25:23.965162+00	shipped	3408.56
613	11	29	2026-03-23 06:27:57.215101+00	shipped	406.72
614	109	\N	2026-01-02 11:20:55.183985+00	processing	6009.47
615	64	\N	2026-04-29 13:29:14.804261+00	cancelled	5524.56
616	116	\N	2025-07-09 12:46:18.078906+00	pending	10313.42
617	23	8	2025-08-29 05:59:55.150863+00	processing	3164.53
618	61	\N	2026-01-28 08:36:45.519075+00	processing	9154.94
619	90	40	2025-07-30 08:08:55.919078+00	shipped	8430.43
620	43	14	2026-01-09 08:39:10.816334+00	processing	4678.41
621	16	35	2025-12-22 07:07:10.07104+00	delivered	8833.79
622	138	\N	2026-01-21 04:15:15.413448+00	cancelled	6239.11
623	75	\N	2026-01-21 19:15:53.235116+00	delivered	536.55
624	132	44	2026-05-18 16:53:59.703885+00	processing	9316.47
625	35	27	2025-09-28 16:45:45.586067+00	pending	792.68
626	71	9	2026-03-17 09:38:09.495132+00	processing	2570.91
627	34	\N	2025-07-08 06:45:00.245672+00	processing	5379.35
628	64	44	2025-07-05 14:25:37.137032+00	delivered	8772.20
629	37	18	2025-08-19 16:04:25.459057+00	shipped	3169.67
630	97	41	2026-02-27 08:47:59.823809+00	processing	7385.48
631	24	48	2025-12-20 09:18:06.929275+00	delivered	3938.00
632	95	32	2026-02-05 17:58:00.205012+00	delivered	3754.62
633	1	47	2025-08-19 07:34:36.146208+00	delivered	739.93
634	118	45	2025-10-14 05:30:28.433658+00	delivered	8296.62
635	17	26	2025-11-15 17:09:59.423613+00	delivered	7404.81
636	110	32	2026-02-02 18:53:09.117895+00	delivered	510.35
637	73	37	2026-02-06 18:16:23.781224+00	delivered	871.32
638	125	44	2025-07-24 15:27:34.037606+00	processing	4508.94
639	12	\N	2026-05-29 23:41:17.512391+00	processing	5405.08
640	118	\N	2025-11-22 21:55:15.661733+00	pending	3646.10
641	41	1	2025-09-15 11:45:12.588793+00	cancelled	2694.58
642	110	\N	2026-05-01 19:21:51.842633+00	shipped	4620.42
643	34	20	2025-06-30 22:38:53.239635+00	delivered	1832.29
644	71	\N	2026-03-30 05:11:50.601839+00	delivered	3590.72
645	22	42	2026-02-21 06:23:29.606639+00	delivered	3707.29
646	102	47	2025-10-04 19:25:51.322545+00	shipped	6235.32
647	60	6	2025-10-02 21:18:20.677778+00	processing	1798.57
648	1	\N	2026-03-13 00:47:17.264734+00	delivered	2753.97
649	152	\N	2025-12-06 22:01:59.109699+00	shipped	3347.65
650	3	\N	2025-10-04 19:10:56.509653+00	delivered	5552.36
651	31	28	2025-07-05 05:48:20.220754+00	shipped	8015.50
652	123	\N	2026-02-18 06:53:28.261677+00	delivered	1135.51
653	27	\N	2025-11-11 20:06:32.631547+00	delivered	1023.54
654	77	\N	2025-06-24 02:53:58.914663+00	processing	9305.13
655	35	44	2025-06-15 21:44:47.296949+00	delivered	3132.61
656	136	40	2026-02-14 04:35:00.934053+00	shipped	4883.71
657	113	14	2025-06-07 20:02:28.517994+00	shipped	4445.64
658	39	40	2025-10-02 21:24:16.21847+00	shipped	1269.35
659	56	\N	2025-07-09 12:42:45.277334+00	delivered	572.92
660	32	25	2026-03-18 19:06:46.605077+00	delivered	5117.35
661	110	9	2026-05-05 05:32:33.144315+00	delivered	6409.97
662	166	\N	2026-02-25 01:01:07.179357+00	shipped	1560.46
663	154	19	2025-12-05 01:08:39.33977+00	processing	442.09
664	7	43	2025-12-18 03:58:43.311692+00	pending	8419.43
665	53	33	2025-09-28 11:26:29.179022+00	delivered	2750.95
666	101	\N	2025-11-02 07:31:02.077432+00	delivered	5360.19
667	62	8	2025-11-15 08:19:17.065754+00	delivered	7593.65
668	164	34	2026-03-17 23:00:04.80399+00	pending	7282.33
669	4	21	2026-01-15 14:23:36.12613+00	delivered	8052.51
670	146	35	2025-08-06 15:53:18.995028+00	shipped	10823.42
671	121	50	2026-01-25 15:52:08.223144+00	delivered	2532.87
672	151	\N	2025-10-22 01:38:44.672841+00	delivered	6263.79
673	11	26	2026-02-23 21:50:06.107238+00	shipped	10255.59
674	161	50	2026-04-18 03:05:06.706843+00	delivered	4488.09
675	103	\N	2025-11-10 18:55:55.946129+00	shipped	2718.05
676	158	\N	2025-11-03 11:25:21.604748+00	delivered	3394.77
677	21	14	2025-06-01 05:04:24.842432+00	cancelled	12358.96
678	40	26	2025-08-17 00:54:59.981532+00	shipped	6364.76
679	167	5	2025-09-09 05:58:10.33354+00	delivered	2044.53
680	112	16	2026-02-11 15:03:16.427954+00	delivered	5439.08
681	23	8	2026-03-17 07:40:51.916374+00	delivered	2473.24
682	156	\N	2025-12-27 10:57:31.424608+00	shipped	684.97
683	169	8	2026-03-18 14:18:40.807652+00	delivered	5862.59
684	36	11	2025-12-12 16:18:20.767879+00	delivered	5018.48
685	89	47	2025-10-11 04:31:10.059811+00	delivered	4708.98
686	96	\N	2025-08-10 13:34:16.873222+00	processing	5333.19
687	69	8	2025-07-11 04:58:02.92643+00	processing	7998.26
688	8	28	2026-01-30 13:16:23.905301+00	delivered	5533.23
689	17	\N	2025-11-25 08:45:52.695404+00	cancelled	5871.15
690	161	\N	2026-05-18 09:03:24.831264+00	delivered	6683.32
691	93	\N	2025-09-22 01:17:26.762209+00	pending	7936.93
692	43	17	2025-10-19 12:47:02.555859+00	processing	2184.18
693	147	8	2025-10-20 23:00:43.556712+00	delivered	160.65
694	131	\N	2025-07-11 07:23:47.381006+00	pending	2754.82
695	4	\N	2025-10-06 03:28:51.335811+00	delivered	1623.37
696	99	12	2025-11-13 19:33:41.642778+00	pending	2733.45
697	10	46	2025-08-01 14:24:01.180804+00	processing	2934.87
698	108	\N	2026-01-31 14:35:01.900606+00	delivered	3342.94
699	82	\N	2026-03-19 00:03:01.171227+00	delivered	10852.66
700	96	\N	2026-05-01 03:00:59.638677+00	shipped	3524.54
701	14	\N	2026-01-01 03:20:23.289146+00	processing	1056.76
702	12	5	2026-01-31 01:37:16.411681+00	pending	8451.25
703	73	20	2025-09-21 23:22:35.86969+00	delivered	4622.56
704	142	24	2025-08-25 17:20:12.545029+00	delivered	10120.17
705	145	48	2025-07-12 07:12:41.688094+00	shipped	1878.34
706	119	32	2025-10-13 22:22:37.128618+00	cancelled	6121.56
707	51	35	2025-07-21 05:10:50.231254+00	processing	1721.94
708	63	\N	2025-10-19 11:14:28.835312+00	pending	1712.62
709	7	\N	2026-01-03 10:11:28.064662+00	delivered	4385.99
710	3	1	2025-12-26 12:40:38.609306+00	processing	4478.62
711	97	47	2025-11-01 02:19:19.163646+00	delivered	4649.66
712	53	16	2025-11-24 08:05:59.515668+00	delivered	8615.63
713	16	10	2025-12-12 20:36:11.7552+00	processing	5026.99
714	24	\N	2026-05-01 07:12:36.914822+00	delivered	6598.63
715	134	24	2026-05-05 12:18:50.445701+00	delivered	8470.42
716	22	33	2025-08-01 20:36:00.917415+00	delivered	8331.87
717	101	\N	2025-07-30 12:46:07.282923+00	shipped	11142.39
718	112	9	2025-09-13 01:55:18.712295+00	delivered	3051.98
719	67	26	2025-08-06 22:07:36.493848+00	processing	3364.28
720	84	18	2026-04-03 02:42:21.118411+00	delivered	3837.32
721	52	\N	2026-01-11 19:39:53.176416+00	processing	1469.82
722	28	\N	2026-04-11 17:01:32.541267+00	delivered	4456.16
723	120	8	2026-05-13 05:41:01.145274+00	shipped	6092.55
724	54	30	2025-11-23 14:01:51.734193+00	delivered	4052.64
725	31	\N	2025-08-09 20:30:54.29658+00	processing	1428.38
726	78	45	2025-10-17 19:37:40.996603+00	shipped	8000.49
727	56	21	2025-12-21 16:45:33.356796+00	delivered	6193.32
728	64	26	2026-01-24 02:43:06.025245+00	shipped	1930.76
729	174	\N	2025-10-27 00:26:20.619977+00	processing	14025.55
730	45	\N	2025-11-26 04:24:59.780287+00	delivered	8430.18
731	116	36	2026-02-13 23:00:11.382308+00	delivered	7033.91
732	119	\N	2025-11-08 16:45:48.270972+00	processing	7865.00
733	32	\N	2025-07-30 16:10:10.147846+00	processing	9244.45
734	57	\N	2025-12-23 02:12:25.085755+00	processing	7236.53
735	96	42	2026-03-17 06:33:59.120629+00	delivered	1497.43
736	151	\N	2025-08-19 03:10:27.410412+00	processing	6093.08
737	6	13	2025-06-11 12:39:46.224477+00	pending	9132.01
738	114	6	2025-08-20 16:59:20.340348+00	pending	4799.95
739	85	\N	2025-09-13 00:28:48.768164+00	pending	3859.90
740	13	\N	2026-03-11 17:50:48.294885+00	shipped	13953.78
741	102	25	2025-12-23 04:25:18.27192+00	shipped	3855.50
742	45	12	2026-03-08 18:01:57.864913+00	delivered	2423.99
743	115	3	2025-11-27 11:51:48.403311+00	shipped	10669.92
744	158	\N	2025-12-03 03:40:05.464852+00	delivered	451.12
745	106	31	2025-12-25 18:20:22.203841+00	delivered	888.32
746	72	27	2025-09-05 10:18:55.59104+00	delivered	912.13
747	135	\N	2025-12-14 22:48:14.408278+00	cancelled	3700.43
748	140	25	2026-05-27 12:00:04.370605+00	processing	572.92
749	92	32	2025-12-14 13:29:15.815363+00	delivered	287.10
750	145	25	2026-03-02 23:52:19.66103+00	delivered	5960.42
751	7	15	2026-03-04 04:04:45.717478+00	delivered	4020.20
752	72	\N	2025-11-07 18:58:44.63573+00	cancelled	6307.92
753	136	38	2025-08-18 09:45:06.148042+00	cancelled	2465.69
754	41	\N	2025-11-01 20:52:10.208528+00	shipped	4809.89
755	69	48	2026-02-23 09:33:57.03021+00	delivered	2411.67
756	57	25	2026-01-24 07:59:41.342679+00	delivered	8428.77
757	45	\N	2025-08-28 23:52:06.137558+00	shipped	3926.77
758	92	2	2026-04-15 02:26:19.36916+00	processing	2393.96
759	91	37	2025-06-11 08:35:22.080366+00	delivered	2820.20
760	49	32	2025-09-03 13:50:26.663939+00	shipped	10199.48
761	45	6	2026-04-10 11:54:01.961124+00	delivered	18069.31
762	155	\N	2025-07-01 08:32:15.756626+00	shipped	3253.52
763	1	40	2026-04-11 14:59:38.93698+00	delivered	5072.39
764	34	12	2025-07-12 11:02:35.848315+00	pending	10899.51
765	83	\N	2026-03-23 02:53:20.0761+00	delivered	631.83
766	37	34	2025-08-15 05:48:25.926794+00	pending	604.36
767	19	43	2026-02-23 23:48:14.143283+00	delivered	4551.68
768	26	21	2026-02-06 06:50:42.677219+00	delivered	2335.89
769	41	28	2026-04-10 01:48:42.391344+00	processing	3466.73
770	125	12	2026-01-08 11:28:26.596147+00	processing	6416.81
771	144	40	2025-11-02 23:16:30.915896+00	processing	4063.49
772	58	12	2026-01-10 15:05:56.747609+00	delivered	2452.40
773	76	\N	2026-03-13 05:51:58.474524+00	processing	6011.61
774	147	50	2026-03-23 17:16:23.193555+00	cancelled	2679.20
775	9	\N	2026-03-20 18:21:49.012996+00	delivered	2839.28
776	157	\N	2025-12-24 19:12:01.599384+00	shipped	4783.39
777	128	\N	2025-12-10 23:54:40.600487+00	processing	1848.54
778	61	21	2026-01-03 13:58:36.423031+00	delivered	1701.86
779	23	43	2025-07-31 02:01:16.043155+00	shipped	3626.96
780	86	17	2026-05-23 03:44:45.479568+00	delivered	5754.99
781	18	7	2025-09-14 11:13:51.906829+00	processing	1032.90
782	13	47	2025-12-25 18:31:41.489985+00	delivered	5150.35
783	43	32	2026-05-13 10:33:07.597111+00	pending	2450.24
784	90	7	2025-12-04 11:18:13.981805+00	processing	9725.01
785	148	44	2026-04-24 08:36:38.800466+00	delivered	4693.90
786	116	\N	2026-03-24 07:44:44.638868+00	processing	5322.20
787	76	\N	2025-07-19 02:36:19.324677+00	delivered	3055.04
788	27	\N	2026-02-28 13:12:38.640335+00	delivered	3215.08
789	97	\N	2025-10-27 22:01:09.351177+00	delivered	3178.39
790	24	40	2025-06-21 05:45:05.069745+00	pending	9427.23
791	8	42	2025-09-08 21:01:01.599019+00	delivered	5567.68
792	112	\N	2026-01-25 03:29:41.662383+00	delivered	2811.73
793	53	27	2026-02-10 18:36:07.748446+00	shipped	3501.48
794	139	\N	2025-07-18 01:12:06.31969+00	delivered	9374.12
795	61	\N	2025-07-23 00:00:01.735893+00	delivered	3049.69
796	141	10	2025-09-25 05:29:16.894725+00	delivered	8798.44
797	1	19	2025-08-29 00:04:15.576444+00	processing	879.35
798	161	13	2026-04-03 16:28:19.158005+00	delivered	12.18
799	53	\N	2025-10-21 00:23:09.904289+00	delivered	7232.93
800	21	8	2025-07-21 12:18:28.691648+00	delivered	12081.28
801	102	43	2026-01-16 13:32:58.406423+00	delivered	11618.43
802	165	12	2026-01-14 21:19:19.442737+00	delivered	2714.88
803	98	29	2025-10-14 14:44:10.104349+00	delivered	5904.00
804	113	15	2025-06-27 04:01:23.101237+00	processing	10601.85
805	145	\N	2026-03-16 19:19:35.213941+00	processing	4427.23
806	171	\N	2026-03-07 09:55:12.812903+00	shipped	1263.81
807	139	49	2025-10-24 17:21:31.500481+00	shipped	391.50
808	142	\N	2026-02-28 10:39:11.8485+00	delivered	4710.97
809	134	35	2026-02-08 07:40:14.59976+00	shipped	4875.70
810	122	16	2026-04-16 00:25:08.217792+00	delivered	3389.45
811	21	46	2025-11-12 15:49:06.55819+00	delivered	1307.69
812	147	37	2025-11-24 20:08:46.82543+00	shipped	2341.71
813	159	\N	2025-12-29 03:20:53.486855+00	pending	6150.30
814	115	\N	2026-04-12 22:42:08.881277+00	cancelled	3519.92
815	55	9	2026-04-05 00:07:51.654683+00	delivered	9493.47
816	21	28	2025-07-03 14:31:22.714934+00	delivered	8039.42
817	161	\N	2026-05-20 15:42:06.115009+00	shipped	924.31
818	82	5	2026-01-17 10:55:31.497581+00	delivered	2516.04
819	143	21	2026-02-09 06:20:00.187783+00	pending	5169.18
820	134	1	2026-04-06 01:53:34.181028+00	processing	4000.26
821	160	27	2026-03-17 04:47:14.272254+00	delivered	810.24
822	39	\N	2025-10-22 20:20:50.655441+00	shipped	4284.04
823	26	37	2026-05-19 04:26:54.015508+00	processing	4613.69
824	74	23	2026-03-27 20:28:55.456671+00	pending	5779.64
825	68	32	2025-11-27 06:37:04.995262+00	shipped	7482.16
826	122	\N	2025-09-25 12:13:26.289211+00	delivered	886.77
827	37	44	2025-09-11 03:58:27.830878+00	shipped	5107.76
828	10	22	2025-12-16 11:39:30.077066+00	shipped	6593.18
829	13	18	2025-07-17 06:49:24.280073+00	pending	5453.58
830	6	20	2026-04-06 22:11:50.200373+00	delivered	8438.45
831	126	44	2026-03-14 12:08:46.280599+00	delivered	2768.27
832	59	\N	2026-04-22 04:00:38.486893+00	cancelled	321.45
833	114	21	2026-03-04 23:48:04.950525+00	delivered	4554.97
834	107	6	2025-06-16 08:47:24.776077+00	delivered	3689.36
835	55	27	2026-01-14 07:00:17.86928+00	processing	1772.18
836	133	4	2026-04-01 04:23:45.768991+00	shipped	4147.14
837	41	\N	2025-06-05 12:47:02.33855+00	processing	11686.99
838	104	\N	2026-05-05 01:15:03.877063+00	pending	5232.95
839	146	\N	2025-07-27 06:54:40.074392+00	delivered	7256.70
840	52	16	2025-11-13 07:47:38.296015+00	delivered	2876.36
841	13	46	2026-05-27 20:16:53.457169+00	delivered	519.38
842	95	33	2025-11-02 20:03:05.598435+00	delivered	2920.58
843	32	16	2026-05-29 06:04:50.863814+00	delivered	2500.09
844	153	31	2026-04-27 17:42:39.378574+00	shipped	2911.86
845	90	17	2026-04-17 18:45:40.102864+00	processing	5221.72
846	24	\N	2025-09-17 20:08:46.029114+00	delivered	2936.32
847	42	50	2026-04-14 23:03:03.416096+00	cancelled	4123.89
848	57	44	2026-04-15 18:05:14.168997+00	delivered	6143.17
849	167	2	2025-07-03 16:15:41.24992+00	pending	3804.87
850	175	\N	2025-10-09 05:33:20.238926+00	pending	9914.60
851	166	\N	2025-06-29 16:32:38.928453+00	processing	5246.26
852	58	\N	2026-01-28 06:59:25.131426+00	processing	1611.94
853	79	46	2026-01-22 14:15:55.714512+00	shipped	9582.00
854	109	23	2025-06-18 12:01:13.36687+00	delivered	2886.09
855	56	44	2026-01-14 01:57:44.920295+00	shipped	4378.08
856	160	7	2026-02-19 17:54:19.125109+00	delivered	3255.52
857	170	24	2026-03-02 10:14:57.799291+00	shipped	3487.16
858	153	20	2025-11-03 08:36:03.480448+00	shipped	8893.03
859	124	\N	2025-07-02 21:29:44.674418+00	cancelled	387.57
860	164	18	2025-07-04 08:25:22.197507+00	delivered	7944.03
861	167	\N	2025-08-16 12:51:51.737701+00	delivered	8967.71
862	62	39	2025-06-28 01:15:27.660844+00	delivered	2720.90
863	82	47	2026-01-02 10:07:03.150426+00	delivered	1795.03
864	128	17	2025-12-06 07:23:21.210285+00	pending	542.52
865	104	3	2025-11-09 03:24:53.932848+00	shipped	5355.87
866	147	22	2025-06-02 12:44:24.36202+00	processing	5179.64
867	57	41	2025-10-03 01:45:14.749051+00	processing	814.10
868	172	20	2025-07-13 15:09:42.272819+00	processing	4660.58
869	169	12	2026-04-09 19:36:07.493777+00	delivered	7484.09
870	121	\N	2026-02-08 01:46:29.078226+00	delivered	1683.09
871	144	12	2025-11-21 01:28:16.406188+00	pending	2951.84
872	86	15	2025-08-22 04:57:31.854432+00	delivered	6327.88
873	79	22	2025-07-02 05:07:13.339514+00	delivered	6548.18
874	150	\N	2026-03-20 22:53:23.032496+00	pending	1024.53
875	121	\N	2025-07-07 06:42:19.538254+00	shipped	4953.79
876	149	5	2025-10-11 20:01:23.203135+00	delivered	1043.05
877	50	44	2025-09-16 21:15:57.363733+00	delivered	2479.58
878	77	10	2025-10-17 08:54:23.132892+00	delivered	3032.66
879	52	37	2026-03-23 15:51:12.840495+00	pending	5806.41
880	118	\N	2026-04-14 23:41:56.284219+00	pending	6396.50
881	47	32	2026-01-19 21:58:05.142647+00	delivered	6419.75
882	46	4	2026-02-01 21:41:12.003703+00	delivered	1686.84
883	71	\N	2025-06-24 13:44:43.037926+00	processing	4439.11
884	148	32	2025-12-22 07:44:28.146137+00	processing	1639.89
885	23	\N	2026-01-08 11:58:39.109485+00	delivered	5324.05
886	110	31	2025-07-29 12:40:18.634974+00	delivered	9717.67
887	10	47	2025-10-05 20:29:34.129459+00	delivered	6655.62
888	4	49	2025-08-16 09:39:30.633933+00	processing	8241.21
889	49	\N	2026-02-27 21:12:38.126494+00	delivered	1821.83
890	64	\N	2026-05-01 13:38:12.039681+00	pending	6778.65
891	80	\N	2026-01-10 14:26:24.085573+00	delivered	4797.31
892	151	5	2025-11-08 03:53:46.978548+00	processing	7359.60
893	77	30	2025-08-17 22:22:48.947627+00	processing	3802.45
894	153	28	2026-04-23 01:23:02.884045+00	pending	1464.69
895	35	32	2025-07-20 17:23:13.745238+00	delivered	12091.69
896	49	\N	2025-07-14 13:37:55.956651+00	pending	1476.00
897	104	\N	2026-02-21 05:09:01.989295+00	delivered	6603.35
898	34	\N	2025-10-05 23:32:33.398161+00	delivered	3807.00
899	130	\N	2025-11-03 09:59:03.157263+00	delivered	6290.86
900	167	25	2026-03-15 12:27:13.353189+00	pending	3821.92
901	66	40	2025-08-29 02:06:05.219123+00	delivered	6947.16
902	13	42	2026-01-21 00:39:17.090476+00	processing	4969.86
903	13	27	2025-08-29 05:26:17.360808+00	delivered	4386.12
904	32	31	2026-01-05 02:16:44.728314+00	processing	4946.09
905	53	41	2026-02-17 23:45:11.472067+00	delivered	1116.48
906	108	43	2025-09-11 15:36:46.782276+00	shipped	417.84
907	160	9	2026-05-09 09:05:36.639806+00	delivered	3473.06
908	27	40	2025-06-09 09:12:06.703112+00	delivered	751.36
909	30	32	2026-04-04 23:16:41.022185+00	delivered	1070.88
910	52	34	2026-04-15 11:21:23.355139+00	cancelled	3687.35
911	92	19	2025-08-13 14:57:12.290067+00	delivered	3176.95
912	141	14	2026-01-07 06:14:26.997545+00	shipped	2742.61
913	124	1	2025-08-07 11:41:44.532019+00	delivered	4873.75
914	23	37	2025-10-20 16:03:39.38643+00	shipped	4121.05
915	39	50	2026-01-21 14:14:04.989521+00	shipped	7543.04
916	26	42	2026-03-12 20:40:56.154211+00	delivered	6129.07
917	76	\N	2026-03-16 12:07:59.789799+00	delivered	13974.86
918	45	19	2025-08-26 00:04:19.162711+00	delivered	605.85
919	174	48	2025-10-18 12:38:45.209023+00	delivered	5423.76
920	12	\N	2025-08-26 15:19:49.31605+00	delivered	6884.94
921	166	\N	2026-01-18 15:20:31.630403+00	delivered	609.50
922	113	18	2025-06-25 12:32:22.990333+00	pending	4481.72
923	24	22	2026-04-20 04:24:41.309563+00	delivered	4172.14
924	103	30	2025-06-03 23:50:31.524335+00	delivered	7257.06
925	99	31	2025-10-09 11:21:56.789668+00	processing	993.24
926	167	11	2025-09-23 04:11:19.884867+00	delivered	7592.88
927	16	11	2025-10-18 20:59:48.492878+00	delivered	5678.37
928	152	37	2026-04-02 00:18:15.030778+00	shipped	1200.51
929	47	50	2025-10-31 07:15:15.442431+00	delivered	5934.26
930	8	47	2025-12-16 03:17:35.033146+00	cancelled	1228.14
931	34	32	2025-08-01 16:31:43.129179+00	delivered	8612.32
932	106	5	2025-11-18 14:52:00.204342+00	delivered	3553.95
933	81	\N	2026-05-26 05:04:52.55479+00	pending	9169.55
934	135	37	2025-06-26 05:53:40.246042+00	processing	2893.02
935	58	43	2025-12-31 02:45:10.808528+00	pending	2268.01
936	133	45	2025-06-04 14:58:31.494148+00	shipped	612.50
937	111	16	2025-08-17 09:12:58.954653+00	delivered	1430.31
938	170	25	2026-05-02 13:10:27.059932+00	delivered	4817.31
939	143	40	2026-05-12 01:58:00.212141+00	delivered	389.44
940	165	33	2025-10-22 22:37:08.763337+00	processing	1251.09
941	127	5	2025-09-12 05:20:55.874843+00	processing	2843.96
942	83	\N	2026-02-14 20:48:03.620451+00	cancelled	502.51
943	13	36	2026-03-06 18:22:03.773968+00	shipped	7275.70
944	104	6	2025-11-01 07:01:27.872451+00	delivered	4301.58
945	147	32	2025-10-24 12:19:58.046472+00	delivered	2243.72
946	31	48	2026-01-19 12:51:42.105429+00	shipped	2277.01
947	27	3	2025-12-12 23:01:24.195685+00	shipped	4193.48
948	1	39	2025-07-25 08:25:32.4575+00	cancelled	6776.65
949	164	33	2025-06-30 02:51:26.787579+00	shipped	4054.54
950	168	22	2025-06-28 10:44:58.569555+00	delivered	6737.38
951	14	30	2026-05-01 22:40:18.644129+00	delivered	1896.25
952	159	46	2026-05-21 10:39:46.251343+00	shipped	13533.80
953	116	\N	2025-07-26 08:03:51.110555+00	processing	2268.72
954	57	\N	2025-09-26 22:16:48.837795+00	delivered	9755.04
955	163	19	2025-12-30 18:37:58.733772+00	shipped	2506.91
956	96	3	2026-03-05 08:18:18.414778+00	pending	2806.31
957	127	\N	2026-01-22 22:24:10.584589+00	processing	5258.72
958	105	\N	2026-01-20 11:48:14.955731+00	shipped	6986.60
959	49	\N	2025-09-20 20:56:12.818388+00	pending	4511.49
960	56	13	2025-11-06 08:57:47.564232+00	processing	1877.48
961	28	3	2026-05-13 19:35:10.956243+00	pending	1998.28
962	173	50	2025-08-25 17:54:13.058651+00	pending	4421.74
963	118	33	2025-08-27 21:06:59.045467+00	delivered	6753.63
964	128	\N	2026-05-03 07:07:49.942269+00	processing	4291.10
965	142	38	2025-07-11 22:46:33.933338+00	delivered	2304.14
966	131	12	2026-01-09 05:18:44.295181+00	shipped	2306.35
967	45	9	2025-06-19 16:25:59.623889+00	delivered	3867.25
968	169	21	2026-01-28 20:45:33.425055+00	shipped	1291.97
969	99	39	2026-01-25 22:23:40.616665+00	pending	3840.24
970	64	\N	2025-08-02 17:44:07.410737+00	cancelled	221.57
971	76	9	2025-06-04 05:05:01.163951+00	delivered	1896.76
972	155	48	2025-07-19 16:49:52.466561+00	shipped	3850.93
973	141	46	2025-06-03 17:33:43.986483+00	processing	10617.40
974	142	13	2025-11-27 21:30:07.858605+00	delivered	1225.84
975	75	44	2025-10-04 05:11:58.184008+00	delivered	4395.38
976	167	12	2025-12-05 11:55:00.692281+00	shipped	11974.40
977	164	8	2026-03-26 23:57:48.240587+00	processing	429.54
978	144	37	2025-09-02 06:33:43.923687+00	pending	10995.33
979	107	35	2025-10-13 09:47:01.457118+00	delivered	11835.75
980	109	34	2026-02-28 10:25:31.411882+00	delivered	226.02
981	98	\N	2026-04-14 14:36:24.406361+00	shipped	4237.98
982	52	\N	2026-02-22 06:48:18.730663+00	processing	2894.40
983	74	10	2025-07-12 16:55:20.754976+00	processing	7039.05
984	76	\N	2026-04-24 06:21:01.517839+00	shipped	3920.57
985	92	7	2025-09-29 22:41:30.514549+00	shipped	375.20
986	173	15	2025-11-03 09:25:18.093114+00	processing	4237.67
987	144	33	2025-12-07 22:02:45.053174+00	processing	3615.59
988	74	4	2025-09-03 15:01:08.712423+00	pending	144.06
989	100	44	2026-05-21 17:07:29.985161+00	delivered	2276.29
990	142	\N	2026-01-14 18:52:03.939117+00	processing	2026.11
991	52	50	2025-11-27 19:10:33.849928+00	pending	4102.17
992	114	41	2025-12-03 03:27:24.922629+00	processing	3021.74
993	166	38	2025-06-19 20:01:53.384929+00	shipped	3268.50
994	155	\N	2026-04-09 11:00:25.791286+00	processing	6104.37
995	50	\N	2025-07-30 12:54:28.05134+00	delivered	9692.49
996	175	\N	2025-07-27 01:00:25.543773+00	cancelled	4263.13
997	132	\N	2026-03-09 00:52:53.619118+00	delivered	710.52
998	72	9	2026-04-22 05:00:28.447629+00	delivered	5783.99
999	66	\N	2026-01-31 19:14:36.491043+00	delivered	171.06
1000	40	\N	2025-07-11 17:03:08.078655+00	pending	923.69
\.


--
-- Data for Name: suppliers; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.suppliers (id, name, country, contact_email, rating) FROM stdin;
1	Keller PLC	Croatia	josephbrennan@brandt-hickman.com	4.10
2	Collins, Carney and Santos	Germany	clam@wright.com	2.56
3	Chapman and Sons	Italy	adrianzimmerman@perez.com	3.19
4	Palmer LLC	USA	ilewis@walls.info	3.06
5	Lee-Davis	Croatia	agomez@shields-brown.com	4.34
6	Powell LLC	Germany	wrightjames@taylor-white.info	4.19
7	Baxter Inc	Italy	jmorton@williams.com	4.73
8	House and Sons	USA	richardolson@barrera-martin.com	2.72
9	Baker-Bowers	Croatia	smitchell@cowan.com	3.55
10	Phillips Inc	Germany	adkinsbrian@woods.com	2.57
11	Miller, Lopez and Larson	Italy	richarddavid@sanchez.biz	3.05
12	Silva, Mills and Donovan	USA	elizabethedwards@foster-powers.com	3.76
13	Stewart-Walton	Croatia	smithchristine@ferrell.com	2.57
14	Mahoney Inc	Germany	mikemoore@warner.net	3.00
15	Contreras PLC	Italy	sarah12@wilson-rodriguez.net	4.12
16	Nelson PLC	USA	jenniferharris@farrell.com	3.86
17	Walters LLC	Croatia	smithkellie@whitney.biz	3.05
18	Smith, Jones and Ware	Germany	amydavenport@tran.com	3.97
19	Nolan and Sons	Italy	elizabethgomez@henson.com	4.52
20	Hancock and Sons	USA	vjohnson@patton-jenkins.com	2.52
21	Moore-Haynes	Croatia	ebrennan@gonzalez.com	4.51
22	Hoover-Savage	Germany	andrewlee@ramirez-jones.com	4.25
23	May-Ross	Italy	sheila14@carpenter.com	3.35
24	Carlson LLC	USA	samuel81@lam-lee.com	2.89
25	Graham, Meyer and Drake	Croatia	michaeljones@mccall.com	4.89
26	Mccullough, Hunter and Estrada	Germany	richard48@lee.biz	3.34
27	Adkins, Thompson and Carroll	Italy	akelley@mitchell-jordan.org	2.73
28	Pena, Marshall and Ramos	USA	williamleon@jackson.org	2.74
29	Davis-Crane	Croatia	emilywalker@hernandez.com	4.62
30	Carr-Mack	Germany	operry@lee.com	4.01
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.products (id, name, category_id, supplier_id, price, stock, is_discontinued, created_at) FROM stdin;
1	Digitized solution-oriented solution	13	2	730.35	274	f	2024-06-03 09:30:52.7243+00
2	Versatile zero administration benchmark	15	13	83.33	150	f	2025-12-19 23:11:54.546738+00
3	Face-to-face context-sensitive website	10	29	861.54	295	f	2026-04-30 02:54:22.986361+00
4	Programmable maximized application	2	2	662.30	395	f	2025-07-11 12:28:34.974365+00
5	Decentralized logistical challenge	2	28	236.39	51	f	2026-01-05 18:21:24.253133+00
6	Synchronized multi-tasking open architecture	8	21	834.11	83	f	2025-08-08 07:29:23.229055+00
7	Versatile leadingedge pricing structure	4	22	270.38	479	f	2026-01-15 16:36:30.380296+00
8	Profit-focused interactive neural-net	2	20	636.17	273	f	2025-04-21 01:50:56.270222+00
9	Diverse value-added leverage	3	15	382.18	473	f	2025-04-24 02:42:45.022049+00
10	Versatile dynamic productivity	9	8	685.51	431	f	2024-12-18 21:59:42.321099+00
11	Vision-oriented multi-state matrix	1	8	821.87	412	f	2025-08-31 04:09:29.928493+00
12	Grass-roots leadingedge archive	5	3	214.72	482	f	2025-11-02 13:49:53.707147+00
13	Front-line encompassing groupware	12	11	216.35	255	f	2025-01-18 21:18:00.89453+00
14	Quality-focused attitude-oriented challenge	15	21	461.10	135	f	2024-09-17 12:35:46.51125+00
15	Networked system-worthy collaboration	12	18	540.74	382	f	2025-10-28 08:54:24.719603+00
16	Cloned intangible installation	15	19	402.00	112	f	2025-01-27 01:09:33.408603+00
17	Persistent intangible approach	3	17	495.55	386	t	2024-10-28 10:25:36.451255+00
18	Operative human-resource throughput	2	5	628.68	405	f	2025-07-31 00:06:19.754155+00
19	Total 3rdgeneration task-force	10	3	387.46	305	f	2025-07-24 21:01:56.584068+00
20	Polarized 24hour help-desk	9	9	970.25	440	f	2025-01-03 11:26:21.27435+00
21	Networked intangible monitoring	11	24	118.86	453	f	2025-11-27 09:23:29.243608+00
22	Quality-focused real-time definition	5	25	642.12	57	f	2025-05-21 23:42:37.460942+00
23	Future-proofed intermediate matrix	3	15	8.23	369	f	2024-06-20 13:09:17.161012+00
24	Mandatory static service-desk	5	17	762.39	259	f	2026-01-03 08:57:13.244308+00
25	Up-sized composite Local Area Network	14	21	301.65	327	f	2026-04-02 01:16:04.328926+00
26	Secured national algorithm	4	5	376.67	82	f	2026-03-23 20:08:49.374862+00
27	Reverse-engineered non-volatile protocol	13	30	532.17	0	f	2024-06-19 03:26:44.242842+00
28	Stand-alone interactive challenge	8	1	116.20	185	f	2026-02-22 13:31:38.759515+00
29	Enterprise-wide actuating firmware	14	26	310.67	29	f	2025-03-03 06:34:21.11753+00
30	Extended logistical Graphic Interface	10	3	90.14	248	f	2025-01-31 21:12:11.390845+00
31	Multi-tiered even-keeled system engine	13	18	766.24	65	f	2026-04-25 04:21:34.585104+00
32	Operative eco-centric artificial intelligence	9	6	268.47	446	f	2025-05-08 21:29:57.338741+00
33	User-friendly needs-based application	4	30	541.06	373	f	2026-05-30 18:12:34.737197+00
34	Monitored directional projection	12	10	401.60	343	f	2024-07-19 11:17:23.602257+00
35	Streamlined 6thgeneration system engine	8	29	519.47	61	f	2024-06-22 00:18:30.965518+00
36	Fully-configurable dedicated adapter	2	11	25.91	283	f	2025-08-27 05:15:50.564552+00
37	Front-line clear-thinking leverage	4	1	75.57	323	f	2025-10-01 08:56:12.045071+00
38	Re-contextualized didactic Local Area Network	2	29	36.22	169	f	2025-10-23 06:59:22.877725+00
39	Visionary holistic concept	4	9	669.96	109	f	2025-08-15 22:31:31.48691+00
40	User-friendly transitional budgetary management	12	30	882.09	295	f	2025-12-19 12:10:46.42996+00
41	Diverse fault-tolerant benchmark	13	16	807.65	97	f	2025-07-27 01:31:42.66205+00
42	Integrated object-oriented service-desk	11	14	357.17	210	f	2026-03-24 15:23:03.059401+00
43	Multi-tiered hybrid structure	12	2	674.32	330	f	2024-10-22 05:19:40.833244+00
44	Reverse-engineered system-worthy product	7	24	342.27	441	f	2024-11-23 17:49:27.578748+00
45	Total zero administration framework	4	7	538.07	71	f	2026-02-10 11:14:18.53702+00
46	Right-sized bottom-line utilization	5	15	253.31	472	f	2026-05-19 00:35:32.931679+00
47	Balanced grid-enabled monitoring	13	28	855.83	50	f	2025-04-08 06:25:23.743707+00
48	Multi-layered asymmetric middleware	9	27	19.67	47	f	2025-09-15 08:43:23.033703+00
49	Advanced intangible matrix	14	8	170.31	248	f	2024-08-15 10:33:44.557302+00
50	Multi-lateral scalable knowledgebase	14	13	902.03	84	f	2025-10-29 00:30:04.279902+00
51	Optional context-sensitive superstructure	7	9	925.96	401	f	2025-06-15 11:19:08.703993+00
52	Streamlined encompassing pricing structure	7	23	956.57	401	f	2026-01-10 17:15:58.766582+00
53	Public-key zero-defect matrices	12	16	158.87	151	f	2025-05-04 22:14:57.769589+00
54	Upgradable optimizing flexibility	1	19	736.32	31	f	2025-01-20 18:47:41.27345+00
55	Fully-configurable background focus group	1	2	585.67	257	f	2026-03-05 08:38:25.045886+00
56	Fully-configurable web-enabled Local Area Network	9	6	61.54	260	f	2025-07-20 14:38:09.593615+00
57	Synchronized homogeneous Graphical User Interface	3	3	596.46	345	f	2024-06-20 07:27:36.505663+00
58	Inverse contextually-based matrix	7	4	940.95	291	f	2024-11-01 07:05:20.224963+00
59	Fundamental global focus group	10	2	620.67	214	f	2026-03-04 09:39:10.393511+00
60	Total even-keeled open architecture	10	17	319.47	133	f	2024-06-06 18:16:12.076894+00
61	Ergonomic attitude-oriented encoding	12	11	242.25	202	f	2025-11-07 08:18:32.15085+00
62	Pre-emptive next generation task-force	11	10	459.48	475	f	2024-11-21 21:32:58.013505+00
63	Phased secondary structure	2	1	460.54	288	f	2025-05-23 21:08:58.588485+00
64	Ameliorated background frame	2	18	216.88	135	f	2024-11-08 05:13:38.216524+00
65	Team-oriented dynamic function	6	29	73.38	125	f	2025-09-27 08:32:02.23217+00
66	Multi-layered methodical neural-net	3	15	833.74	360	f	2025-06-22 04:10:26.435554+00
67	Optimized value-added neural-net	13	21	530.77	341	f	2025-01-26 23:34:47.273419+00
68	Total logistical flexibility	5	30	664.41	480	f	2025-01-09 07:52:21.579051+00
69	Focused bottom-line success	5	4	889.37	380	f	2024-10-18 00:36:03.412392+00
70	Decentralized value-added monitoring	5	10	606.20	367	f	2026-04-24 22:38:04.283319+00
71	Team-oriented contextually-based core	11	21	852.80	258	f	2024-11-04 09:51:25.910208+00
72	Polarized even-keeled success	15	30	846.03	47	f	2025-08-04 00:39:36.680923+00
73	Virtual multi-tasking policy	14	9	48.82	170	f	2024-12-23 01:42:10.73518+00
74	Cross-platform content-based frame	11	9	165.61	226	f	2024-11-12 12:25:52.268928+00
75	Enhanced exuding access	7	18	14.61	38	f	2025-10-29 12:56:44.873405+00
76	De-engineered even-keeled analyzer	12	29	153.16	18	f	2026-05-12 01:10:35.853894+00
77	Reactive explicit standardization	10	18	152.21	65	t	2026-04-19 23:37:53.468902+00
78	Sharable web-enabled matrix	6	29	932.49	497	f	2024-08-13 06:49:22.573085+00
79	Advanced object-oriented forecast	15	12	213.82	127	f	2025-05-08 05:32:50.940757+00
80	Organic global contingency	6	25	561.52	447	f	2026-05-05 14:56:48.466275+00
81	Function-based mission-critical budgetary management	10	24	158.63	476	f	2026-01-20 21:14:32.760368+00
82	Open-architected mobile archive	3	26	810.91	451	f	2025-07-25 20:21:48.602329+00
83	Synergized actuating collaboration	3	24	923.94	400	f	2024-09-16 07:57:57.570146+00
84	Re-contextualized exuding artificial intelligence	13	22	863.88	415	f	2026-05-26 09:12:03.607964+00
85	Decentralized next generation task-force	3	26	702.07	195	f	2025-03-30 08:28:07.447408+00
86	Right-sized regional definition	14	16	226.10	418	f	2025-12-17 23:23:32.498324+00
87	Multi-tiered local intranet	6	10	820.61	446	f	2025-01-02 13:21:28.603248+00
88	Reverse-engineered interactive function	1	22	196.97	168	f	2025-07-19 17:14:40.172617+00
89	Centralized reciprocal support	2	25	282.45	328	f	2024-08-10 20:01:15.443008+00
90	Virtual demand-driven product	11	27	538.00	480	t	2024-10-31 11:53:52.755201+00
91	Switchable attitude-oriented complexity	15	9	182.50	492	f	2024-11-21 13:30:24.174947+00
92	Reactive asynchronous complexity	1	4	597.99	176	f	2024-06-01 07:12:54.143577+00
93	Organized system-worthy policy	6	14	607.57	261	f	2025-05-08 14:35:08.086302+00
94	Automated discrete forecast	15	19	193.94	22	f	2025-10-28 18:18:56.974307+00
95	Total logistical archive	1	17	925.02	275	f	2025-10-14 11:12:28.906139+00
96	Fundamental zero tolerance utilization	12	24	671.60	186	f	2025-08-29 22:31:21.033535+00
97	Switchable dedicated interface	11	30	333.22	160	f	2024-08-22 04:30:30.951639+00
98	Face-to-face secondary collaboration	2	24	899.65	259	f	2026-03-24 22:08:20.311905+00
99	Digitized asynchronous approach	7	11	404.99	151	f	2024-09-28 13:11:03.311644+00
100	Integrated radical synergy	4	14	665.94	194	f	2026-01-22 10:29:27.178632+00
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.order_items (id, order_id, product_id, quantity, unit_price) FROM stdin;
1	1	77	1	774.02
2	2	81	5	843.08
3	3	39	4	790.17
4	4	71	3	77.44
5	5	91	3	527.24
6	6	24	5	72.77
7	7	65	2	418.44
8	8	69	4	96.39
9	9	29	2	664.35
10	10	43	3	296.81
11	11	97	5	532.32
12	12	72	1	119.03
13	13	45	4	243.91
14	14	83	5	918.10
15	15	32	1	683.46
16	16	42	4	915.44
17	17	15	4	260.05
18	18	93	3	29.56
19	19	67	3	516.22
20	20	66	4	488.88
21	21	38	2	323.39
22	22	11	1	171.39
23	23	99	5	535.01
24	24	81	1	214.52
25	25	81	2	864.76
26	26	55	1	209.35
27	27	90	4	647.68
28	28	10	2	28.61
29	29	92	3	42.66
30	30	10	1	181.92
31	31	33	5	75.02
32	32	30	3	410.19
33	33	58	4	435.43
34	34	3	4	674.26
35	35	69	1	642.57
36	36	80	1	756.42
37	37	75	1	701.68
38	38	10	3	927.48
39	39	14	3	787.17
40	40	39	5	90.99
41	41	98	4	384.13
42	42	85	1	476.14
43	43	69	2	140.56
44	44	51	5	298.21
45	45	82	2	301.27
46	46	94	3	956.65
47	47	2	5	874.52
48	48	19	1	46.52
49	49	74	5	396.72
50	50	71	1	307.86
51	51	96	3	215.47
52	52	83	5	146.60
53	53	24	2	618.18
54	54	33	2	118.93
55	55	86	5	852.14
56	56	97	5	463.50
57	57	71	1	293.91
58	58	9	3	102.61
59	59	93	5	489.27
60	60	43	3	132.45
61	61	84	2	104.44
62	62	80	1	899.72
63	63	41	4	452.94
64	64	79	3	694.30
65	65	20	5	568.46
66	66	41	4	172.63
67	67	41	2	785.95
68	68	92	4	280.02
69	69	47	2	680.50
70	70	43	4	465.07
71	71	46	3	489.05
72	72	14	2	646.68
73	73	11	3	858.56
74	74	18	5	200.25
75	75	94	1	728.06
76	76	3	5	632.84
77	77	75	5	407.70
78	78	76	2	905.87
79	79	71	3	545.21
80	80	70	4	654.98
81	81	20	3	395.14
82	82	99	5	733.83
83	83	38	2	466.91
84	84	66	1	399.40
85	85	65	1	663.70
86	86	79	2	757.66
87	87	18	4	163.27
88	88	73	5	660.46
89	89	19	4	938.54
90	90	6	2	761.90
91	91	30	1	267.77
92	92	30	1	669.57
93	93	67	3	390.76
94	94	59	1	44.67
95	95	84	3	107.61
96	96	67	3	834.86
97	97	34	5	546.08
98	98	23	4	654.75
99	99	47	5	654.42
100	100	10	5	255.08
101	101	29	5	408.41
102	102	45	4	792.90
103	103	78	1	503.83
104	104	18	4	169.61
105	105	10	5	644.62
106	106	28	2	190.78
107	107	47	5	718.00
108	108	16	2	417.13
109	109	43	1	483.63
110	110	62	4	214.44
111	111	21	4	27.31
112	112	6	2	575.05
113	113	21	2	630.76
114	114	6	5	150.98
115	115	22	3	921.91
116	116	67	4	600.76
117	117	73	1	878.24
118	118	94	3	946.57
119	119	28	4	607.89
120	120	61	4	174.54
121	121	53	5	146.86
122	122	75	2	624.47
123	123	66	3	171.72
124	124	88	3	921.82
125	125	77	5	73.43
126	126	49	4	136.42
127	127	3	2	524.58
128	128	65	4	826.56
129	129	78	1	181.36
130	130	79	5	43.80
131	131	69	5	752.87
132	132	12	4	660.44
133	133	78	5	827.56
134	134	100	4	523.91
135	135	48	1	698.46
136	136	55	2	937.79
137	137	62	4	353.41
138	138	95	5	102.13
139	139	18	3	479.28
140	140	30	1	286.57
141	141	70	4	261.26
142	142	1	1	579.52
143	143	16	5	12.15
144	144	84	2	688.64
145	145	41	4	365.10
146	146	20	4	652.67
147	147	33	3	854.85
148	148	55	5	368.45
149	149	36	4	755.44
150	150	53	5	784.09
151	151	62	2	372.99
152	152	72	4	257.25
153	153	40	5	347.29
154	154	91	4	736.37
155	155	85	1	748.33
156	156	58	2	104.68
157	157	66	4	786.36
158	158	71	5	697.88
159	159	91	1	164.77
160	160	82	1	804.54
161	161	19	4	925.31
162	162	56	1	68.70
163	163	29	3	84.56
164	164	5	4	930.10
165	165	52	5	657.24
166	166	37	5	62.12
167	167	100	2	641.45
168	168	57	1	205.50
169	169	85	5	289.29
170	170	5	5	512.48
171	171	90	2	616.50
172	172	87	1	362.58
173	173	84	1	974.79
174	174	12	3	779.99
175	175	46	4	408.02
176	176	26	5	20.27
177	177	91	1	918.66
178	178	71	3	726.78
179	179	72	5	351.01
180	180	36	2	607.73
181	181	25	4	929.14
182	182	74	1	264.54
183	183	53	5	110.83
184	184	10	5	297.49
185	185	15	5	955.97
186	186	69	5	253.64
187	187	57	4	564.79
188	188	99	2	757.93
189	189	100	4	682.51
190	190	76	1	484.08
191	191	34	1	385.38
192	192	29	2	800.36
193	193	53	3	518.41
194	194	2	3	251.77
195	195	12	4	674.66
196	196	44	1	556.22
197	197	23	4	316.99
198	198	28	5	272.46
199	199	96	2	501.01
200	200	26	2	736.02
201	201	34	2	232.83
202	202	32	5	358.89
203	203	100	1	124.16
204	204	11	4	615.14
205	205	98	5	957.25
206	206	62	3	621.94
207	207	64	5	868.56
208	208	63	2	983.49
209	209	66	3	400.49
210	210	97	5	132.48
211	211	68	4	480.45
212	212	70	1	504.46
213	213	51	2	459.45
214	214	16	5	462.31
215	215	89	1	16.75
216	216	27	4	582.52
217	217	42	3	614.10
218	218	34	2	550.27
219	219	31	3	473.52
220	220	79	3	368.73
221	221	64	4	214.27
222	222	90	3	367.89
223	223	52	3	453.02
224	224	74	2	978.40
225	225	88	2	814.31
226	226	93	3	804.26
227	227	72	4	856.17
228	228	26	2	800.24
229	229	95	2	475.15
230	230	2	2	423.99
231	231	18	5	535.78
232	232	41	4	303.23
233	233	72	5	52.42
234	234	13	2	64.68
235	235	33	4	838.94
236	236	13	4	745.13
237	237	34	3	363.14
238	238	72	3	347.08
239	239	53	1	353.98
240	240	87	5	202.76
241	241	74	5	178.49
242	242	100	3	357.98
243	243	87	5	489.57
244	244	95	4	889.29
245	245	49	5	289.80
246	246	81	2	868.05
247	247	82	3	424.29
248	248	79	5	407.34
249	249	10	1	166.03
250	250	30	3	319.98
251	251	38	3	606.75
252	252	51	3	887.37
253	253	100	3	748.41
254	254	67	4	416.51
255	255	24	1	129.29
256	256	31	3	939.79
257	257	90	1	214.31
258	258	51	1	99.98
259	259	61	5	58.50
260	260	99	4	525.84
261	261	11	1	265.88
262	262	20	1	655.90
263	263	50	3	232.98
264	264	95	3	445.50
265	265	17	2	528.58
266	266	22	1	39.94
267	267	46	3	864.06
268	268	60	5	934.25
269	269	71	4	139.30
270	270	90	5	180.97
271	271	77	4	632.26
272	272	82	5	437.37
273	273	82	5	312.80
274	274	45	4	541.43
275	275	12	4	311.02
276	276	53	3	159.78
277	277	2	1	525.18
278	278	98	2	346.82
279	279	61	5	13.27
280	280	63	4	302.81
281	281	99	4	798.18
282	282	77	2	796.99
283	283	71	3	192.44
284	284	72	4	397.38
285	285	21	4	828.46
286	286	29	3	83.73
287	287	81	2	518.51
288	288	79	3	287.97
289	289	96	5	808.96
290	290	53	2	853.36
291	291	24	2	292.86
292	292	82	4	619.02
293	293	35	5	494.04
294	294	42	1	156.24
295	295	69	1	189.82
296	296	14	3	272.58
297	297	92	4	727.74
298	298	30	1	154.78
299	299	64	2	344.86
300	300	40	4	996.98
301	301	60	1	333.27
302	302	97	2	60.70
303	303	100	4	75.96
304	304	61	2	196.04
305	305	33	4	828.28
306	306	16	2	387.49
307	307	57	2	738.19
308	308	5	2	463.07
309	309	99	1	523.01
310	310	27	4	391.79
311	311	40	3	162.66
312	312	94	1	745.26
313	313	71	5	126.41
314	314	62	3	202.53
315	315	7	2	972.43
316	316	31	4	327.57
317	317	22	3	586.19
318	318	51	2	13.88
319	319	6	5	783.77
320	320	61	5	159.06
321	321	99	1	252.23
322	322	64	1	686.83
323	323	44	1	64.42
324	324	83	2	702.12
325	325	14	2	489.92
326	326	41	5	788.83
327	327	97	3	805.69
328	328	57	2	26.22
329	329	49	3	725.05
330	330	33	1	487.39
331	331	57	5	297.95
332	332	90	4	193.64
333	333	24	5	350.58
334	334	94	4	278.67
335	335	77	5	164.38
336	336	68	2	451.69
337	337	34	5	369.91
338	338	1	5	381.77
339	339	24	1	621.02
340	340	47	5	242.35
341	341	93	1	659.34
342	342	69	4	193.73
343	343	88	4	766.14
344	344	20	5	286.43
345	345	53	3	114.80
346	346	67	1	48.51
347	347	17	2	873.25
348	348	26	1	487.46
349	349	13	1	572.59
350	350	50	4	527.67
351	351	90	5	259.40
352	352	47	2	607.32
353	353	10	1	929.63
354	354	27	4	927.83
355	355	11	4	801.21
356	356	8	3	559.67
357	357	54	3	794.48
358	358	8	5	269.22
359	359	6	1	834.45
360	360	10	2	959.82
361	361	13	1	725.82
362	362	69	4	193.32
363	363	68	2	571.61
364	364	23	5	749.70
365	365	54	1	766.69
366	366	74	3	675.45
367	367	90	4	882.53
368	368	22	2	551.67
369	369	65	3	658.59
370	370	69	5	445.35
371	371	46	3	551.78
372	372	42	3	414.87
373	373	82	4	826.20
374	374	42	5	244.28
375	375	70	2	377.81
376	376	71	3	362.85
377	377	58	4	959.07
378	378	1	1	982.06
379	379	77	1	519.50
380	380	39	1	303.53
381	381	29	2	855.59
382	382	3	3	918.60
383	383	66	5	572.24
384	384	74	2	98.72
385	385	59	3	160.17
386	386	34	3	889.29
387	387	32	2	259.71
388	388	39	1	572.06
389	389	73	2	734.86
390	390	93	3	793.15
391	391	23	4	825.75
392	392	89	5	819.60
393	393	13	5	643.40
394	394	5	5	384.26
395	395	100	1	921.34
396	396	43	3	879.51
397	397	56	4	929.66
398	398	16	2	748.19
399	399	78	1	635.08
400	400	81	4	58.80
401	401	68	1	322.40
402	402	73	2	329.87
403	403	90	2	157.28
404	404	87	4	970.21
405	405	97	5	576.80
406	406	12	2	434.34
407	407	51	2	136.40
408	408	11	4	573.01
409	409	7	5	401.80
410	410	11	4	503.81
411	411	100	2	762.46
412	412	62	5	201.92
413	413	51	5	199.92
414	414	79	5	249.77
415	415	10	3	777.11
416	416	42	5	94.06
417	417	86	4	426.00
418	418	45	2	323.81
419	419	77	1	770.06
420	420	22	3	617.52
421	421	57	5	149.94
422	422	6	2	203.49
423	423	48	2	758.19
424	424	11	1	740.14
425	425	32	5	926.17
426	426	37	1	346.21
427	427	15	3	452.36
428	428	3	3	212.76
429	429	69	2	207.58
430	430	67	3	550.51
431	431	80	2	695.90
432	432	86	1	379.35
433	433	85	5	48.22
434	434	22	1	287.31
435	435	90	5	274.65
436	436	60	1	71.20
437	437	85	3	664.00
438	438	85	3	864.10
439	439	3	3	867.21
440	440	84	4	234.78
441	441	49	5	975.75
442	442	13	3	486.75
443	443	77	5	92.49
444	444	26	5	965.99
445	445	72	1	44.51
446	446	68	3	336.57
447	447	51	2	23.26
448	448	88	3	358.25
449	449	39	2	995.02
450	450	65	3	812.02
451	451	81	3	878.41
452	452	4	5	948.42
453	453	29	2	344.74
454	454	51	2	92.27
455	455	49	5	959.84
456	456	79	2	419.83
457	457	74	2	428.91
458	458	40	5	332.31
459	459	70	2	210.52
460	460	18	5	543.11
461	461	26	2	312.14
462	462	91	5	909.11
463	463	56	2	657.29
464	464	73	2	320.59
465	465	72	5	947.91
466	466	16	2	320.69
467	467	19	1	765.84
468	468	53	4	306.53
469	469	96	3	156.05
470	470	25	1	135.76
471	471	4	5	618.24
472	472	78	5	613.69
473	473	77	2	234.53
474	474	4	3	84.00
475	475	100	4	138.28
476	476	78	4	712.75
477	477	48	2	852.02
478	478	63	4	141.69
479	479	25	2	37.04
480	480	98	1	924.88
481	481	53	2	742.91
482	482	26	2	70.74
483	483	57	5	492.00
484	484	42	4	887.26
485	485	55	4	776.56
486	486	78	4	720.88
487	487	51	5	938.50
488	488	74	5	537.94
489	489	83	1	522.53
490	490	58	4	827.05
491	491	6	2	520.59
492	492	51	1	559.35
493	493	67	1	193.71
494	494	57	4	884.09
495	495	100	3	463.58
496	496	55	3	614.46
497	497	7	5	903.25
498	498	60	4	94.90
499	499	65	1	183.69
500	500	75	5	139.49
501	501	53	3	453.18
502	502	23	4	591.77
503	503	92	2	882.25
504	504	12	3	327.13
505	505	84	2	719.06
506	506	16	1	118.48
507	507	58	3	89.79
508	508	91	4	727.51
509	509	66	5	949.06
510	510	49	5	383.32
511	511	99	2	911.78
512	512	73	2	166.15
513	513	19	2	769.54
514	514	7	4	311.21
515	515	94	4	292.05
516	516	24	1	898.15
517	517	26	1	623.82
518	518	33	1	460.89
519	519	64	5	807.61
520	520	78	4	241.45
521	521	76	4	456.02
522	522	57	1	602.61
523	523	1	2	881.87
524	524	36	5	629.86
525	525	27	1	188.73
526	526	8	3	41.50
527	527	5	5	837.99
528	528	39	3	919.86
529	529	7	1	419.46
530	530	23	2	673.06
531	531	79	5	573.85
532	532	72	2	965.50
533	533	96	5	363.03
534	534	5	1	768.90
535	535	42	3	897.14
536	536	9	4	843.25
537	537	9	3	472.99
538	538	16	3	332.23
539	539	53	5	213.59
540	540	27	5	62.84
541	541	74	5	986.27
542	542	62	5	933.29
543	543	91	3	429.49
544	544	41	3	527.24
545	545	80	3	926.54
546	546	79	5	498.42
547	547	94	4	494.55
548	548	24	5	236.33
549	549	38	2	6.57
550	550	4	4	626.71
551	551	16	2	799.77
552	552	54	4	50.22
553	553	45	5	806.21
554	554	28	1	641.77
555	555	89	3	257.89
556	556	9	3	303.48
557	557	71	3	767.43
558	558	15	3	344.31
559	559	93	5	617.30
560	560	4	2	197.85
561	561	44	4	915.67
562	562	5	2	483.61
563	563	81	4	891.71
564	564	69	3	464.70
565	565	53	1	835.10
566	566	39	5	725.61
567	567	41	5	537.67
568	568	27	5	686.38
569	569	46	1	968.80
570	570	36	1	342.12
571	571	49	5	842.35
572	572	74	5	392.23
573	573	77	1	864.41
574	574	97	3	706.03
575	575	41	1	274.87
576	576	12	4	876.79
577	577	48	4	829.48
578	578	39	2	526.95
579	579	23	1	376.97
580	580	5	2	912.87
581	581	57	5	29.79
582	582	62	5	158.15
583	583	44	4	733.05
584	584	68	3	775.88
585	585	19	1	822.21
586	586	67	2	208.96
587	587	5	4	390.26
588	588	67	1	9.09
589	589	6	5	871.64
590	590	43	4	888.85
591	591	14	5	766.58
592	592	96	3	27.35
593	593	98	3	640.02
594	594	27	3	204.35
595	595	37	3	534.08
596	596	99	4	672.10
597	597	35	2	161.55
598	598	15	1	957.55
599	599	72	5	106.76
600	600	70	3	551.07
601	601	35	2	942.62
602	602	37	5	248.36
603	603	10	3	614.58
604	604	44	5	445.99
605	605	17	1	472.91
606	606	87	1	110.29
607	607	7	1	428.91
608	608	23	5	890.93
609	609	81	4	617.62
610	610	40	3	817.54
611	611	92	5	83.07
612	612	97	4	569.38
613	613	12	4	101.68
614	614	40	4	472.72
615	615	29	2	860.93
616	616	79	3	912.38
617	617	51	2	700.42
618	618	86	3	789.05
619	619	42	4	489.58
620	620	9	4	117.21
621	621	62	4	845.69
622	622	37	3	605.81
623	623	17	5	107.31
624	624	92	1	328.91
625	625	84	1	792.68
626	626	69	4	403.41
627	627	53	2	622.15
628	628	71	2	973.05
629	629	50	1	343.67
630	630	89	5	433.56
631	631	56	5	787.60
632	632	70	2	177.05
633	633	86	1	739.93
634	634	92	5	836.73
635	635	15	5	597.50
636	636	42	5	102.07
637	637	57	2	311.19
638	638	52	1	599.67
639	639	88	5	771.72
640	640	49	3	496.33
641	641	85	1	94.99
642	642	18	5	902.84
643	643	82	1	757.54
644	644	85	2	455.26
645	645	38	4	616.88
646	646	58	2	209.43
647	647	41	3	571.85
648	648	87	3	917.99
649	649	56	3	989.35
650	650	75	1	612.82
651	651	66	4	847.55
652	652	38	1	372.01
653	653	71	1	5.84
654	654	72	3	114.04
655	655	37	1	238.83
656	656	90	5	396.90
657	657	41	4	408.60
658	658	56	5	214.95
659	659	23	4	143.23
660	660	72	4	843.27
661	661	47	4	158.34
662	662	86	2	138.47
663	663	10	1	148.13
664	664	63	4	974.13
665	665	18	1	141.40
666	666	54	4	893.22
667	667	90	5	929.73
668	668	80	2	456.67
669	669	55	5	820.15
670	670	50	3	229.39
671	671	55	5	12.39
672	672	64	2	712.86
673	673	35	4	926.01
674	674	74	3	38.26
675	675	5	5	485.37
676	676	48	1	581.79
677	677	89	1	146.23
678	678	94	5	982.68
679	679	97	3	467.15
680	680	11	5	889.58
681	681	12	2	474.62
682	682	95	1	684.97
683	683	70	5	315.62
684	684	7	3	536.82
685	685	2	4	456.31
686	686	61	5	734.41
687	687	54	3	959.82
688	688	38	3	171.50
689	689	89	5	749.93
690	690	94	5	263.88
691	691	81	4	579.67
692	692	74	1	657.38
693	693	38	5	32.13
694	694	63	1	131.06
695	695	10	3	255.54
696	696	79	3	278.57
697	697	33	1	741.98
698	698	78	2	909.67
699	699	95	2	660.20
700	700	48	2	264.69
701	701	90	2	487.01
702	702	68	1	345.79
703	703	11	2	596.97
704	704	20	4	753.24
705	705	53	4	241.52
706	706	57	2	214.59
707	707	94	3	59.00
708	708	34	1	57.21
709	709	60	4	478.37
710	710	61	5	237.26
711	711	88	4	476.74
712	712	19	5	870.06
713	713	2	3	926.66
714	714	58	4	679.42
715	715	68	1	101.78
716	716	69	3	955.45
717	717	56	5	917.53
718	718	35	3	273.70
719	719	13	3	655.42
720	720	51	4	773.51
721	721	96	2	734.91
722	722	76	2	521.83
723	723	87	2	316.39
724	724	2	1	831.70
725	725	2	4	102.11
726	726	14	4	354.41
727	727	93	3	255.38
728	728	5	1	620.68
729	729	8	5	657.67
730	730	28	5	639.25
731	731	91	1	90.87
732	732	78	2	378.70
733	733	98	5	803.38
734	734	24	1	696.48
735	735	33	3	469.15
736	736	10	4	922.16
737	737	36	4	693.07
738	738	86	3	260.79
739	739	100	1	280.62
740	740	8	4	391.26
741	741	8	3	954.87
742	742	34	2	442.93
743	743	63	2	611.64
744	744	23	4	112.78
745	745	70	4	222.08
746	746	83	1	912.13
747	747	92	3	107.67
748	748	10	1	572.92
749	749	33	4	23.65
750	750	64	2	653.95
751	751	1	1	665.62
752	752	35	2	700.85
753	753	51	5	8.68
754	754	91	4	480.27
755	755	52	1	541.89
756	756	1	4	953.43
757	757	100	4	125.48
758	758	69	3	336.44
759	759	39	4	59.86
760	760	83	1	368.16
761	761	44	1	841.13
762	762	98	3	648.91
763	763	23	5	44.10
764	764	50	2	302.08
765	765	50	1	631.83
766	766	46	4	89.35
767	767	81	4	735.91
768	768	18	1	196.93
769	769	93	5	242.05
770	770	50	1	792.98
771	771	83	3	501.69
772	772	58	1	41.82
773	773	8	3	788.05
774	774	6	4	122.48
775	775	84	5	460.62
776	776	87	5	153.06
777	777	75	2	924.27
778	778	5	2	490.96
779	779	3	4	906.74
780	780	80	1	246.23
781	781	84	2	19.28
782	782	81	1	904.23
783	783	13	4	612.56
784	784	76	1	817.89
785	785	14	1	499.16
786	786	79	2	67.73
787	787	26	4	340.32
788	788	95	4	327.29
789	789	88	5	547.61
790	790	42	2	764.64
791	791	76	2	338.49
792	792	16	3	145.39
793	793	54	2	697.12
794	794	71	2	441.03
795	795	75	1	137.57
796	796	81	5	378.87
797	797	21	1	879.35
798	798	11	1	12.18
799	799	12	5	886.59
800	800	54	4	693.20
801	801	27	2	640.99
802	802	67	4	414.56
803	803	23	5	692.52
804	804	77	2	717.90
805	805	79	1	628.43
806	806	39	3	421.27
807	807	72	2	195.75
808	808	68	1	620.21
809	809	98	5	509.50
810	810	60	2	279.77
811	811	25	1	796.83
812	812	88	4	499.53
813	813	21	1	58.70
814	814	47	3	213.33
815	815	33	3	618.12
816	816	98	4	48.06
817	817	95	1	924.31
818	818	23	2	785.78
819	819	63	5	120.37
820	820	31	4	594.15
821	821	42	4	202.56
822	822	87	3	233.68
823	823	15	3	231.42
824	824	31	4	869.67
825	825	49	2	78.09
826	826	75	4	59.01
827	827	56	2	219.87
828	828	79	4	181.99
829	829	48	2	459.99
830	830	25	3	974.70
831	831	26	3	131.45
832	832	89	5	64.29
833	833	18	1	851.54
834	834	59	4	175.17
835	835	44	2	886.09
836	836	78	2	789.81
837	837	82	5	905.14
838	838	74	5	854.87
839	839	12	4	856.83
840	840	63	2	593.03
841	841	60	3	19.42
842	842	55	2	251.34
843	843	56	5	226.07
844	844	76	2	913.27
845	845	1	4	979.30
846	846	6	4	734.08
847	847	65	1	428.14
848	848	51	4	809.86
849	849	90	1	454.73
850	850	31	1	560.14
851	851	2	4	949.23
852	852	17	3	299.02
853	853	83	1	20.83
854	854	86	3	165.83
855	855	59	5	747.80
856	856	4	4	465.98
857	857	18	4	188.84
858	858	48	4	704.68
859	859	1	1	387.57
860	860	89	3	532.73
861	861	38	4	753.37
862	862	90	5	544.18
863	863	27	1	621.73
864	864	43	1	516.65
865	865	87	3	887.65
866	866	15	4	368.40
867	867	80	1	368.38
868	868	23	5	705.64
869	869	72	2	142.58
870	870	43	2	541.40
871	871	84	4	737.96
872	872	97	5	870.90
873	873	90	2	753.65
874	874	98	2	323.54
875	875	35	5	681.15
876	876	36	1	67.99
877	877	45	4	488.31
878	878	68	1	472.34
879	879	69	5	899.05
880	880	58	5	370.94
881	881	87	1	192.22
882	882	59	1	84.69
883	883	23	3	957.51
884	884	10	1	168.78
885	885	15	2	498.35
886	886	27	5	951.39
887	887	3	3	419.04
888	888	88	5	931.13
889	889	61	3	422.61
890	890	95	1	294.77
891	891	9	1	871.56
892	892	30	5	645.80
893	893	53	5	345.74
894	894	83	3	488.23
895	895	86	5	841.86
896	896	57	4	307.26
897	897	17	3	175.71
898	898	34	2	486.34
899	899	37	1	152.45
900	900	37	4	955.48
901	901	80	2	712.54
902	902	37	2	972.37
903	903	91	2	165.29
904	904	15	1	992.81
905	905	74	2	443.24
906	906	48	2	208.92
907	907	91	1	666.56
908	908	45	2	375.68
909	909	70	2	535.44
910	910	16	1	407.13
911	911	64	2	947.10
912	912	41	2	9.27
913	913	95	5	974.75
914	914	43	3	476.07
915	915	38	5	667.89
916	916	73	4	341.65
917	917	15	4	899.77
918	918	18	5	121.17
919	919	4	4	618.82
920	920	29	4	360.25
921	921	42	1	609.50
922	922	25	5	528.28
923	923	99	3	199.54
924	924	11	5	849.35
925	925	87	1	974.98
926	926	51	2	492.52
927	927	78	5	513.49
928	928	8	3	400.17
929	929	92	4	372.41
930	930	48	1	287.94
931	931	45	3	976.66
932	932	72	1	219.40
933	933	57	4	803.86
934	934	37	2	805.84
935	935	55	4	143.73
936	936	76	5	90.56
937	937	27	3	476.77
938	938	68	3	70.72
939	939	76	4	92.92
940	940	53	3	417.03
941	941	72	4	710.99
942	942	97	2	203.06
943	943	49	3	555.54
944	944	6	3	834.58
945	945	39	4	560.93
946	946	60	2	31.68
947	947	1	2	266.10
948	948	82	4	128.43
949	949	86	3	419.65
950	950	63	2	33.27
951	951	98	3	495.09
952	952	9	5	746.09
953	953	75	4	567.18
954	954	34	4	973.41
955	955	16	3	514.45
956	956	74	1	845.21
957	957	21	5	63.16
958	958	41	4	878.05
959	959	18	3	167.33
960	960	35	3	422.00
961	961	46	1	293.12
962	962	68	1	515.78
963	963	99	2	765.10
964	964	77	2	545.45
965	965	41	3	274.83
966	966	90	3	100.26
967	967	75	3	823.37
968	968	2	2	520.06
969	969	48	4	414.52
970	970	21	1	221.57
971	971	65	2	831.58
972	972	72	5	690.51
973	973	68	5	713.27
974	974	90	1	419.84
975	975	10	1	818.93
976	976	3	4	351.12
977	977	89	3	143.18
978	978	57	5	524.98
979	979	44	2	710.64
980	980	4	1	226.02
981	981	89	2	688.92
982	982	40	2	213.58
983	983	11	4	691.67
984	984	15	1	23.69
985	985	62	4	47.26
986	986	14	1	793.30
987	987	66	5	63.91
988	988	16	3	48.02
989	989	39	1	755.02
990	990	16	5	209.17
991	991	26	2	671.58
992	992	4	1	149.68
993	993	96	3	948.10
994	994	45	3	164.59
995	995	65	5	245.37
996	996	73	1	103.51
997	997	75	1	530.67
998	998	92	2	963.48
999	999	22	5	9.30
1000	1000	93	1	923.69
1001	943	65	4	369.26
1002	604	24	4	674.48
1003	110	24	3	980.41
1004	435	28	5	231.19
1005	116	98	3	127.87
1006	113	67	2	497.84
1007	370	91	3	558.79
1008	42	11	3	495.75
1009	395	37	4	601.79
1010	320	88	4	229.52
1011	418	38	4	192.65
1012	72	61	3	183.22
1013	691	63	1	398.99
1014	536	85	1	123.50
1015	405	52	5	976.71
1016	760	22	1	366.53
1017	204	44	2	596.39
1018	414	16	2	838.08
1019	743	64	3	765.23
1020	785	75	5	276.33
1021	809	83	4	358.96
1022	683	78	4	986.60
1023	151	99	4	112.39
1024	257	63	4	234.44
1025	966	18	1	104.01
1026	55	9	4	679.04
1027	996	23	4	605.96
1028	335	20	3	623.23
1029	99	98	1	662.11
1030	533	99	4	792.98
1031	207	38	4	492.31
1032	268	70	3	809.62
1033	554	70	1	951.87
1034	33	56	1	386.33
1035	323	49	4	461.90
1036	34	23	5	660.45
1037	799	39	2	493.53
1038	138	40	4	489.53
1039	113	73	4	661.12
1040	702	70	5	472.00
1041	576	21	5	60.40
1042	270	64	5	970.05
1043	632	87	3	766.87
1044	292	42	1	32.98
1045	47	17	3	351.78
1046	760	75	1	765.60
1047	641	44	4	101.77
1048	354	46	4	354.16
1049	678	32	2	238.21
1050	320	76	1	909.93
1051	68	40	1	340.57
1052	21	69	3	42.15
1053	674	55	5	516.67
1054	432	35	1	696.78
1055	603	3	3	380.47
1056	400	42	5	102.14
1057	501	13	2	338.95
1058	515	98	3	170.63
1059	307	47	4	205.55
1060	651	10	5	217.80
1061	272	7	3	995.25
1062	412	29	5	743.43
1063	95	92	5	99.17
1064	345	35	1	568.03
1065	544	61	4	213.48
1066	815	10	3	506.61
1067	308	56	5	316.47
1068	425	52	3	626.21
1069	465	86	5	184.52
1070	20	81	5	862.53
1071	591	64	2	661.84
1072	844	96	4	271.33
1073	654	69	5	852.66
1074	929	56	5	727.26
1075	62	67	2	367.09
1076	152	31	2	746.95
1077	784	39	4	412.80
1078	881	9	2	845.89
1079	274	37	2	259.91
1080	616	31	4	242.05
1081	154	25	1	249.11
1082	848	40	4	487.47
1083	447	55	1	205.78
1084	280	18	1	261.85
1085	823	36	5	179.93
1086	873	6	4	782.54
1087	57	11	3	602.99
1088	888	9	4	896.39
1089	688	85	1	399.51
1090	860	93	2	239.62
1091	585	95	5	932.34
1092	535	86	5	948.98
1093	954	68	3	498.47
1094	93	31	5	126.54
1095	827	41	3	832.34
1096	755	50	2	934.89
1097	224	19	1	179.10
1098	994	36	4	410.93
1099	884	76	1	492.42
1100	384	90	1	319.59
1101	434	61	2	962.54
1102	901	19	3	477.37
1103	377	40	1	646.53
1104	36	95	1	691.54
1105	808	86	2	256.46
1106	394	40	3	902.74
1107	702	16	5	866.75
1108	879	57	4	12.82
1109	984	51	3	304.08
1110	959	97	2	300.64
1111	881	21	4	632.56
1112	901	99	4	789.58
1113	281	11	4	473.26
1114	423	43	4	876.50
1115	840	13	2	699.29
1116	519	9	3	423.35
1117	747	71	3	455.54
1118	29	98	1	642.52
1119	189	81	4	791.27
1120	140	1	4	203.87
1121	313	41	5	86.74
1122	162	32	5	714.28
1123	787	84	2	846.88
1124	703	53	3	453.78
1125	895	95	2	264.12
1126	704	76	3	799.73
1127	425	48	2	396.13
1128	387	74	2	25.61
1129	24	72	5	627.87
1130	929	12	4	202.08
1131	719	22	1	403.63
1132	440	77	3	153.36
1133	982	48	2	946.56
1134	121	2	5	437.55
1135	943	59	4	122.80
1136	731	27	2	945.38
1137	833	35	3	746.96
1138	392	17	4	856.20
1139	615	28	3	727.35
1140	194	54	2	411.07
1141	150	4	3	975.27
1142	242	80	4	906.88
1143	379	75	4	90.22
1144	481	18	3	973.55
1145	408	88	2	714.06
1146	726	55	5	259.69
1147	98	72	1	56.80
1148	954	31	4	907.78
1149	621	86	5	710.31
1150	830	6	1	257.13
1151	635	49	3	976.66
1152	688	48	2	967.25
1153	573	6	5	183.30
1154	174	65	4	929.74
1155	899	60	2	94.11
1156	728	68	4	145.94
1157	120	41	1	977.65
1158	512	36	3	925.68
1159	290	34	5	829.61
1160	949	34	5	316.13
1161	915	22	3	737.45
1162	504	98	2	557.34
1163	946	85	4	57.90
1164	153	7	2	187.04
1165	482	34	2	706.73
1166	447	15	4	45.55
1167	366	91	5	487.29
1168	505	15	2	127.91
1169	96	27	3	184.57
1170	173	96	5	822.64
1171	577	85	5	216.12
1172	995	1	5	767.25
1173	185	54	1	249.68
1174	511	87	1	887.04
1175	27	37	1	396.80
1176	605	14	3	157.85
1177	84	59	4	456.33
1178	979	35	5	659.06
1179	338	6	5	950.19
1180	333	94	5	133.54
1181	884	7	3	326.23
1182	57	96	1	548.87
1183	617	49	1	401.47
1184	183	31	4	93.65
1185	873	27	2	391.17
1186	413	37	2	124.88
1187	503	56	3	903.31
1188	618	17	3	666.53
1189	853	48	5	203.67
1190	457	50	4	271.87
1191	615	55	1	756.95
1192	831	48	5	190.24
1193	646	55	1	45.20
1194	350	60	2	648.72
1195	731	20	4	529.12
1196	663	68	1	293.96
1197	448	11	4	303.59
1198	131	88	3	841.49
1199	536	55	3	570.12
1200	565	10	1	515.33
1201	523	55	4	98.92
1202	677	93	5	812.95
1203	364	33	5	86.28
1204	516	3	1	741.07
1205	474	23	2	842.85
1206	47	11	4	876.49
1207	305	41	5	724.75
1208	776	86	4	625.07
1209	272	44	2	214.80
1210	81	96	5	262.76
1211	690	14	4	536.17
1212	6	51	1	18.22
1213	672	62	4	692.66
1214	890	85	5	726.56
1215	311	80	5	363.56
1216	690	89	4	804.81
1217	90	17	2	18.79
1218	115	3	2	858.86
1219	215	62	2	650.84
1220	447	81	5	194.77
1221	475	19	4	424.35
1222	120	22	2	739.35
1223	456	63	4	24.51
1224	461	75	2	205.13
1225	584	51	1	336.85
1226	106	81	4	978.61
1227	869	64	5	597.26
1228	568	38	1	489.57
1229	498	66	5	725.27
1230	958	87	4	235.51
1231	63	68	1	424.47
1232	324	71	1	271.24
1233	664	54	4	121.24
1234	638	83	3	450.64
1235	447	3	2	291.28
1236	197	61	3	440.48
1237	520	29	5	908.62
1238	348	78	4	135.37
1239	301	93	4	959.04
1240	854	87	3	796.20
1241	819	21	5	210.97
1242	708	96	1	668.05
1243	133	23	2	160.38
1244	504	13	4	942.40
1245	506	39	2	213.18
1246	49	3	3	880.62
1247	366	87	2	178.67
1248	881	65	1	806.97
1249	346	56	1	618.86
1250	124	72	2	488.45
1251	349	46	1	770.47
1252	571	35	2	853.29
1253	895	66	5	670.47
1254	724	7	4	799.19
1255	986	97	1	973.81
1256	801	79	5	782.46
1257	971	14	5	46.72
1258	108	22	1	870.64
1259	933	47	2	728.98
1260	726	57	5	500.40
1261	892	13	2	648.21
1262	343	18	1	848.50
1263	450	54	1	248.84
1264	829	61	3	290.04
1265	176	11	3	375.20
1266	773	54	3	630.66
1267	252	20	5	424.19
1268	234	18	4	415.93
1269	420	59	5	794.84
1270	371	4	4	149.71
1271	11	92	5	942.98
1272	87	44	3	404.24
1273	791	22	4	66.10
1274	677	83	2	902.10
1275	60	81	5	971.83
1276	430	52	5	873.31
1277	739	96	3	908.78
1278	9	36	5	611.74
1279	151	90	4	448.51
1280	211	70	5	788.61
1281	668	57	3	887.35
1282	801	84	4	775.75
1283	903	39	1	41.75
1284	343	50	2	522.35
1285	554	37	2	97.26
1286	566	40	5	343.66
1287	651	21	1	32.72
1288	816	70	5	262.14
1289	853	100	3	727.15
1290	518	15	1	841.53
1291	266	81	5	357.35
1292	49	97	1	451.04
1293	587	95	1	455.43
1294	242	96	5	567.20
1295	916	81	5	844.43
1296	240	45	3	287.83
1297	804	92	5	673.40
1298	732	49	5	738.09
1299	108	42	5	583.87
1300	843	100	3	456.58
1301	151	92	4	828.47
1302	84	12	1	427.34
1303	134	61	2	448.49
1304	379	87	5	405.34
1305	573	67	4	871.78
1306	599	64	4	995.53
1307	706	63	4	823.87
1308	148	65	2	486.86
1309	469	17	5	863.09
1310	121	89	2	457.70
1311	34	96	2	943.41
1312	379	16	5	852.20
1313	113	16	3	573.33
1314	42	67	2	122.04
1315	313	48	3	297.22
1316	29	19	2	784.09
1317	432	7	3	888.72
1318	221	24	4	7.07
1319	561	45	1	870.20
1320	428	62	5	312.84
1321	464	44	4	477.38
1322	738	78	2	762.38
1323	517	82	4	762.11
1324	684	58	2	866.15
1325	334	12	5	665.52
1326	420	50	2	899.84
1327	348	70	1	957.33
1328	912	57	3	647.04
1329	887	22	1	573.56
1330	816	99	3	562.68
1331	127	83	5	89.64
1332	979	80	5	578.39
1333	55	73	5	193.26
1334	488	65	1	124.56
1335	959	69	2	961.60
1336	282	27	2	829.71
1337	860	75	4	89.14
1338	547	78	3	404.39
1339	47	63	1	342.92
1340	25	68	3	384.72
1341	94	15	1	543.53
1342	293	19	2	259.02
1343	92	20	3	951.45
1344	695	22	1	615.79
1345	334	24	1	714.02
1346	306	50	1	323.12
1347	423	42	3	378.26
1348	848	16	1	206.34
1349	771	77	5	240.07
1350	521	97	5	387.74
1351	118	35	1	321.43
1352	567	53	1	486.27
1353	418	82	2	913.25
1354	20	35	5	962.69
1355	692	13	2	763.40
1356	668	17	3	569.84
1357	457	11	5	207.24
1358	992	19	3	542.20
1359	173	32	5	951.90
1360	985	72	4	46.54
1361	833	60	5	292.51
1362	996	22	1	64.81
1363	944	62	3	599.28
1364	860	88	4	998.25
1365	863	81	2	586.65
1366	523	37	1	165.45
1367	547	73	1	303.83
1368	405	90	1	830.52
1369	743	72	3	878.01
1370	216	79	5	956.67
1371	326	88	3	636.36
1372	771	91	4	276.38
1373	679	42	3	214.36
1374	983	77	3	20.78
1375	709	18	1	610.13
1376	5	2	2	415.68
1377	917	90	4	762.89
1378	552	11	1	540.42
1379	914	86	4	673.21
1380	362	49	5	360.82
1381	182	99	1	129.02
1382	380	25	4	14.31
1383	761	3	3	681.47
1384	727	46	2	94.43
1385	629	81	3	808.56
1386	227	30	4	966.49
1387	38	36	4	904.08
1388	724	78	2	12.09
1389	841	82	4	115.28
1390	285	73	5	496.05
1391	566	25	5	673.14
1392	618	73	2	69.97
1393	132	96	1	131.67
1394	956	73	2	880.72
1395	747	36	2	847.58
1396	24	89	5	615.77
1397	698	72	4	6.94
1398	438	83	1	853.74
1399	331	56	4	277.39
1400	697	67	4	497.60
1401	530	98	1	883.50
1402	230	7	3	917.88
1403	546	58	3	10.13
1404	200	43	1	879.82
1405	828	4	2	977.23
1406	434	10	2	200.70
1407	338	40	1	627.24
1408	100	4	4	434.36
1409	25	76	3	840.46
1410	254	14	4	241.93
1411	349	7	3	521.56
1412	243	10	5	620.85
1413	641	58	5	129.08
1414	998	8	1	380.13
1415	912	89	1	782.95
1416	64	57	1	304.66
1417	642	56	1	106.22
1418	58	72	1	298.15
1419	391	52	1	618.60
1420	421	30	5	787.75
1421	639	2	4	386.62
1422	815	55	5	620.52
1423	348	84	1	456.35
1424	337	76	2	112.36
1425	13	77	1	594.33
1426	861	25	5	130.23
1427	522	33	3	423.48
1428	743	80	4	189.81
1429	141	6	1	131.91
1430	599	56	5	958.98
1431	773	46	3	585.16
1432	555	100	2	151.52
1433	317	78	3	294.32
1434	994	2	5	587.92
1435	695	19	1	240.96
1436	839	72	1	424.53
1437	201	26	2	785.55
1438	350	25	4	695.61
1439	479	77	3	851.90
1440	580	43	5	302.83
1441	337	21	1	456.58
1442	809	6	4	223.09
1443	4	82	2	694.06
1444	478	80	2	242.58
1445	753	99	3	807.43
1446	385	27	4	188.14
1447	7	47	1	78.29
1448	31	72	1	146.55
1449	451	25	5	912.23
1450	369	6	1	202.93
1451	291	23	2	885.07
1452	737	23	3	847.45
1453	252	23	2	26.36
1454	864	34	1	25.87
1455	694	18	4	655.94
1456	907	15	3	935.50
1457	313	59	2	372.42
1458	382	85	2	940.51
1459	819	80	4	878.12
1460	67	16	2	882.43
1461	134	25	2	534.36
1462	712	48	3	600.95
1463	652	32	1	763.50
1464	602	25	5	297.42
1465	153	42	2	57.94
1466	815	36	2	851.39
1467	992	75	4	212.98
1468	84	61	5	69.48
1469	521	50	5	377.02
1470	532	60	2	324.89
1471	383	68	4	716.36
1472	507	61	3	582.70
1473	654	75	1	210.96
1474	917	26	4	862.99
1475	406	28	3	427.47
1476	161	48	3	552.25
1477	138	97	1	298.28
1478	532	46	2	585.46
1479	477	66	5	339.36
1480	462	60	4	411.50
1481	824	64	3	276.38
1482	26	23	4	237.39
1483	661	10	3	901.07
1484	302	65	5	548.37
1485	81	36	2	102.82
1486	74	47	1	547.75
1487	342	26	3	253.52
1488	764	99	3	194.50
1489	619	18	5	911.91
1490	9	99	3	285.15
1491	355	52	4	821.93
1492	776	84	1	474.17
1493	525	98	2	865.27
1494	234	30	2	476.59
1495	529	76	5	758.08
1496	740	60	3	792.16
1497	321	25	4	770.51
1498	715	54	2	441.05
1499	874	72	1	377.45
1500	592	17	3	942.69
1501	10	64	3	342.78
1502	430	55	4	763.26
1503	708	69	3	329.12
1504	24	73	1	921.61
1505	158	43	5	631.06
1506	618	78	5	866.74
1507	391	27	4	68.33
1508	396	25	4	112.99
1509	584	58	3	97.68
1510	107	87	5	181.57
1511	847	89	5	490.68
1512	192	26	1	910.88
1513	396	37	2	236.64
1514	676	68	1	456.94
1515	378	67	1	175.79
1516	881	53	4	161.09
1517	114	17	5	420.90
1518	761	9	4	954.37
1519	887	27	2	870.23
1520	318	56	4	162.83
1521	589	40	5	206.76
1522	734	88	4	278.79
1523	8	19	4	68.59
1524	409	78	2	527.70
1525	933	73	4	462.44
1526	590	6	1	291.18
1527	903	59	3	701.11
1528	729	39	4	614.35
1529	830	23	4	252.64
1530	922	80	4	460.08
1531	933	85	2	699.33
1532	98	51	1	243.26
1533	892	21	3	882.26
1534	551	38	1	698.86
1535	740	28	4	413.81
1536	781	71	1	994.34
1537	79	97	1	506.37
1538	799	42	4	453.23
1539	259	27	5	49.37
1540	655	89	4	383.87
1541	764	52	2	399.29
1542	11	33	1	709.85
1543	140	42	4	486.85
1544	70	11	5	658.08
1545	731	57	2	472.96
1546	286	21	2	838.46
1547	622	13	2	297.38
1548	548	95	4	172.44
1549	688	98	1	678.32
1550	158	57	3	181.87
1551	732	5	5	219.87
1552	714	7	5	642.17
1553	734	85	1	393.27
1554	316	57	1	599.62
1555	50	99	4	767.51
1556	952	32	3	908.30
1557	205	12	1	424.15
1558	15	44	2	680.88
1559	65	29	1	797.14
1560	851	86	2	724.67
1561	46	54	5	112.04
1562	335	42	5	628.03
1563	640	27	5	397.69
1564	439	16	2	217.50
1565	366	42	2	19.90
1566	670	41	1	391.85
1567	470	29	1	659.01
1568	286	84	5	371.77
1569	69	28	4	304.73
1570	614	64	1	713.26
1571	811	73	2	255.43
1572	98	77	3	980.53
1573	714	50	2	335.05
1574	651	98	3	977.15
1575	683	62	1	338.09
1576	624	75	4	385.08
1577	656	95	2	505.40
1578	722	2	2	26.09
1579	778	16	3	239.98
1580	439	97	2	621.05
1581	62	18	3	500.73
1582	207	20	4	208.16
1583	39	31	5	987.62
1584	455	95	3	138.46
1585	326	83	1	522.75
1586	425	83	3	751.05
1587	235	94	3	345.67
1588	56	86	2	801.64
1589	713	93	2	609.41
1590	391	67	3	187.44
1591	645	1	1	869.65
1592	72	25	1	635.56
1593	145	27	2	96.21
1594	607	71	2	239.89
1595	81	55	4	314.59
1596	739	26	2	426.47
1597	621	32	3	288.64
1598	460	82	2	275.23
1599	801	62	1	950.31
1600	369	51	4	171.76
1601	452	55	5	610.74
1602	444	98	2	819.69
1603	813	62	1	762.36
1604	438	11	3	596.61
1605	157	71	2	260.75
1606	475	40	4	286.53
1607	576	78	4	76.51
1608	140	92	4	199.54
1609	939	25	1	17.76
1610	513	94	3	493.50
1611	948	54	4	969.67
1612	383	50	4	310.96
1613	419	5	1	387.52
1614	580	21	2	763.37
1615	981	33	3	511.55
1616	501	82	3	697.28
1617	667	50	4	736.25
1618	249	62	1	920.94
1619	371	81	1	698.29
1620	661	19	3	606.80
1621	967	88	2	257.76
1622	617	75	2	17.26
1623	790	12	4	400.28
1624	601	11	5	909.49
1625	898	55	2	829.77
1626	259	89	3	502.64
1627	546	85	4	587.56
1628	752	53	1	113.62
1629	587	100	3	814.34
1630	276	96	2	929.44
1631	408	90	3	11.38
1632	173	63	1	101.29
1633	793	90	4	526.81
1634	671	37	4	174.61
1635	384	24	2	201.83
1636	187	65	1	452.96
1637	834	28	2	204.74
1638	768	24	2	262.80
1639	924	53	4	628.08
1640	640	14	2	84.33
1641	88	49	1	280.10
1642	351	4	5	238.37
1643	497	87	1	14.45
1644	273	97	1	666.33
1645	100	28	5	792.04
1646	385	78	5	985.98
1647	780	35	4	475.39
1648	346	78	4	339.53
1649	699	44	3	816.95
1650	964	47	4	381.17
1651	59	46	3	806.43
1652	4	59	4	725.87
1653	910	18	1	603.30
1654	890	68	3	950.36
1655	770	32	3	454.21
1656	703	85	4	516.82
1657	677	25	1	985.26
1658	981	42	1	634.97
1659	895	6	3	678.86
1660	240	78	4	402.76
1661	628	11	3	430.35
1662	954	61	1	734.87
1663	301	78	2	712.67
1664	891	67	5	785.15
1665	734	65	1	132.09
1666	816	12	3	832.36
1667	562	60	2	896.03
1668	978	15	4	663.67
1669	247	32	2	174.41
1670	967	85	1	109.84
1671	733	4	2	928.43
1672	335	50	3	224.05
1673	264	86	4	950.79
1674	687	16	2	922.20
1675	649	93	4	94.90
1676	709	43	2	931.19
1677	785	77	1	645.12
1678	387	92	4	655.00
1679	804	72	4	808.60
1680	229	34	1	294.23
1681	115	12	3	741.14
1682	960	25	1	574.40
1683	131	41	4	578.46
1684	2	40	1	591.52
1685	195	50	4	322.73
1686	374	87	2	521.63
1687	617	76	2	110.95
1688	10	69	4	319.03
1689	836	38	2	501.83
1690	616	37	2	747.58
1691	870	90	1	600.29
1692	317	65	1	276.81
1693	869	91	5	480.41
1694	849	28	4	294.75
1695	990	49	1	980.26
1696	342	20	2	847.98
1697	957	29	1	922.62
1698	795	23	4	728.03
1699	307	85	2	990.12
1700	562	51	3	424.90
1701	485	45	4	393.72
1702	541	94	3	285.67
1703	946	25	5	396.41
1704	135	42	5	865.66
1705	56	91	3	459.79
1706	168	74	2	444.23
1707	495	38	2	213.51
1708	824	96	2	735.91
1709	10	47	5	106.34
1710	805	19	4	949.70
1711	438	87	2	925.43
1712	99	46	4	183.56
1713	54	16	5	651.20
1714	608	56	2	628.21
1715	414	32	1	123.09
1716	407	63	3	688.86
1717	978	23	4	776.19
1718	815	86	1	778.06
1719	886	84	4	278.56
1720	669	57	3	16.53
1721	120	11	1	491.28
1722	685	66	2	27.89
1723	587	74	4	277.08
1724	764	13	5	185.01
1725	496	83	4	301.57
1726	129	13	3	68.12
1727	931	69	2	407.90
1728	718	3	4	557.72
1729	550	68	4	68.55
1730	858	75	5	714.47
1731	810	84	1	753.99
1732	213	85	1	184.58
1733	614	89	2	10.29
1734	458	41	1	43.91
1735	589	27	2	92.29
1736	263	97	1	89.10
1737	306	47	5	175.57
1738	968	85	1	251.85
1739	48	67	3	660.20
1740	456	18	5	492.50
1741	321	67	3	607.54
1742	523	27	1	663.64
1743	46	31	1	191.95
1744	307	28	2	603.53
1745	222	76	3	280.73
1746	747	80	4	78.91
1747	262	34	4	650.87
1748	168	52	4	87.75
1749	261	87	4	939.56
1750	147	69	2	75.13
1751	751	35	2	715.16
1752	578	85	5	606.32
1753	430	20	3	991.49
1754	445	49	1	963.23
1755	254	10	3	128.87
1756	113	88	5	409.34
1757	338	82	1	365.64
1758	342	100	3	150.45
1759	818	29	3	14.80
1760	387	29	4	951.07
1761	802	16	2	528.32
1762	897	40	5	821.42
1763	502	13	5	351.81
1764	586	37	5	274.43
1765	102	7	2	321.09
1766	186	45	5	553.36
1767	904	52	4	593.76
1768	266	2	5	713.94
1769	674	17	2	381.53
1770	754	35	1	917.93
1771	655	48	2	679.15
1772	429	91	4	187.01
1773	363	60	5	290.10
1774	976	55	5	941.03
1775	903	30	3	636.82
1776	90	40	4	770.95
1777	866	12	1	81.23
1778	246	12	2	576.86
1779	87	96	3	555.83
1780	505	2	4	677.97
1781	955	94	2	481.78
1782	528	88	5	698.69
1783	416	2	5	194.04
1784	852	96	1	714.88
1785	720	69	3	247.76
1786	757	85	5	684.97
1787	44	78	4	963.86
1788	691	98	5	903.38
1789	180	10	3	839.37
1790	527	46	1	425.19
1791	389	22	3	968.91
1792	347	87	2	831.74
1793	872	99	1	293.32
1794	272	28	1	738.60
1795	583	51	2	922.52
1796	952	83	5	825.77
1797	37	60	5	848.26
1798	7	79	4	331.58
1799	363	14	1	352.62
1800	740	24	4	357.41
1801	104	56	4	201.36
1802	542	66	2	413.25
1803	936	63	1	159.70
1804	673	33	2	472.87
1805	384	39	3	430.77
1806	187	69	3	113.04
1807	450	85	4	165.86
1808	363	96	4	10.78
1809	905	91	2	115.00
1810	292	6	2	397.18
1811	762	43	1	164.35
1812	204	62	3	123.08
1813	501	71	4	800.02
1814	732	17	3	751.58
1815	800	52	5	726.64
1816	760	50	2	114.07
1817	111	3	2	159.61
1818	513	2	2	56.73
1819	850	44	4	975.58
1820	756	2	4	482.31
1821	289	63	1	761.33
1822	254	80	2	729.87
1823	192	32	3	767.13
1824	885	34	2	667.33
1825	440	26	4	707.22
1826	830	14	5	612.43
1827	194	76	2	233.01
1828	136	52	1	277.22
1829	197	19	4	22.56
1830	886	7	4	409.85
1831	314	90	2	225.44
1832	437	62	1	511.80
1833	660	7	3	114.39
1834	373	36	3	712.32
1835	253	41	1	185.66
1836	1	7	3	215.71
1837	484	36	5	105.16
1838	190	33	4	366.40
1839	312	15	1	669.93
1840	700	71	2	334.22
1841	760	47	5	530.69
1842	381	31	3	213.77
1843	394	12	1	134.70
1844	761	78	1	45.79
1845	992	84	2	196.77
1846	457	13	1	941.17
1847	634	44	3	726.00
1848	780	26	5	721.44
1849	45	17	2	420.70
1850	729	33	5	974.28
1851	917	47	4	631.09
1852	121	56	1	484.92
1853	537	65	1	170.93
1854	281	90	2	292.92
1855	979	73	1	794.62
1856	711	25	4	497.06
1857	546	66	1	169.53
1858	769	66	4	564.12
1859	400	52	5	274.87
1860	189	1	2	573.47
1861	607	90	1	878.88
1862	810	66	4	505.79
1863	738	68	3	306.59
1864	226	38	3	553.84
1865	176	29	1	535.36
1866	299	6	2	941.39
1867	285	18	3	873.14
1868	53	83	2	988.60
1869	216	69	1	6.39
1870	356	81	5	971.39
1871	333	11	5	267.45
1872	137	53	5	298.13
1873	59	81	1	823.99
1874	225	94	3	180.67
1875	995	3	5	658.37
1876	889	100	5	110.80
1877	764	89	4	944.98
1878	264	81	5	552.57
1879	837	57	2	327.32
1880	209	75	4	159.71
1881	238	94	4	371.43
1882	924	62	1	497.99
1883	471	24	2	192.73
1884	503	94	2	648.68
1885	22	40	2	884.94
1886	838	51	5	191.72
1887	147	10	4	248.78
1888	931	83	4	104.63
1889	540	18	1	604.67
1890	387	50	1	114.38
1891	14	98	1	136.39
1892	789	11	3	146.78
1893	643	77	1	792.65
1894	10	14	5	736.71
1895	347	91	1	206.11
1896	492	98	5	892.04
1897	836	21	3	334.77
1898	159	32	1	545.27
1899	274	81	5	127.34
1900	845	6	1	546.37
1901	106	66	4	145.98
1902	935	29	1	230.32
1903	395	19	3	656.43
1904	232	88	4	687.65
1905	733	15	4	173.54
1906	113	29	1	955.73
1907	289	46	1	617.00
1908	122	47	1	895.21
1909	620	20	2	431.06
1910	343	77	2	680.36
1911	154	86	3	626.01
1912	294	45	1	274.47
1913	512	85	3	932.28
1914	831	92	1	789.12
1915	883	20	2	323.33
1916	400	58	4	814.76
1917	116	74	4	958.83
1918	286	19	1	326.12
1919	131	24	4	355.49
1920	507	55	4	694.26
1921	424	78	3	142.39
1922	967	84	2	385.89
1923	563	64	5	535.57
1924	546	69	2	387.32
1925	595	92	4	528.78
1926	796	89	2	703.87
1927	241	47	1	207.06
1928	872	3	3	560.02
1929	981	18	1	64.22
1930	358	47	2	297.93
1931	148	71	4	246.04
1932	848	29	1	747.51
1933	121	90	2	380.20
1934	989	55	3	58.76
1935	109	85	5	78.33
1936	858	77	2	35.00
1937	375	19	1	248.58
1938	13	73	4	153.82
1939	187	61	2	748.62
1940	716	39	4	414.05
1941	346	57	1	290.05
1942	160	8	1	605.55
1943	178	65	2	15.80
1944	853	55	4	555.83
1945	850	34	5	503.86
1946	727	30	4	930.86
1947	279	12	5	380.29
1948	974	17	2	403.00
1949	58	29	4	187.59
1950	764	72	5	841.66
1951	837	89	4	479.55
1952	669	83	4	827.29
1953	169	7	3	647.77
1954	200	35	1	108.77
1955	372	78	3	32.88
1956	289	21	5	110.83
1957	217	77	1	756.98
1958	317	25	5	205.52
1959	952	5	2	272.55
1960	584	73	1	565.36
1961	810	62	1	52.76
1962	96	40	1	979.66
1963	770	37	4	502.21
1964	323	97	4	726.33
1965	998	17	1	334.33
1966	919	95	5	105.40
1967	827	100	2	28.54
1968	816	49	4	587.84
1969	873	5	3	165.26
1970	699	60	1	884.89
1971	96	92	2	884.10
1972	827	88	2	769.21
1973	165	65	5	991.33
1974	624	84	5	929.65
1975	350	58	2	341.99
1976	369	80	4	44.77
1977	730	100	4	242.68
1978	626	78	1	957.27
1979	581	81	4	101.82
1980	16	19	3	548.85
1981	993	12	4	98.55
1982	322	22	3	165.50
1983	287	74	3	356.25
1984	73	23	4	261.40
1985	485	33	4	651.39
1986	144	16	5	490.33
1987	373	37	4	411.58
1988	635	88	2	443.18
1989	525	80	3	376.44
1990	699	53	5	452.39
1991	899	88	1	621.89
1992	660	8	2	700.55
1993	575	2	2	852.94
1994	298	49	2	571.71
1995	875	10	2	390.89
1996	474	86	1	351.84
1997	480	83	5	899.73
1998	477	14	1	184.19
1999	111	51	4	203.27
2000	337	9	3	345.37
2001	619	63	2	703.08
2002	488	15	3	456.85
2003	559	20	4	149.64
2004	219	41	5	36.14
2005	616	100	4	67.03
2006	828	47	4	977.69
2007	219	7	2	867.81
2008	976	98	4	273.23
2009	651	23	1	145.89
2010	281	52	1	301.55
2011	730	58	4	526.63
2012	686	34	2	830.57
2013	95	55	3	962.59
2014	305	22	2	352.18
2015	430	62	4	537.29
2016	803	21	4	357.56
2017	710	74	4	823.08
2018	575	77	2	82.34
2019	684	75	5	148.75
2020	681	94	3	19.10
2021	919	59	2	501.45
2022	325	15	4	266.23
2023	740	1	4	942.66
2024	878	17	4	640.08
2025	593	13	1	222.31
2026	193	54	5	774.74
2027	616	49	2	351.00
2028	976	25	5	954.37
2029	380	47	1	305.13
2030	315	65	1	700.12
2031	665	59	4	412.92
2032	361	70	4	525.03
2033	784	43	1	925.79
2034	470	55	3	180.83
2035	610	21	5	438.26
2036	292	85	4	635.30
2037	719	80	1	994.39
2038	826	14	1	650.73
2039	632	53	1	498.43
2040	770	80	5	104.10
2041	455	65	5	806.04
2042	684	38	4	215.60
2043	796	59	5	383.79
2044	201	61	1	353.51
2045	813	60	4	907.55
2046	661	91	4	12.56
2047	384	29	5	286.90
2048	901	85	3	310.55
2049	925	54	2	9.13
2050	931	54	1	20.44
2051	158	48	5	820.11
2052	615	41	3	174.39
2053	586	56	2	557.41
2054	401	25	5	645.57
2055	849	7	5	431.53
2056	962	82	4	976.49
2057	178	52	3	519.17
2058	448	30	1	710.76
2059	130	65	1	632.65
2060	804	51	3	837.31
2061	163	42	2	97.69
2062	27	56	1	630.12
2063	608	20	1	619.39
2064	557	11	5	385.11
2065	761	94	2	982.51
2066	650	81	3	190.44
2067	669	29	3	197.67
2068	861	32	4	770.77
2069	676	7	3	87.47
2070	148	81	1	639.56
2071	594	14	1	461.37
2072	611	16	1	145.98
2073	269	24	1	81.92
2074	865	47	2	393.46
2075	503	3	4	78.13
2076	983	81	1	214.03
2077	430	49	3	634.75
2078	462	21	2	301.96
2079	926	23	5	632.43
2080	876	5	1	975.06
2081	356	62	5	601.39
2082	6	21	5	742.25
2083	949	16	2	607.47
2084	549	3	5	513.67
2085	157	28	3	119.10
2086	223	4	3	142.73
2087	86	94	2	270.98
2088	494	26	1	351.46
2089	565	84	3	469.24
2090	829	64	4	514.58
2091	410	25	3	176.92
2092	704	92	3	961.10
2093	106	75	5	314.72
2094	814	27	4	435.87
2095	457	55	5	747.60
2096	836	41	5	111.91
2097	393	55	2	568.74
2098	383	81	1	451.71
2099	911	5	5	256.55
2100	420	38	5	826.73
2101	661	68	3	400.92
2102	118	24	3	431.81
2103	191	46	2	77.20
2104	673	48	3	149.17
2105	322	16	1	321.68
2106	12	92	3	217.49
2107	582	42	2	563.27
2108	617	28	5	221.16
2109	575	36	5	945.59
2110	827	86	1	575.50
2111	662	54	4	320.88
2112	328	26	2	54.36
2113	506	64	1	989.32
2114	432	16	1	455.07
2115	616	42	5	385.56
2116	591	3	3	22.73
2117	803	74	1	911.17
2118	292	17	4	41.79
2119	547	68	1	340.37
2120	17	9	4	99.55
2121	822	54	3	278.03
2122	772	45	4	84.29
2123	794	41	4	613.65
2124	403	39	4	495.38
2125	657	16	3	937.08
2126	106	4	2	52.55
2127	11	18	1	992.58
2128	883	89	4	229.98
2129	91	25	3	816.25
2130	551	1	1	263.13
2131	804	6	1	52.72
2132	312	10	3	332.35
2133	628	49	3	699.47
2134	948	18	5	462.93
2135	130	41	2	753.52
2136	910	53	4	669.23
2137	535	68	2	579.42
2138	678	63	3	324.98
2139	749	62	2	96.25
2140	785	38	1	355.89
2141	856	32	2	695.80
2142	77	64	1	216.20
2143	687	28	4	818.60
2144	193	63	1	343.41
2145	834	76	5	515.84
2146	321	98	3	709.26
2147	672	20	5	110.03
2148	134	29	3	388.26
2149	464	80	5	206.80
2150	71	36	4	168.21
2151	315	74	1	151.41
2152	898	14	1	244.12
2153	916	59	2	270.16
2154	488	85	5	454.93
2155	272	16	5	88.56
2156	442	28	2	399.55
2157	442	66	3	57.84
2158	280	48	1	53.84
2159	392	94	4	197.77
2160	194	52	2	595.48
2161	543	78	4	520.51
2162	112	88	1	647.47
2163	982	15	2	119.50
2164	917	5	5	269.58
2165	68	69	1	278.81
2166	904	80	4	394.56
2167	104	29	3	497.20
2168	176	27	3	638.08
2169	723	77	3	734.48
2170	97	24	5	907.34
2171	638	62	3	852.45
2172	705	31	2	318.22
2173	72	22	2	335.16
2174	986	2	4	430.36
2175	22	23	3	880.97
2176	175	87	1	595.44
2177	993	61	5	6.00
2178	895	32	4	113.73
2179	839	3	5	680.97
2180	538	65	2	755.46
2181	794	13	1	307.77
2182	754	43	4	492.72
2183	360	70	3	664.43
2184	260	47	4	18.48
2185	362	39	3	891.02
2186	794	85	5	486.45
2187	277	88	5	728.85
2188	22	19	4	856.13
2189	676	19	3	499.85
2190	251	74	4	362.26
2191	763	12	2	920.12
2192	387	82	1	964.66
2193	899	81	5	898.83
2194	461	68	2	268.72
2195	696	45	3	393.68
2196	428	36	3	194.43
2197	594	67	3	834.17
2198	126	56	4	568.26
2199	812	45	3	114.53
2200	9	64	2	468.52
2201	154	67	3	625.05
2202	681	21	3	488.90
2203	67	38	1	456.14
2204	223	37	5	127.70
2205	501	40	1	432.74
2206	677	1	1	254.92
2207	359	37	5	666.33
2208	788	72	2	952.96
2209	731	35	2	994.94
2210	202	56	5	917.75
2211	298	29	1	475.34
2212	364	32	4	425.03
2213	991	13	3	919.67
2214	612	40	2	565.52
2215	696	42	5	143.34
2216	257	18	4	555.96
2217	309	40	1	300.55
2218	950	81	4	547.56
2219	385	56	1	142.78
2220	453	89	3	505.79
2221	702	92	3	470.57
2222	438	60	4	960.68
2223	473	4	5	31.26
2224	786	54	1	756.32
2225	630	39	2	581.84
2226	383	17	5	545.01
2227	580	38	1	755.80
2228	403	17	4	671.06
2229	474	98	5	462.46
2230	56	11	1	273.55
2231	666	14	3	595.77
2232	842	38	5	483.58
2233	340	8	1	741.03
2234	691	66	1	702.36
2235	529	19	5	740.98
2236	508	18	2	894.68
2237	656	20	3	629.47
2238	737	1	4	624.92
2239	206	15	1	5.04
2240	619	16	5	101.28
2241	210	14	4	29.51
2242	518	57	4	60.32
2243	125	39	4	485.82
2244	189	31	5	263.71
2245	628	88	4	859.16
2246	632	16	4	150.37
2247	23	24	2	818.64
2248	674	31	2	513.45
2249	717	70	2	478.30
2250	297	38	1	958.34
2251	505	48	3	393.84
2252	715	14	4	419.40
2253	436	19	1	286.72
2254	124	73	4	15.95
2255	311	5	5	446.81
2256	930	46	2	470.10
2257	741	59	3	14.07
2258	163	46	5	855.70
2259	516	27	3	902.14
2260	538	50	5	67.39
2261	361	84	5	342.26
2262	733	18	3	785.25
2263	675	39	4	72.80
2264	860	83	4	379.26
2265	484	78	2	577.58
2266	950	65	5	262.67
2267	715	42	5	954.46
2268	357	75	5	829.91
2269	70	6	1	851.92
2270	163	30	1	666.27
2271	512	87	4	326.72
2272	238	99	2	109.80
2273	902	23	4	756.28
2274	431	9	1	613.23
2275	118	5	1	443.88
2276	384	78	1	923.01
2277	329	14	4	380.36
2278	653	74	5	203.54
2279	259	63	4	679.78
2280	231	26	2	436.46
2281	542	25	1	583.62
2282	645	86	1	207.32
2283	830	18	1	362.40
2284	418	73	5	864.30
2285	349	24	5	498.20
2286	853	27	5	827.61
2287	513	46	3	619.77
2288	573	18	1	441.24
2289	641	49	1	570.74
2290	131	67	3	105.31
2291	511	30	1	602.88
2292	339	3	2	821.40
2293	297	33	4	704.05
2294	70	21	3	79.33
2295	590	31	5	931.22
2296	513	40	4	619.93
2297	560	90	1	584.28
2298	960	34	1	37.08
2299	432	34	2	337.53
2300	784	8	2	208.01
2301	837	94	3	923.63
2302	680	8	2	495.59
2303	825	73	5	703.87
2304	784	5	3	980.17
2305	973	54	5	739.85
2306	952	11	5	480.90
2307	133	35	1	108.44
2308	509	65	2	651.43
2309	442	62	3	781.85
2310	898	30	1	930.66
2311	27	100	2	535.98
2312	881	49	1	554.18
2313	54	50	4	696.27
2314	441	90	4	551.25
2315	119	57	1	896.76
2316	926	48	3	197.48
2317	448	8	2	235.64
2318	603	2	2	415.59
2319	771	69	5	50.51
2320	822	2	2	812.75
2321	79	8	2	440.92
2322	290	6	3	352.57
2323	671	32	3	133.94
2324	408	62	1	657.65
2325	79	33	5	209.63
2326	723	95	3	897.25
2327	880	29	4	713.86
2328	965	47	5	295.93
2329	670	32	5	892.62
2330	327	90	5	505.42
2331	56	45	4	706.27
2332	637	63	3	82.98
2333	934	18	5	234.15
2334	760	71	2	127.01
2335	743	19	1	977.04
2336	716	57	4	952.33
2337	22	64	1	273.68
2338	603	50	3	827.22
2339	87	8	3	854.45
2340	394	64	1	862.60
2341	394	57	1	228.10
2342	389	24	4	534.30
2343	677	40	1	543.30
2344	357	4	5	754.95
2345	345	34	5	220.24
2346	29	44	5	436.47
2347	438	94	1	807.55
2348	567	50	3	858.36
2349	961	69	4	426.29
2350	737	73	5	263.54
2351	984	49	4	746.16
2352	947	31	2	907.27
2353	288	88	3	90.02
2354	256	99	5	299.05
2355	585	51	1	616.85
2356	371	35	3	782.73
2357	830	99	5	17.27
2358	315	73	3	835.98
2359	455	60	1	442.27
2360	478	5	3	482.33
2361	865	72	2	411.16
2362	594	11	3	896.66
2363	565	41	1	442.80
2364	265	99	3	262.98
2365	507	17	2	631.56
2366	151	80	1	236.28
2367	671	5	2	685.33
2368	882	57	5	320.43
2369	567	92	2	65.45
2370	732	34	3	21.02
2371	866	46	5	719.01
2372	615	31	3	113.51
2373	520	57	1	512.97
2374	243	27	3	571.94
2375	850	88	4	75.96
2376	437	37	2	29.55
2377	622	47	3	974.25
2378	919	84	3	472.86
2379	997	38	5	35.97
2380	378	6	3	929.73
2381	934	76	1	110.59
2382	217	41	5	716.47
2383	760	66	5	713.56
2384	963	28	4	830.74
2385	34	85	2	383.80
2386	665	11	1	957.87
2387	230	73	5	996.83
2388	646	71	4	540.73
2389	125	68	1	608.46
2390	533	57	3	272.57
2391	857	74	3	910.60
2392	337	32	3	234.51
2393	323	96	1	693.91
2394	456	94	4	364.71
2395	361	72	5	80.99
2396	371	84	4	606.59
2397	460	54	2	570.93
2398	847	17	5	248.47
2399	932	53	5	666.91
2400	621	34	3	344.52
2401	121	11	4	423.50
2402	152	74	4	633.83
2403	792	26	2	876.15
2404	16	22	1	421.11
2405	784	71	4	743.40
2406	130	5	4	28.79
2407	171	10	2	516.81
2408	543	50	4	357.24
2409	412	90	5	244.99
2410	301	16	3	897.04
2411	920	44	5	610.10
2412	111	93	1	78.31
2413	943	46	4	910.21
2414	759	56	3	758.11
2415	717	18	2	724.37
2416	604	66	1	156.34
2417	8	76	5	372.65
2418	389	42	4	180.66
2419	740	76	3	944.10
2420	100	30	3	495.33
2421	50	73	5	896.92
2422	594	66	4	288.55
2423	394	41	2	952.79
2424	43	95	2	432.95
2425	285	74	5	317.48
2426	356	37	2	122.84
2427	281	63	4	227.29
2428	174	37	3	987.87
2429	772	14	2	667.44
2430	145	13	2	553.85
2431	173	4	5	902.13
2432	983	70	5	799.20
2433	7	63	1	372.32
2434	289	74	4	732.70
2435	534	17	4	298.17
2436	113	92	1	446.74
2437	443	64	3	91.34
2438	141	36	1	967.63
2439	823	11	2	728.00
2440	335	21	5	338.33
2441	465	81	5	673.05
2442	76	91	3	891.92
2443	40	56	1	931.77
2444	814	67	3	194.26
2445	572	85	1	948.49
2446	643	2	2	141.05
2447	386	29	2	268.69
2448	156	63	2	734.16
2449	290	17	2	635.96
2450	91	67	2	8.18
2451	69	63	5	612.55
2452	728	23	1	420.65
2453	270	79	4	632.24
2454	241	82	3	486.33
2455	673	24	3	840.65
2456	897	38	4	492.28
2457	646	51	5	359.99
2458	493	38	1	222.62
2459	987	97	3	422.08
2460	458	42	2	663.44
2461	119	23	4	955.58
2462	677	15	3	697.79
2463	722	17	4	840.08
2464	885	63	5	414.53
2465	241	4	3	271.32
2466	221	53	1	563.88
2467	331	34	3	413.76
2468	829	57	4	401.29
2469	935	7	3	487.59
2470	225	44	1	311.66
2471	420	29	5	875.37
2472	549	27	1	947.19
2473	629	79	3	133.44
2474	553	3	1	802.60
2475	93	100	3	911.76
2476	786	99	5	68.08
2477	51	67	2	364.93
2478	204	21	5	398.15
2479	736	30	3	801.48
2480	933	48	3	415.91
2481	567	94	2	939.37
2482	37	3	5	106.91
2483	408	63	1	161.00
2484	309	4	2	632.77
2485	705	32	1	275.82
2486	127	49	4	135.41
2487	759	35	1	81.07
2488	517	93	4	25.03
2489	761	70	5	918.46
2490	98	95	5	792.86
2491	199	78	3	785.06
2492	436	66	1	305.34
2493	470	26	1	267.68
2494	672	74	4	379.32
2495	440	12	2	966.09
2496	495	37	5	508.55
2497	392	3	4	728.19
2498	975	48	5	715.29
2499	464	29	5	974.34
2500	407	99	2	449.40
2501	489	73	1	643.96
2502	341	19	1	99.82
2503	174	27	4	594.85
2504	86	19	4	617.79
2505	485	67	5	761.02
2506	61	99	4	255.51
2507	319	95	3	834.32
2508	38	42	5	600.14
2509	893	1	3	691.25
2510	774	72	4	547.32
2511	321	84	2	324.91
2512	726	62	5	556.48
2513	758	94	1	920.70
2514	436	90	1	378.43
2515	776	2	2	521.82
2516	125	22	2	439.98
2517	996	15	1	885.19
2518	508	22	5	489.27
2519	767	71	4	402.01
2520	304	16	4	994.77
2521	738	87	3	524.35
2522	630	48	5	651.32
2523	145	38	5	685.91
2524	823	79	3	521.26
2525	258	61	4	214.35
2526	339	96	2	168.25
2527	733	61	1	320.78
2528	184	20	4	71.65
2529	6	40	2	203.07
2530	97	69	4	334.05
2531	63	80	4	595.89
2532	69	45	5	883.04
2533	354	81	1	927.31
2534	282	37	4	585.96
2535	314	48	5	767.39
2536	957	33	5	542.77
2537	676	26	1	594.08
2538	106	94	2	283.31
2539	270	73	1	130.94
2540	535	76	4	333.18
2541	620	36	5	669.49
2542	485	27	2	7.65
2543	238	28	1	928.97
2544	630	19	2	168.83
2545	896	1	3	82.32
2546	994	7	2	513.64
2547	451	55	4	330.13
2548	513	98	1	244.33
2549	403	49	4	707.01
2550	364	40	5	320.07
2551	81	78	2	954.63
2552	969	82	3	712.08
2553	861	56	5	444.00
2554	712	33	1	559.56
2555	446	84	3	181.94
2556	887	47	4	771.12
2557	355	94	4	217.50
2558	574	25	4	376.96
2559	956	96	1	199.66
2560	370	68	2	10.58
2561	318	43	1	910.57
2562	938	33	5	921.03
2563	622	35	1	648.33
2564	658	62	4	48.65
2565	713	91	3	277.53
2566	59	74	1	863.01
2567	950	61	5	633.45
2568	503	23	4	750.44
2569	664	97	5	807.59
2570	40	48	1	614.24
2571	182	17	1	422.06
2572	867	16	1	445.72
2573	728	8	3	101.89
2574	558	36	2	656.17
2575	756	3	3	837.25
2576	869	41	2	905.29
2577	601	93	3	518.24
2578	964	86	4	418.88
2579	684	86	1	69.57
2580	845	98	5	151.63
2581	274	11	2	445.74
2582	283	78	2	689.58
2583	420	23	1	314.30
2584	575	45	1	344.40
2585	582	90	1	567.79
2586	475	12	1	917.50
2587	187	94	1	189.54
2588	606	81	1	767.12
2589	808	2	2	639.12
2590	472	11	2	310.94
2591	698	83	2	747.92
2592	756	17	3	58.02
2593	723	37	2	282.29
2594	579	41	4	229.60
2595	193	35	2	181.05
2596	303	34	4	267.96
2597	502	46	5	366.43
2598	791	83	5	451.98
2599	647	88	2	41.51
2600	855	75	4	159.77
2601	583	27	4	349.84
2602	831	88	3	211.20
2603	717	65	5	829.88
2604	814	35	1	515.19
2605	216	34	2	469.88
2606	33	15	5	659.38
2607	191	61	2	469.44
2608	331	48	5	380.64
2609	603	5	3	702.08
2610	645	46	1	162.80
2611	487	43	3	648.99
2612	103	24	3	309.44
2613	479	70	2	752.53
2614	450	79	4	595.01
2615	712	56	4	475.73
2616	250	33	3	602.34
2617	495	87	4	303.37
2618	995	30	5	112.21
2619	437	100	3	953.26
2620	411	76	1	168.04
2621	171	39	5	964.44
2622	966	68	2	950.78
2623	582	97	2	134.11
2624	342	7	1	312.42
2625	785	19	3	460.96
2626	170	59	1	659.66
2627	206	23	3	310.68
2628	190	31	2	438.93
2629	742	32	2	685.61
2630	866	100	3	9.92
2631	164	45	1	472.98
2632	704	51	2	912.36
2633	685	49	4	706.99
2634	782	13	4	132.73
2635	782	18	4	773.62
2636	920	37	4	598.36
2637	547	10	3	490.38
2638	759	76	1	225.36
2639	624	23	2	371.92
2640	349	65	1	611.90
2641	770	51	1	646.70
2642	142	64	2	48.98
2643	310	56	1	342.55
2644	670	24	4	154.84
2645	319	50	4	39.62
2646	982	54	2	167.56
2647	699	67	1	467.13
2648	85	45	1	656.93
2649	415	2	2	322.11
2650	589	65	4	687.18
2651	12	63	4	424.92
2652	56	39	4	262.10
2653	650	15	5	807.28
2654	931	58	5	375.59
2655	485	92	3	844.10
2656	996	47	1	785.78
2657	435	69	4	870.09
2658	82	20	1	340.09
2659	957	91	5	261.29
2660	528	79	4	437.28
2661	476	37	1	125.82
2662	502	59	3	54.77
2663	614	88	3	255.81
2664	346	87	3	767.23
2665	25	70	3	182.66
2666	366	54	1	449.09
2667	305	82	1	597.20
2668	366	94	1	533.08
2669	406	32	2	88.54
2670	97	17	2	634.12
2671	442	36	3	971.02
2672	706	80	2	918.26
2673	926	94	5	570.65
2674	42	10	3	375.56
2675	151	78	1	384.62
2676	743	11	3	926.88
2677	768	39	4	403.34
2678	189	96	3	722.26
2679	761	11	4	964.37
2680	813	25	5	264.41
2681	311	79	5	540.92
2682	813	32	1	376.99
2683	485	28	4	278.14
2684	706	100	2	280.19
2685	688	6	5	401.28
2686	186	87	3	276.04
2687	417	27	1	782.36
2688	673	17	3	270.45
2689	614	82	3	101.56
2690	231	3	3	224.73
2691	627	37	5	827.01
2692	603	54	5	331.78
2693	399	61	5	17.49
2694	349	41	3	822.69
2695	156	60	4	214.37
2696	715	22	4	259.16
2697	873	74	1	632.60
2698	86	27	5	371.98
2699	299	97	3	453.79
2700	479	4	2	626.11
2701	171	80	3	566.50
2702	426	98	1	751.88
2703	291	72	4	988.74
2704	385	69	2	381.16
2705	972	16	1	398.38
2706	217	15	5	292.61
2707	886	21	4	551.77
2708	361	97	2	420.67
2709	614	36	3	770.88
2710	646	14	3	504.29
2711	546	51	2	858.90
2712	507	97	4	289.57
2713	947	58	2	923.37
2714	182	52	3	8.32
2715	850	43	4	657.25
2716	700	13	4	581.68
2717	429	54	4	192.74
2718	30	80	2	142.74
2719	635	65	1	600.97
2720	750	53	1	328.07
2721	256	22	5	626.74
2722	701	12	3	27.58
2723	616	84	4	553.75
2724	885	25	2	460.02
2725	741	31	2	474.34
2726	730	26	3	136.85
2727	67	4	2	579.14
2728	471	32	5	445.99
2729	248	23	4	502.21
2730	114	78	3	871.85
2731	931	21	2	464.44
2732	986	9	1	749.12
2733	699	87	4	866.86
2734	482	50	1	783.34
2735	981	34	5	125.26
2736	796	78	5	715.48
2737	450	62	1	296.21
2738	408	93	1	366.19
2739	734	66	4	431.02
2740	128	14	2	846.99
2741	772	15	2	369.27
2742	673	44	2	912.50
2743	815	62	2	267.92
2744	338	83	1	460.49
2745	727	63	2	757.44
2746	351	38	4	333.68
2747	462	90	3	569.82
2748	609	5	2	152.14
2749	296	4	2	879.89
2750	578	47	3	309.82
2751	734	21	5	635.09
2752	487	92	4	674.24
2753	159	96	2	150.65
2754	300	50	3	637.94
2755	29	28	5	306.14
2756	599	2	3	366.98
2757	521	96	5	408.41
2758	634	22	3	644.99
2759	602	65	3	525.20
2760	388	63	2	870.56
2761	494	23	4	896.75
2762	15	86	1	345.31
2763	317	27	2	154.19
2764	624	100	1	651.10
2765	366	64	4	570.99
2766	654	2	5	897.75
2767	760	26	3	665.26
2768	409	81	1	951.32
2769	520	9	3	554.96
2770	551	11	1	448.95
2771	536	32	2	259.54
2772	758	24	2	231.97
2773	735	59	2	44.99
2774	624	35	5	280.81
2775	761	25	1	905.70
2776	136	67	3	65.50
2777	234	32	5	762.11
2778	489	60	1	538.71
2779	801	7	3	790.28
2780	75	26	4	120.71
2781	86	61	2	104.28
2782	604	28	5	489.31
2783	583	2	5	432.18
2784	927	15	4	777.73
2785	200	76	5	756.01
2786	1	33	4	602.75
2787	505	81	2	331.67
2788	495	66	3	950.73
2789	307	34	5	252.53
2790	282	87	5	505.04
2791	641	57	1	976.37
2792	969	24	4	11.48
2793	915	66	4	497.81
2794	184	9	4	673.94
2795	97	57	3	639.06
2796	552	24	2	779.12
2797	782	30	2	310.36
2798	785	68	4	107.30
2799	308	79	2	572.58
2800	159	42	2	195.75
2801	406	22	2	611.46
2802	161	42	5	980.27
2803	670	77	4	780.08
2804	276	30	3	474.15
2805	877	39	3	149.12
2806	342	94	3	829.26
2807	323	58	3	427.75
2808	403	98	4	10.64
2809	963	52	1	967.87
2810	363	83	2	974.14
2811	786	36	1	818.62
2812	208	27	3	298.03
2813	383	4	3	429.93
2814	392	42	5	561.61
2815	205	28	5	504.93
2816	877	36	1	78.98
2817	165	42	4	940.85
2818	608	61	1	781.54
2819	400	89	4	253.35
2820	622	76	4	63.96
2821	58	82	3	279.39
2822	379	57	3	115.36
2823	138	96	1	327.60
2824	794	94	4	824.36
2825	895	20	5	302.06
2826	205	72	1	440.63
2827	336	74	5	763.21
2828	267	72	5	817.41
2829	707	3	2	772.47
2830	70	90	3	956.46
2831	370	99	4	747.79
2832	220	24	3	470.52
2833	472	47	3	202.79
2834	995	91	3	258.83
2835	766	3	2	123.48
2836	421	55	4	806.23
2837	818	7	5	64.92
2838	525	48	1	567.32
2839	33	65	3	790.40
2840	504	37	5	336.75
2841	69	95	1	566.91
2842	998	72	1	533.57
2843	818	66	1	575.48
2844	480	79	2	752.40
2845	786	88	4	817.85
2846	477	58	2	651.54
2847	75	24	5	342.77
2848	541	100	4	889.06
2849	412	74	3	11.32
2850	849	50	1	13.49
2851	331	55	2	262.30
2852	229	75	3	534.17
2853	670	86	2	770.31
2854	589	46	5	156.69
2855	792	19	2	311.63
2856	104	4	5	603.31
2857	865	6	2	541.84
2858	978	9	3	870.33
2859	951	30	2	205.49
2860	168	55	3	236.58
2861	942	28	3	32.13
2862	899	57	1	834.15
2863	385	4	4	867.33
2864	875	95	2	383.13
2865	458	57	4	202.45
2866	790	49	5	814.61
2867	96	23	5	912.80
2868	742	67	1	166.91
2869	215	16	4	741.20
2870	367	96	3	417.64
2871	216	12	5	362.70
2872	262	66	1	944.23
2873	17	1	4	803.59
2874	410	13	3	363.23
2875	318	9	4	945.26
2876	668	39	2	998.71
2877	87	84	4	875.69
2878	17	36	3	50.10
2879	868	32	2	566.19
2880	132	67	2	144.38
2881	482	98	1	65.81
2882	822	27	3	374.47
2883	425	21	4	176.39
2884	959	67	2	742.51
2885	830	86	2	367.88
2886	948	15	2	34.80
2887	209	40	4	626.56
2888	931	34	5	324.15
2889	803	4	3	33.33
2890	482	5	2	913.10
2891	48	70	4	762.93
2892	740	68	2	162.22
2893	16	45	2	96.57
2894	68	15	4	466.65
2895	426	69	4	138.60
2896	618	82	1	314.56
2897	481	33	2	325.94
2898	553	47	5	669.42
2899	99	62	4	749.23
2900	201	17	2	516.65
2901	825	19	2	660.25
2902	762	13	4	285.61
2903	630	14	2	229.87
2904	190	94	3	331.65
2905	998	60	5	521.80
2906	592	35	2	330.98
2907	384	85	2	580.89
2908	958	5	4	633.09
2909	814	26	2	19.24
2910	650	5	2	165.91
2911	331	2	5	482.89
2912	879	45	2	629.94
2913	837	74	4	454.39
2914	220	59	5	266.23
2915	451	16	3	656.53
2916	527	44	3	995.71
2917	191	33	3	807.15
2918	500	99	5	458.58
2919	99	86	3	763.69
2920	270	9	3	428.96
2921	27	70	2	99.02
2922	999	59	1	124.56
2923	730	38	2	873.07
2924	315	58	4	554.98
2925	963	11	5	186.52
2926	840	66	2	145.86
2927	697	29	1	202.49
2928	763	46	5	602.33
2929	156	73	5	526.89
2930	820	69	3	541.22
2931	711	68	2	377.23
2932	103	88	2	636.10
2933	880	80	2	843.18
2934	770	92	2	542.58
2935	979	79	4	858.15
2936	286	7	4	299.72
2937	923	67	4	893.38
2938	480	42	2	722.22
2939	308	1	1	254.82
2940	570	86	3	212.50
2941	752	79	5	958.52
2942	61	97	4	144.46
2943	493	21	2	393.89
2944	164	83	4	393.65
2945	199	32	3	75.11
2946	987	36	2	892.28
2947	127	93	5	943.68
2948	156	27	4	146.55
2949	283	98	3	15.70
2950	121	67	3	526.10
2951	791	81	5	473.28
2952	677	57	3	822.31
2953	555	96	5	456.64
2954	73	97	3	874.98
2955	973	6	4	837.95
2956	262	15	4	428.36
2957	173	91	4	758.91
2958	231	67	1	93.04
2959	750	78	5	864.89
2960	248	86	4	836.69
2961	987	56	4	61.31
2962	108	99	3	842.27
2963	751	36	3	641.42
2964	337	54	3	982.19
2965	86	2	1	713.82
2966	498	32	5	497.01
2967	606	56	3	108.34
2968	800	91	4	562.31
2969	858	73	4	607.99
2970	892	86	4	46.85
2971	111	76	1	577.17
2972	121	98	2	363.54
2973	689	91	5	424.30
2974	404	92	1	350.22
2975	808	57	4	574.90
2976	536	5	4	813.28
2977	644	96	4	670.05
2978	27	28	5	184.65
2979	646	43	1	295.52
2980	423	4	4	849.33
2981	260	46	3	355.26
2982	989	32	3	448.33
2983	49	42	4	699.91
2984	651	34	2	213.12
2985	790	71	3	741.26
2986	800	23	4	856.51
2987	342	46	5	540.01
2988	825	30	3	828.71
2989	104	93	1	640.62
2990	321	80	4	640.64
2991	775	49	2	268.09
2992	725	63	3	339.98
2993	449	47	2	958.55
2994	331	3	1	193.65
2995	318	65	5	299.43
2996	574	69	2	400.58
2997	713	10	2	97.80
2998	729	77	4	852.10
2999	150	92	3	534.63
3000	407	18	4	108.00
\.


--
-- Data for Name: reviews; Type: TABLE DATA; Schema: ecommerce_v1; Owner: sandbox_admin
--

COPY ecommerce_v1.reviews (id, product_id, customer_id, rating, comment, created_at) FROM stdin;
1	38	158	5	Able teach activity animal hair turn condition whether along sort research pretty different eat trouble.	2025-09-24 10:32:24.673243+00
2	11	83	2	Number budget pull apply development middle animal husband.	2026-04-15 21:33:36.977716+00
3	57	11	2	Similar financial beat lead hard factor six science drug happy will.	2026-05-30 00:25:40.612141+00
4	71	40	3	Run national somebody character usually agency must player really act.	2025-09-29 22:44:50.643965+00
5	4	127	2	Support road billion morning draw man art young Republican behavior TV today.	2025-12-06 10:09:00.441519+00
6	29	63	2	Learn security oil measure PM hour option artist production candidate factor surface.	2026-05-03 19:31:37.397298+00
7	57	166	2	Red save fish evening avoid dark sister once choice clearly letter image movie.	2026-05-17 21:49:19.266484+00
8	19	4	3	Later leg system bed space fight relate owner Democrat task.	2025-07-23 18:14:10.916094+00
9	32	6	5	Why how any federal star community weight take new nearly.	2025-07-04 04:24:16.558565+00
10	62	113	4	Sound cause activity store work candidate statement head.	2026-01-15 19:06:09.342738+00
11	72	142	5	Old else spend against ask total kitchen can.	2026-04-26 03:45:42.570702+00
12	25	106	2	Business walk anything under item right many him interview government traditional every.	2025-11-09 11:41:40.969899+00
13	67	149	4	Alone people early far include nearly article evidence case.	2025-08-11 10:27:53.348116+00
14	81	148	4	Eat yes myself affect him require look sit general not focus establish ago others ahead.	2026-03-22 16:22:26.291525+00
15	34	181	3	Around yard morning short yourself wind beyond prevent entire staff true.	2025-06-20 00:08:50.692851+00
16	34	111	3	Offer work home very yard community door fish scene grow.	2026-01-01 15:33:37.477348+00
17	47	61	3	Way nor none could write think man finally make bed discussion despite.	2025-12-08 20:47:12.778577+00
18	70	92	1	Forward pass southern future concern sort than.	2025-06-21 08:07:07.796726+00
19	18	83	2	Only true similar suffer team whether health walk how.	2025-07-06 11:41:21.521899+00
20	69	149	2	Follow wish run join police maintain fish religious no threat party.	2025-10-07 21:54:45.587683+00
21	13	130	4	Sport her safe family concern ability reduce of surface side nothing consider fish speak particularly policy.	2025-07-07 14:40:15.138121+00
22	69	81	1	Cell seat draw word collection those become remember police though land enter economic attack.	2025-09-01 07:52:02.903567+00
23	78	59	3	Result answer just information coach increase think goal.	2025-10-14 16:16:20.185478+00
24	83	142	2	Small official serve difficult later son almost after end bit game thousand claim avoid.	2026-05-09 13:57:27.423327+00
25	60	69	5	Full world throw relate issue president parent its.	2025-06-19 03:31:20.432424+00
26	7	118	5	Day couple recent reveal role enter example down anyone occur style child.	2025-10-09 09:00:19.008334+00
27	57	128	5	Because station person lose best deal point with list break size likely thus.	2025-09-04 09:01:49.79868+00
28	56	17	2	Hold he high cost and keep enjoy student nor character recent benefit property space including.	2026-03-02 20:59:06.251787+00
29	3	144	4	Network subject stand industry movement term little think live bad.	2026-04-25 07:35:37.809479+00
30	72	167	1	Maybe too song quality per build serious.	2025-08-01 17:28:52.104806+00
31	45	123	2	Will speak call interest write itself young physical street.	2025-09-01 18:38:07.780135+00
32	9	175	3	Beautiful news need task mind true actually red.	2025-12-31 04:36:59.480482+00
33	9	185	3	Both change note old who beyond black single size test they there enough.	2026-01-24 17:46:37.660762+00
34	73	65	1	Participant also every century participant really although threat former down second TV today after stage.	2025-09-18 06:34:21.159454+00
35	77	126	4	Successful teach range win direction feel season similar fly rock painting.	2025-07-02 04:43:57.563281+00
36	18	102	2	Deep station scientist service test start middle city find medical career surface these.	2025-06-10 03:49:05.421353+00
37	85	116	3	Themselves customer arm almost anything growth current happy less however.	2026-05-02 17:30:24.905724+00
38	69	179	3	Drop major land whether listen necessary general.	2026-04-01 12:44:14.887396+00
39	43	60	5	See read expect hit clear occur who tax positive question especially.	2025-10-27 03:42:26.48991+00
40	66	105	2	Ten whose radio listen car community song.	2025-08-20 07:34:47.815804+00
41	70	175	5	Source figure whom poor interest heavy give edge level quality station however bill memory production successful.	2025-10-14 06:28:25.839417+00
42	41	2	5	Participant fear blue as write political technology end represent throughout federal change she tonight south sort.	2026-01-04 17:48:48.475459+00
43	7	183	3	Race return pretty young else industry home along remain occur couple risk.	2025-08-19 19:14:52.608426+00
44	76	31	1	Point little wait grow feel color price next family likely scientist rise next tree water.	2026-04-24 03:39:56.676234+00
45	79	17	5	Develop development the inside thought he one less.	2025-07-12 14:30:34.793661+00
46	53	187	2	Term on want author threat matter test.	2025-10-16 23:41:10.808731+00
47	25	64	5	Including that character yeah garden would throughout would century television Congress.	2025-06-29 02:26:22.127657+00
48	23	47	1	Piece computer play above event seven collection share majority shake because pass.	2026-01-16 23:03:55.081241+00
49	84	127	1	Investment local above move room wear throughout series most adult above safe difficult.	2026-04-15 21:30:24.389319+00
50	43	23	1	Can himself open cold statement fear fact road others full thousand.	2026-05-29 04:08:16.032224+00
51	52	147	4	You majority seek close trade speech affect difference world deep against mean.	2025-07-14 13:40:26.143352+00
52	53	98	4	Heart policy side perhaps order answer blue.	2026-03-31 23:17:34.406299+00
53	18	88	2	Ready indicate herself natural listen check receive.	2026-01-15 19:13:24.559328+00
54	13	80	3	Inside big minute performance red industry together memory pay executive size.	2025-11-28 09:07:36.214077+00
55	23	182	4	Current enjoy mission cut region far always many debate value former able public trade structure protect.	2025-07-24 01:25:49.380939+00
56	33	128	1	Single avoid rich toward popular lead with enough.	2025-06-17 21:03:23.518097+00
57	24	67	4	Them system growth quality international break surface three act.	2025-07-20 03:11:52.891289+00
58	26	59	3	Forget thus western environmental run head garden box hundred.	2025-11-13 07:58:26.80971+00
59	83	163	1	Ready long instead though coach car risk word such billion treat lot notice.	2025-11-06 14:53:43.962417+00
60	44	116	1	Here grow agreement range stuff wind candidate turn both in animal energy fire relate question should.	2025-12-27 04:49:56.514011+00
61	68	66	1	Difference what their mind read peace item risk loss professional political chance step throughout party.	2025-06-03 20:08:30.005852+00
62	78	16	5	Measure light many close seem fly former everything medical.	2025-12-17 15:34:39.363161+00
63	8	175	3	Idea dog learn soon large task language budget market president bill include.	2025-12-20 01:44:32.244315+00
64	13	44	1	Stay social white point three none pressure.	2025-11-13 05:04:28.994201+00
65	68	4	1	Guy approach development lawyer nice people list price respond box service develop.	2025-10-02 06:19:12.346423+00
66	42	99	3	Natural hear blood to manage state score important effect cultural building.	2026-04-06 20:11:48.810524+00
67	4	146	5	Lead sit response blue increase unit study open sign late.	2026-01-26 01:56:20.091554+00
68	48	18	2	Care material morning any very stuff lot meet TV concern official room campaign hold.	2026-01-04 22:18:28.265964+00
69	25	163	5	Mean his woman trouble several event white wife laugh card include record.	2026-02-27 22:35:45.021817+00
70	64	47	5	Successful natural finish say network design decide research rather TV car.	2026-02-14 01:13:49.028567+00
71	28	89	1	Mean reason follow break good lose number project individual.	2026-02-27 17:42:11.866252+00
72	88	40	5	Experience suggest space mission agent certainly prove customer seek claim expert economy style real far.	2026-03-01 19:53:21.269659+00
73	48	147	2	Grow laugh pattern push no difference positive.	2025-10-19 14:57:09.730053+00
74	57	181	2	Six sometimes explain professor unit hold what wish fine need actually edge per sit thank.	2026-03-29 17:30:05.624419+00
75	65	39	4	Sense national owner simply who family concern radio cost community message help.	2025-11-03 02:15:43.972981+00
76	4	160	1	Enough claim suffer accept letter visit always up others similar personal successful feeling so nearly.	2025-06-26 04:55:16.022403+00
77	69	31	3	Moment whatever minute skill city myself idea glass third professional former family.	2026-05-12 16:14:23.395712+00
78	38	28	3	Most you statement wonder across protect knowledge toward party perform where radio fly trouble war history.	2025-12-13 21:39:22.261878+00
79	88	47	5	Agency might side method meet main fast prepare fly bank benefit.	2026-05-20 11:07:48.581942+00
80	67	43	1	Mouth phone decision picture defense rate structure day stock these scientist itself stage authority rather.	2025-06-08 06:16:41.449389+00
81	64	50	5	Also available concern edge audience start treat imagine later identify first hope.	2025-07-12 19:06:19.68693+00
82	20	157	3	Political peace series one red authority up.	2025-07-08 08:25:27.275008+00
83	59	169	5	Paper example unit high state air choose detail section someone support.	2025-09-15 07:46:33.6818+00
84	50	115	1	Fear thought whole term possible whatever action themselves center.	2025-06-14 20:14:19.965637+00
85	86	142	1	Others Mr water fight security tough gas include position mention claim determine strong create consider.	2026-03-18 15:41:37.201375+00
86	44	64	3	Surface usually yes leave near fact attack.	2025-07-05 10:53:03.254926+00
87	19	62	4	Maintain former campaign pretty beyond people too fish late pattern figure once not hair first into.	2025-06-01 08:25:14.445632+00
88	25	104	1	Size Republican political everybody growth quickly former lose knowledge simple.	2025-11-24 10:44:23.35511+00
89	46	16	4	Compare parent success teach cause Mrs enjoy though.	2025-06-27 12:18:59.094062+00
90	85	182	5	Throughout support place spend often shoulder defense already.	2025-09-02 18:33:56.452991+00
91	13	134	1	Line simple hand development sign run fact let member however maybe production summer southern pass.	2025-07-30 03:48:37.188781+00
92	85	168	3	Cell city not not the certainly rule voice American seven discussion enough doctor protect military.	2026-03-15 15:49:04.700895+00
93	68	145	5	Like lawyer another wonder food region miss stop strong enjoy name community president.	2025-10-11 00:10:09.984714+00
94	69	134	4	Might heavy trade might good test main lot.	2026-01-06 06:26:02.393177+00
95	70	165	2	Think key discover method exactly change church own stage produce increase form box push.	2025-11-21 13:03:00.390707+00
96	37	83	2	Claim street against amount of claim picture always occur argue election conference when out nor affect.	2026-02-17 09:26:40.169963+00
97	58	196	2	Water describe paper likely loss detail improve central old should perhaps.	2025-12-03 03:39:31.643723+00
98	38	161	4	Right garden law opportunity discover history board dark teacher.	2025-11-30 19:09:36.413299+00
99	52	112	4	Step painting concern top outside there mother sell behavior process top much ability.	2026-05-08 02:01:26.803544+00
100	11	126	1	Miss have analysis morning director sort smile high open scientist seven recent best.	2025-07-18 11:39:09.819056+00
101	63	27	3	She travel base our myself election accept season according mission mind heart day sound.	2025-10-26 21:54:12.165277+00
102	72	124	5	Choice prepare effect talk interest hand every quite.	2026-03-02 07:58:04.954963+00
103	50	79	4	Need newspaper condition next low write officer similar huge catch tell budget discover.	2026-03-12 14:36:48.187873+00
104	37	198	1	Beyond meet skill song pass range appear home player.	2026-03-20 08:58:27.568005+00
105	68	11	2	Likely outside because enjoy he participant right us husband.	2026-01-25 05:56:24.498271+00
106	12	79	5	Represent our watch star policy keep cut prevent sound experience almost.	2026-01-04 13:16:09.834211+00
107	74	139	2	Recognize past purpose growth pretty wish beautiful every human prove if customer address region try.	2025-12-17 07:39:46.275504+00
108	83	81	1	Trip give white everybody paper create upon offer end imagine blood authority family water sort.	2026-05-15 00:21:00.373594+00
109	69	8	1	Spend offer reason whom none show serious which learn leave only agree break attack plant.	2026-05-28 16:58:00.870634+00
110	39	99	2	Son include good movie red enjoy expert human see garden.	2025-12-19 03:07:51.411432+00
111	46	138	1	Live government thus especially water raise travel material current.	2026-02-23 04:39:36.858595+00
112	88	112	5	Deal dark economic peace choose blood turn put professional pass share.	2025-12-14 08:29:46.636284+00
113	68	46	5	Summer he firm together thing off ever.	2025-08-05 09:04:35.106612+00
114	48	175	1	Exactly develop office approach son long must maybe hour rather company with recently least ready.	2025-06-03 21:40:35.944535+00
115	28	26	4	Here beyond gun technology cost enjoy especially when gas contain.	2025-11-01 10:14:49.556208+00
116	24	57	3	Red head take evidence conference capital office direction between establish dog it herself.	2025-07-22 20:29:48.2533+00
117	10	183	2	List act instead care throw piece move firm main.	2025-08-30 06:02:37.317726+00
118	64	53	5	Answer between clear democratic effect stuff benefit seat employee growth newspaper special general in go.	2026-02-02 19:09:07.303673+00
119	82	157	1	Current office power company sister great pull maintain say threat high expert place certain cold space.	2025-09-30 19:31:49.828122+00
120	6	98	2	Partner if trade bad gas finish president report painting house thought sit voice security minute late.	2025-07-30 16:44:09.332755+00
121	15	75	1	By doctor edge season see decision however.	2025-07-04 11:39:59.483752+00
122	31	169	3	Nature ago however share bar energy choice pressure those finally easy exist phone capital.	2026-04-01 20:18:40.179829+00
123	23	100	2	Along ground trip ten level that various.	2025-12-16 22:28:54.410578+00
124	48	103	1	Wide recently computer our piece player nor model police.	2025-09-20 16:28:56.780703+00
125	20	37	5	Loss dinner become film include choose action model serve carry expert movement.	2026-02-05 18:53:31.175005+00
126	32	160	3	Water local across involve fall discuss account health in night house clear say hope.	2025-10-15 18:39:41.421569+00
127	55	175	5	Bad personal might son party really even possible mother especially could.	2025-06-24 14:12:14.881132+00
128	81	80	2	Face PM pay evening performance could affect anyone movement.	2025-08-06 11:56:59.697026+00
129	84	189	3	Example by just account bed address describe inside.	2026-03-13 13:32:43.08354+00
130	53	177	1	Your less social form such weight argue simply author like court success stage stock.	2025-07-14 03:09:04.630703+00
131	54	106	4	His window east yes current same behind program decade home.	2026-05-16 15:50:09.171817+00
132	36	49	4	City rock seat near business loss federal growth appear project wind door.	2025-11-05 03:49:20.588427+00
133	33	154	1	Cold everybody build smile across among situation.	2025-11-20 04:10:27.338222+00
134	81	178	4	Choice side eat matter rather full wide service art green child movie blue maintain first next.	2026-01-21 00:52:38.994156+00
135	6	179	4	South just cover ready group care together magazine join far recent couple.	2025-08-06 17:59:26.41599+00
136	17	170	2	Food life test out team civil most last standard must law simply.	2025-12-01 09:10:10.6055+00
137	10	164	1	Third people hair per fly as whose standard couple.	2026-02-04 03:02:41.157789+00
138	15	41	4	Child executive important focus benefit probably analysis visit condition all blood court all politics home.	2025-11-25 12:29:45.107438+00
139	9	47	5	Red eight hand paper audience us decade man threat bag song art newspaper voice indeed hard.	2026-02-13 08:01:33.926058+00
140	42	43	3	Entire American audience fight war whether best rise mother country moment eat personal condition see indeed.	2025-07-08 02:58:39.182448+00
141	88	184	4	Group learn professor third coach Congress husband front citizen your kitchen good firm yard foot.	2025-10-13 08:28:10.519972+00
142	37	138	3	Step food drive nation heart nearly season growth laugh where a alone expect.	2025-06-05 12:58:08.044448+00
143	37	146	3	Year few feel develop talk against state ready every.	2025-12-18 19:20:37.961152+00
144	14	195	1	Number occur behind leave choose enter threat economic eight feel now notice design baby foot.	2025-11-22 19:50:07.953534+00
145	51	52	1	Stay ready office traditional organization feel room office bad argue side girl stage indicate.	2026-04-12 13:15:52.81908+00
146	72	128	2	Section support up plant place approach modern floor north force.	2026-02-09 10:32:17.158987+00
147	17	133	1	Anything rule hotel knowledge organization measure develop face hour.	2025-07-17 20:48:10.806861+00
148	61	123	1	Live seat nature energy huge its recently seven.	2025-11-22 05:43:00.431317+00
149	15	59	1	Maintain present cultural pattern save east author since food under.	2025-07-02 07:25:50.657948+00
150	50	48	1	Interest give fly order agency fight write pattern wrong kind certainly and stand.	2025-08-11 12:27:29.568861+00
151	9	62	4	Choose rock beat science drug per challenge strategy explain gas sound figure.	2025-11-18 16:24:24.02068+00
152	79	95	4	Decade Mrs data model else low role center recognize adult on professional.	2025-06-15 11:13:06.231411+00
153	19	114	5	Art customer recent even let war at produce production.	2026-04-29 00:03:15.104004+00
154	6	170	5	Ten affect test power discuss herself with between firm term mother cost.	2025-11-29 10:39:01.845456+00
155	25	197	2	Night Republican always two figure majority season adult range green few you without every.	2025-06-22 05:37:39.63308+00
156	41	12	5	These three spring ahead never exactly charge today prevent because him.	2026-05-16 10:30:16.268127+00
157	2	40	3	Their rather individual of interview fine painting last capital present ok range dark catch read together.	2026-04-27 19:04:26.485498+00
158	33	45	3	Yet wish certain usually true fish newspaper we brother fish they risk she.	2026-04-17 01:05:26.016905+00
159	60	52	1	Which field seat start PM scene charge could capital ago worry pay paper.	2026-01-09 05:53:02.646949+00
160	51	98	2	Discussion reach grow read live maybe painting Republican hear system man case cover allow share address.	2025-09-06 03:34:55.836708+00
161	38	130	1	Development provide dark daughter computer western keep pay reach term thought into simply.	2026-01-07 15:02:01.188613+00
162	29	48	2	Result hour voice occur movie political region although body lead there there.	2025-08-28 08:00:09.22332+00
163	43	169	4	How same newspaper might piece any fact huge fight still leave institution party approach might.	2025-07-21 12:54:14.098426+00
164	4	113	1	Bed may conference one thus national hotel food agent law to time think bed.	2025-09-25 22:49:38.280954+00
165	32	155	5	Responsibility but box last guy model himself social memory.	2026-05-12 11:22:48.74465+00
166	37	143	2	Nearly analysis color friend the television class certain shoulder anything final role.	2026-05-16 13:39:49.950382+00
167	19	141	3	Phone brother capital dark performance education learn talk myself accept third.	2025-08-25 11:15:00.417907+00
168	8	29	1	Process law kind over according think everything pick star debate continue area give certainly allow official.	2026-01-05 22:19:16.116544+00
169	53	133	5	Turn any indicate condition public particularly reality organization skin concern lay often.	2026-05-05 19:11:38.749692+00
170	3	159	2	Shoulder follow today star serve successful assume likely.	2025-07-14 03:41:30.855165+00
171	42	95	1	Forget including decide decade around number without more because right painting.	2026-03-14 11:06:17.036739+00
172	19	27	2	Interview summer employee offer perhaps until pass market role marriage space.	2026-04-18 08:02:57.501034+00
173	1	98	1	Remember without ability agency personal brother summer son yourself increase.	2025-09-29 12:00:30.130905+00
174	73	15	4	South defense political real effort attack feel nearly short box four how notice whether story.	2025-08-09 10:45:34.434729+00
175	73	31	2	Two look listen along career choice leave tend time leg sport until.	2025-06-20 01:08:36.463748+00
176	81	10	5	Federal right firm movie decade rate son thousand government wide exactly all worker phone success.	2025-12-25 03:09:12.910811+00
177	70	19	1	Cost bring site final tax report even beautiful theory he stop few modern.	2025-08-02 12:11:07.015826+00
178	84	122	5	Size sing tree kitchen agent lot matter couple type run model simply.	2025-07-21 22:09:19.998261+00
179	83	99	3	State visit quality car right least require mission.	2025-06-01 02:05:30.058416+00
180	88	158	4	Reach organization beautiful level animal minute probably.	2025-09-21 17:11:50.111341+00
181	58	192	2	Serve police decide customer expert mother significant provide evening church boy when nice bill my.	2025-12-17 05:40:23.004174+00
182	88	126	5	Center region exist each author party full kitchen candidate likely push.	2025-07-08 06:35:43.813798+00
183	33	89	4	Beat hot relate through picture real knowledge.	2025-10-07 11:22:58.560527+00
184	62	40	4	Stage require provide move wind sense letter capital spend turn life lay.	2026-02-04 14:02:06.748748+00
249	47	65	2	Out gun lose job election rather window stand.	2025-10-13 21:27:59.80409+00
185	69	93	2	Like water century time election guy contain true form team foot maintain assume both.	2025-11-21 09:48:53.508076+00
186	19	74	2	Executive give offer meet if research blood news audience.	2025-09-17 22:21:37.960256+00
187	50	66	2	Husband including per nature wind himself future sport opportunity six itself skin name door.	2026-01-27 14:21:56.062189+00
188	48	190	1	School Republican student boy other foot best knowledge.	2025-09-20 02:13:58.006205+00
189	56	77	2	Attorney board sport side her management produce bed stage thought tough player a.	2025-07-23 04:13:29.262332+00
190	6	118	4	Laugh factor past language day theory feel some quickly.	2026-05-01 01:25:49.218466+00
191	70	59	4	Response trip wrong old particularly member summer system artist too whose a nice.	2026-05-23 01:04:54.546424+00
192	17	161	3	Technology tend dog reduce hour fish him high.	2025-12-15 16:26:45.680555+00
193	27	104	4	Little could his under style child young prove care.	2025-06-25 18:58:25.471798+00
194	54	118	4	Century those price window career case south.	2026-04-09 17:57:29.63186+00
195	57	100	4	Us perhaps lawyer interest star his difficult interesting account marriage room Republican especially unit office almost.	2025-06-13 09:58:52.819035+00
196	47	87	3	Relate both loss real center rule worker worker single let back three because line.	2026-02-25 11:30:28.789387+00
197	86	103	2	Range much often party tough movement action law.	2026-04-26 12:19:37.005403+00
198	68	53	2	Safe inside whether sometimes eye along type see risk nor article list college appear wrong.	2026-03-22 00:39:06.570862+00
199	28	183	2	Agree machine camera baby six edge past every either scientist page travel school process have compare.	2026-03-12 09:30:56.208451+00
200	73	50	5	Machine son television garden base certain value child many year.	2026-03-07 22:55:28.944892+00
201	47	119	5	Produce rise cold official success approach enough standard apply less.	2025-11-20 12:36:01.679065+00
202	53	96	3	Second sell mouth here relationship listen certain that activity until large question which raise.	2025-06-14 13:36:58.048865+00
203	28	101	2	Pm what it truth teach friend environment better pressure hospital significant see same open crime.	2025-09-30 19:41:27.098081+00
204	61	28	5	Finish action across attack in moment rate goal rise.	2025-08-30 14:07:34.95261+00
205	84	116	3	Agency begin voice prevent structure wear point.	2026-02-13 04:52:55.182834+00
206	80	106	1	Beat painting heavy shake possible sort continue book contain.	2025-09-15 04:11:00.06953+00
207	26	56	3	Police two everybody interview tough show food class.	2025-06-26 14:42:21.688468+00
208	71	41	4	Him four art western enough key man up.	2026-01-08 11:49:31.463794+00
209	67	111	2	Population board music issue pass blood kid else alone.	2025-06-25 07:16:59.218566+00
210	57	7	2	Since affect marriage present a also hospital charge form hospital about.	2026-02-13 00:46:00.754273+00
211	50	146	2	Long identify road speech audience difficult his ready sister building movement yard four field.	2025-06-19 17:53:19.73023+00
212	35	191	5	Half table future subject set face data never.	2026-05-18 23:03:07.074674+00
213	20	165	4	Federal hope blood read main those just country along agent.	2026-05-29 12:07:28.946655+00
214	74	51	2	Majority as music film move strong last yet already argue.	2026-03-14 07:32:35.158158+00
215	53	82	4	If deep president mission vote thank Mr.	2026-02-25 05:56:42.528708+00
216	32	190	2	Under already center president likely truth animal red candidate common.	2025-06-17 19:59:07.334618+00
217	63	81	5	Star best particularly structure ask stage box organization past as dark.	2025-09-30 19:08:03.470946+00
218	79	136	1	Food wish office case student soldier share or friend building center indeed recent.	2025-12-18 17:06:17.632858+00
219	87	25	1	During old card social place heavy citizen they ball account unit religious order.	2025-09-11 05:11:17.480279+00
220	11	6	1	Realize deal policy mission include visit particular also conference matter wear physical site girl.	2025-06-01 06:07:31.586239+00
221	7	85	1	Court worry with peace television would medical less phone decade.	2025-06-18 23:15:21.030909+00
222	41	92	2	Someone rate why listen computer prove amount population.	2025-09-11 16:52:21.801025+00
223	20	55	3	Edge pattern three law bit appear Mr citizen ahead method audience dog know.	2025-12-28 08:07:05.301071+00
224	9	93	5	Cup quality for single for better scene thank heart determine likely machine three.	2025-07-22 12:35:09.454808+00
225	41	150	4	Lawyer hold carry rest place wish dark camera realize arrive carry surface learn commercial gas though.	2026-01-06 01:23:37.350807+00
226	61	87	2	Town official need discover in miss television describe list leg address into their easy its develop.	2026-05-04 08:07:47.448506+00
227	38	78	1	Trial together individual analysis yard safe mean international hour.	2026-03-22 07:50:46.493992+00
228	72	41	2	Laugh drive next actually rule wear car fast.	2026-01-22 03:07:26.765832+00
229	21	107	1	Administration protect class learn now on with less.	2025-07-20 05:12:34.278698+00
230	69	159	4	Continue the phone region ability physical his real most fast send recently partner.	2025-12-26 16:23:17.291937+00
231	21	144	5	Skin ball thing save area war push thousand book half.	2026-01-11 17:14:26.842897+00
232	81	121	3	Hand possible relate night similar catch friend much power say sell that.	2026-02-11 07:01:26.423167+00
233	32	30	2	Fly today me institution approach health laugh may stop like.	2025-12-10 20:36:45.219587+00
234	57	25	1	Tonight later happy pull really within third could this beautiful hospital condition when baby clearly.	2025-07-10 12:02:46.117573+00
235	18	98	4	Many themselves minute physical fall wide must car get.	2025-11-08 16:50:10.483863+00
236	49	123	2	Factor as the discussion water popular in.	2025-10-02 18:54:07.750572+00
237	3	151	3	Main program morning nature leader note together fill smile dinner head explain.	2026-04-04 09:38:08.906932+00
238	57	150	5	Good lay coach under Republican expect win stuff realize.	2026-01-28 23:10:55.300779+00
239	24	115	1	Claim bring year off kid hard day religious program.	2026-05-22 19:10:35.823869+00
240	63	172	5	Health music class feeling turn identify material certainly leader.	2025-09-24 13:01:08.70924+00
241	45	87	1	Wife national medical positive far time wide.	2026-03-02 00:51:56.272109+00
242	23	35	5	Project son rock two full both look always question bring agent pay detail group for.	2026-01-07 16:58:23.171391+00
243	39	174	4	On develop very everyone against Mrs knowledge public beautiful memory.	2025-08-09 14:34:04.556816+00
244	20	29	2	Owner memory argue project huge respond into history activity general final knowledge.	2025-12-21 11:56:46.619686+00
245	82	83	3	Road know yeah sound eye south wife interest to cause.	2025-12-31 01:08:42.377193+00
246	11	91	5	Century field write moment friend value opportunity heart.	2025-06-02 00:05:05.866467+00
247	64	5	5	Increase new report sense carry control high network amount step strong.	2025-09-18 14:06:21.833686+00
248	76	107	2	Science different social child feel policy PM buy program explain conference trade population agreement share.	2025-11-26 16:01:31.786228+00
250	66	72	5	Adult employee ok certainly leave really group apply guess player western any factor police baby.	2025-08-09 08:59:59.571585+00
251	4	126	3	Consumer behind sell myself their step rate feeling rate read benefit oil statement actually million health.	2025-11-23 16:34:26.510842+00
252	22	14	2	Tv clear design me story somebody next ready weight suffer Republican reduce.	2026-03-19 17:17:30.107581+00
253	40	68	4	Leave baby standard type look find guy stage threat our shake garden report.	2025-06-10 02:09:53.123642+00
254	56	87	1	Develop task central dinner by candidate bad real six.	2025-06-27 23:28:28.261783+00
255	35	192	4	Serious amount blue soldier message arrive budget education at property senior site turn day.	2026-04-24 17:32:53.372593+00
256	85	21	3	Provide ahead certainly second everyone often goal talk sit.	2026-01-09 11:05:40.204389+00
257	71	9	2	Now between official add describe course example top Mr wind better degree mean remain.	2025-10-11 10:23:32.954053+00
258	80	3	5	Continue pull blue strong wonder interest method imagine seven fire letter mind many guess explain reveal.	2025-06-29 15:01:52.691033+00
259	3	78	4	Break exist outside find wish know network fact talk country attorney subject little quickly.	2025-08-04 01:44:33.037363+00
260	26	121	4	Public how mission put budget house reason within scientist throughout collection hair current customer.	2026-04-03 20:37:32.139614+00
261	50	10	3	But study rise everything require old event smile popular hundred live owner identify.	2025-11-23 13:21:51.523038+00
262	49	86	3	Challenge lawyer business majority discuss wall ahead scene store marriage ago.	2025-08-03 23:58:31.355458+00
263	66	109	4	Quickly check perform benefit baby seem should society dark product make energy gas teacher national weight.	2025-06-11 03:03:02.254295+00
264	44	34	3	They budget late table kind along computer process single those clearly issue fine.	2025-10-19 16:39:06.331668+00
265	34	142	2	Notice make network much like no choose argue.	2025-09-03 18:53:15.757807+00
266	63	73	3	Wife pay good within fly agreement and student give score agree through game best generation group.	2025-10-05 21:12:27.317549+00
267	11	116	1	Easy possible or travel assume figure front after for leave.	2026-04-10 22:08:48.513096+00
268	86	82	5	Method inside after like against first now follow best major real day market specific property.	2025-07-30 10:40:47.126938+00
269	15	6	2	Guy job market suggest skin subject movie explain answer you I.	2025-08-21 02:07:40.143366+00
270	14	63	1	Response official option event note most interview girl.	2025-06-27 14:03:45.60796+00
271	23	96	1	Measure feel professional finish increase economy middle public natural thing physical.	2025-12-05 03:09:44.115911+00
272	20	147	2	Officer defense while score level view mouth pass shoulder.	2025-11-04 23:59:25.065171+00
273	12	20	1	Risk art customer leg drive second she such improve team treat plant suffer environment expert.	2025-07-28 05:42:32.680127+00
274	2	189	3	Door draw change agree someone financial magazine yard instead town dark evening ahead smile everyone nearly.	2026-01-20 21:47:26.023596+00
275	80	19	2	White magazine after teacher base own test.	2026-04-24 12:17:19.893359+00
276	75	161	4	To public though however style successful door number matter building professional oil simple.	2025-12-08 10:22:11.487494+00
277	81	85	1	This draw business southern forget once hope security door institution certain compare wide keep.	2025-08-31 11:15:00.795619+00
278	79	32	1	Argue mouth record both nation little east everyone six certain little happy final population toward alone.	2026-02-24 15:54:15.428523+00
279	18	52	1	Real small dream need finally when guy.	2026-03-23 06:03:24.248207+00
280	24	24	1	Movement door kind account whether until truth feeling view.	2026-03-02 22:50:06.064449+00
281	1	111	2	Decision three trouble place these short image almost term statement wait.	2025-11-18 15:32:19.261776+00
282	27	13	1	Unit four institution truth beyond civil end at inside role natural force receive.	2026-03-04 21:21:33.963968+00
283	50	83	5	Picture social carry husband pick finish bank citizen might.	2026-05-19 17:54:45.375432+00
284	25	122	2	Suggest rate society floor long same end reach step.	2026-03-18 14:32:31.09862+00
285	64	155	2	Base happen hour help strong now again age next partner.	2025-08-22 02:51:30.176629+00
286	61	74	5	Wind cup red collection husband investment employee become.	2025-10-11 23:09:55.172345+00
287	8	114	2	Bring responsibility itself turn law purpose budget require course technology site explain management candidate task.	2026-01-04 18:14:50.071637+00
288	65	2	1	Risk country Congress society agreement wish dog late eat old positive.	2025-06-30 21:37:48.696718+00
289	23	51	3	Card follow realize rather require remain save eight believe arrive four dog traditional you.	2026-05-08 15:56:10.485099+00
290	19	139	5	Remember special accept mean herself within provide car throughout American conference college manage fund life bed.	2026-02-13 23:59:43.662127+00
291	25	180	1	Center bring analysis campaign the strong security unit executive theory party seven enough.	2025-09-21 21:50:19.902984+00
292	10	49	2	Firm yes shake character table price sometimes apply chance.	2025-08-22 12:58:04.553344+00
293	42	194	2	Like clear level break time manager kid.	2026-05-26 17:48:42.997865+00
294	21	102	5	Magazine manage suffer term buy behavior test Congress collection meet evening through one on will.	2025-12-08 16:59:25.318009+00
295	38	154	4	Congress turn east marriage behind forget expect wonder business health upon black food ahead least.	2026-02-13 01:39:07.920916+00
296	65	164	3	Law western order accept wide prevent week foot rule same whatever notice deep any.	2026-01-20 16:05:40.717542+00
297	28	110	3	Sometimes season natural own begin effort drive side human after decade home.	2025-10-24 13:22:27.724132+00
298	45	189	2	Building make it south financial rate capital program story.	2025-12-03 19:51:38.501681+00
299	68	2	3	Knowledge hold environmental outside bed institution happy control piece behavior message wind put positive.	2026-02-15 05:37:22.538822+00
300	37	194	2	Money positive base life bad soon feel worker range feel eat into notice necessary.	2026-04-30 14:54:53.449552+00
301	9	16	1	Blue interesting behind produce nothing effect effort bank me box product conference consider hotel bar.	2026-04-15 19:29:33.026144+00
302	64	89	1	Finish right serious last space game truth special decision back word.	2025-09-02 07:10:55.34025+00
303	80	194	4	Its adult house actually pretty least if price.	2026-02-26 09:57:16.735048+00
304	11	173	4	Field spend pattern real white push source because career course staff receive could agree.	2025-11-22 07:25:24.268644+00
305	2	191	1	Power job personal so course feeling leg listen against.	2025-07-30 06:06:23.196308+00
306	41	151	3	School knowledge machine after last drug far stop hot.	2025-09-29 12:30:54.080514+00
307	88	156	1	Piece require woman support say other never fact.	2025-11-24 15:20:34.765635+00
308	73	68	3	Message right very toward test discussion art affect office network environmental possible threat bring.	2026-01-13 00:28:31.048301+00
309	58	92	4	Large job claim risk light just medical onto rate two table resource.	2025-11-17 16:32:14.318914+00
310	48	128	3	Rich hospital indicate wait present growth line wife class debate real.	2025-07-01 01:36:10.957708+00
311	70	191	2	Can current paper beyond indeed year field decide another adult thing ground city still.	2026-04-22 06:39:54.264579+00
312	30	151	2	Southern front box dinner no main year.	2026-03-13 06:11:10.107659+00
313	6	177	3	Show news to table them page bit.	2025-06-18 00:03:11.06992+00
314	53	120	4	Sometimes while sense window sit participant teach big none medical cold brother day.	2025-10-09 16:06:04.633411+00
315	42	104	4	Remain seven marriage that child hair standard but dark wide shoulder.	2025-06-01 23:48:38.340653+00
316	60	116	2	Game measure be head senior guess professor charge send instead direction soon including important.	2025-11-14 03:23:05.327188+00
317	19	189	4	Some gun ahead certainly act south want be fire word clearly article service produce political.	2026-04-25 05:15:41.516139+00
318	54	7	2	Within woman sometimes then win information though red.	2026-04-14 15:21:47.998523+00
319	41	98	2	Training account evidence month turn record land day name small present recently.	2026-04-19 19:12:38.362905+00
320	52	94	1	Simple thing base Mr hope rest they minute must degree memory fine future.	2026-01-17 18:19:55.650059+00
321	56	170	2	Agreement someone or drop similar risk would.	2025-07-09 22:10:22.078662+00
322	20	152	2	Success employee medical buy series walk large occur.	2025-06-01 11:45:53.828681+00
323	28	25	1	Work south writer not thus physical mouth other go expect size resource.	2026-01-31 04:27:31.968396+00
324	51	121	2	Mind easy foreign old state guess better Republican stock bank artist thousand.	2025-11-20 12:47:08.447698+00
325	35	87	2	Back quality idea next single the once PM you ready way rule indicate clear.	2025-12-01 07:39:47.830732+00
326	3	128	4	Represent can relate tell brother defense list second want hard weight own impact building.	2025-12-25 10:01:05.409539+00
327	21	78	5	Mission brother figure hear family agreement central.	2026-03-12 20:36:09.005085+00
328	36	59	2	Any thus threat democratic standard major business give that individual of not too.	2026-03-11 23:11:11.12552+00
329	63	156	4	Strong street car catch PM seven project chance road become person perhaps hold too.	2025-10-01 09:38:22.672039+00
330	56	112	2	When three save position tend religious occur.	2026-03-17 09:00:08.479859+00
331	63	171	1	Night buy nice court peace officer apply now country live to.	2025-07-13 12:26:20.444124+00
332	46	28	1	Conference affect skill early relationship thought know southern parent I and technology age join increase.	2026-04-09 13:32:13.941036+00
333	42	181	4	High before woman my experience consumer shoulder child weight question arrive which.	2025-08-04 20:40:53.155439+00
334	78	75	2	Fear better central throw election walk tonight appear.	2025-08-26 02:32:34.602125+00
335	31	133	4	Only manage sell his boy art let imagine machine imagine do though especially white push east.	2025-12-19 04:29:52.558735+00
336	28	107	4	Fight image base player data whose health world site.	2025-12-12 21:58:25.960617+00
337	2	79	2	Which new among spend which per president cold art two event economy quite.	2026-05-30 13:10:47.853541+00
338	44	162	3	Defense subject example claim move attorney bed recognize store rise your there decision measure soon this.	2026-05-10 21:17:21.374703+00
339	88	159	4	Woman remain event production focus decision where foreign trial card two.	2026-01-07 22:32:38.762985+00
340	77	34	5	Top pull including time reflect several Mrs.	2026-03-14 03:23:39.450553+00
341	37	88	3	Much throughout staff knowledge but will heavy over.	2025-10-18 20:13:56.299309+00
342	17	95	5	By have cover act sea serve quite.	2026-02-13 14:43:23.026743+00
343	61	17	1	Bed party field response doctor management guy exactly toward religious.	2025-08-14 22:51:57.843973+00
344	58	95	4	Worker point book everyone matter color create school public owner.	2025-08-02 16:42:33.255352+00
345	32	54	3	Campaign assume employee now direction mission site court question yeah realize mouth education nice law visit.	2026-01-19 16:37:19.881979+00
346	30	81	4	Take follow such imagine business million many.	2025-12-05 12:12:55.872137+00
347	36	143	3	This different everyone information large accept create.	2025-06-29 11:10:57.904874+00
348	74	85	2	Space wrong difficult ready when true culture forget as personal agreement it agency something various.	2026-04-02 13:45:11.924684+00
349	17	83	5	Blue draw future approach four some want simply people shake.	2026-01-13 23:43:21.650044+00
350	30	182	5	By window true help three really site artist sort area particularly it big argue appear sure.	2025-10-24 07:07:22.375677+00
351	79	61	2	Sell do outside process action himself somebody they people fund visit situation law foreign court bill.	2026-01-02 23:13:39.746438+00
352	63	145	4	Or subject toward call meeting green loss per.	2025-08-06 11:49:31.864711+00
353	3	81	5	Someone art find job where senior find those simply.	2025-07-23 10:13:04.87265+00
354	13	99	2	Owner fact wife military price certain down standard nice area gas.	2026-05-22 05:55:28.636688+00
355	80	83	1	Size game property reason word outside former official white pattern.	2025-10-30 12:14:52.67937+00
356	68	126	4	Bit then treat many turn police really level defense.	2025-11-22 04:10:17.157621+00
357	78	187	3	Southern heavy hundred step according act group never central key place tree.	2025-10-09 00:56:36.768341+00
358	9	116	4	Current exist despite energy company suggest early.	2025-08-10 04:02:43.690681+00
359	25	198	3	Successful treat again quality her skin book very figure.	2025-08-26 07:09:44.032108+00
360	19	94	1	Produce wait with young think there assume certain under some court her.	2025-10-14 06:41:51.759829+00
361	61	64	2	Involve player TV several onto take family chance easy picture evidence call meet once major road.	2026-03-13 04:15:09.290356+00
362	82	1	3	Ask meet seem population meeting material less focus hear reason resource manager environmental husband TV once.	2025-06-12 22:55:54.162641+00
363	46	159	4	Thus later doctor despite interesting help church successful effort be.	2026-03-01 02:36:36.755865+00
364	72	38	3	Know goal once let perform international level important source first him.	2025-08-04 04:05:44.367863+00
365	41	125	3	Enter away top family maybe national back everybody direction budget.	2025-10-09 03:48:56.463568+00
366	78	138	2	Customer cultural forget few spring raise ever relationship your your sell science treatment across federal.	2026-03-26 22:13:39.47456+00
367	83	49	5	Watch state serious activity pressure writer week tend dinner rich decide do only.	2025-12-18 10:09:29.658326+00
368	78	31	3	Reveal left social fine could show recently decide last next hear officer campaign wall.	2025-06-03 02:55:41.622247+00
369	8	189	2	Fund industry rate idea single Mrs for age size two child well.	2025-09-28 04:57:44.732829+00
370	68	130	3	Sometimes trial off hospital high we as hit little forget while police fight commercial push concern.	2026-03-28 10:44:43.963878+00
371	32	97	4	Major cost attorney white exist do process attorney arm million commercial teacher improve church book movie.	2025-11-21 06:18:01.041665+00
372	2	77	3	Home tough deal that finally stand professor city.	2025-12-26 15:10:42.977541+00
373	27	37	3	Onto maybe range every account central ask human space moment travel.	2026-04-16 17:16:01.357361+00
374	4	8	4	Leg although before position try get successful society hospital statement sure indeed conference pay.	2025-11-04 09:32:43.640904+00
375	11	95	4	Treat contain notice hour watch dream that event physical factor trouble recently reveal.	2025-08-17 22:28:10.544482+00
376	19	115	4	In seven building hard sense mean single improve close debate and ago police put.	2025-11-15 07:00:17.632429+00
377	77	114	3	Second talk however action boy true force security machine attention nature drug.	2026-05-12 13:41:56.603726+00
378	14	71	4	Likely evidence claim stuff parent concern buy scientist collection.	2026-01-30 19:19:41.0166+00
379	36	51	5	Quality child group describe alone push democratic.	2026-02-09 01:32:30.829085+00
380	59	73	2	Political respond to hospital final appear above significant short up hear draw before instead writer.	2025-09-30 17:08:56.886977+00
381	76	33	3	Quite as when benefit structure professional right analysis mention spring.	2025-09-25 10:35:50.192267+00
382	3	32	1	Couple debate must voice building degree ground community I first home learn at spring practice hard.	2025-06-24 04:16:31.065548+00
383	42	142	4	In should matter wrong Republican social two notice edge behind.	2025-09-26 01:16:38.725992+00
384	48	37	3	Recent question win really forward play this fish surface lot friend part one him political discussion.	2025-12-31 03:40:25.858874+00
385	49	141	1	Discussion pattern to final scene serious people.	2025-06-21 11:20:10.8139+00
386	81	112	3	Material dark heart politics draw rise write kitchen theory care fish skin.	2025-06-14 01:15:18.682647+00
387	51	46	3	Possible eye agency suggest former drug much trade professor eat reach rest part.	2025-10-16 22:04:46.48281+00
388	79	195	1	Contain picture ask man west appear yeah voice by community nature somebody.	2025-08-13 05:33:11.271957+00
389	83	73	3	Back right find return each computer eat experience large player even sit bag win.	2025-10-23 00:58:51.703351+00
390	73	194	5	Likely institution participant item choose west lot seven into.	2025-06-29 23:39:53.247233+00
391	6	131	1	Organization check risk either less law heart paper author carry light.	2025-07-26 02:20:34.802689+00
392	17	128	1	Above technology room hear identify indeed house score himself film.	2026-05-26 06:26:49.022765+00
393	9	36	2	Impact although TV his not create job effort.	2026-04-29 01:57:29.69752+00
394	14	134	2	Meeting major read recent prepare unit save drug alone spend piece put.	2026-02-09 07:55:57.545684+00
395	31	24	3	End lay race effect own weight success activity side.	2026-01-20 22:41:54.33805+00
396	46	87	1	Huge only too million country institution stop education few whose probably him final.	2025-10-27 22:07:52.300908+00
397	53	88	1	Body of something sport especially decide security recognize.	2025-06-01 22:20:39.925614+00
398	64	103	5	Staff ability attorney recent modern pressure run color hear.	2026-02-11 17:34:27.515095+00
399	8	135	4	Main me book note defense cut seek speak court work.	2026-04-13 22:26:17.710404+00
400	83	102	2	Phone person than coach fall help everybody garden one long pull beyond article.	2026-03-01 04:09:08.990036+00
401	71	23	2	Program smile among decision social heart mind.	2026-05-16 23:14:02.513136+00
402	58	41	1	Usually list front investment he three yourself stage wait professor her.	2025-06-20 11:49:52.290457+00
403	34	59	2	Their south able that I structure understand agent but most week seem.	2025-08-29 08:41:12.692753+00
404	8	166	5	Peace probably little including could worry whatever spend admit growth animal space for know.	2026-01-07 04:48:16.320489+00
405	4	14	2	School soldier give voice walk live probably record beyond his parent Republican thank.	2026-04-15 14:55:21.22278+00
406	62	11	1	All marriage beautiful strategy you would level to western lot music during color want.	2026-02-10 05:17:59.608189+00
407	29	195	2	Itself respond civil upon total short detail election.	2025-11-20 13:13:02.502589+00
408	20	36	5	Program two plant man somebody four difference office under.	2025-06-23 04:55:16.346797+00
409	41	83	4	Help response save high politics no task speak difference break because become.	2026-02-25 01:49:22.009498+00
410	82	172	4	Seat break happy table west officer ability artist movie suggest.	2026-05-23 11:11:27.932867+00
411	3	131	3	Side something value call professional opportunity blood across system firm staff father.	2025-08-18 12:55:39.253937+00
412	64	7	4	Challenge exist section support still alone floor maybe read event summer off piece democratic.	2025-09-14 01:14:30.070937+00
413	71	18	1	Arrive special check respond summer various different save type simply task road.	2025-09-16 19:55:11.822075+00
414	26	151	1	Yard nature front question wrong serious hospital month executive.	2026-02-08 22:19:59.550445+00
415	27	59	5	Red nature best food social tend approach various fight pressure.	2025-12-27 09:17:19.987013+00
416	63	2	3	Receive fact certain design security same across rise offer question write challenge wear.	2025-11-02 14:01:07.104775+00
417	11	149	3	Unit benefit wind conference appear woman practice order wide.	2026-01-14 13:57:23.132192+00
418	66	43	4	Each budget however few other common seat simply yard provide bed less stand.	2025-10-17 03:28:13.840424+00
419	28	39	5	President happen build bar majority protect meeting age of of event seat some Congress machine popular.	2025-11-04 23:23:39.011796+00
420	1	161	5	By foot research television Mr if red hour stage situation morning ask student much standard.	2026-01-23 14:43:01.726325+00
421	37	69	5	Whole today Congress out conference never song but can deal.	2025-07-28 11:11:45.676519+00
422	48	131	4	Either send be by fear whom commercial with probably eat animal watch toward fall move.	2025-07-20 16:00:04.777496+00
423	21	52	5	Reason mission worry goal Mrs decide between standard down could feel strategy whatever own.	2025-08-17 11:49:12.219079+00
424	33	86	2	Everyone rock instead near end power clear lay war put vote century.	2025-08-13 00:12:07.943585+00
425	42	67	4	Run yet recent cover head price star painting information child yeah its ago page back by.	2025-07-09 18:12:45.573299+00
426	16	167	3	Image forget become training sing chair something event better woman develop weight situation but money.	2026-04-15 08:35:34.657658+00
427	58	8	4	Start majority more red tend necessary parent to color water hope generation scientist whose mother organization.	2026-04-05 21:43:06.116004+00
428	78	167	5	Or else rather require price central nothing environment truth police have since question industry.	2025-11-13 18:54:46.603632+00
429	52	53	2	Worry sometimes maybe every into walk thing sport figure teach water image fine.	2025-07-02 12:12:58.905976+00
430	15	11	4	Baby drive behavior offer be experience upon space.	2025-06-03 11:48:45.266457+00
431	14	191	2	Quality usually carry marriage rate quality mother by add couple story account interesting.	2025-12-11 17:49:43.375919+00
432	26	195	5	Each school week statement they month participant parent who purpose think model.	2025-08-20 18:57:45.695834+00
433	39	177	2	Happen card government anything many color wide full.	2026-02-02 14:34:13.277973+00
434	76	78	3	Surface tax face low enter able piece hour type upon where middle throw very throughout.	2026-04-05 10:30:49.164093+00
435	60	14	2	Green past forget government accept three control great.	2025-07-06 14:22:05.532348+00
436	28	131	1	Culture more together improve tree according show economic likely hear hair throughout movie especially.	2026-05-26 22:38:20.123085+00
437	40	4	2	Class government its grow that cup couple American house season too civil current.	2025-11-21 15:27:01.315106+00
438	24	86	2	Budget major many race camera seem sister hundred rise score stay.	2025-07-17 14:02:28.723398+00
439	64	185	4	Society call general add range appear stop involve.	2026-01-03 15:59:07.227356+00
440	42	118	4	Its face magazine set easy check memory.	2025-08-29 16:49:53.518974+00
441	78	193	2	Ten yes easy star cup relationship special red.	2025-11-30 01:24:15.642924+00
442	63	123	5	Country talk pick chance build husband event court certainly.	2025-06-06 00:52:50.405601+00
443	77	74	2	Before anything imagine fill plan discuss from look member popular.	2025-09-18 17:23:54.881664+00
444	10	158	1	Hair wall represent east time consider a produce focus experience exactly.	2026-01-07 02:41:25.054945+00
445	1	8	5	Continue way hair fight best add necessary technology former scientist guess single more.	2025-10-13 07:21:15.63814+00
446	7	3	3	Decide himself thought candidate sea build only treatment pressure couple relate.	2026-05-03 14:46:55.349097+00
447	1	78	4	Walk people feeling listen set move child campaign.	2025-10-30 08:00:59.33046+00
448	49	187	5	Through service suffer night girl hand picture brother job lot model.	2026-05-13 10:57:47.098864+00
449	21	25	1	Cold ever whose face what article win.	2025-08-08 01:14:00.551428+00
450	48	56	2	Manager mouth message avoid just meeting none hope parent deal about occur option.	2025-06-02 19:44:30.486719+00
451	55	190	3	Lay remain modern field detail remain need commercial animal draw although challenge third until establish.	2026-03-15 08:27:44.217783+00
452	10	72	4	Writer decide break possible plan win foot watch this enough.	2025-07-18 09:16:21.992886+00
453	84	6	3	Far world personal action green room evidence eight administration price test voice on reveal read watch.	2025-09-01 13:53:29.553147+00
454	5	31	3	Plant nearly stage determine environmental ok space send choose discussion risk happy total behavior consider continue.	2026-04-10 13:14:15.810706+00
455	19	68	4	Now wall Congress example financial those stage reach could century.	2025-11-02 07:44:31.41415+00
456	27	31	1	Training wife beyond money risk space owner help again step shake popular analysis eat.	2025-06-30 02:50:38.578864+00
457	61	45	1	Voice outside society act social my stand system be.	2025-07-20 10:31:23.459394+00
458	15	23	2	Throughout spring film look during myself environment myself again and name bill though indeed ability.	2025-08-20 12:20:14.082138+00
459	59	149	5	Interview challenge pretty difficult these his this state both college.	2025-07-09 19:29:17.751081+00
460	35	70	1	What example baby free guess under be analysis.	2025-07-24 18:35:52.497983+00
461	73	123	1	Most outside quickly change project feeling stage give billion trouble product usually specific.	2026-02-14 09:12:33.185828+00
462	20	56	1	Small technology within sing chair challenge land someone.	2026-05-22 04:25:15.861399+00
463	51	174	4	Both into risk certain follow camera should good.	2025-11-27 02:09:39.304901+00
464	4	10	4	Really including soldier four soon president early industry market move mouth start his ok.	2025-10-31 15:49:13.530735+00
465	56	120	4	Since specific despite beautiful gun data sure gun listen card body treat guess support single.	2025-07-20 11:34:04.331342+00
466	23	4	5	Century table will tree drug still argue case while region help ago who he.	2026-02-10 18:23:06.279257+00
467	6	169	1	Available study that air half bad baby notice sport change consumer sea security recognize federal in.	2025-09-30 19:04:50.35429+00
468	36	182	3	Expert choose thing allow seem me action.	2026-03-30 17:08:21.912007+00
469	62	52	3	Never stop try maybe remember interest church win miss within by deep people despite.	2025-08-05 16:16:51.890635+00
470	4	172	3	Painting baby realize local present if herself area he interest establish bit guy single friend.	2025-08-26 01:43:38.362968+00
471	25	61	4	Must assume others series finally necessary point allow especially.	2026-05-22 07:15:37.08104+00
472	1	167	1	And worry low answer behavior final wonder seem when matter fire hospital green can push.	2025-09-28 14:19:16.58339+00
473	73	112	5	Big space change onto him only system face charge leg those behavior responsibility this.	2026-03-21 12:12:24.027392+00
474	63	60	1	Shoulder claim white might rock prepare us game size.	2025-10-01 09:50:23.008663+00
475	37	94	1	Perhaps vote always require raise dream young parent when note yes best.	2025-06-05 01:02:28.955415+00
476	77	95	4	Natural why sit beautiful behind finish value claim evidence guy become.	2025-08-04 00:46:09.267622+00
477	61	140	2	Election list eight theory practice cell buy notice always teacher husband tax true can.	2025-10-11 12:45:09.297474+00
478	48	169	3	Weight health radio media enjoy then radio per popular scientist each start account table fact citizen.	2025-10-23 10:03:42.814852+00
479	71	139	2	Development them protect give life movement stand board.	2025-08-04 10:17:54.813754+00
480	42	189	3	True two should current forget fish you main.	2026-02-11 02:10:42.586374+00
481	53	45	5	Boy lawyer nation we certainly degree nothing write similar artist speak smile without degree.	2025-08-15 19:57:41.221326+00
482	52	96	4	Well raise establish player base attorney if.	2025-09-16 13:12:51.730493+00
483	45	197	3	The modern prove else store begin top garden send clearly glass industry little read.	2025-07-28 06:37:41.399279+00
484	19	173	4	Great realize home act situation others back property pattern food worry voice sea.	2026-02-23 15:58:12.012629+00
485	87	139	4	Add to value material first society purpose enjoy reveal write wall tax.	2026-01-17 06:07:34.417683+00
486	47	111	1	Best despite without information national coach help girl weight will officer add sport administration to maybe.	2026-04-12 12:37:30.799264+00
487	78	65	2	Power lay improve goal my mission share box compare into computer organization myself high.	2026-04-04 05:56:08.788746+00
488	43	92	4	Plant reduce visit town between because student bed administration usually billion seek perhaps.	2025-12-15 13:04:14.859201+00
489	58	193	5	Me south property system deep since necessary boy task wear go soldier less.	2026-04-27 05:19:09.335022+00
490	88	43	1	Account hear difference exist they enough stuff somebody increase drop too increase administration.	2025-07-25 14:31:01.377674+00
491	44	130	2	Subject million scientist fish color occur involve new hot pattern hotel appear.	2026-05-05 23:13:52.102741+00
492	77	88	5	Can player within community tough military join between song mean place six successful.	2026-01-14 16:59:16.557433+00
493	81	191	2	Study city follow behavior agent activity show check peace myself win.	2025-12-25 10:16:23.089128+00
494	74	36	2	Score candidate law place group dream today.	2025-09-16 00:49:01.14522+00
495	51	21	4	Subject risk southern her employee appear bar century age world term book until but center.	2025-09-03 06:38:52.761347+00
496	15	129	5	Behavior management guess stuff hospital make against available where.	2025-06-27 11:00:15.256821+00
497	6	134	1	Heart finish traditional speak conference act condition note parent all wish year low.	2026-01-09 20:17:09.574672+00
498	74	2	3	Above miss effort business paper movie military set describe half together ahead catch base reality.	2025-07-15 19:38:15.462215+00
499	71	171	2	Loss well give necessary family seat many mention hundred cover common.	2026-02-05 12:38:46.778455+00
500	30	176	3	Which bill soldier onto close day reveal item land others even.	2025-09-24 00:08:24.177947+00
\.


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.categories_id_seq', 16, true);


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.customers_id_seq', 201, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.employees_id_seq', 50, true);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.order_items_id_seq', 3000, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.orders_id_seq', 1001, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.products_id_seq', 100, true);


--
-- Name: reviews_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.reviews_id_seq', 500, true);


--
-- Name: suppliers_id_seq; Type: SEQUENCE SET; Schema: ecommerce_v1; Owner: sandbox_admin
--

SELECT pg_catalog.setval('ecommerce_v1.suppliers_id_seq', 30, true);


--
-- PostgreSQL database dump complete
--

\unrestrict o9RxaIZY2WfhMqrTIs7hwrQ9tIePHsSKoIXUtHv5PaIgeo8OLSyfCBeEPjzPUai

