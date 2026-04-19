% Test ontologija za provjeru pyswip integracije

% Činjenice
concept(select).
concept(where).
concept(group_by).
concept(inner_join).
concept(left_join).

% Ovisnosti
prerequisite(where, select).
prerequisite(group_by, select).
prerequisite(inner_join, select).
prerequisite(left_join, inner_join).

% Pravilo: može se učiti X ako su svi prerequisites zadovoljeni
can_learn(User, Concept) :-
    concept(Concept),
    forall(prerequisite(Concept, Pre), mastered(User, Pre)).

% Dummy fakti o korisniku (kasnije dolaze iz baze)
mastered(marko, select).
mastered(marko, where).
mastered(marko, group_by).
mastered(marko, inner_join).
