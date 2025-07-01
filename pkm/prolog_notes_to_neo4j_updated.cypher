// Nodes
MERGE (:Note {id:'convex_optimization_problem', path:'files/nn_convex_optimization_problem.pdf'});
MERGE (:Note {id:'dependent_type_theory', path:'files/Dependent Type Theory.pdf'});
MERGE (:Note {id:'joint_cdf', path:'files/Joint CDF.pdf'});
MERGE (:Note {id:'joint_discrete_random_variables', path:'files/Joint Discrete Random Variables.pdf'});
MERGE (:Note {id:'joint_distributions', path:'files/Joint Distributions.pdf'});
MERGE (:Note {id:'kth_moment', path:'files/nn_kth_moment.pdf'});
MERGE (:Note {id:'kth_moment_of_gam_a_b', path:'files/kth_moment_of_gam_a_b.pdf'});
MERGE (:Note {id:'linear_program', path:'files/nn_linear_program.pdf'});
MERGE (:Note {id:'mathematical_optimization_problem', path:'files/nn_mathematical_optimization_problem.pdf'});
MERGE (:Note {id:'mgf', path:'files/mgf.pdf'});
MERGE (:Note {id:'mgf_of_gam_a_b', path:'files/nn_mgf_of_gam_a_b.pdf'});
MERGE (:Note {id:'mgf_of_linear_transform_of_n_0_1', path:'files/Mgf of linear transform of N(0,1).pdf'});
MERGE (:Note {id:'mgf_of_n_0_1', path:'files/MGF of N (0,1).pdf'});
MERGE (:Note {id:'mgf_of_normal', path:'files/MGF of Normal.pdf'});
MERGE (:Note {id:'mgf_of_poisson', path:'files/mgf of poisson.pdf'});
MERGE (:Note {id:'mgf_vs_distribution_uniqueness_of_mgf', path:'files/MGF vs Distribution (uniqueness of mgf).pdf'});
MERGE (:Note {id:'moments_of_gam', path:'files/Moments of Gam.pdf'});
MERGE (:Note {id:'moments_of_poisson', path:'files/moments of Poisson.pdf'});
MERGE (:Note {id:'nn_1_1_1_example', path:'files/nn_1_1_1_example_mechanics_of_proof.pdf'});
MERGE (:Note {id:'nn_1_1_1_example_mechanics_of_proof', path:'files/nn_1_1_1_example_mechanics_of_proof.pdf'});
MERGE (:Note {id:'nn_1_1_3_example', path:'files/1.1.3-Example.pdf'});
MERGE (:Note {id:'nn_1_1_4_example', path:'files/1.1.4-Example.pdf'});
MERGE (:Note {id:'nn_ppp', path:'files/nn_ppp.pdf'});
MERGE (:Note {id:'ppp', path:'files/nn_ppp.pdf'});
MERGE (:Note {id:'prepositions_and_proofs', path:'files/Prepositions and Proofs.pdf'});
MERGE (:Note {id:'properties_of_mgf', path:'files/properties of mgf.pdf'});
MERGE (:Note {id:'stat330_lec4_mgf_and_their_applications', path:'files/stat330_lec4 MGF and Their Applications.pdf'});
MERGE (:Note {id:'uncertainty_quantification', path:'files/Uncertainty Quantification.md'});
MERGE (:Note {id:'uniqueness_of_mgf', path:'files/MGF vs Distribution (uniqueness of mgf).pdf'});

// Relationships
MATCH (a:Note {id:'convex_optimization_problem'}), (b:Note {id:'mathematical_optimization_problem'})
MERGE (a)-[:SPECIAL_CASE_OF]->(b);
MATCH (a:Note {id:'kth_moment_of_gam_a_b'}), (b:Note {id:'kth_moment'})
MERGE (a)-[:EXAMPLE_OF]->(b);
MATCH (a:Note {id:'linear_program'}), (b:Note {id:'convex_optimization_problem'})
MERGE (a)-[:SPECIAL_CASE_OF]->(b);
MATCH (a:Note {id:'linear_program'}), (b:Note {id:'mathematical_optimization_problem'})
MERGE (a)-[:SPECIAL_CASE_OF]->(b);
MATCH (a:Note {id:'mgf_of_gam_a_b'}), (b:Note {id:'mgf'})
MERGE (a)-[:EXAMPLE_OF]->(b);
MATCH (a:Note {id:'mgf_of_gam_a_b'}), (b:Note {id:'moments_of_gam'})
MERGE (a)-[:GENERALIZATION_OF]->(b);
MATCH (a:Note {id:'mgf_of_n_0_1'}), (b:Note {id:'mgf'})
MERGE (a)-[:EXAMPLE_OF]->(b);
MATCH (a:Note {id:'mgf_of_normal'}), (b:Note {id:'mgf'})
MERGE (a)-[:EXAMPLE_OF]->(b);
MATCH (a:Note {id:'mgf_of_normal'}), (b:Note {id:'mgf_of_n_0_1'})
MERGE (a)-[:GENERALIZATION_OF]->(b);
MATCH (a:Note {id:'mgf_of_normal'}), (b:Note {id:'properties_of_mgf'})
MERGE (a)-[:APPLIES]->(b);
MATCH (a:Note {id:'mgf_of_poisson'}), (b:Note {id:'mgf'})
MERGE (a)-[:EXAMPLE_OF]->(b);
MATCH (a:Note {id:'moments_of_gam'}), (b:Note {id:'kth_moment'})
MERGE (a)-[:CALCULATES_SPECIFIC_VALUE_OF]->(b);
MATCH (a:Note {id:'moments_of_gam'}), (b:Note {id:'properties_of_mgf'})
MERGE (a)-[:APPLIES]->(b);
MATCH (a:Note {id:'moments_of_poisson'}), (b:Note {id:'kth_moment'})
MERGE (a)-[:CALCULATES_SPECIFIC_VALUE_OF]->(b);
MATCH (a:Note {id:'properties_of_mgf'}), (b:Note {id:'kth_moment'})
MERGE (a)-[:WAY_TO_CALCULATE]->(b);
MATCH (a:Note {id:'properties_of_mgf'}), (b:Note {id:'mgf'})
MERGE (a)-[:RELATED_TO]->(b);
MATCH (a:Note {id:'uniqueness_of_mgf'}), (b:Note {id:'mgf'})
MERGE (a)-[:RELATED_TO]->(b);