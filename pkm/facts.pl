:- discontiguous note/2.
:- discontiguous rel/3.

note(convex_optimization_problem, 'files/nn_convex_optimization_problem.pdf').
note(dependent_type_theory, 'files/Dependent Type Theory.pdf').
note(joint_cdf, 'files/Joint CDF.pdf').
note(joint_discrete_random_variables, 'files/Joint Discrete Random Variables.pdf').
note(joint_distributions, 'files/Joint Distributions.pdf').
note(kth_moment, 'files/nn_kth_moment.pdf').
note(kth_moment_of_gam_a_b, 'files/kth_moment_of_gam_a_b.pdf').
note(linear_program, 'files/nn_linear_program.pdf').
note(mathematical_optimization_problem, 'files/nn_mathematical_optimization_problem.pdf').
note(mgf, 'files/mgf.pdf').
note(mgf_of_gam_a_b, 'files/nn_mgf_of_gam_a_b.pdf').
note(mgf_of_linear_transform_of_n_0_1, 'files/Mgf of linear transform of N(0,1).pdf').
note(mgf_of_n_0_1, 'files/MGF of N (0,1).pdf').
note(mgf_of_normal, 'files/MGF of Normal.pdf').
note(mgf_of_poisson, 'files/mgf of poisson.pdf').
note(mgf_vs_distribution_uniqueness_of_mgf, 'files/MGF vs Distribution (uniqueness of mgf).pdf').
note(moments_of_gam, 'files/Moments of Gam.pdf').
note(moments_of_poisson, 'files/moments of Poisson.pdf').
note(nn_1_1_1_example, 'files/nn_1_1_1_example_mechanics_of_proof.pdf').
note(nn_1_1_1_example_mechanics_of_proof, 'files/nn_1_1_1_example_mechanics_of_proof.pdf').
note(nn_1_1_3_example, 'files/1.1.3-Example.pdf').
note(nn_1_1_4_example, 'files/1.1.4-Example.pdf').
note(prepositions_and_proofs, 'files/Prepositions and Proofs.pdf').
note(properties_of_mgf, 'files/properties of mgf.pdf').
note(stat330_lec4_mgf_and_their_applications, 'files/stat330_lec4 MGF and Their Applications.pdf').
note(uncertainty_quantification, 'files/Uncertainty Quantification.md').
note(uniqueness_of_mgf, 'files/MGF vs Distribution (uniqueness of mgf).pdf').

rel(convex_optimization_problem, mathematical_optimization_problem, 'special case of').
rel(kth_moment_of_gam_a_b, kth_moment, 'example of').
rel(linear_program, convex_optimization_problem, 'special case of').
rel(linear_program, mathematical_optimization_problem, 'special case of').
rel(mgf_of_gam_a_b, mgf, 'example of').
rel(mgf_of_gam_a_b, moments_of_gam, 'generalization of').
rel(mgf_of_linear_transform_of_n_0_1, mgf, 'example of').
rel(mgf_of_n_0_1, mgf, 'example of').
rel(mgf_of_normal, mgf, 'example of').
rel(mgf_of_normal, mgf_of_n_0_1, 'generalization of').
rel(mgf_of_normal, properties_of_mgf, 'applies').
rel(mgf_of_poisson, mgf, 'example of').
rel(moments_of_gam, kth_moment, 'calculates specific value of').
rel(moments_of_gam, properties_of_mgf, 'applies').
rel(moments_of_poisson, kth_moment, 'calculates specific value of').
rel(prepositions_and_proofs, dependent_type_theory, 'related to').
rel(properties_of_mgf, kth_moment, 'way to calculate').
rel(properties_of_mgf, mgf, 'related to').
rel(uniqueness_of_mgf, mgf, 'related to').
