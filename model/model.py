#!/usr/bin/python3

import numpy as np
from settings import hparams
from keras.preprocessing import text, sequence
from keras.models import Sequential , Model
from keras.layers import Embedding, Input, LSTM, Bidirectional, TimeDistributed, Flatten, dot
from keras.layers import Activation, RepeatVector, Permute, Merge, Dense ,Reshape, Lambda
from keras.layers import Concatenate, Add, Multiply
from keras.models import load_model
from keras import optimizers
from keras.utils import to_categorical
from random import randint
from keras import backend as K
import tensorflow as tf
#from keras.engine.topology import merge
import gensim.models.word2vec as w2v
import os
import tensorflow as tf
#print(hparams)

words = hparams['num_vocab_total']
text_fr = hparams['data_dir'] + hparams['test_name'] + '.' + hparams['src_ending']
text_to = hparams['data_dir'] + hparams['test_name'] + '.' + hparams['tgt_ending']

train_fr = hparams['data_dir'] + hparams['train_name'] + '.' + hparams['src_ending']
train_to = hparams['data_dir'] + hparams['train_name'] + '.' + hparams['tgt_ending']

vocab_fr = hparams['data_dir'] + hparams['vocab_name'] + '.' + hparams['src_ending']
vocab_to = hparams['data_dir'] + hparams['vocab_name'] + '.' + hparams['tgt_ending']
oov_token = hparams['unk']
batch_size = hparams['batch_size']
units = hparams['units']
tokens_per_sentence = hparams['tokens_per_sentence']
raw_embedding_filename = hparams['raw_embedding_filename']

base_file_num = str(hparams['base_file_num'])
batch_constant = int(hparams['batch_constant'])
filename = None
model = None

if True:
    print ("stage: load w2v model")
    word2vec_book = w2v.Word2Vec.load(os.path.join(hparams['save_dir'], raw_embedding_filename + "_1.w2v"))
    words = len(word2vec_book.wv.vocab)
    vocab_size = words



def open_sentences(filename):
    t_yyy = []
    with open(filename, 'r') as r:
        for xx in r:
            t_yyy.append(xx)
    #r.close()
    return t_yyy

def vector_input_one(filename, length, start=0,batch=-1, shift_output=False):
    tokens = units
    text_x1 = open_sentences(filename)
    out_x1 = np.zeros((units, length * tokens))
    if batch == -1: batch = length
    #print(filename)
    #if start is not 0: start -= 1
    for ii in range( length ):

        i = text_x1[start + ii].split()
        words = len(i)
        if words >= tokens: words = tokens - 1
        for index_i in range(words ):
            if index_i < len(i) and i[index_i] in word2vec_book.wv.vocab:
                vec = word2vec_book.wv[i[index_i]]
                # print(vec.shape,'vocab', i[index_i])
            else:
                vec = np.zeros((units))
            try:
                out_x1[:, index_i + (ii * tokens)  ] = vec[:units]
            except:
                print(out_x1.shape, index_i, tokens, ii, words, start, length)
                #exit()
    if shift_output:
        #print('stage: start shift y')
        out_y_shift = np.zeros((units, length * tokens))
        out_y_shift[:, : length * tokens - 1] = out_x1[:, 1:]
        out_x1 = out_y_shift

    #### test ####
    #print(out_x1.shape,  'sentences')

    return out_x1


def embedding_model_lstm():


    x_shape = (None,units)
    lstm_unit =  units

    valid_word_a = Input(shape=x_shape)
    valid_word_b = Input(shape=x_shape)


    ### encoder for training ###
    lstm_a = LSTM(units=lstm_unit, input_shape=(None,lstm_unit),return_sequences=True,
                  return_state=True)

    recurrent_a, lstm_a_h, lstm_a_c = lstm_a(valid_word_a)

    lstm_a_states = [lstm_a_h , lstm_a_c]

    ### decoder for training ###

    lstm_b = LSTM(units=lstm_unit ,return_sequences=True,
                  return_state=True
                  )


    recurrent_b, inner_lstmb_h, inner_lstmb_c = lstm_b(valid_word_b, initial_state=lstm_a_states)


    dense_b = Dense(lstm_unit, activation='softmax', name='dense_layer_b',
                                    batch_input_shape=(None,lstm_unit,units))


    decoder_b = dense_b(recurrent_b) # recurrent_b

    #reshape_b = Permute((2,1))(decoder_b)


    model = Model([valid_word_a,valid_word_b], decoder_b) # decoder_b

    ### encoder for inference ###
    model_encoder = Model(valid_word_a, lstm_a_states)

    ### decoder for inference ###

    input_h = Input(shape=(None,lstm_unit))
    input_c = Input(shape=(None,lstm_unit))

    inputs_inference = [input_h, input_c]

    outputs_inference, outputs_inference_h, outputs_inference_c = lstm_b(valid_word_b,
                                                                         initial_state=inputs_inference)

    outputs_states = [outputs_inference_h, outputs_inference_c]


    dense_outputs_inference = dense_b(outputs_inference)

    model_inference = Model([valid_word_b] + inputs_inference,
                            [dense_outputs_inference] + outputs_states)

    ### boilerplate ###

    adam = optimizers.Adam(lr=0.001)

    model.compile(optimizer=adam, loss='categorical_crossentropy')

    return model, model_encoder, model_inference



