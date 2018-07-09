import os
import shutil

aim_categories = [
    'coughing',

    'clock_alarm',
    'glass_breaking',

    'pouring_water',
    'toilet_flush',

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

#         print('ffmpeg -i',
#               new_file_name,
#               '-acodec pcm_s16le -ac 1 -ar 16000',
#               '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/scripts/addit_data/16_k_add_data/' + '16k_' + f
#               )
#
#         # ffmpeg -i 111.mp3 -acodec pcm_s16le -ac 1 -ar 16000 out.wav


freiburg_data_path = '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/scripts/addit_data/Freiburg_106/'
for catalogs in os.listdir(freiburg_data_path):
    for f in os.listdir(freiburg_data_path + catalogs):
        print('ffmpeg -i',
              freiburg_data_path + catalogs + '/' + f,
              '-acodec pcm_s16le -ac 1 -ar 16000',
              '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/scripts/addit_data/16_k_add_data/' + '16k_%s_' % (catalogs,) + f)








