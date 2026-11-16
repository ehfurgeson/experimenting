# Preliminary dietary-candidate triage

Rule-based research screening; not a safety or plant-activity assessment.

| Triage | Count |
| --- | ---: |
| exclude_presumed_plant_negative | 2 |
| priority_review | 26 |
| evidence_gap | 0 |
| provisional_dietary_shortlist | 12 |

## Provisional shortlist

Glycerol, Glycine, L-Alanine, L-Asparagine, L-Aspartic acid, L-Glutamic acid, L-Isoleucine, L-Leucine, L-Serine, L-Threonine, L-Tyrosine, L-Valine

Lower review burden under this bounded policy, not proven benign at high doses.
All high-dose and plant-activity labels remain unknown. A missing signal is not safety.
CFR food checks use the 2025 edition; verify current text before acceptance.
GHS codes are supplier/contributor handling leads, not dietary dose-response evidence.
Text hits are unadjudicated: null findings, other exposures and historical contamination can match.
See triage.csv, curated_leads.csv, text_flags.csv and pubchem_extracts.csv for context.

## Review queue

| Candidate | Triage | Flags / gaps |
| --- | --- | --- |
| Capric acid | exclude_presumed_plant_negative | free_acid_vs_food_fat_exposure;prior_hold;registered_herbicide_active  |
| Caprylic acid | exclude_presumed_plant_negative | free_acid_vs_food_fat_exposure;ghs_systemic_hazard_lead;prior_hold;registered_herbicide_active  |
| Citric acid | priority_review | pH_and_concentration_review;text_gastrointestinal_tolerance  |
| D-Fructose | priority_review | food_reference_is_mixture;hereditary_fructose_intolerance;sugar_dose_and_anomer_review;text_specific_population specific_food_use_not_confirmed |
| D-Glucose | priority_review | sugar_dose_and_anomer_review  |
| Erythritol | priority_review | erythritol_dose_bound;polyol_dose_tolerance_review;text_gastrointestinal_tolerance  |
| L-Arginine | priority_review | arginine_population_and_dose  |
| L-Cysteine | priority_review | ghs_systemic_hazard_lead;text_organ_disease_context  |
| L-Glutamine | priority_review | text_gastrointestinal_tolerance  |
| L-Histidine | priority_review | ghs_systemic_hazard_lead  |
| L-Lysine | priority_review | text_gastrointestinal_tolerance;text_organ_disease_context  |
| L-Malic acid | priority_review | pH_and_concentration_review no_toxicity_text_extracted |
| L-Methionine | priority_review | text_methionine_homocysteine;text_organ_disease_context  |
| L-Phenylalanine | priority_review | phenylalanine_pku;text_specific_population  |
| L-Proline | priority_review | existing_selection_overlap  |
| L-Tryptophan | priority_review | text_serotonergic_interaction  |
| Lactose | priority_review | lactose_intolerance;sugar_dose_and_anomer_review no_toxicity_text_extracted;no_ghs_statement_field |
| Lauric acid | priority_review | free_acid_vs_food_fat_exposure;prior_hold  |
| Maltose | priority_review | food_reference_is_mixture;sugar_dose_and_anomer_review specific_food_use_not_confirmed |
| Mannitol | priority_review | mannitol_laxative_warning;polyol_dose_tolerance_review  |
| Myristic acid | priority_review | free_acid_vs_food_fat_exposure  |
| Oleic acid | priority_review | free_acid_vs_food_fat_exposure  |
| Palmitic acid | priority_review | free_acid_vs_food_fat_exposure;text_organ_disease_context  |
| Sorbitol | priority_review | hereditary_fructose_intolerance;polyol_dose_tolerance_review;sorbitol_laxative_warning;text_gastrointestinal_tolerance  |
| Stearic acid | priority_review | free_acid_vs_food_fat_exposure;ghs_systemic_hazard_lead  |
| Sucrose | priority_review | sugar_dose_and_anomer_review  |
| Trehalose | priority_review | sugar_dose_and_anomer_review  |
| Xylitol | priority_review | polyol_dose_tolerance_review;xylitol_dog_toxicity no_toxicity_text_extracted;hazard_retrieval_gap |
| Glycerol | provisional_dietary_shortlist |   |
| Glycine | provisional_dietary_shortlist |   |
| L-Alanine | provisional_dietary_shortlist |   |
| L-Asparagine | provisional_dietary_shortlist |   |
| L-Aspartic acid | provisional_dietary_shortlist |   |
| L-Glutamic acid | provisional_dietary_shortlist |   |
| L-Isoleucine | provisional_dietary_shortlist |   |
| L-Leucine | provisional_dietary_shortlist |   |
| L-Serine | provisional_dietary_shortlist |   |
| L-Threonine | provisional_dietary_shortlist |   |
| L-Tyrosine | provisional_dietary_shortlist |   |
| L-Valine | provisional_dietary_shortlist |   |
