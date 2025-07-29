# Franchise Matching Platform - TODO

## Main Functions (./src/data/functions/)

### RAW_DATA_DIR

- [x] Create a function that compares the content of two html files, and return a boolean if there are changes
- [x] Create a function that browses the content of the html files between two dates, and apply the previous function. It then return a list with the names of the files chat changed.

### INTERIM_DATA_DIR

- [ ] Create a function to save the keywords into a .csv in the interim dir
- [ ] Create a function to save the embeddings into a .csv in the interim dir
- [ ] Create a function to combine the structured json outputs into a .csv saved in the interim dir

Note1: _Adapt the functions to handle the different format of outputs in the raw folder, notably for the bulk processing_
Note2: _Save by date_

### PROCESSED_DATA_DIR

- [ ] Create a funciton to combine the above .csv into a final folder in the processed dir
