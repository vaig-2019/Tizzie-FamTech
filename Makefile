VERSION = 0.0.1
BOTNAME = fambot

NLU_CHATITO_FOLDER = data/nlu_chatito/
NLU_CHATETTE_FOLDER = data/nlu_chatette/

NLU_DATA_FOLDER = data/
NLU_TRAINING_FILE = nlu.json
NLU_BASE_FOLDER = data_base/
NLU_BASE_FILE = base.md

TRAINTEST_FOLDER = train_test_split/
TRAINING_FILE = rasa_training.json
TESTING_FILE = rasa_testing.json

MODEL_FOLDER = models/

AUG_RATE = 30

train-all:
	python -m rasa train --fixed-model-name $(BOTNAME)_$(VERSION) --augmentation $(AUG_RATE)

run-action:
	rasa run actions --actions actions

run-server:
	#rasa run --endpoints endpoints.yml --port 5005 --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION) --credentials credential.yml
	rasa run --endpoints endpoints.yml --port 5005 --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION).tar.gz --enable-api --jwt-method HS256 --jwt-secret ${JWT_SECRET} --auth-token ${RASA_TOKEN} --cors "*" -v -vv

run-x-server:
	rasa x --endpoints endpoints.yml --port 5005 --rasa-x-port 5002 --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION) --credentials credential.yml

run-interactive:
	rasa interactive --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION)

generate-augmented:
	bash ./augment_chatitodata.sh

generate-training-data:
	rasa data convert nlu --data $(NLU_BASE_FOLDER)$(NLU_BASE_FILE) --out $(NLU_BASE_FOLDER)$(NLU_BASE_FILE).json -f json
	python -m chatette --seed ftech -f -o $(TRAINTEST_FOLDER) --adapter rasa --base-file $(NLU_BASE_FOLDER)$(NLU_BASE_FILE).json ${NLU_CHATETTE_FOLDER}master.chatette
	jq -s add $(TRAINTEST_FOLDER)train/*.json > $(NLU_DATA_FOLDER)$(NLU_TRAINING_FILE)

test-nlu:
	rasa test nlu -u ./unittest/test_nlu.md --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION) --errors ./results/errors.json

test-core:
	rasa test core --stories unittest/test_core.md --e2e --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION)

start-rasa-module:
	echo "start rasa action server"
	rasa run actions --actions actions -v -vv &
	echo "start rasa core server"
	rasa run --port 5005 --model $(MODEL_FOLDER)$(BOTNAME)_$(VERSION).tar.gz --enable-api --jwt-method HS256 --jwt-secret ${JWT_SECRET} --auth-token ${RASA_TOKEN} --cors "*" -v -vv
