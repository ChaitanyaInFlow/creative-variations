import math
import sys
import traceback

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language



class HeadlineInterest(Lever):
    
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
                "content": f'''You are a helpful digital marketing assistant. Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest Keyword.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
    },


            
            {
                "role": "user", 
                "content": f'''#
Example 1

Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
Interest Keyword: "cyber insurance for business"
#
Write 10 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: On-Demand "Cyber Insurance"
2: Worried About "Cyber" Attacks?
3: Fast & Paperless "IT" Insurance
4: Buy "Cyber" Insurance In A Blink
5: "Cyber" Insurance, On Your Terms
6: Protection From "Cyber" Liability
7: 100% Online "Cyber" Coverage
8: "Cyber" Safety in Minutes
9: "Cyber" Coverage per your needs
10: "Cyber" Insurance - 100% Online
###
Example 2

Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users" doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
Interest: "Vegan Meal, easy preparation"
#
Write 8 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
#
1: Craving Tasty "Vegan Meals"?
2: Choose Fresh "Vegan Meals"
3: Delight In Delicious "Vegan Meals"
4: Taste Terrific "Vegan Meals"
5: 14 Free Nutritious "Vegan Meals"
6: Yummy "Vegan" for Happy Heart
7: 14 Free "Vegan" Meals Delivered
8: Order "Vegan" Meals Today!
###
Example 3

Brand: {self.input_dict['bu_detail']}
Reference Copy: {self.input_dict['reference_headline']}
Interest Keyword: "{self.input_dict['interest_keyword']}"
#
Write 8 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''} 
#
1:'''
        },
            {
                "role": "assistant",
                "content": f'''Do not include "{self.input_dict['bu_name']}" in Headlines'''
            }]

        self.nlg_parameters = {
            'n' : 6,
            'response_length': 300,
            'temperature': 0.85,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 0
            # 'stop_seq' : ["###", "Brand:"],
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

        self.log_json['self.postprocess_class_labels'] = self.post_process_list


    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=30, 
            filter_phrase=self.input_dict['interest_keyword'])
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

            no_of_outputs = self.input_dict['n_generations']
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            self.filter_generations_list = {
                'interest': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"interest":[]}, updated_log_json 

if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

#     pt= '''Rephrase the given Reference Copy to generate creative Google ad Headlines for the given Brand, Reference Copy, and Interest Keyword.
# #
# Example 1

# Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
# Reference Copy: Insurance for business. On-demand liability insurance. 100% Online, In Minutes.
# Interest Keyword: "cyber insurance for business"
# #
# Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
# #
# 1: On-demand "Cyber Insurance"
# 2: Worried about "Cyber" attacks?
# 3: Fast & Paperless "IT" Insurance
# 4: Buy "Cyber" Insurance in a Blink
# 5: "Cyber" Insurance, on your terms
# 6: Protection from "Cyber" Liability
# ###
# Example 2

# Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
# Reference Copy: Modern Home Interior Designs. Unbeatable Quality & 23% Off. Customize your Dream Home
# Interest Keyword: "Modular Kitchen"
# #
# Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
# #
# 1: Get 23% off on "Modular Kitchen"
# 2: The "Kitchen" of Your Dreams
# 3: Compact "Kitchen" Interiors
# 4: 1000s of "Modular Kitchen" Ideas
# 5: Eying for "Modular Style Kitchen"?
# 6: "Modular Kitchen" on Your Budget
# ###
# Example 3

# Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users" doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
# Reference Copy: Get Fresher, Faster Meals. Order today. Get 14 Free Meals.
# Interest: "Vegan Meal, easy preparation"
# #
# Write 6 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
# #
# 1: Craving Tasty "Vegan Meals"?
# 2: Choose Fresh "Vegan Meals"
# 3: Delight in Delicious "Vegan Meals"
# 4: Taste Terrific "Vegan Meals"
# 5: 14 Free Nutritious "Vegan Meals"
# 6: Yummy "Vegan" for Happy Heart

# ###
# Example 4

# Brand: {self.input_dict['bu_detail']}
# Reference Copy: {reference_headline}
# Interest Keyword: "{self.input_dict['interest_keyword']}"
# #
# Write 5 Headlines for the Interest keyword given above. Each Headline must be less than 6 words.
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
#         "bu_detail": "SwiGGy delivers yummy food to your doorsteps.",
#         "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
#         "interest_keyword": "Pizza",
#         "bu_name": "Swiggy",
#         "benefit_used": "Gluten free",
#         "n_generations": 10
#     }

#     headline_gen_obj = HeadlineInterest()
#     gens, rej_gens = headline_gen_obj.run(input_dict=id)
#     print(gens)
#     print(len(gens['interest']))


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

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineInterest().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['interest']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(len(output),'\n')
        print(output)
