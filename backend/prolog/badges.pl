% ============================================================
% badges.pl — DEKLARATIVNI mirror seed-pravila bedževa (Faza 3D.2)
% ============================================================
% Vjerni odraz `badges.rule` tekstova iz app/db/seed_data.py BADGES.
%
% VAŽNO: Eval bedževa se izvodi u Pythonu (agents/gamification_logic.py,
% Opcija A) zbog thread-safety jednog globalnog pyswip VM-a. Ovaj file se
% NE KONZULTIRA nigdje — nije na hot pathu, nema `consult('badges.pl')` u
% kodu. Postoji kao čitljiva specifikacija/dokumentacija pravila.
%
% `mastered/2` referira semantiku iz rules.pl (P_L >= 0.85). NE redefinira
% se ovdje — kad bi se ovaj file ikad konzultirao, mastered/2 dolazi iz
% rules.pl (mastery_threshold(0.85)).
% ============================================================

user_badge(UserID, first_correct) :-
    attempt(UserID, _, correct).

user_badge(UserID, join_master) :-
    forall(member(C, [inner_join, left_join, right_join]), mastered(UserID, C)).

user_badge(UserID, streak_7) :-
    current_streak(UserID, N), N >= 7.

user_badge(UserID, null_ninja) :-
    mastered(UserID, null_handling).

% NALAZ #22 (4.4-0f): kriterij više NIJE fiksnih 1..6 nego moduli koji STVARNO
% imaju aktivne zadatke — modul 6 je izvan opsega (NALAZ #19) pa bi fiksna
% šestica činila bedž nedostižnim. evaluable_module/1 = modul (≠0) s barem
% jednim aktivnim zadatkom; u Pythonu: BadgeFacts.evaluable_modules.
user_badge(UserID, explorer) :-
    forall(evaluable_module(M), attempted_in_module(UserID, M)).
