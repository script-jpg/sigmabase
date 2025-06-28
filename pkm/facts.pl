note(nn_mgf, 'files/mgf.pdf').
note(nn_mgf_of_gam_a_b, 'files/nn_mgf_of_gam_a_b.pdf').
note(nn_kth_moment,'files/nn_kth_moment.pdf').
note(nn_kth_moment_of_gam_a_b, 'files/nn_kth_moment_of_gam_a_b.pdf').
note(nn_mathematical_optimization_problem, 'files/nn_mathematical_optimization_problem.pdf').
note(nn_linear_program, 'files/nn_linear_program.pdf').
note(nn_convex_optimization_problem, 'files/nn_convex_optimization_problem.pdf').

rel(nn_mgf_of_gam_a_b, nn_mgf, 'example of').
rel(nn_kth_moment_of_gam_a_b, nn_kth_moment, 'example of').
rel(nn_linear_program, nn_mathematical_optimization_problem, 'special case of').
rel(nn_convex_optimization_problem,nn_mathematical_optimization_problem, 'special case of').
rel(nn_linear_program, nn_convex_optimization_problem, 'special case of').
