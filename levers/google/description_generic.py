import sys
import traceback
import math
import os
import re
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


class DescriptionGeneric(Lever):

    # Lever has support_dict, prompt_templete, self.nlg_parameters, min_length
    @Lever.log_generate
    def generate(self) -> None:
        brand_name = self.input_dict['bu_name']
        brand_detail = self.input_dict['bu_detail']
        article = self.input_dict['reference_description']

        if brand_detail.lower().split()[0] in brand_name.lower().split():
            brand_name = brand_name
            brand_detail = brand_detail.replace(brand_name, f"_{brand_name}_")
        else:
            brand_name = brand_detail.split()[0]
            brand_detail = brand_detail.replace(brand_name, f"_{brand_name}_")

        article = article.replace(brand_name, f"_{brand_name}_")

        self.input_dict['bu_detail'] = brand_detail
        self.input_dict['reference_description'] = article

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
                "content" : f'''Write creative Google Ad Descriptions for the given Brand, Article, and Interest Keyword.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
                },

            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: _CoverWallet_ makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Article:
1. We help your business by providing expert coverage recommendations and average pricing.
2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
Interest Keyword: "cyber insurance for business"
Write 5 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad. All Descriptions must be less than 100 Characters.
Ad 1: Protect your business from Data Breaches and Malware in minutes with _CoverWallet_. (83)
Ad 2: Find the right protection against Hackers at the right price with _CoverWallet_. In Minutes. (92)
Ad 3: Talk to _CoverWallet_ experts for information about the right coverage for your business needs. (95)
Ad 4: Get advice and competitive pricing for protection against Data Breach from _CoverWallet_. (89)
Ad 5: The coverage tailored to your needs - get liability protection against hackers with _CoverWallet_. (98)

###
Example 2
Brand: _HomeLane_ is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Article:
1. Thousands of design experts. Your search for the best home interior brand ends here.
2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
Interest Keyword: "London"
Write 4 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad. All Descriptions must be less than 115 Characters.
Ad 1: Modern Aesthetic Interior Designs on _HomeLane_. 1000+ Design Experts, 23% Off. Book now! (89)
Ad 2: Book a free online consultation with one of our 1000+ brilliant designers. Get Up to 23% Off on _HomeLane_. (107)
Ad 3: Does a mix of Art Deco and Minimalism Styles sound good? Explore Interiors on _HomeLane_ at 23% Off! (100)
Ad 4: Explore Modular Style Interior Designs - Austere Elegance and High-Quality Material at 23% Off. Only on _HomeLane_. (115)

###
Example 3
Brand: {self.input_dict['bu_detail']}
Article:
{self.input_dict['reference_description']}
Interest Keyword: "{self.input_dict['interest_keyword']}"
Write 10 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad. All Descriptions must be less than 95 Characters.
All Descriptions must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
Ad 1:'''
},
            {"role": "assistant",
             "content": f'''Do not include "{self.input_dict['interest_keyword']}" in any Descriptions\nInclude Article in all Descriptions'''}]

        self.nlg_parameters = {
            'n': 3,
            'response_length': 400,
            'temperature': 0.85,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 0
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)



    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:

            generation = generation.split('\n')
            temp_gens = []
            temp_gens.append(generation[0] if ("Ad" not in generation[0] and '1.' not in generation[0]) \
                              else generation[0].split("1.")[1].strip() if "1." in generation[0] \
                              else generation[0].split(':')[1].strip())
            temp_gens.extend([el.split(':')[1].strip() for el in generation[1:] if (el.strip() != '') and (len(el.split(':')) > 1)])
            self.extracted_generations_list.extend(temp_gens)
        self.extracted_generations_list = [re.sub(r'\s*\(\d+\)$', '', element) for element in self.extracted_generations_list]
        # [description[:-5] for description in self.extracted_generations_list]
    
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

        self.post_process_list = [el.replace("_", "") for el in self.post_process_list]
        self.log_json['self.postprocess_class_labels'] = self.post_process_list
        

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=15, 
            max_length=90,
            similar_to_reference_threshold=80)
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_description'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        # Selecting the first word from bu_details as brand_name

        self.log_json['filtered_generations'] = self.filter_generations_list
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filter_generations_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 0.1
            self.input_dict['n_generations'] = math.ceil(self.input_dict['n_generations']) + 2

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

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
#     # TODO: add prompt temptlate, params, support dict to csv for google

