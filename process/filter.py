import yaml
import re
import os
import random
import numpy as np
from thefuzz import fuzz
from typing import List
from nltk.stem.snowball import EnglishStemmer
from ds.process.stopwords import stop_words

import nltk
nltk.download('words')
nltk.download('averaged_perceptron_tagger')

from nltk.tag import pos_tag
from nltk.corpus import words
english_dict = words.words()

class FilterGenerations:
    def __init__(self, max_length: int=float('inf'), filter_phrase :str=str(), min_length: int=15, threshold :int = 80, similar_to_reference_threshold: int =90, filter_phrase_threshold: int=50) -> None:
        self.max_length = max_length
        self.min_length = min_length
        self.filter_ref_ad_similar_ratio = 0
        self.discarded_generations = {
            "compliance" : [],
            "length" : []
        }
        self.filter_phrase = filter_phrase 
        self.filter_phrase_threshold = filter_phrase_threshold
        self.similar_to_reference_threshold = similar_to_reference_threshold


    def run(self, generations_list: List, reference_ad: str, input_dict="", check_english = True):
        brand_id = input_dict.get('brand_id', '')
        # Filter by compliance requirements for account name
        compliance_file_path = 'ds/process/brand_specific/' + str(brand_id) + '.yaml'
        if os.path.exists(compliance_file_path):
            with open(compliance_file_path, "r") as f:
                data = yaml.safe_load(f)
            exclusions_list = data.get('exclusions')
            if exclusions_list:
                exclusions_regex = '|'.join(exclusions_list)
                compliance_generations_list = []
                for generation in generations_list:
                    if re.search(exclusions_regex, generation, re.IGNORECASE):
                        self.discarded_generations['compliance'].append(generation)
                    else:
                        compliance_generations_list.append(generation)
        else:
            compliance_generations_list = generations_list
        # generations_compliance = [ for generation in generations_list]
        # TODO: remove first_filter and seperate keys for each filter    
        len_generations_list = self._filter_by_length(compliance_generations_list)

        deduplicated_generations_list = self._remove_duplicates(len_generations_list)
        filter_phone_generations_list = self._remove_phone_numbers(deduplicated_generations_list)

        filter_domain_generations_list = self._remove_domain(filter_phone_generations_list)
        filter_pronoun_generations_list = self._remove_pronoun(filter_domain_generations_list)

        
        if (reference_ad != '') and (len(reference_ad.strip()) > 15):
            filter_similiar_generations_list = self.filter_similar_to_input(reference_ad=reference_ad, input_assets=filter_pronoun_generations_list)

        else: 
            filter_similiar_generations_list = filter_pronoun_generations_list
        
        if self.filter_phrase:
            generations_list, discard_generations = self.filter_fuzzy_partial_by_word(self.filter_phrase, filter_similiar_generations_list)
            self.discarded_generations['partial_fuzzy'] = discard_generations
        else:
            generations_list = filter_similiar_generations_list

        
        if input_dict != "" and check_english:
            english_generations, non_english_generations = self.filter_non_english_generations(generations_list, input_dict)
            generations_list = english_generations
            self.discarded_generations['non_english_generations'] = non_english_generations

        return generations_list, self.discarded_generations

        
    #TODO remove phone_numbers
    def _remove_phone_numbers(self, generations_list: List):
        filtered_list = []
        for generation in generations_list:
            x = re.findall(r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]', generation)
            if(len(x)==0):
                filtered_list.append(generation)
        return filtered_list
    #https://stackoverflow.com/questions/37393480/python-regex-to-extract-phone-numbers-from-string 

    #TODO remove domain_names
    def _remove_domain(self, generations_list: List):
        '''
         Please note this would also filter out : Fast food delivery.Now
         It will not filter out : Fast food delivery. Now
         '''
        filtered_list = []
        for generation in generations_list:
            myregex = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}'
            x = re.findall(myregex, generation)
            if(len(x)==0):
                filtered_list.append(generation)
        return filtered_list

    #TODO Filter first and third_person
    def _remove_pronoun(self, generations_list: List):
        generations_list = [el for el in generations_list if all(f' {wrd} ' not in ' '+el.lower()+' ' for wrd in ['i', 'me', 'my', 'they'])]
        return generations_list
    
    def _remove_propernoun_from_text(self, generations_list):
        tagged_assets = [pos_tag(text.split()) for text in generations_list]
        generations_list = [[word for word,tag in asset if tag != 'NNP' and tag != 'NNPS'] for asset in tagged_assets]
        generations_list = [' '.join(generation) for generation in generations_list]
        return generations_list

    def _filter_by_length(self, generations_list: List):
        filterd_generations = []
        self.discarded_generations['length'] = []
        for generation in generations_list:
            if len(generation) >= self.min_length and len(generation) <= self.max_length:
                filterd_generations.append(generation)
            else:
                self.discarded_generations['length'].append(generation)
        return filterd_generations
    
    def _remove_duplicates(self, all_sens: List):
        all_uniq_sens = []
        t_all_uniq_sens = []
        for sen in all_sens:
            t_sen = re.sub(r'\W', '', sen.lower())
            if t_sen not in t_all_uniq_sens:
                all_uniq_sens.append(sen)
                t_all_uniq_sens.append(t_sen)
        return all_uniq_sens

    def filter_brand_specific(self, generation_list: List, exclusion_list: List):    
        filtered_list = []
        for generation in generation_list:
            flag = True
            for exclusion in exclusion_list:
                if exclusion.lower().strip() in generation.lower().strip():
                    flag = False
                    # print('\nBBBBBBBBBBBBBB\n',exclusion)
                    break
            if(flag):
                filtered_list.append(generation)
        return filtered_list

    #TODO Filter generations similar to ref_ad
    def filter_similar_to_input(self, reference_ad: str, input_assets: List):
        filtered_list = []
        for input_asset in input_assets:
            if (fuzz.partial_ratio(input_asset, reference_ad) < self.similar_to_reference_threshold):
                filtered_list.append(input_asset)
        return filtered_list

    def filter_fuzzy_partial_by_word(self, input_phrase: str, asset_list: List):
        stemmer = EnglishStemmer()

        filtered_assets, discard_generations = [], []

        input_phrase_stop_word_excluded = [stemmer.stem(word) for word in input_phrase.lower().split(" ") if word not in stop_words]
        processed_input_phrase = " ".join(input_phrase_stop_word_excluded)
        for asset in asset_list:
            processed_asset = [stemmer.stem(word) for word in asset.lower().split(" ") if word not in stop_words]
            processed_asset = " ".join(processed_asset)

            threshold = fuzz.partial_ratio(processed_asset, processed_input_phrase)
            if threshold > self.filter_phrase_threshold:
                filtered_assets.append(asset)
            else:
                discard_generations.append(processed_asset)
                
        return filtered_assets, discard_generations

    def filter_non_english_generations(self, generations, input_dict):     
        all_english_generations = []
        all_non_english_generations = []

        # Creating a string from all values in the input_dict and removing special characters
        input_dict_values = ' '.join([value for value in input_dict.values() if isinstance(value, str)])
        input_dict_words = re.sub("[^A-Za-z0-9']+", ' ', input_dict_values).strip().lower().split()
        # Removing proper_nouns each sentence
        all_assets_without_propernouns = self._remove_propernoun_from_text(generations)
        
        for idx, asset in enumerate(generations):
            asset_without_propernouns = all_assets_without_propernouns[idx]
            # Removing special characters except ' from head
            asset_remove_special_chars = re.sub("[^A-Za-z0-9']+", ' ', asset_without_propernouns).strip().lower()
            # Removing all words from head present in the input_dict
            asset_words = asset_remove_special_chars.split()
            # asset_unique_words = [word for word in asset_words if (word not in input_dict_words) and (word not in stop_words)]

            # Checking if all_words from the head (after removing special chars and input_dict values) are English
            # if all(word in english_dict for word in asset_unique_words):
            #     all_english_generations.append(asset)

            eng_words = [word for word in asset_words if word in english_dict]
            non_eng_words = [word for word in asset_words if word not in english_dict]
            # non_eng_words = [word for word in non_eng_words if word not in input_dict_words + stop_words]

            try:
                if len(eng_words) / len(eng_words + non_eng_words) > 0.42:
                    all_english_generations.append(asset)
                else:
                    # import ipdb; ipdb.set_trace()
                    all_non_english_generations.append(asset)

                    # print(asset)
                    # print('en words:', eng_words)
                    # print('non-en words:', non_eng_words)
                    # print(len(eng_words) / len(asset_words))
                    # print('-')
            except ZeroDivisionError as e:
                # import ipdb; ipdb.set_trace()
                all_non_english_generations.append(asset)
                

        return all_english_generations, all_non_english_generations
    

