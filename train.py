# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
# Modifications Copyright 2017 Arm Inc. All Rights Reserved.           
# Added model dimensions as command line argument and changed to Adam optimizer
#
#
"""Simple speech recognition to spot a limited number of keywords.

This is a self-contained example script that will train a very basic audio
recognition model in TensorFlow. It downloads the necessary training data and
runs with reasonable defaults to train within a few hours even only using a CPU.
For more information, please see
https://www.tensorflow.org/tutorials/audio_recognition.

It is intended as an introduction to using neural networks for audio
recognition, and is not a full speech recognition system. For more advanced
speech systems, I recommend looking into Kaldi. This network uses a keyword
detection style to spot discrete words from a small vocabulary, consisting of
"yes", "no", "up", "down", "left", "right", "on", "off", "stop", and "go".

To run the training process, use:

bazel run tensorflow/examples/speech_commands:train

This will write out checkpoints to /tmp/speech_commands_train/, and will
download over 1GB of open source training data, so you'll need enough free space
and a good internet connection. The default data is a collection of thousands of
one-second .wav files, each containing one spoken word. This data set is
collected from https://aiyprojects.withgoogle.com/open_speech_recording, please
consider contributing to help improve this and other models!

As training progresses, it will print out its accuracy metrics, which should
rise above 90% by the end. Once it's complete, you can run the freeze script to
get a binary GraphDef that you can easily deploy on mobile applications.

If you want to train on your own data, you'll need to create .wavs with your
recordings, all at a consistent length, and then arrange them into subfolders
organized by label. For example, here's a possible file structure:

my_wavs >
  up >
    audio_0.wav
    audio_1.wav
  down >
    audio_2.wav
    audio_3.wav
  other>
    audio_4.wav
    audio_5.wav

You'll also need to tell the script what labels to look for, using the
`--wanted_words` argument. In this case, 'up,down' might be what you want, and
the audio in the 'other' folder would be used to train an 'unknown' category.

To pull this all together, you'd run:

bazel run tensorflow/examples/speech_commands:train -- \
--data_dir=my_wavs --wanted_words=up,down

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import numpy as np
import tensorflow as tf
import pandas as pd
from six.moves import xrange
from tensorflow.python.platform import gfile
from tensorflow.contrib import slim as slim

import input_data
import models

data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tf_data'))


background_volume = 0.1
background_frequency = 0.8
silence_percentage = 0.0
unknown_percentage = 10.0
time_shift_ms = 100.0
testing_percentage = 0
validation_percentage = 10
sample_rate = 16000
clip_duration_ms = 1000
window_size_ms = 30.0
window_stride_ms = 10.0
dct_coefficient_count = 40

how_many_training_steps = '3000,2000,2000'
eval_step_interval = 250
learning_rate = '0.0005,0.0001,0.00002'
batch_size = 256
save_step_interval = 100
model_architecture = 'crnn'


summaries_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'logs'))
wanted_words = 'background,bags,door,knocking_door,ring,speech,tool,keyboard'
train_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'models'))
start_checkpoint = ''
model_size_info = [128, 10, 4, 2, 2, 2, 76, 164]
check_nans = False


# We want to see all the logging messages for this tutorial.
tf.logging.set_verbosity(tf.logging.INFO)

# Start a new TensorFlow session.
sess = tf.InteractiveSession()

# Begin by making sure we have the training data we need. If you already have
# training data of your own, use `--data_url= ` on the command line to avoid
# downloading.
model_settings = models.prepare_model_settings(
    len(input_data.prepare_words_list(wanted_words.split(','))),
    sample_rate,
    clip_duration_ms,
    window_size_ms,
    window_stride_ms,
    dct_coefficient_count)
audio_processor = input_data.AudioProcessor(
    data_dir,
    silence_percentage,
    unknown_percentage,
    wanted_words.split(','),
    validation_percentage,
    testing_percentage,
    model_settings)
fingerprint_size = model_settings['fingerprint_size']
label_count = model_settings['label_count']
time_shift_samples = int((time_shift_ms * sample_rate) / 1000)

training_steps_list = list(map(int, how_many_training_steps.split(',')))
learning_rates_list = list(map(float, learning_rate.split(',')))
if len(training_steps_list) != len(learning_rates_list):
    raise Exception(
        '--how_many_training_steps and --learning_rate must be equal length '
        'lists, but are %d and %d long instead' % (len(training_steps_list),
                                                   len(learning_rates_list)))

fingerprint_input = tf.placeholder(tf.float32, [None, fingerprint_size], name='fingerprint_input')

logits, dropout_prob = models.create_model(
    fingerprint_input,
    model_settings,
    model_architecture,
    model_size_info,
    is_training=True)

# Define loss and optimizer
ground_truth_input = tf.placeholder(tf.float32, [None, label_count], name='groundtruth_input')

# Optionally we can add runtime checks to spot when NaNs or other symptoms of
# numerical errors start occurring during training.
control_dependencies = []
if check_nans:
    checks = tf.add_check_numerics_ops()
    control_dependencies = [checks]

# Create the back propagation and training evaluation machinery in the graph.
with tf.name_scope('cross_entropy'):
    cross_entropy_mean = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=ground_truth_input, logits=logits))
tf.summary.scalar('cross_entropy', cross_entropy_mean)

update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
with tf.name_scope('train'), tf.control_dependencies(update_ops), tf.control_dependencies(control_dependencies):
    learning_rate_input = tf.placeholder(tf.float32, [], name='learning_rate_input')
    train_op = tf.train.AdamOptimizer(learning_rate_input)
    train_step = slim.learning.create_train_op(cross_entropy_mean, train_op)

predicted_indices = tf.argmax(logits, 1)
expected_indices = tf.argmax(ground_truth_input, 1)
correct_prediction = tf.equal(predicted_indices, expected_indices)
confusion_matrix = tf.confusion_matrix(expected_indices, predicted_indices, num_classes=label_count)
evaluation_step = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
tf.summary.scalar('accuracy', evaluation_step)

global_step = tf.train.get_or_create_global_step()
increment_global_step = tf.assign(global_step, global_step + 1)

saver = tf.train.Saver(tf.global_variables())

# Merge all the summaries and write them out to /tmp/retrain_logs (by default)
merged_summaries = tf.summary.merge_all()
train_writer = tf.summary.FileWriter(summaries_dir + '/train',  sess.graph)
validation_writer = tf.summary.FileWriter(summaries_dir + '/validation')

tf.global_variables_initializer().run()

# Parameter counts
params = tf.trainable_variables()
num_params = sum(map(lambda t: np.prod(tf.shape(t.value()).eval()), params))
print('Total number of Parameters: ', num_params)

start_step = 1

if start_checkpoint:
    models.load_variables_from_checkpoint(sess, start_checkpoint)
    start_step = global_step.eval(session=sess)

tf.logging.info('Training from step: %d ', start_step)

# Save graph.pbtxt.
tf.train.write_graph(sess.graph_def, train_dir, model_architecture + '.pbtxt')

# Save list of words.
with gfile.GFile(os.path.join(train_dir, model_architecture + '_labels.txt'), 'w') as f:
    f.write('\n'.join(audio_processor.words_list))

# Training loop.
best_accuracy = 0
training_steps_max = np.sum(training_steps_list)
for training_step in xrange(start_step, training_steps_max + 1):
    # Figure out what the current learning rate is.
    training_steps_sum = 0
    for i in range(len(training_steps_list)):
        training_steps_sum += training_steps_list[i]
        if training_step <= training_steps_sum:
            learning_rate_value = learning_rates_list[i]
            break
    # Pull the audio samples we'll use for training.
    train_fingerprints, train_ground_truth = audio_processor.get_data(
        batch_size, 0, model_settings, background_frequency,
        background_volume, time_shift_samples, 'training', sess)
    # Run the graph with this batch of training data.
    train_summary, train_accuracy, cross_entropy_value, _, _ = sess.run(
        [
            merged_summaries, evaluation_step, cross_entropy_mean, train_step,
            increment_global_step
        ],
        feed_dict={
            fingerprint_input: train_fingerprints,
            ground_truth_input: train_ground_truth,
            learning_rate_input: learning_rate_value,
            dropout_prob: 0.7
        })
    train_writer.add_summary(train_summary, training_step)
    tf.logging.info('Step #%d: rate %f, accuracy %.2f%%, cross entropy %f' %
                    (training_step, learning_rate_value, train_accuracy * 100,
                     cross_entropy_value))
    is_last_step = (training_step == training_steps_max)

    if (training_step % eval_step_interval) == 0 or is_last_step:
        set_size = audio_processor.set_size('validation')
        total_accuracy = 0
        total_conf_matrix = None
        for i in xrange(0, set_size, batch_size):
            validation_fingerprints, validation_ground_truth = (
                audio_processor.get_data(batch_size, i, model_settings, 0.0,
                                         0.0, 0, 'validation', sess))

            # Run a validation step and capture training summaries for TensorBoard
            # with the `merged` op.
            validation_summary, validation_accuracy, conf_matrix = sess.run(
                [merged_summaries, evaluation_step, confusion_matrix],
                feed_dict={
                    fingerprint_input: validation_fingerprints,
                    ground_truth_input: validation_ground_truth,
                    dropout_prob: 1.0
                })
            validation_writer.add_summary(validation_summary, training_step)
            batch_size = min(batch_size, set_size - i)
            total_accuracy += (validation_accuracy * batch_size) / set_size
            if total_conf_matrix is None:
                total_conf_matrix = conf_matrix
            else:
                total_conf_matrix += conf_matrix
        tf.logging.info('Confusion Matrix:\n %s' % (total_conf_matrix))
        tf.logging.info(
            'Step %d: Validation accuracy = %.5f%% (N=%d)' % (training_step, total_accuracy * 100, set_size))

        # Save the model checkpoint when validation accuracy improves
        # if total_accuracy > best_accuracy:
        #     best_accuracy = total_accuracy
        #     checkpoint_path = os.path.join(FLAGS.train_dir, 'best', FLAGS.model_architecture + '_' + str(
        #         int(best_accuracy * 10000)) + '.ckpt')
        #     tf.logging.info('Saving best model to "%s-%d"', checkpoint_path, training_step)
        #     saver.save(sess, checkpoint_path, global_step=training_step)
        # tf.logging.info('So far the best validation accuracy is %.5f%%' % (best_accuracy * 100))

        tf.logging.info('Step %d: Validation accuracy = %.5f%% (N=%d)' %
                        (training_step, total_accuracy * 100, set_size))

    # Save the model checkpoint periodically.
    if (training_step % save_step_interval == 0 or training_step == training_steps_max):
        checkpoint_path = os.path.join(train_dir,  model_architecture + '.ckpt')
        tf.logging.info('Saving to "%s-%d"', checkpoint_path, training_step)
        saver.save(sess, checkpoint_path, global_step=training_step)

####################################################################################################################

test_batch_size = 512

test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test'))
test_files_names = sorted([test_files for test_files in os.listdir(test_path)])

test_data_index = []
for test_file in test_files_names:
    test_data_index.append({'label': '_'.join([el for el in test_file.split('.')[0].split('_')[:-1] if el != 't']),
                            "file": test_path + '/' + test_file})
audio_processor.data_index = {'testing': test_data_index}

predictions = []
prob = []

set_size = len(test_files_names)
total_accuracy = 0

for i in xrange(0, set_size, test_batch_size):

    test_fingerprints, test_ground_truth = audio_processor.get_data(
        test_batch_size, i, model_settings, 0.0, 0.0, 0, 'testing', sess)

    test_accuracy, prediction, probability = sess.run(
        [evaluation_step, predicted_indices, logits],
        feed_dict={
            fingerprint_input: test_fingerprints,
            ground_truth_input: test_ground_truth,
            dropout_prob: 1.0
        })

    predictions.append(prediction.tolist())
    prob.append(probability.tolist())

    batch_size = min(test_batch_size, set_size - i)
    total_accuracy += (test_accuracy * batch_size) / set_size
tf.logging.info('Final test accuracy = %.1f%% (N=%d)' % (total_accuracy * 100, set_size))

index2word = {audio_processor.word_to_index[word]: word for word in audio_processor.word_to_index}

predictions = [sub_el for el in predictions for sub_el in el]
prob = [sub_el[np.argmax(sub_el)] for el in prob for sub_el in el]
prediction = [index2word[el] for index, el in enumerate(predictions)]

result = pd.DataFrame()
result['fname'] = test_files_names
result['prob'] = prob
result['pred'] = prediction

result.to_csv(
    path_or_buf=os.path.abspath(os.path.join(os.path.dirname(__file__), 'result/') + 'result.csv'),
    sep=' ',
    header=False,
    index=False)





