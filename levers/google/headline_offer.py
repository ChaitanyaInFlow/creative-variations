import sys

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import math
import traceback

class HeadlineOffer(Lever):

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
                "content": f'''Write creative Google Offer Headlines for a given Brand, Interest Keyword, and Offer.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
    },

            {
                "role": "user", 
                "content": f'''###
Example 1
Brand: Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.
Interest Keyword: <<Pizza>>
Offer: 20% Off
Write 5 Headlines. Each Headline must be less than 34 characters. Each Headline must contain the Offer.
1: Get <<Pizza>> @ 20% Off on Swiggy
2: Enjoy 20% Off On <<Pizza>> Tonight
3: <<Pizza>> at 20% Off on Swiggy!
4: Swiggy: <<Pizza>> Party at 20% Off 
5: Feast on a <<Pizza>> @ 20% Off
###
Example 2
Brand: Carsome is an online used car platform that provides efficient car buying services to individuals and entities. Through its online bidding portal, customers are able to buy vehicles directly from the dealers.
Interest Keyword: <<Jeep>>
Offer: 1-Year Warranty
Write 3 Headlines. Each Headline must be less than 34 characters. Each Headline must contain the Offer.
1: Buy <<Jeep>> with 1-Year Warranty!
2: 1-Year warranty On <<Jeep>>!
3: Carsome: 1-Year Warranty On <<Jeep>>
###
Example 3
Brand: Allbirds, Inc. is a New Zealand-American company that sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Interest Keyword: <<Shoes>>
Offer: 30 days return
Write 2 Headlines. Each Headline must be less than 34 characters. Each Headline must contain the Offer.
1: Allbirds <<Shoes>>: 30-Day Return
2: <<Shoes>> With 30-Day Return Policy
###
Example 4
Brand: {self.input_dict['bu_detail']}
Interest Keyword: <<{self.input_dict['interest_keyword']}>>
Offer: {self.input_dict['offer_used']}
Write 8 Headlines. Each Headline must be less than 30 characters. Each Headline must contain the Offer. All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
1:'''
        }]

        self.nlg_parameters = {
            'n' : 5,
            'response_length': 300,
            'temperature': 0.75,
            'top_p': 1,
            'frequency_penalty': 0.4,
            'presence_penalty': 0.4,
            'stop_seq' : [],
        }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)


    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations.extend(t_gens)

    
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
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            # n_gen is the value that core sends to us referring to how many outputs they want to be displayed
            self.filter_generations_dict = {
                'offer': self.performance_generations_dict_list[:no_of_outputs]
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
    #     # "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
    #     "interest_keyword": "Pizza",
    #     "bu_name": "Swiggy",
    #     "benefit_used": "Gluten free",
    #     "n_generations": 5,
    #     "offer_used": "2.3% Off"
    # }

    # gens, rej_gens = HeadlineOffer().run(input_dict=id)
    # print(gens)

    id1 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9",
        "offer_used" : "free"
    }

    id2 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "276cb088-ce1a-42f6-9ec7-867ee22ef70f",
        "offer_used" : "free"
    }

    id3 = {
        "bu_detail": "Semrush is an all-in-one tool suite for improving online visibility and discovering marketing insights. The tools and reports can help marketers with the following services: SEO, PPC, SMM, Keyword Research, Competitive Research, PR, Content Marketing, Marketing Insights, and Campaign Management.\n",
        "reference_headline": "Research Your Competitors,The Ultimate 20-in-1 SEO Tool,{KeyWord Semrush SEO Tools}",
        "interest_keyword": "local",
        "bu_name": "Semrush",
        "benefit_used": "free",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_",
        "offer_used" : "free"
    }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineOffer().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['offer']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(len(output),'\n')
        print(output)