def predict_word(txt):
    model, infer_enc, infer_dec = embedding_model_lstm()
    switch = False
    vec = []
    t = txt.lower().split()
    steps = 1
    #decode = False
    for i in range(0,len(t) * 3):
        if switch or t[i] in word2vec_book.wv.vocab:
            if not switch:
                print(t[i])
                steps = 1
                #decode = True
            if len(vec) == 0:
                vec = word2vec_book.wv[t[i]]
                vec = vec[:units]
                vec = np.expand_dims(vec, 0)
                vec = np.expand_dims(vec, 0)
                #print(vec[:,:,0:10])
            predict = predict_sequence(infer_enc, infer_dec, vec, steps)

            if switch or t[i] == hparams['eol']:
                predict = np.expand_dims(predict,0)
                predict = np.expand_dims(predict,0)
                vec = predict

                #print(vec.shape)
                switch = True
                #decode = False
                steps = 1
            elif not switch:
                pass
                vec = []


def predict_sequence(infer_enc, infer_dec, source, n_steps,decode=False ,simple_reply=True):
    # encode
    #print(source.shape,'s')
    if len(source.shape) > 3: source = source[0]
    state = infer_enc.predict(source)
    # start of sequence input

    yhat = np.zeros((1,1,units))
    target_seq = state[0] # np.zeros((1,1,units))
    # collect predictions
    output = list()
    if not decode or True:
        for t in range(n_steps):
            # predict next char
            target_values = [target_seq] + state
            #print(target_values)
            target_values = _set_t_values(target_values)
            yhat, h, c = infer_dec.predict(target_values)
            # store prediction
            output.append(yhat[0,:])
            # update state
            state = [h, c]
            # update target sequence
            target_seq = h #yhat
            #print(word2vec_book.wv.most_similar(positive=[yhat[0,0,:]], topn=1)[0][0])
            print(word2vec_book.wv.most_similar(positive=[h[0,0,:]], topn=1)[0],'< h')
    if not simple_reply: return np.array(output)
    else: return yhat[0,:]


def _set_t_values(l):
    out = list([])
    for i in l:
        if len(i.shape) < 3:
            i = np.expand_dims(i, 0)
        #print(i.shape)
        out.append(i)
    return out


def model_infer(filename):
    print('stage: try predict')
    c = open_sentences(filename)
    line = c[0]
    print(line)
    predict_word(line)
    print('----------------')
    predict_word('sol what is up ? eol')


def check_sentence(x2,y, start = 0):
    for j in range(start, start + 4):
        print("x >",j,end=' ')
        for i in range(5):
            vec_x = x2[j,i,:]
            print(word2vec_book.wv.most_similar(positive=[vec_x])[0][0],end=' ')
        print()
        print("y >",j, end=' ')
        for i in range(5):
            vec_y = y[j,i,:]
            print(word2vec_book.wv.most_similar(positive=[vec_y])[0][0],end=' ')
        print()


def stack_sentences(xx):
    batch = units # tokens_per_sentence
    tot = xx.shape[1] // batch
    out = np.zeros((tot,batch,units)) # [] #
    #print(tot,'tot', xx.shape)
    for i in range(tot):
        start = i * batch
        end = (i + 1) * batch
        x = xx[:,start:end]
        #x = xx[:,i]
        #out.append(x)
        out[i,:,:] = x

    #out = np.array(out)
    #print(out.shape, 'swap')
    out = np.swapaxes(out,1,2)
    #out = np.expand_dims(out, 0)
    return out


def train_model(model, check_sentences=False):
    print ('stage: arrays prep for test/train')
    if model is None: model , _, _ = embedding_model_lstm()
    model.summary()
    tot = len(open_sentences(train_fr))
    length = tot // int(units ) * batch_constant
    steps = tot // length

    for z in range(steps):
        try:
            s = (length )* z
            print(s,s + length,'start, stop')
            x1 = vector_input_one(train_to,length,s) ## change this to 'train_fr' when not autoencoding
            x2 = vector_input_one(train_to,length,s)
            y =  vector_input_one(train_to,length,s,shift_output=True)

            x1 = stack_sentences(x1)
            x2 = stack_sentences(x2)
            y =  stack_sentences(y)
            if check_sentences: check_sentence(x2,y,0)
            model.fit([x1,x2], y, batch_size=16)
        except:
            save_model(filename + ".backup")
            pass
        finally:

            pass
        #model.train_on_batch([x1, x2], y)
    return model

def save_model(model, filename):
    print ('stage: save lstm model')
    if filename == None:
        filename = hparams['save_dir'] + hparams['base_filename']+'-'+base_file_num +'.h5'
    model.save(filename)


def load_model_file(filename):
    print('stage: checking for load')
    if filename == None:
        filename = hparams['save_dir'] + hparams['base_filename']+'-'+base_file_num +'.h5'
    if os.path.isfile(filename):
        model = load_model(filename)
        print ('stage: load works')
    else:
        print('stage: load failed')
    return model


if False:
    model, _, _ = embedding_model_lstm()

if True:
    model = load_model_file(filename)


if True:
    train_model(model, check_sentences=False)

if True:
    save_model(model,filename)


if True:
    model_infer(train_to)


if True:
    print ('\n',len(word2vec_book.wv.vocab))

    vec = word2vec_book.wv['sol']
    print ( word2vec_book.wv.most_similar(positive=[vec], topn=5))
    #print ( word2vec_book.wv.most_similar(positive=["she's"], topn=5))
    print ('k', word2vec_book.wv.most_similar(positive=['k'], topn=5))

