import sys
import re

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import math
import traceback

import logging


class HeadlineCompetitor(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        text = self.input_dict.get('reference_headline',"")
        if text:
            self.input_dict['language'] = detect_language(text)
        else:
            self.input_dict['language'] = 'English'

        ## Compliance
        additional_instructions, replacement_instructions = '', ''
        brand_id = self.input_dict.get('brand_id', '')
        compliance_file_path = 'ds/process/brand_specific/' + str(brand_id) + '.yaml'
        if os.path.exists(compliance_file_path):
            with open(compliance_file_path, "r") as f:
                data = yaml.safe_load(f) 
            additional_instructions = data.get('additional_instructions')
            replacement_instructions = data.get('replacement_instructions')

        self.prompt = [
            {
                "role" : "system",
                "content": f'''You are a helpful digital marketing assistant. Write Competitor Based Google ad Headlines for a given Brand.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
},


            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: Livspace is an interior design startup that offers a platform that connects people to designers, services, and products. With a variety of interior designs to choose from, Livspace makes it easy for customers to get the exact look they want for their homes.
Write 5 Headlines. Each Headline must be less than 50 characters. Each headline must indicate that "Livspace" is the best in its space.
Headline 1: Choose Livspace For Hassle-free Design (38)
Headline 2: Livspace: India's Best Interior Design Platform (47)
Headline 3: Unmatched Home Design With Livspace (35)
Headline 4: Transform Your Home With Livspace (33)
Headline 5: We Listen, We Design, We Deliver (32)
###
Example 2
Brand Info: HelloFresh is a food subscription company that sends pre-portioned ingredients to users. HelloFresh's meal kits include all the ingredients you need to cook a healthy, delicious meal. With HelloFresh, you can choose from a variety of recipes and meals, and the company delivers them to you.
Write 5 Headlines. Each Headline must be less than 45 characters. Each headline must indicate that "HelloFresh" is the best in its space.
Headline 1: We Bet No One Can Match Our Dinners (35)
Headline 2: Goodbye Boring Dinner: Switch to HelloFresh (43)
Headline 3: HelloFresh: Your Go-To Meal Kit Provider (40)
Headline 4: HelloFresh: Faster, Fresher, Healthier Meals (44)
Headline 5: Say Goodbye to Meal Prep with HelloFresh (40)
###
Example 3
Brand: Carsome is an online used car platform that provides efficient car buying services to individuals and entities. Through its online bidding portal, customers are able to buy vehicles directly from the dealers.
Write 5 Headlines. Each Headline must be less than 45 characters. Each headline must indicate that "Carsome" is the best in its space.
Headline 1: Get the Best Deals with Carsome (31)
Headline 2: Make Car Buying Hassle-Free With Carsome (40)
Headline 3: Carsome: The #1 Used Car Platform (33)
Headline 4: Stress-Free Car Buying With Carsome (35)
Headline 5: Carsome: The Preferred Car Buying Platform (42)
###
Example 4
Brand: {self.input_dict['bu_detail']}
Write 10 Headlines. Each Headline must be less than 30 characters. Each headline must indicate that "{self.input_dict['bu_name']}" is the best in its space.
All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
Headline 1:'''
            }]

        self.nlg_parameters = {
            'n' : 3,
            'response_length': 250,
            'temperature': 0.8,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 0,
            'stop_seq' : [],
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation = 'Headline 1: ' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations.extend(t_gens)
        self.extracted_generations = [re.sub(r'\s*\(\d+\)$', '', element) for element in self.extracted_generations]
    
    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=False)
            self.post_process_list = []
            for generation in self.extracted_generations:
                self.post_process_list.append(post_process_obj.run(generation, self.input_dict))
        else:
            self.post_process_list = self.extracted_generations

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(min_length=self.min_length, max_length=30)
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list, reference_ad='',
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            logging.debug("Google headline_competitor generate started")
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 2

            self.generate()
            logging.debug("Google headline_competitor generate completed")            
            self.extract_label()
            logging.debug("Google headline_competitor label extraction completed")            
            self.postprocess()
            logging.debug("Google headline_competitor post processing completed")            
            self.filter_generations()
            logging.debug("Google headline_competitor filteration completed")            
            # n_gen is the value that core sends to us referring to how many outputs they want to be displayed
            self.filter_generations_dict = {
                'competitor': self.performance_generations_dict_list[:no_of_outputs]
            }
            return self.filter_generations_dict, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"interest":[]}, updated_log_json 

if __name__ == "__main__":

    # id = {
    #     "bu_detail": "Swiggy delivers yummy food to your doorsteps.",
    #     "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
    #     "interest_keyword": "Pizza",
    #     "bu_name": "Swiggy",
    #     "benefit_used": "Gluten free",
    #     "n_generations": 5
    # }

    # gens, rej_gens = HeadlineCompetitor().run(input_dict=id)
    # print(gens)


    id1 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9"
    }

    id2 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "276cb088-ce1a-42f6-9ec7-867ee22ef70f"
    }

    id3 = {
        "bu_detail": "Capitalize helps people find and transfer old retirement accounts and open new ones. Users roll over and consolidate legacy retirement accounts. Capitalize helps users instantly locate misplaced 401k accounts, select and open IRAs at leading financial institutions, and initiate rollovers on their behalf for free.",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Capitalize",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineCompetitor().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['competitor']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)
