# tigi

tigi bot 

## Generating training and testing data from chatito files
* Requirement packages
    > pip install chatette

* Augmenting chatette data before generating
Any update on chatette data requires regenerating data
    > make generate-augmented

* Generating training data  
Any update on generated chatette data requires regenerating training data
    > make generate-training-data

## Training RASA NLU and core
* Training NLU and core  
Any update on generated training data and update to domain or stories requires retraining models
    > make train-all

## Evaluating NLU model only on testing data
* Testing NLU
    > rasa test nlu -u train_test_split/test/output.json --model models/tigi_0.0.1.tar.gz

## Evaluating NLU and core models on manual test cases
* Testing NLU
    > make test-nlu

* Testing core
    > make test-core

## Rasa with Docker
* Accept agreement for nginx module
    > echo $USER $(date) > terms/agree.txt
* Change access permission of db folder to 777 if required.
    > chmod 777 db
* Create environment files by template file. Ex
    > cp .env.template .env
* Run docker-compose to start all of rasa module. It requires the training step must be passed.
    > docker-compose up -d

