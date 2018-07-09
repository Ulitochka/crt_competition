
result_file = '/home/mdomrachev/PycharmProjects/competitions/speech_commands/crt_competition/result/result.csv'

data = [el.strip().split() for el in open(result_file).readlines()]


def metrics(data):
    data_no_unknown = [el for el in data if 'unknown' not in el[0]]
    print('data_no_unknown', len(data_no_unknown))
    positive_no_unknown = len([el for el in data_no_unknown if el[-1] in el[0]])
    print('acc_no_unknown',  positive_no_unknown / len(data_no_unknown) * 100)

    data_unknown = [el for el in data if 'unknown' in el[0]]
    print('data_unknown', len(data_unknown))
    positive_unknown = len([el for el in data_unknown if el[-1] in el[0]])
    print('acc_unknown',  positive_unknown / len(data_unknown) * 100)


metrics(data)

