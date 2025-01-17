import sys
import traceback
import re
import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import logging


class DescriptionUSP(Lever):


    @Lever.log_generate
    def generate(self) -> None:
        text = self.input_dict['reference_description']
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
                "content" : f'''You are a helpful digital marketing assistant. Paraphrase Brand, Article, Topic, and Brand USP to write Creative Ads. Each Ad must be at least 12-15 words long.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
        },

            {
                "role": "user", 
                "content": f'''###                
Example 1
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance.
Article:
1. We help your business by providing expert coverage recommendations and average pricing.
2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
Topic: "Cyber"
Brand USP: All online, in minutes
Write 2 Descriptions for the given Brand USP:
1: Coverwallet's "Cyber" Insurance. Protect your business from Data Breaches and Malware.
2: Talk to our experts or get free personalized quotes online. All online, in minutes.

###
Example 2
Brand: HomeLane specialises in home interior designs and home décor and helps to create a personalized home to suit your lifestyle.
Article:
1: Thousands of design experts. Your search for the best home interior brand ends here.
2: Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
Topic: "London"
Brand USP: 45-day project completion
Write 2 Descriptions for the given Brand USP:
1: Does a mix of Elegance and Luxury sound good? HomeLane's London-style interiors at up to 23% off.
2: Book a free online consultation with one of 1000+ brilliant designers. Interiors delivered in 45-days!

###
Example 3
Brand: {self.input_dict['bu_detail']}
Article:
{self.input_dict['reference_description']}
Topic: "{self.input_dict['interest_keyword']}"
Brand USP: {self.input_dict['usp_used']}
Write 6 Descriptions for the given Brand USP. All Descriptions must be in {self.input_dict['language']}:
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
###
1:'''
            }]

        self.nlg_parameters = {
            "n" : 3,
            "response_length": 400,
            "temperature": 0.7,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1
            # "stop_seq": ["3.", "Article:", "Brand:", "\n\n"]
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            t_gens = re.sub(r'\d+\s*[:\.]', '', generation)
            '''
            \d+ matches one or more digits, \s* matches zero or more whitespace characters, and [:\.] matches either a colon or a period. This pattern will replace the occurrence of a digit followed by an optional space and either a colon or a period in the generation string.
            '''
            t_gens = t_gens.split('\n')
            self.extracted_generations_list.extend(t_gens)
        return

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=False, ending_exclusions='!#', exclude_domain=True, exclude_phone_number=True)
            # TODO: + pass inputs to self.postprocess_class
            #       - fix long sentences
            #       - remove incomplete sentences
            #       - make domain lowercase

            self.post_process_list = []
            for generation in self.extracted_generations_list:
                self.post_process_list.append(post_process_obj.run(generation, input_dict=self.input_dict))
        else:
            self.post_process_list = self.extracted_generations_list
        self.log_json['self.postprocess_class_labels'] = self.post_process_list
        
        
    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=40, 
            max_length=90, 
            filter_phrase=self.input_dict['usp_used'])
        self.filter_generations_list_target, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_description'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list_target)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)



    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] += 6

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            # TODO: + prepare output in desired format
            self.filter_generations_list = {
                'usp': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"usp":[]}, updated_log_json

if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

#     pt="""Paraphrase Brand, Article, Topic, and Brand USP to write Creative Ads. Each Ad must be at least 12-15 words long.

# Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance.
# Article:
# 1. We help your business by providing expert coverage recommendations and average pricing.
# 2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
# Topic: "Cyber"
# Brand USP: All online, in minutes
# ###
# 1: Coverwallet's "Cyber" Insurance. Protect your business from Data Breaches and Malware.
# 2: Talk to our experts or get free personalized quotes online. All online, in minutes.
# Brand: HomeLane specialises in home interior designs and home décor and helps to create a personalized home to suit your lifestyle.
# Article:
# 1: Thousands of design experts. Your search for the best home interior brand ends here.
# 2: Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
# Topic: "London"
# Brand USP: 45-day project completion
# ###
# 1: Does a mix of Elegance and Luxury sound good? HomeLane's London-style interiors at up to 23% off.
# 2: Book a free online consultation with one of 1000+ brilliant designers. Interiors delivered in 45-days!

# Brand: {self.input_dict['bu_detail']}
# Article:
# {self.input_dict['reference_description']}
# Topic: "{self.input_dict['interest_keyword']}"
# Brand USP: {self.input_dict['usp_used']}
# ###
# 1:"""

#     pp = {
#         'engine': 'text-davinci-001',
#         'response_length': 1050,
#         'temperature': 0.7,
#         'top_p': 1,
#         'frequency_penalty': 1,
#         'presence_penalty': 1,
#         'stop_seq': ["3:"]
#     }
#     sd = {}

#     id = {
#         "bu_detail": "Carsome is the #1 online used car buying platform. Buyers can browse 50K pre-loved cars inspected on 175-point and get a 360-degree view of the car's interior and exterior, take a test drive, trade-in your old car, and get doorstep delivery. All cars come with a 1-year warranty, 5 days money-back guarantee, fixed price, and no hidden fees.",
#         "reference_description": "1. Buy pre-loved Cars. Carsome Certified Cars. 175-Point Inspection Checklist.\n2. Carsome's Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee.",
#         "interest_keyword": "Family Car",
#         "bu_name": "Carsome",
#         "usp_used": "5 years engine warrenty",
#         "n_generations": 10
#     }

#     gens, rej_gens = DescriptionUSP().run(input_dict=id)
#     print(gens)
#     print(len(gens['usp']))

    id1 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "usp_used": "SEO Tools",
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9"
    }

    id2 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "usp_used": "SEO Tools",
        "brand_id" : "276cb088-ce1a-42f6-9ec7-867ee22ef70f"
    }

    id3 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "usp_used": "SEO Tools",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    for id in [id1, id2, id3]:

        gens, rej_gens = DescriptionUSP().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['usp']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)
