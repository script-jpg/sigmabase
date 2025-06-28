% Notes
note(nn_problem, 'files/problem.pdf').
note(nn_mgf, 'files/mgf.pdf').
note(nn_pdf, 'files/pdf.pdf').
note(nn_pmf, 'files/pmf.pdf').

% Alias
alias(pmf, nn_probability_mass_function).

% Tags
tag(nn_schaums_q3_2, problem).

% Relations
rel(nn_moment_generating_function, nn_probability_mass_function, 'used_to_compute').
rel(nn_mgf, nn_pdf, 'derived_from').
rel(nn_pdf, nn_pmf, 'continuous_analog_of').
rel(nn_pmf, nn_problem, 'used_in').
rel(nn_mgf, nn_problem, 'used_to_solve').
rel(nn_pdf, nn_problem, 'used_to_solve').

% Tag attributes and note attributes
% Example:
tag_attr(problem, [source, identifier, solution_link]).

% Attribute Realization
note_attr(nn_schaums_q3_2, problem, ['schaums', 'Q3-2', 'link']).