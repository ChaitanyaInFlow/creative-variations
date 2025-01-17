#from ds.process.filter import FilterGenerations
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktLanguageVars
import os
import sys

import time
import requests
import json
import copy
import numpy as np
import pandas as pd
from thefuzz import fuzz
import random
import re
from collections import Counter
import nltk

from ds.process.cluster_text import ClusterText

class BulletPointLangVars(PunktLanguageVars):
    sent_end_chars = ('.', '?', '!', '•', '·', '–', ';', '|', '-')


sentence_tokenizer = PunktSentenceTokenizer(lang_vars=BulletPointLangVars())

def get_text_from_json_obj(obj, text, req_tags=['', 'title', 'description'], last_key=''):
    if '' not in req_tags:
        req_tags.append('')

    if isinstance(obj, str):
        if last_key in req_tags:
            text.append(obj)
        return text

    if isinstance(obj, list):
        for val in obj:
            text = get_text_from_json_obj(val, text, req_tags, last_key)

    if isinstance(obj, dict):
        for c in obj:
            text = get_text_from_json_obj(obj[c], text, req_tags, c)
    return text


def serp_search(search_term, country='us'):
    serp_api_url = 'https://serpapi.com/search'

    print('Reading creds for serp..')
    # params = load_parameters()
    # serp_api_key = params['serp']['key']
    serp_api_key = ''
    search_params = {'api_key': serp_api_key,
                     'engine': 'google', 'gl': 'us', 'hl': 'en', 'num': '10',
                     "hl": "en", "gl": country,
                     }
    search_params['q'] = search_term
    search_params['gl'] = country.lower()
    json_response = None


    if json_response == None:
        try:
            response = requests.get(serp_api_url, params=search_params)
            json_response = response.json()

            return json_response
        except Exception as e:
            print('Error while retrieving search info %s' % e)
            return {}
    else:
        return json_response


def get_text_from_organic_results(obj, site):
    max_n_res = 20
    out_text = []
    for i, organic_result in enumerate(obj):
        if i >= max_n_res:
            print('Taking top %d organic results!!' % max_n_res)
            return out_text

        elements_needed_with_tags = [
            'title', 'snippet', 'sitelinks']

        for element in organic_result:
            if element in elements_needed_with_tags:
                relevant_tags = ['title', 'snippet', 'description']
                out_text = list(set(get_text_from_json_obj(
                    organic_result[element], text=out_text, req_tags=relevant_tags)))
    return out_text


def remove_website(text):
    return re.sub(r'(https?:\/\/)?([\da-zA-Z\.-]+)\.([a-zA-Z\.]{2,6})([\/\w\.-]*)', '', text)


def remove_uppercase(text):
    return re.sub(r'[A-Z]{2,}', '', text)


def postprep_serp_text(texts):
    texts = list(map(remove_website, texts))
    texts = list(map(remove_uppercase, texts))
    texts = [el.strip('.?!•· –-;|\n') for el in texts]

    return texts


