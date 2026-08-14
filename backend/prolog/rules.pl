% ============================================================
% rules.pl — pravila za odlučivanje što korisniku preporučiti
% Sub-faza 1B: ZPD-based recommend_next s 4 klauzule + helperi
% ============================================================

:- consult('ontology.pl').

:- dynamic(mastery/3).  % Python injecta BKT snapshot: mastery(UserID, Concept, P_L)

% Python injecta koncepte koji OVOM korisniku mogu dati zadatak, tj. imaju barem
% jedan aktivan primary zadatak koji korisnik NIJE riješio.
%
% 🔴 JEST po korisniku (skup ovisi o riješenom), pa se injektira i briše unutar
% iste kritične sekcije kao mastery/3 (prolog_lock u RecommenderAgentu).
%
% Zašto postoji — DVA oblika istog ćorsokaka, oba su davala „Nema novih zadataka"
% uz neriješene zadatke drugdje:
%
%   (a) transverzalni koncepti (Kat. A, npr. join_condition) po dizajnu nemaju
%       zadatke, a u snapshotu dobivaju 0.0 da bi BLOKIRALI nizvodne koncepte.
%       Ta 0.0 ih ujedno čini `weak`, pa su pretjecali prave koncepte kroz
%       klauzulu 1. Jedna vrijednost je nosila dvije uloge; ovaj predikat ih
%       razdvaja tako da 0.0 zadrži SAMO ulogu blokade.
%
%   (b) koncept kojemu je student riješio SVE zadatke, a mastery mu je ispod
%       praga, ostajao je kandidat zauvijek — Prolog ga preporuči, task selekcija
%       nema što vratiti. Izmjereno na `admin`: where_filter (3/3, p_l 0.77) uz
%       71 neriješen zadatak drugdje.
%
% Invarijanta je zato „koncept može dati zadatak OVOM korisniku", ne „koncept ima
% zadatke" — potonja pokriva samo (a).
:- dynamic(recommendable/1).

% --- Pragovi ---
mastery_threshold(0.85).    % P_L >= 0.85 → concept mastered
weak_threshold(0.30).       % P_L < 0.30 → concept weak

% --- Osnovne klasifikacije ---
mastered(User, Concept) :-
    mastery(User, Concept, P_L),
    mastery_threshold(Threshold),
    P_L >= Threshold.

weak(User, Concept) :-
    mastery(User, Concept, P_L),
    weak_threshold(Threshold),
    P_L < Threshold.

partial(User, Concept) :-
    mastery(User, Concept, P_L),
    weak_threshold(W),
    mastery_threshold(M),
    P_L >= W,
    P_L < M.

% --- Prerequisite-i savladani? ---
% "ne postoji prereq koncepta koji nije mastered"
prereqs_met(User, Concept) :-
    \+ ( prerequisite(Concept, Prereq),
         \+ mastered(User, Prereq) ).

% --- Može li otključati koncept? ---
can_unlock(User, Concept) :-
    concept(Concept),
    prereqs_met(User, Concept),
    mastery(User, Concept, P_L),
    mastery_threshold(M),
    P_L < M.

% --- Je li spreman za koncept (može rješavati zadatke)? ---
ready_for(User, Concept) :-
    concept(Concept),
    prereqs_met(User, Concept).

% --- Glavno pravilo preporuke (Zone of Proximal Development) ---
% Prioriteti:
% 1) Ako postoji slab koncept s ispunjenim prereq-ima → ojačaj ga
% 2) Ako postoji partial koncept s ispunjenim prereq-ima → nastavi
% 3) Otključaj novi koncept čiji su prereq-i ispunjeni
% 4) Fallback: ready_for + još nije mastered
%
% `recommendable(Concept)` je ZADNJI cilj prije cuta u svakoj klauzuli, i to je
% bitno: kao PRVI cilj s nevezanim Conceptom on postaje GENERATOR, pa poredak
% rješenja prestaje ovisiti o `mastery/3` (kanonski pedagoški slijed) i počinje
% ovisiti o poretku `recommendable/1` fakata. To je mehanizam ERRATE #60 —
% preporuka koja se mijenja bez ijedne izmjene koda. Kao zadnji cilj on je čisti
% FILTER nad već vezanim konceptom i ne dira nabrajanje.
%
% Filtriranje tek u select_task_for_concept dalo bi reason="exhausted" = tiši
% ćorsokak umjesto rješenja (isto pravilo koje maska 0.99 već provodi za Kat. B i C).
recommend_next(User, Concept) :-
    weak(User, Concept),
    prereqs_met(User, Concept),
    recommendable(Concept), !.
recommend_next(User, Concept) :-
    partial(User, Concept),
    prereqs_met(User, Concept),
    recommendable(Concept), !.
recommend_next(User, Concept) :-
    can_unlock(User, Concept),
    recommendable(Concept), !.
recommend_next(User, Concept) :-
    ready_for(User, Concept),
    \+ mastered(User, Concept),
    recommendable(Concept), !.

% --- Lista svih prerequisite-a (tranzitivno) ---
all_prereqs(Concept, Prereqs) :-
    findall(P, transitive_prereq(Concept, P), Raw),
    sort(Raw, Prereqs).

transitive_prereq(Concept, Prereq) :-
    prerequisite(Concept, Prereq).
transitive_prereq(Concept, Prereq) :-
    prerequisite(Concept, Intermediate),
    transitive_prereq(Intermediate, Prereq).

% --- Obrazloženje preporuke (za logging i UI) ---
explain_recommendation(User, Concept, Reason) :-
    weak(User, Concept), prereqs_met(User, Concept),
    Reason = weak_with_prereqs_met, !.
explain_recommendation(User, Concept, Reason) :-
    partial(User, Concept), prereqs_met(User, Concept),
    Reason = partial_continuation, !.
explain_recommendation(User, Concept, Reason) :-
    can_unlock(User, Concept),
    Reason = unlock_new, !.
explain_recommendation(_, _, fallback).
