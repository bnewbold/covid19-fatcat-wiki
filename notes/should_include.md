
## Queries

    pandemic influenza
    epidemic influenza
    pandemic ventilator
    SARS
    sars-cov-2
    covid-19

## Should not include?

Duplicate releases:

- zenodo versions
- figshare versions
    eg "Coronavirus Research on Figshare" (12 versions)

Remove anything researchgate? Quality is low. DOI prefix: 

"TOF-SARS" => time of flight physics thing

These should not end up in the corpus:

    "Description of a new Norwegian star-fish"
    by M. Sars
    https://fatcat.wiki/release/ngp3qkqf4fccbdlxz2u4h4taoe

## Specific Articles

Expect these to end up in the corpus (they are not already):

    "100 Years of Medical Countermeasures and Pandemic Influenza Preparedness"
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6187768/


## Hacks

    10.2210/pdb4njl/pdb
    no release_type
    => dataset
    => published

    no release_type
    title starts "figure"
    => graphic/figure, skip it

    journal: "Emerald Expert Briefings"
    container_id:fnllqvywjbec5eumrbavqipfym
    => skip it

