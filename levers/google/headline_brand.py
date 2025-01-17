import sys
import traceback
import math
import re

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


# from ds.process.content_filtering import content_filter_inputs_outputs

import logging

class HeadlineBrand(Lever):

    @Lever.log_generate
    def generate(self) -> None:


        # Pre-processing inputs for prompt
        # We need to pass brand_details and input ads with "_"
        # before and after the brand_name in prompt
        brand_name = self.input_dict['bu_name']
        brand_detail = self.input_dict['bu_detail']
        article = self.input_dict['reference_headline']

        brand_detail = brand_detail.replace(brand_name, "_{}_".format(brand_name))
        article = article.replace(brand_name, "_{}_".format(brand_name))

        self.input_dict['bu_detail'] = brand_detail
        self.input_dict['reference_headline'] = article

        text = self.input_dict['reference_headline']
        self.input_dict['language'] = detect_language(text)

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
                "content": f'''You are a digital marketing assistant. Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand and Reference Copy.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
                },

            {
                "role": "user", 
                "content": f'''#
Example 1

Brand: _CoverWallet_ makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. Talk to our experts or get a free quote tailored to your needs.
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest: Cyber
Write 7 Headlines for the Brand given above. Each Headline must be less than 34 Characters. Each Headline must include the Brand Name. Use some context from Interest.
Use the phrase "Cyber" contextually in headlines.
#
1: Talk to _CoverWallet_ Experts (29)
2: _CoverWallet_ Is Fast & Paperless (33)
3: _CoverWallet_ Online Insurance (30)
4: _CoverWallet_ Says No To Hackers! (33)
5: No Data Spill With _CoverWallet_ (32)
6: Go Paperless With _CoverWallet_ (31)
7: Go 100% Online at _CoverWallet_ (31)
###
Example 2

Brand: _HomeLane_ is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
Interest: Modular Kitchen
Write 10 Headlines for the Brand given above. Each Headline must be less than 33 Characters. Each Headline must include the Brand Name. Use some context from Interest.
Use the phrase "Modular Kitchen" contextually in headlines.
#

1: 1000+ Interiors On _HomeLane_ (29)
2: _HomeLane's_ Compact Cookeries (30)
3: Get Free Estimates On _HomeLane_ (32)
4: _HomeLane's_ Efficient Galleys (30)
5: Look No Further Than _HomeLane_ (31)
6: Spice your Space With _HomeLane_ (32)
7: Explore Designs On _HomeLane_ (29)
8: 23% Off on _HomeLane_ (21)
9: _HomeLane_: Customize Dream Home (32)
10: _HomeLane_: Designs @ 23% Off (29)
###
Example 3

Brand: _HelloFresh_ is a food subscription company that sends pre-portioned ingredients to users_ doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
Interest: Vegan
Write 7 Headlines for the Brand given above. Each Headline must be less than 34 Characters. Each Headline must include the Brand Name. Use some context from Interest.
Use the phrase "Vegan" contextually in headlines.
#
1: Go Green With _HelloFresh_! (27)
2: Say Hello To _HelloFresh_! (26)
3: Healthy Meals? Try _HelloFresh_ (31)
4: Get 14 Free Meals On _HelloFresh_ (33)
5: Healthify With _HelloFresh_! (28)
6: Fresh Veggies on _HelloFresh_ (29)
7: _HelloFresh_: 14 Free Meals (27)
###
Example 4

