import os

# data_set: https://github.com/karoldvl/ESC-50

aim_categories = [
    'Coughing',

    'Mouse click',
    'Clock alarm',
    'Glass breaking',

    'Train'

]

meta_path = '/home/mdomrachev/Data/ESC-50-master/meta/esc50.csv'
meta_info = [el.strip().split(',') for el in open(meta_path).readlines()]

data = [el for el in meta_info]