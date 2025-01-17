
import requests
import json
import time 
import pickle
import re
import textstat
import pointofview
import multiprocessing
import numpy as np
import pandas as pd
import tensorflow as tf
from typing import List, Dict
from thefuzz import fuzz
from ds.process.stopwords import stop_words
from nltk.stem.snowball import EnglishStemmer

from ds.scripts.brand_api import brand_api_industry
from ds.scripts.detect_gibberish import classify as gibberish_classifier
from ds.process.filter import FilterGenerations

class ScorePerformance:
    '''
    This Class Labels the performance of text

    Argument:
        brand_name (str): Brand name of the given input assets
    '''
    def __init__(self, brand_name : str):
        '''
        Constrcutor for the class

        Parameters:
            brand_name (str): Brand name of the given input assets
        '''
        self.brand_name = brand_name

    #### Performance Parameters ####
    def get_normalised_fsescores(self, generations_list: List):
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            normalized_fsescores (List[str]): normalised readability scores
        '''
        normalized_fsescores = []
        for generation in generations_list:
            score = textstat.flesch_reading_ease(generation)
            if score <= 0:
                normalised_score = 0
            else:
                normalised_score = round((score / 121.22) * 100)
            normalized_fsescores.append(normalised_score)
        return normalized_fsescores

    def get_customer_centric_labels(self, generations_list: List):
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            customer_centric_labels (List[str]): Customer centricity of the input sentences
        '''
        customer_centric_labels = []
        for gen in generations_list:
            if pointofview.get_text_pov(gen) == 'second':
                customer_centric_labels.append(1)
            else:
                customer_centric_labels.append(0)
        return customer_centric_labels

    
    def get_brand_centric_labels(self, generations_list: List):
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            brand_centric_labels (List[str]): Brand centricity of the input sentences
        '''
        brand_centric_gens, rej_gens = FilterGenerations().filter_fuzzy_partial_by_word(input_phrase=self.brand_name, asset_list=generations_list)
        brand_centric_labels = []
        for gen in generations_list:
            if gen in brand_centric_gens:
                brand_centric_labels.append(1)
            else:
                brand_centric_labels.append(0)
        return brand_centric_labels


    def get_benefit_results(self, generations_list: List):
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            benefit_labels (List[str]): Benifit labels for the input sentences
        '''
        generation_flag_list = [1 if len(generation) > 8 else 0 for generation in generations_list]
        generations_list = [[generation] for generation in generations_list if len(generation) > 8]
        request_count = 10
        while(request_count):
            try:
                headers = {} 
                HOST = ""
                prediction = requests.post(
                    json={"instances": generations_list },
                    url=f"{HOST}/v1/models/benefit-bert:predict",
                    headers=headers)
                    
                if (prediction.status_code == 200):
                    break
            except:
                pass
            request_count = request_count - 1
            time.sleep(1)
        try: 
            benefit_probabilities = [tf.sigmoid(pred[0]).numpy().item() for pred in json.loads(prediction.text)['predictions']]
        except Exception as e:
            print("benefit model failed", str(e)) 
            benefit_probabilities = [0] * len(generations_list)
        benefit_probabilities = [benefit_probabilities.pop(0) if generation_flag else 0 for generation_flag in generation_flag_list]
        benefit_labels = [1 if p>=0.5 else 0 for p in benefit_probabilities]
        return benefit_labels


    def get_offer_results(self, generations_list: List):
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            offer_labels (List[str]): Offer labels for the input sentences
        '''
        offer_labels = []
        for generation in generations_list:
            if not isinstance(generation, str):
                offer_labels.append(0)
            # What about low cost emi? buy one get one, coupon, deal
            offer_words = 'off offer offers free sale % discount discounts discounted'.split() 
            if any(re.findall(f'\s({wrd})\s', generation.lower()) for wrd in offer_words):
                offer_labels.append(1)
            else:
                offer_labels.append(0)
        return offer_labels

    def get_performance_feature_df(self, generations_list: List[str]) -> pd.DataFrame:
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            Pandas DataFrame with features and predictions from the model
        '''
        test_df = pd.DataFrame(columns=[
            'flesch_reading_ease', 
            'customer_centric', 
            'brand_centric',
            'offer_probabilities_AM', 
            'benefit_probabilities_AM', 
            'India', 
            'Europe',
            'Rest of Asia', 
            'North America',
            'Apparel',
            'Automotive',
            'Education',
            'Finance',
            'Food and Grocery',
            'Healthcare',
            'IT',
            'Lifestyle',
            'Media',
            'Others'
            ])

        test_df['flesch_reading_ease'] = self.get_normalised_fsescores(generations_list) 
        test_df['customer_centric'] = self.get_customer_centric_labels(generations_list) 
        test_df['brand_centric'] = self.get_brand_centric_labels(generations_list)
        test_df['offer_probabilities_AM'] = self.get_offer_results(generations_list)
        test_df['benefit_probabilities_AM'] = self.get_benefit_results(generations_list)

        test_df['India'] = [0]*len(test_df)
        test_df['Europe'] = [0]*len(test_df)
        test_df['Rest of Asia'] = [0]*len(test_df)
        test_df['North America'] = [0]*len(test_df)

        industry = brand_api_industry(self.brand_name)
        test_df['industry'] = [industry]*len(test_df)
        test_df.reset_index(drop=True, inplace=True)
        test_df.iloc[:,9:19] = 0
        test_df.reset_index(drop=True, inplace=True)
        for ind,val in enumerate(test_df['industry']):
            if (val!=''):
                indus = test_df.loc[ind,'industry']
                test_df.loc[ind,indus] = 1
        test_df.drop('industry', axis=1, inplace=True)

        model_path = "ds/performance/v1_asset_ws.sav"
        loaded_model = pickle.load(open(model_path, 'rb'))
        performance_probabilities = loaded_model.predict_proba(test_df)[:, 1]
        

        test_df['performance_probabilities'] = performance_probabilities
        test_df['text'] = generations_list

        # Adding Logics for Edge Cases 1. Readability, Length, Gibberish

        test_df.loc[test_df['flesch_reading_ease'] < 20, 'performance_probabilities'] = 0
        test_df.loc[test_df['text'].apply(len) < 8, 'performance_probabilities'] = 0
        test_df.loc[test_df['text'].apply(len) < 2, 'flesch_reading_ease'] = 0
        test_df.loc[test_df['text'].apply(gibberish_classifier) > 60, 'performance_probabilities'] = 0
        test_df.loc[test_df['text'].apply(gibberish_classifier) > 60, 'benefit_probabilities_AM'] = 0
        test_df.loc[test_df['text'].apply(gibberish_classifier) > 60, 'flesch_reading_ease'] = 0

        test_df['gibberish'] = test_df['text'].apply(lambda x: gibberish_classifier(x))

        # Normalizing performance probability between 0-10
        test_df['performance_score'] = test_df['performance_probabilities'].apply(lambda probability:round(probability * 10, 1) )
       
        test_df = test_df.rename(columns={
            'flesch_reading_ease': 'readability_score', 
            'offer_probabilities_AM': 'offer_label',
            'benefit_probabilities_AM': 'benefit_label',
            })
        # print(test_df.to_dict())
        # print(test_df)
        return test_df

    def __format_features(self, perf_scores_df: pd.DataFrame):
        '''
        Helper function to change the format of the features to Boolean
        and label performance labels
        '''
        performance_probabilities = perf_scores_df['performance_probabilities']
        performance_labels = []
        for probability in performance_probabilities:
            if probability >= 0.5847:
                performance_labels.append('High Performance')
            elif probability >= 0.3935 and probability < 0.5847:
                performance_labels.append('Medium Performance')
            else:
                performance_labels.append('Low Performance')
        perf_scores_df['performance_labels'] = performance_labels
        perf_scores_df['performance_score'] = perf_scores_df['performance_score'].apply(lambda x: round(x,1))
        perf_scores_df['customer_centric'] = perf_scores_df['customer_centric'].apply(lambda x: True if x > .5 else False)
        perf_scores_df['brand_centric'] = perf_scores_df['brand_centric'].apply(lambda x: True if x > .5 else False)
        perf_scores_df['benefit_label'] = perf_scores_df['benefit_label'].apply(lambda x: True if x > .5 else False)
        perf_scores_df['offer_label'] = perf_scores_df['offer_label'].apply(lambda x: True if x > .5 else False)

        return perf_scores_df

    def get_performance_scores(self, generations_list: List[str]) -> List[Dict]:
        '''
        Parameters:
            generations_list (List[str]): List of input sentences
        Returns:
            List[Dict]: key, value pairs perforamance labels and its score for the given text
                [
                    {
                        "text" : Sent1,
                        "readability_score" : int,
                        ...
                    },
                    {
                        "text" : Sent2,
                        "readability_score" : int,
                        ...
                    }
                ]
        ''' 
        if(len(generations_list)>0):
            perf_scores_df = self.get_performance_feature_df(generations_list=generations_list)
            perf_scores_df = self.__format_features(perf_scores_df)
        else:
            print("EMPTY")
            perf_scores_df = pd.DataFrame(columns=['text','readability_score', 'customer_centric', 'brand_centric', 'benefit_label','offer_label','performance_score','performance_probabilities','performance_labels'])

        return perf_scores_df[['text','readability_score', 'customer_centric', 'brand_centric', 'benefit_label','offer_label','performance_score','performance_probabilities','performance_labels']].to_dict("records")
        
    def get_perforamnce_bundle_score(self, bundle_dict: Dict) -> Dict:
        '''
        This function is for scoring performance at bundle level
        It should have atleast of the asset types headline, description or primary text
        It shall return the mean of the asset level performance 
        Parameters:
            bundle_dict (Dict) : keys shall have 'headline', 'description' or 'primary_text'
        Returns:
            (Dict) dictionary of bundle dict along with each of performance features
            'readability_score' : int (normalised readability score range 0 -100), 
            'customer_centric' : boolean, 
            'brand_centric': boolean, 
            'benefit_label': boolean,
            'offer_label' : boolean,
            'performance_score' : float (0-10)
            'performance_labels: 'High Performance', 'Medium Performance','Low Performance',   
        '''
        input_list = []
        for asset_type in ['headline', 'description', 'primary_text']:
            if bundle_dict.get(asset_type, ""):
                input_list.append(bundle_dict.get(asset_type, ""))
        
        if(len(input_list) > 0):
            perf_scores_df = self.get_performance_feature_df(generations_list=input_list)
            perf_scores_df = perf_scores_df[['readability_score', 'customer_centric', 'brand_centric', 'benefit_label','offer_label','performance_score','performance_probabilities']].mean().to_frame().T
            perf_scores_df = self.__format_features(perf_scores_df)
        else:
            perf_scores_df = pd.DataFrame()

        if len(perf_scores_df):
            return perf_scores_df.to_dict("records")[0]
        else:
            return {}