def is_sentence_informative(sentence, input_dict):
    ''' What do this fxn do?
    non_fluff_sentence = sentence - digits - special symbols - stop words - search query - ctas
    if num_words(non_fluff_sentence)/num_words(sentence) < thresh: reject sentence'''

    # remove digits and special symbols
    sentence = re.sub(r'[^A-Za-z \']', '', sentence)
    # new_sen = re.sub(r'[^A-Za-z \']', '', new_sen)

    # also removing 's' to change plural -> singular
    sentence = re.sub('s', '', sentence)

    new_sen = sentence.lower().strip()

    # remove ctas
    ctas = ['Act Now', 'Apply today', 'Book now', 'Buy and Save', 'Buy Now', 'Call today', 'Check our', 'Check out', 'Check this out', 'Choose your', 'Click button', 'Click for more', 'Click Here', 'Come see our prices', 'Compare prices', 'Contact us', 'Contact us today', 'Discover', "Don't forget to", "Don't miss", "Don't wait", 'Download now', 'Find Items', 'Find out more', 'Find savings', 'Find yours', 'Follow this', 'Get a quote', 'Get Free', 'Get it here', 'Get More Info Here', 'Get the Best', 'Get your', 'Hurry', 'Investigate', 'Join today', 'Join us', 'Learn more', 'Learn to', 'Look at', 'Need more', 'No obligation to try', 'Now you can', 'Order Now', 'Order Your', 'Pay Less', 'Please see', 'Please view our', 'Purchase', 'Read reviews', 'Register', 'Request yours today', 'Research',
            'Respond by', 'Rush today', 'Save Big', 'Save Money', 'Save on', 'Save Today', 'Save up to', 'Save with', 'Search for', 'Search Now', 'Search our', 'See deals', 'See more', 'See our coupon', 'See our products', 'See pricing', 'Send for', 'Shop at', 'Shop low prices', 'Shop now', 'Shop online', 'Shop today', 'Show price', 'Sign me up now', 'Sign up', 'Start now', 'Start today', 'Stock up', 'Submit', 'Take a closer look', 'Take a look at', 'Take a tour', 'Tour our', 'Try it today', 'View all Products', 'View features', 'Visit our', 'Visit us at', 'Watch for', 'You might also try', 'You might consider', 'Yours for asking', 'Buy', 'Sell', 'Try', 'Check', 'Choose', 'Click', 'Find', 'Search', 'Show', 'Shop', 'Order', 'Apply', 'Book', 'Call', 'Contact', 'View', 'Download', 'View', 'Pay', 'Save']
    for cta in ctas:
        new_sen = re.sub(f'[^a-z]{cta.lower()}[^a-z]', '', new_sen)

    # remove stop words
    stop_words = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
                  'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't", 'best', 'good', 'new', 'near']
    # stop_words = [el.replace('\'', '') for el in stop_words]
    info_words = new_sen.split()
    info_words = [el for el in info_words if el not in stop_words]

    # remove search query
    input_data = [el.lower() for el in list(input_dict.values())
                  if type(el) == type('asdf')]
    input_data = ' '.join(input_data)
    # print('sq and mc:', input_data)
    # info_words = [el for el in info_words if el not in input_data]
    info_words = [el for el in info_words if fuzz.partial_ratio(
        el, input_data) < 90]

    # print(f'sentence: {sentence}\ninfo data: {info_words}')
    info_words = [el for el in info_words if el]
    all_words = [el for el in sentence.split() if el]
    # print('info %:', len(info_words) / len(all_words))
    if len(all_words) == 0 or len(info_words) / len(all_words) < 0.4:
        return False
    else:
        return True


def find_most_frequent_words(texts):
    if type(texts) == type(['a', 'b']):
        texts = ' '.join(texts)

    texts = re.sub(r'[^A-Za-z \']', '', texts)
    most_common = Counter(texts.split()).most_common()
    # print('most_common:', most_common)

    def _cumulative_sum(lists):
        cu_list = []
        length = len(lists)
        cu_list = [sum(lists[0:x:1]) for x in range(0, length+1)]
        return cu_list[1:]

    freq = [el[1] for el in most_common]
    cum_freq = _cumulative_sum(freq)
    converg_combo = [el for el in cum_freq if el/cum_freq[-1] < 0.5]

    top_10_per = int(len(most_common)/10) + 1
    top_50_share = len(converg_combo)

    top_words_to_return = min(top_10_per, top_50_share)

    words = [el[0] for el in most_common[:top_words_to_return]]

    return words


def filter_serp_text(texts, input_dict={}):
    most_common_words = find_most_frequent_words(texts)
    input_dict['most_common_words'] = most_common_words

    final_texts = [el for el in texts if el]
    final_texts = [
        el for el in final_texts if is_sentence_informative(el, input_dict)]
    # print('rejected due to less info:')
    # print('\n'.join([el for el in texts if el not in final_texts]))
    # print('---\n')
    #filter_obj = FilterGenerations(max_length=60, threshold=80)
    final_texts = [ text for text in final_texts if len(text)<30 ]
    unique_texts, _ = ClusterText(threshold=80).get_unique_sentences(final_texts)

#   unique_texts = get_top_variations_headlines(final_texts)
    # print('rejected due to variation')
    # print('\n'.join([el for el in final_texts if el not in unique_texts]))
    # print('---')

    unique_texts = [el for el in unique_texts if len(el) > 10]

    return unique_texts


def get_text_data_from_serp(search_term, country='us'):
    res_obj = serp_search(search_term, country)
    org_text = get_text_from_organic_results(res_obj['organic_results'], '')
    sent_end_chars = '.?!•·–;|-'
    sent_toks = []
    for s in org_text:
        s = s.strip(sent_end_chars)
        t_toks = sentence_tokenizer.tokenize(s)
        sent_toks.extend(t_toks)

    sent_toks = [el for el in sent_toks if el]

    sent_toks = postprep_serp_text(sent_toks)
    unique_texts = filter_serp_text(sent_toks, {'search_term': search_term})

    rejected_heads = [el for el in sent_toks if el not in unique_texts]

    return unique_texts, rejected_heads


if __name__ == '__main__':
    print(sentence_tokenizer.tokenize('- this is the best'.strip('.?!•·–;|-')))
