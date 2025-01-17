import math
import sys
import traceback

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


# from ds.process.content_filtering import content_filter_inputs_outputs

import logging



class HeadlineGeneric(Lever):

    @Lever.log_generate
    def generate(self) -> None:
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
                "content": f'''Rephrase the given Paraphrase Copy to generate creative Headlines for the given Brand and Paraphrase Copy.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
},
            
            {
                "role": "user", 
                "content": f'''###
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. 
Paraphrase Copy: <<"Insurance for business. On-demand liability insurance. 100% Online, In Minutes.">>
Interest: ~Cyber~
Write 11 Headlines for the Paraphrase Copy given above. Each Headline must be less than 6 words.
#

1: Quick and Paperless Insurance
2: Immunity from Leaks, in Minutes
3: 100% Online Liability Coverage
4: Instant policies, No Paperwork
5: Protection Against Hackers
6: Defend Your Business From Leaks
7: Coverage Tailored To Your Needs
8: Don't Lose Sleep Over Hackers!
9: Protection Against Data Spill
10: 100% Online Business Security
11: 100% Online Coverage, Fast
###
Example 2

Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way.
Paraphrase Copy: <<"Explore thousands of inspiring interior designs. Unbeatable Quality & 23% Off. Get a free estimate.">>
Interest: ~Modular Kitchen~
Write 8 Headlines for the Paraphrase Copy given above. Each Headline must be less than 6 words.
#

1: Unmatched Quality At 23% Off
2: Design Your Dream Cookery
3: Personalized and Affordable
4: Your Dream Home On A Budget!
5: 1000+ Flawless Interior Designs
6: 23% Off on Cookery Makeover
7: Homeowners, Get Your Free Quote!
8: Compact Interiors at 23% Off!
###
Example 3

Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Paraphrase Copy: <<"Get Fresher, Faster Meals. Order today. Get 14 Free Meals.">>
Interest: ~Vegan~
Write 5 Headlines for the Paraphrase Copy given above. Each Headline must be less than 6 words.
#

1: 14-Free Green Meals Delivered!
2: Fast Home-Cooked Green Meals
3: Fresh Veggies Delivered, Fast!
4: Get 14-Free Green Meals by Us
5: Order Fresh Plant-Based Meals
###
Example 4

Brand: {self.input_dict['bu_detail']}
Paraphrase Copy: <<"{self.input_dict['reference_headline']}">>
Interest: ~{self.input_dict['interest_keyword']}~
Write 10 Headlines for the Paraphrase Copy given above. Each Headline must be less than 6 words.
All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
#

1:'''},
    {
      "role": "assistant",
      "content": f'''Follow the below instructions:\n1. DON'T use "{self.input_dict['interest_keyword']}" in any Headlines\n2. DON'T use "{self.input_dict['bu_name']}" in any Headlines\n3. Use Paraphrase Copy across all Headlines\n4. Use less than 30 characters'''
    },
]

        self.nlg_parameters = {
            'n' : 5,
            'response_length': 400,
            'temperature': 0.75,
            'top_p': 1,
            'frequency_penalty': 1,
            'presence_penalty': 2
        }   
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            # generation = 'Questions:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations_list.extend(t_gens)

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=True, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
            # TODO: + pass inputs to self.postprocess_class
            #       + article fix
            #       + incorrect offer
            #       + preserve unusual capitalization from inputs
            
            self.post_process_list = []
            for generation in self.extracted_generations_list:
                self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        else:
            self.post_process_list = self.extracted_generations_list

        self.post_process_list = [el for el in self.post_process_list if self.input_dict['bu_name'].lower() not in el.lower()]
        self.log_json['self.postprocess_class_labels'] = self.post_process_list  


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=30)
        # TODO: Add ISF filter
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_headline'],
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
            logging.debug("Google headline_generic generate started")
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 4

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            # TODO: - while loop to keep generating
            #       - content filtering

            self.filter_generations_list = {
                'generic': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"generic":[]}, updated_log_json    


if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

#     pt= '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest.
# #
# Example 1

# Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price. 
# Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
# Interest: "Cyber"
# #
# Write 7 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
# #

# 1: Quick and Paperless Insurance
# 2: Instant policies, no paperwork
# 3: Protection against Hackers
# 4: Defend Your Business from Leaks
# 5: Insurance tailored to your needs
# 6: Don't lose sleep over Hackers!
# 7: Protection Against Data Spill
# ###
# Example 2

# Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
# Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
# Interest: "Modular Kitchen"
# #
# Write 9 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
# #

# 1: Unmatched Quality at 23% Off
# 2: Design Your Dream Cookery
# 3: Personalized and affordable
# 4: Your dream home on a budget!
# 6: 1000+ Flawless Interior Designs
# 7: Kitchen Makeover in a Snap
# 8: Homeowners, get your free quote!
# 9: Create Your Dream Kitchen Today
# ###
# Example 3

# Brand: {self.input_dict['bu_detail']}
# Reference Copy: {reference_headline}
# Interest: "{self.input_dict['interest_keyword']}"
# #
# Write 10 Headlines for the Brand, Reference Copy, and Interest given above. Each Headline must be less than 6 words. Use Context from Interest.
# #

# 1:'''


#     pp = {
#         'engine': 'text-davinci-002',
#         'response_length': 100,
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

#     gens, rej_gens = HeadlineGeneric().run(input_dict=id)
#     print(gens)
#     print(len(gens['generic']))
#     # print(pt.format(**id))

#     # t_p = self.postprocess_class(title_case=False, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
#     # print(t_p.run('Get an Pizza" Delivered. thesis is best. $55 Off on Swiggy', id))


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
        "reference_headline": "The Ultimate 20-in-1 SEO Tool. Research Your Competitors. Semrush SEO Tools",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 10,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineGeneric().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['generic']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(len(output),'\n')
        print(output)