if __name__ == "__main__":

    # sample_gens = ["Alert: Back in Stock! We heard you missed us so we restocked our most-wanted pieces for you. Grab 'em while stock lasts. Hurry!",
    #                 "Spring's here! Look eyeconic in trendy textures and revamped classics from our #JJSafari edit. Shop the limited edition now!",
    #                 'Hit the re-style button! Add glamour into your wardrobe with our striking and structured steelworks. Shop now!',
    #                 'Our biggest hits, now available at wow prices! Strike a pose in chic eyewear and update your look for an unforgettable summer.',
    #                 'Life imitates art with our CreatorShop curation! Shop eyewear outfitted with printed details and intricate design elements.',
    #                 'Strike a pose in the coolest summer fashion! Browse our uber-chic range of sunglasses to strut in style this season. Visit now!',
    #                 "Gift mom a stylish new view! Shop our Mother's Day Sale for unmissable offers on uber-chic eyewear. Browse our edit now",
    #                 "Gift mom a stylish new view! Shop our Mother's Day Sale for unmissable offers on uber-chic eyewear. Browse our edit now",
    #                 'Looking for the coolest summer trends? Browse our latest drop of chunky acetates and chiselled frames for an upgrade! Shop now.',
    #                 'Eye-fashion at its best! Strike a pose in our master metalworks and add a touch of glamour to your look. Shop now!',
    #                 "Summer's calling! Jet-set in style this season with our latest collection of sunset-worthy shades and uber-fresh tints. Shop now.",
    #                 'Hey gamers! Spending long hours perfecting your score? Armor up in our Zero Power BLU Lenses & block the digital glare.',
    #                 "Looking for a stylish gift for dad? Say 'Happy Father's Day' with John Jacobs' special SALE. Shop our eye-poppin' offers now!",
    #                 'Looking to make a great escape? Flee to stunning vistas with our latest edition, JJ Voyage! Shop uber-fresh tints now.',
    #                 "This International Yoga Day, go for the ultimate flex! Shop our dynamic TR Flex frames for eye-poppin' prices. Visit now.",
    #                 'Looking to make a great escape? Flee to stunning vistas with our latest edition, JJ Voyage! Shop uber-fresh tints now.',
    #                 "Shop the best deals on iconic eye-fashion with JJ's End Of Season Sale! 👀",
    #                 'Our latest collection, Roman Holiday, is a sight to behold! Fall in love with delicate textures and ornate details. Shop now!',
    #                 'Striking gold accents, rich colours and romantic textures. The Roman Holiday Edit by John Jacobs is here. Shop now.',
    #                 "John Jacobs - The best in business"
    #                 ]

    #sample_gens = ["hgjkdfhgkldjfngkljsf skfjgdkfjg dfojgd;ofkgjhd;o",
    # "hello",
    # " swiggy is an amazing brand that delivers food", "A", "AB", "50% off"]
    # sample_gens = ['Instantly Access Unlimited Content', 'Free Shipping On Myntra Orders', 'Delicious Eats & Great Savings']
    # sample_gens = ['hfjdkgn jsikdjgs joljk josjg os jo', 'dhugjsihglnug hfdkjshgo', 'hfj hfds jfd fdhs dgfd']
    sample_brand = 'Myntra'
    # checklist = []
    score_obj = ScorePerformance(sample_brand)
    # performance_labels = score_obj.get_performance_scores(checklist)
    # print(performance_labels)
    input_dict = {

        "primary_text": "Offer of a lifetime: 10% Off of Fiduciary charges!",
        "headline": "Offer of a lifetime: 10% Off on charges",
        "brand_name": "Vuori"
        }
    # input_dict = {}
    performance_labels = score_obj.get_perforamnce_bundle_score(input_dict)
    print(performance_labels)
