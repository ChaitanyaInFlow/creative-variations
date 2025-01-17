import traceback
import sys
import math
import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import logging

class DescriptionInterest(Lever):

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
                "content" : f'''You are a helpful digital marketing assistant. Rephrase the given Article to write Creative Google Ads for the given Brand, Article, and Interest Keyword. Each Ad must be at least 12-15 words long.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
                },

            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Article:
1. We help your business by providing expert coverage recommendations and average pricing.
2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
Interest Keyword: "cyber insurance for business"
Write 3 Descriptions for the Interest Keyword given above.
#
Ad 1: "Cyber" Insurance to the rescue! Get free personalized quotes online or talk to our experts.
Ad 2: Protect your business against "Cyber" Liabilities. Find the right business insurance tailored to your needs.
Ad 3: Safeguard your business against Hackers with "Cyber" Insurance. Get a quote now!

###
Example 2
Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Article:
1. Thousands of design experts. Your search for the best home interior brand ends here.
2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
Interest Keyword: "London"
Write 4 Descriptions for the Interest Keyword given above.
#
Ad 1: Does a mix of Art Deco and Minimalism Styles sound good? Try "London" Style Interior Designs!
Ad 2: Explore Aesthetic "London" Style Interior Designs - Austere Elegance and High-Quality Material.
Ad 3: Looking for elegant and timeless "London" style interior designs? We've got you covered!
Ad 4: London Interiors - Swinging Sixties, Mock Tudor, Art Deco. Explore 1000+ Designs.

###
Example 3
Brand: VogueLooks is a brand specialising in Clothing and Apparel. Their products are designed with exceptional quality and showcase a confident style. Top Clothing and Apparel for every season.
Article:
1. Add sophistication to your outfits with our trendy and fashionable collection.
2. Amazing Styles and Offers on VogueLooks.com! Buy 3 Get 2 Free on Clothing and Apparel.
Interest Keyword: "Suits"
Write 4 Descriptions for the Interest Keyword given above.
#
Ad 1: Electrify your wardrobe with our premium "Suits" and start turning heads. It's magic!
Ad 2: Look Sharp and Make a Lasting Impression with our Assortment of Elegant "Suits"!
Ad 3: Create an Enviable Wardrobe with our Selection of "Suits" for all Seasons!
Ad 4: "SUITS" - Timeless Classics or Trendy Statement Pieces? Find Yours Now!

###
Example 4
Brand: {self.input_dict['bu_detail']}
Article:
{self.input_dict['reference_description']}
Interest Keyword: "{self.input_dict['interest_keyword']}"
Write 6 Descriptions for the Interest Keyword given above. Do not include Brand Name in Ads.
All Descriptions must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
#
Ad 1:'''
            }]

        self.nlg_parameters = {
            'n' : 5,
            'response_length': 400,
            'temperature': 0.85,
            'top_p': 1,
            'frequency_penalty': 0.6,
            'presence_penalty': 1,
            'stop_seq': ["###"]
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(
            self.prompt, **self.nlg_parameters)


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = []
        for generation in self.nlg_generations_list:

            generation = generation.split('\n')
            temp_gens = []

            temp_gens.append(generation[0])
            temp_gens.extend([el.split(':')[1].strip() for el in generation[1:] if (
                el.strip() != '') and (len(el.split(':')) > 1)])
            self.extracted_generations_list.extend(temp_gens)

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(
                title_case=False, ending_exclusions='!#', exclude_domain=True, exclude_phone_number=True)
            # TODO: + pass inputs to self.postprocess_class
            #       - fix long sentences
            #       - remove incomplete sentences
            #       - make domain lowercase

            self.post_process_list = []
            for generation in self.extracted_generations_list:
                self.post_process_list.append(
                    post_process_obj.run(generation, input_dict=self.input_dict))
        else:
            self.post_process_list = self.extracted_generations_list
        self.log_json['self.postprocess_class_labels'] = self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=15,
            max_length=90,
            filter_phrase=self.input_dict['interest_keyword'])
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list,
            self.input_dict['reference_description'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        # self.log_json['filtered_generations'] = self.filtered_generations

        score_performance_obj = self.score_performance_class(
            brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(
            generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(
            input_assets=self.performance_list)

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            logging.debug("Google description_interest generate started")

            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(
                self.input_dict['n_generations']) + 2

            self.generate()
            logging.debug("Google description_interest generate completed")            
            self.extract_label()
            logging.debug("Google description_interest label extraction completed")            
            self.postprocess()
            logging.debug("Google description_interest post processing completed")            
            self.filter_generations()
            logging.debug("Google description_interest filteration completed")            
            # TODO: + add IBG segregation

            # TODO: + prepare output in desired format
            self.filter_generations_list = {
                'interest': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return {"interest": []}, updated_log_json


if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

#     pt = '''Rephrase the given Article to write Creative Google Ads for the given Brand, Article, and Interest Keyword. Each Ad must be at least 12-15 words long.
# ###
# Example 1
# Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
# Article:
# 1. We help your business by providing expert coverage recommendations and average pricing.
# 2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
# Interest Keyword: "cyber insurance for business"
# #
# Write 3 Descriptions for the Interest Keyword given above.
# #
# Ad 1: "Cyber" Insurance to the rescue! Get free personalized quotes online or talk to our experts.
# Ad 2: Protect your business against "Cyber" Liabilities. Find the right business insurance tailored to your needs.
# Ad 3: Safeguard your business against Hackers with "Cyber" Insurance. Get a quote now!
# ###
# Example 2
# Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
# Article:
# 1. Thousands of design experts. Your search for the best home interior brand ends here.
# 2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
# Interest Keyword: "London"
# #
# Write 4 Descriptions for the Interest Keyword given above.
# #
# Ad 1: Does a mix of Art Deco and Minimalism Styles sound good? Try "London" Style Interior Designs!
# Ad 2: Explore Aesthetic "London" Style Interior Designs - Austere Elegance and High-Quality Material.
# Ad 3: Looking for elegant and timeless "London" style interior designs? We've got you covered!
# Ad 4: London Interiors - Swinging Sixties, Mock Tudor, Art Deco. Explore 1000+ Designs.
# ###
# Example 3
# Brand: VogueLooks is a brand specialising in Clothing and Apparel. Their products are designed with exceptional quality and showcase a confident style. Top Clothing and Apparel for every season.
# Article:
# 1. Add sophistication to your outfits with our trendy and fashionable collection.
# 2. Amazing Styles and Offers on VogueLooks.com! Buy 3 Get 2 Free on Clothing and Apparel.
# Interest Keyword: "Suits"
# #
# Write 4 Descriptions for the Interest Keyword given above.
# #
# Ad 1: Electrify your wardrobe with our premium "Suits" and start turning heads. It's magic!
# Ad 2: Look Sharp and Make a Lasting Impression with our Assortment of Elegant "Suits"!
# Ad 3: Create an Enviable Wardrobe with our Selection of "Suits" for all Seasons!
# Ad 4: "SUITS" - Timeless Classics or Trendy Statement Pieces? Find Yours Now!
# ###
# Example 4
# Brand: {self.input_dict['bu_detail']}
# Article:
# {self.input_dict['reference_description']}
# Interest Keyword: "{self.input_dict['interest_keyword']}"
# #
# Write 10 Descriptions for the Interest Keyword given above. Do not include Brand Name in Ads.
# #
# Ad 1:'''

#     pp = {
#         'engine': 'text-davinci-003',
#         'response_length': 1050,
#         'temperature': 0.85,
#         'top_p': 1,
#         'frequency_penalty': 0.6,
#         'presence_penalty': 1,
#         'stop_seq': ["###"]
#     }
#     sd = {}

#     id = {
#         "bu_detail": "Carsome is the #1 online used car buying platform. Buyers can browse 50K pre-loved cars inspected on 175-point and get a 360-degree view of the car's interior and exterior, take a test drive, trade-in your old car, and get doorstep delivery. All cars come with a 1-year warranty, 5 days money-back guarantee, fixed price, and no hidden fees.",
#         "reference_description": "1. Buy pre-loved Cars. Carsome Certified Cars. 175-Point Inspection Checklist.\n2. Carsome's Certified Cars come with a 1-year warranty and a 5-Day money-back guarantee.",
#         "interest_keyword": "Family Car",
#         "bu_name": "Carsome",
#         "n_generations": 10
#     }

#     gens, rej_gens = DescriptionInterest().run(input_dict=id)
#     print(gens)
#     print(len(gens['interest']))

    id1 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9"
    }

    id2 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "276cb088-ce1a-42f6-9ec7-867ee22ef70f"
    }

    id3 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_description": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    for id in [id1, id2, id3]:

        gens, rej_gens = DescriptionInterest().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['interest']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)