#!/usr/bin/env bash
set -e
python3 train.py --model_architecture crnn --model_size_info 128 10 4 2 2 2 76 164 --learning_rate 0.0005,0.0001,0.00002 --how_many_training_steps 500,500,500