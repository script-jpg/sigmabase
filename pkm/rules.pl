% Load facts
:- op(500, fx, nnopen).
:- consult(facts).

% Rule to extract field value from note attributes
note_field(Note, Tag, FieldName, FieldValue) :-
    tag_attr(Tag, AttrNames),
    note_attr(Note, Tag, AttrValues),
    same_length(AttrNames, AttrValues),  % optional schema check
    nth0(Index, AttrNames, FieldName),
    nth0(Index, AttrValues, FieldValue).

% Convenience wrapper
get_solution_link(Note, SolutionLink) :-
    note_field(Note, problem, solution_link, SolutionLink).

% Autocomplete by title prefix
autoc(Prefix, Title) :-
    note(Title, _), % match on note title
    atom(Title), atom(Prefix),
    sub_atom(Title, 0, _, _, Prefix). % check that Prefix matches start of Title

%% Usage: nnopen image.
nnopen(PartialName) :-
    autoc(PartialName, FullName),
    note(FullName, Link),
    !,
    format(string(Cmd), "open '~w'", [Link]),
    shell(Cmd).

export_rel_csv(File) :-
    open(File, write, Stream),
    write(Stream, 'Source,Target,Label\n'),
    forall(rel(Src, Dst, Label),
           format(Stream, '~w,~w,~w\n', [Src, Dst, Label])),
    close(Stream).

%% viz (visualize)
%%  Exports rel/3 facts to 'relations.csv' and runs 'python3 3dgraph.py'
viz :-
    export_rel_csv('relations.csv'),
    shell("rm layout_*"),
    shell("python3 3dgraph.py").
