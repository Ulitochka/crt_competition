import os
import shutil

# data_set: https://github.com/karoldvl/ESC-50

aim_categories = [
    'coughing',

    'mouse_click',
    'clock_alarm',
    'glass_breaking',

    'train'

]

meta_path = '/home/mdomrachev/Data/ESC-50-master/meta/esc50.csv'
data_path = '/home/mdomrachev/Data/ESC-50-master/audio/'
meta_info = [el.strip().split(',') for el in open(meta_path).readlines()]

categories_stat = {}
data = [el for el in meta_info if el[3] in aim_categories]
for el in data:
    categories_stat[el[3]] = categories_stat.setdefault(el[3], []) + [el[0]]
for categories in categories_stat:
    # print(categories, len(categories_stat[categories]))
    for f in categories_stat[categories]:
        old_file_name = data_path + f
        new_file_name = '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/scripts/addit_data/' + f
        shutil.copy(old_file_name, new_file_name)
        print('ffmpeg -i',
              new_file_name,
              '-acodec pcm_s16le -ac 1 -ar 16000',
              '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/scripts/addit_data/16_k_add_data/' + '16k_' + f
              )

        # ffmpeg -i 111.mp3 -acodec pcm_s16le -ac 1 -ar 16000 out.wav


