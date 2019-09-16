#!/bin/bash

prefix_ali="ali_"
folder_ali="aliases"

prefix_ent="ent_"
folder_ent="slots"

ext_chatette="chatette"

for filename in data_base/nlu_chatito_entities/*.chatito; do
	f1=${filename##*/}
	if [[ ${f1%%.*} == ${prefix_ent}* ]]; then
		f2=${f1#${prefix_ent}}
		echo python data_augmentor.py $filename data/nlu_chatette/${folder_ent}/"${f2%%.*}.${ext_chatette}"
		python data_augmentor.py $filename data/nlu_chatette/${folder_ent}/"${f2%%.*}.${ext_chatette}"
	elif [[ ${f1%%.*} == ${prefix_ali}* ]]; then
		f2=${f1#${prefix_ali}}
		echo python data_augmentor.py $filename data/nlu_chatette/${folder_ali}/"${f2%%.*}.${ext_chatette}"
		python data_augmentor.py $filename data/nlu_chatette/${folder_ali}/"${f2%%.*}.${ext_chatette}"
	fi
done
