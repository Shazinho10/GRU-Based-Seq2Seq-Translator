# -*- coding: utf-8 -*-
"""utils.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rW7yD44mZ6NNQuQK851gZRka0SZV952E
"""

import spacy
import random
from tqdm import tqdm
import torch
import torch.nn as nn
from torchtext.data import Field, BucketIterator
from torchtext.datasets import Multi30k
from torchtext.data.metrics import bleu_score

spacy_de = spacy.load('de_core_news_sm')
spacy_en = spacy.load('en_core_web_sm')
def process_en(text):
    return [tok.text for tok in spacy_en.tokenizer(text)]
def process_de(text):
    return [tok.text for tok in spacy_de.tokenizer(text)]

german = Field(tokenize=process_de, init_token='<sos>', eos_token='<eos>', lower=True)
english = Field(tokenize=process_en, init_token='<sos>', eos_token='<eos>', lower=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

train_data, valid_data, test_data = Multi30k.splits(exts=('.de', '.en'), fields=(german, english))

german.build_vocab(train_data, min_freq=2)
english.build_vocab(train_data, min_freq=2)

def translation(model, sentence, max_length=50):

    spacy_ger = spacy.load("de_core_news_sm")

    if type(sentence) == str:
        tokens = [token.text.lower() for token in spacy_ger(sentence)]
    else:
        tokens = [token.lower() for token in sentence]

    tokens.insert(0, german.init_token)
    tokens.append(german.eos_token)

    text_to_indices = [german.vocab.stoi[token] for token in tokens]

    sentence_tensor = torch.LongTensor(text_to_indices).unsqueeze(0).to(device)

    with torch.no_grad():
        hidden = model.encoder(sentence_tensor)

    outputs = [english.vocab.stoi["<sos>"]]

    for _ in range(max_length):
        previous_word = torch.tensor([outputs[-1]]).to(device)
        previous_word = previous_word.unsqueeze(0)

        with torch.no_grad():
            output, hidden = model.decoder(previous_word, hidden)
            best_guess = output.argmax(2).item()

        outputs.append(best_guess)

        if output.argmax(2).item() == english.vocab.stoi["<eos>"]:
            break

    translated_sentence = [english.vocab.itos[idx] for idx in outputs]

    return translated_sentence[1:]



def score(model, data):
  x = []
  for sentence in data.src:
    x.append([german.vocab.stoi[tok] for tok in sentence])
    

  y = []
  for sentence in data.trg:
    y.append(sentence)
  i = random.randint(1,700)
  input_txt = x[i]
  label_txt = y[i]


  output = translation(model, input_txt)
  if len(label_txt) < len(output):
    label_txt = label_txt + ['<pad>']*abs(len(output) - len(label_txt))

  if len(label_txt) > len(output):
    output = output + ['<pad>']*abs(len(output) - len(label_txt))
    
  return bleu_score(output, label_txt)

