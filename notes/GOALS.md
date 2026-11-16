Research project description: The project involves 
1) studying the toxicity profiles of synthetic herbicides and natural products, and identifying the differentiating properties, 
2) characterizing known binding interactions between natural products and proteins

Research methods: Python, Unix, statistical analyses, computational toxicology, Large language/protein language models

Research significance and applications: This preliminary analysis will contribute towards discovery of novel, safer bioherbicides

Deliverables: Analyzed datasets, computational workflows, end-of-semester presentation

This week: 
Ultimately this projects seeks to find natural compounds with herbicidal properties

Now the next step is to distinguish between natural non herbicidal compounds, natural herbicidal compounds, and herbicidal compounds

Track 1: 
- Start from EPA data (like ECOTOX and other data sources), identify compounds that have toxicological data, then identify which are natural products
- Split into low, medium, high LD50
- Compare that with herbicides

Track 2:
- If a compound is used as a natural herbicide what does it look like
	- From a statistical analysis perspective, so it doesn't need to be a large set
	- This should be found from literature

Also remember to use F1 score, describe weights for different features in logistic and use out of bag significance for the random forest models 