#     pt= '''Rephrase the given Article to write Creative Google Ads for the given Brand, Article, and Interest Keyword. Each Ad must be at least 12-15 words long.
# ###
# Example 1
# Brand: _CoverWallet_ makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
# Article:
# 1. We help your business by providing expert coverage recommendations and average pricing.
# 2. Get Quote online or talk to our helpful and professional advisors. Find the insurance you need.
# Interest Keyword: "cyber insurance for business"
# #
# Write 3 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
# #
# Ad 1: Protect your business from Data Breaches and Malware in minutes with _CoverWallet_.
# Ad 2: Find the right protection against Hackers at the right price with _CoverWallet_. In Minutes.
# Ad 3: Talk to _CoverWallet_ experts for information about the right coverage for your business needs.
# ###
# Example 2
# Brand: _HomeLane_ is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
# Article:
# 1. Thousands of design experts. Your search for the best home interior brand ends here.
# 2. Book a free online consultation today. Renovate your dream home at Up to 23% Off on all Designs.
# Interest Keyword: "London"
# #
# Write 4 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
# #
# Ad 1: Modern Aesthetic Interior Designs on _HomeLane_. 1000+ Design Experts, 23% Off. Book now!
# Ad 2: Book a free online consultation with one of our 1000+ brilliant designers. Get Up to 23% Off on _HomeLane_.
# Ad 3: Does a mix of Art Deco and Minimalism Styles sound good? Explore Interiors on _HomeLane_!
# Ad 4: Explore Modular Style Interior Designs - Austere Elegance and High-Quality Material. Only on _HomeLane_.
# ###
# Example 3
# Brand: _VogueLooks_ is a brand specialising in Clothing and Apparel. Their products are designed with exceptional quality and showcase a confident style. Top Clothing and Apparel for every season.
# Article:
# 1. Add sophistication to your outfits with our trendy and fashionable collection.
# 2. Amazing Styles and Offers on VogueLooks.com! Buy 3 Get 2 Free on Clothing and Apparel.
# Interest Keyword: "Suits"
# #
# Write 3 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
# #
# Ad 1: Electrify your wardrobe with the premium _VogueLooks_ collection and start turning heads. 
# Ad 2: Timeless Classics or Trendy Statement Pieces? Find Yours Now on _VogueLooks_. Buy 3 Get 2 Free!
# Ad 3: Create an Enviable Wardrobe with _VogueLooks_ premium collection. Buy 3 Get 2 Free on Everything!
# ###
# Example 4
# Brand: {self.input_dict['bu_detail']}
# Article:
# {self.input_dict['reference_description']}
# Interest Keyword: "{self.input_dict['interest_keyword']}"
# #
# Write 10 Descriptions for the Brand, Article, and Interest given above. Include Brand Name in each Ad.
# #
# Ad 1:'''

#     pp = {
#         'engine': 'text-davinci-002',
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
#         "reference_description": "1. Planning to change your car? Visit carsome.my. We'll make the switch effortlessly simple.\n2. Strict Assessments, 1-year warranty & best prices - We'll handle it all for you!",
#         "interest_keyword": "Family Car",
#         "bu_name": "Carsome",
#         "n_generations": 5
#     }

#     id3 = {
#         "bu_name": "Claro Shop",
#         "brand_id" : "112811d5-d614-40ce-bcec-8d3945262e2f",
#         # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
#         "n_generations" : 6,

#         "bu_detail": "Claro Shop is an e-commerce website that sells electronic gadgets, kitchen appliances, furniture, apparel, footwear, and gym utilities.", 
#         "brand_name": "Claro Shop", 
#         "interest_keyword": "e-commerce",
#         #   "reference_headline": "¡Solicítalo ahora!", 
#           "reference_description": "¡Solicítalo ahora!", 
#         #   "reference_primary_text": "Estrena millones de productos este Hot Sale a meses, sin tarjeta, sin aval con tu Crédito Claro Shop :fire::fire: Disfruta 15% de descuento adicional en tu primer compra + hasta 24 meses :star-struck:"
#     }

# # {"bu_name":"Interior Design","bu_detail":"Livspace is an interior design startup that offers a platform that connects people to designers, services, and products","interest_keyword":["userbrain"],"reference_headline":["Know Your Users' Pulse","Get Insights from Real Users","Best Human Insights Software"],"generation_type":["interest","brand","generic"],"no_of_outputs":15}


#     gens, rej_gens = DescriptionGeneric().run(input_dict=id3)
#     print(gens)
#     # print(len(gens['generic']))


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
        "bu_detail": "Carsome is the #1 online used car buying platform. Buyers can browse 50K pre-loved cars inspected on 175-point and get a 360-degree view of the car's interior and exterior, take a test drive, trade-in your old car, and get doorstep delivery. All cars come with a 1-year warranty, 5 days money-back guarantee, fixed price, and no hidden fees.",
        "reference_description": "1. Carsome's Certified Cars come with 1-year warranty and 5-Day money-back guarantee.\n2. Find your dream ride from 50K+ pre-loved cars. Book a test drive today.",
        "interest_keyword": "MPV",
        "bu_name": "Carsome",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = DescriptionGeneric().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['generic']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)