Brand: {self.input_dict['bu_detail']}
Reference Copy: {self.input_dict['reference_headline']}
Interest: {self.input_dict['interest_keyword']}
Write 10 Headlines for the Brand given above. Each Headline must be less than 30 Characters. Each Headline must include the Brand Name. Use some context from Interest.
Use the phrase "{self.input_dict['interest_keyword']}" contextually in headlines.
All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
#
1:'''
            }]

        self.nlg_parameters = {
            'n' : 5,
            'response_length': 300,
            'temperature': 0.6,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 0
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)



    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            # generation = 'Questions:' + generation
            generation = '1: ' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations_list.extend(t_gens)
        self.extracted_generations_list = [re.sub(r'\s*\(\d+\)$', '', element) for element in self.extracted_generations_list]

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=True, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
            # TODO: + pass inputs to self.postprocess_class
            #       + article fix
            #       + incorrect offer
            #       + preserve unusual capitalization from inputs
            
            self.extracted_generations_list = [el.replace("_", "") for el in self.extracted_generations_list]
            self.post_process_list = []
            for generation in self.extracted_generations_list:
                self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        else:
            self.post_process_list = self.extracted_generations_list
        self.log_json['self.postprocess_class_labels'] = self.post_process_list  


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=30,
            filter_phrase=self.input_dict['bu_name'],
            filter_phrase_threshold=80)

        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            generations_list=self.post_process_list, 
            reference_ad=self.input_dict['reference_headline'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        self.log_json['filtered_generations'] = self.filter_generations_list
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)

 
    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            logging.debug("Google headline_brand generate started")
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 2

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            self.filter_generations_list = {
                'brand': self.performance_generations_dict_list[:no_of_outputs]
            }
            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"brand":[]}, updated_log_json    


if __name__ == '__main__':

#     # TODO: add prompt temptlate, params, support dict to csv for google

#     pt= '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest
# #
# Example 1

# Brand: _CoverWallet_ makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. Talk to our experts or get a free quote tailored to your needs.
# Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
# Interest: Cyber
# #
# Write 5 Headlines for the Brand given above. Each Headline must be less than 6 words. Each Headline must include the Brand Name. Use some context from Interest.
# #

# 1: Talk to _CoverWallet_ Experts
# 2: _CoverWallet_ is Fast & Paperless
# 3: _CoverWallet_ Online Insurance
# 4: _CoverWallet_ says no to Hackers!
# 4: No Data Spill with _CoverWallet_
# 5: Go Paperless with _CoverWallet_
# ###
# Example 2

# Brand: _HomeLane_ is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
# Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
# Interest: Modular Kitchen
# #
# Write 7 Headlines for the Brand given above. Each Headline must be less than 6 words. Each Headline must include the Brand Name. Use some context from Interest.
# #

# 1: 1000+ Interiors on _HomeLane_
# 2: _HomeLane's_ Compact Cookeries
# 3: Get free estimates on _HomeLane_
# 4: _HomeLane's_ Efficient Galleys
# 5: Look no further than _HomeLane_
# 6: Spice your Space with _HomeLane_
# 7: Explore Designs on _HomeLane_
# ###
# Example 3

# Brand: _HelloFresh_ is a food subscription company that sends pre-portioned ingredients to users_ doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
# Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
# Interest: Vegan
# #
# Write 5 Headlines for the Brand given above. Each Headline must be less than 6 words. Each Headline must include the Brand Name. Use some context from Interest.
# #
# 1: Go Green with _HelloFresh_!
# 2: Say Hello to _HelloFresh_!
# 3: Healthy Meals? Try _HelloFresh_
# 4: Get 14 Free Meals on _HelloFresh_
# 5: Healthify with _HelloFresh_!
# ###
# Example 4

# Brand: {self.input_dict['bu_detail']}
# Reference Copy: {reference_headline}
# Interest: {self.input_dict['interest_keyword']}
# #
# Write 10 Headlines for the Brand given above. Each Headline must be less than 6 words. Each Headline must include the Brand Name. Use some context from Interest.
# #
# 1:'''


#     pp = {
#         'engine': 'text-davinci-002',
#         'response_length': 256,
#         'temperature': 0.85,
#         'top_p': 1,
#         'frequency_penalty': 0.4,
#         'presence_penalty': 0,
#         'stop_seq' : ["###"]
#     }
#     sd = {}

#     id = {
#         "bu_detail": "Swiggy delivers yummy food to your doorsteps.",
#         "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
#         "interest_keyword": "Pizza",
#         "bu_name": "Swiggy",
#         "benefit_used": "Gluten free",
#         "n_generations": 10
#     }

#     gens, rej_gens = HeadlineBrand().run(input_dict=id)
#     print(gens)
#     print(len(gens['brand']))
    # print(pt.format(**id))

    # t_p = self.postprocess_class(title_case=False, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
    # print(t_p.run('Get an Pizza" Delivered. thesis is best. $55 Off on Swiggy', id))


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
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    # id3 = {
    #     "bu_detail": "Carsome is the #1 online used car buying platform. Buyers can browse 50K pre-loved cars inspected on 175-point and get a 360-degree view of the car's interior and exterior, take a test drive, trade-in your old car, and get doorstep delivery. All cars come with a 1-year warranty, 5 days money-back guarantee, fixed price, and no hidden fees.",
    #     "reference_headline": "Carsome's Certified Cars. 1-year warranty and 5-Day money-back guarantee. Find your dream ride",
    #     "interest_keyword": "MPV",
    #     "bu_name": "Carsome",
    #     "benefit_used": "free",
    #     "n_generations": 10,
    #     "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    # }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineBrand().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['brand']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)