if __name__ == '__main__':
    # test capitalisation
        test_set = [
            'submit your visit today',
            'meet our providers',
            "Board-Certified Doctor On Demand",
            "beat our providers",
            "mental health provider IN Days",
            "mental health provider Broker",
            "beat health synopsis"
    ]
        idi = {
            "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
            "refrence_plain_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
            "reference_headline": 'Manifest transformative health tech at HIMSS23.',
            "reference_description": '',
            "brand_name" : 'HEALTHCARE INFORMATION & MANAGEMENT SYSTEMS SOCIETY',
            'bu_name': 'HEALTHCARE INFORMATION & MANAGEMENT SYSTEMS SOCIETY',
            'interest_keyword': 'Mental Health',
            "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
            "n_generations" : 15
        }
        
        test_set = [
                    # "Elevate your style with Vuori's premium apparel. Designed for everyday wear, you'll never want to take them off.",
                    # "Designed for everyday wear, you'll never want to take them off.",
                    # "submit your visit today", 
                    # "mental health provider Broker",
                    # "Level up your wardrobe with Vuori's sustainable and stylish apparel. Look good while doing good for the planet.",
                    # "Experience the perfect blend of style and performance with Vuori's premium apparel. Ready for any adventure, every day.",
                    "Discover the beauty of toxin-free skincare with MamaEarth's natural and safe products.",
                    "Pamper yourself with MamaEarth's 100% toxin-free beauty essentials for a radiant glow.",
                    "Give your skin the love it deserves with MamaEarth's range of toxin-free beauty products.",
                    ]
        
        idi = {
            "bu_detail" : '''Vuori is a premium performance apparel brand inspired by the active Coastal California lifestyle. The brand offers apparel that is ethically manufactured and made with durable performance materials.''',
            "refrence_plain_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
            "reference_headline": 'Offer of a lifetime: 10% Off on charges!',
            "reference_description": 'Offer of a lifetime: 10% Off of charges!',
            "brand_name" : 'Vuori',
            'bu_name': 'Vuori',
            'interest_keyword': 'Clothing',
            "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
            "n_generations" : 15
        }

        post_process_obj = FilterGenerations(max_length=500, filter_phrase='')
        # print(post_process_obj.run(generations_list=test_set, reference_ad='',input_dict=idi, check_english = True))
        english_generations, non_english_generations = post_process_obj.filter_non_english_generations(test_set, idi)
