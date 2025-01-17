import sys
import traceback

import os
import yaml

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


# from ds.process.content_filtering import content_filter_inputs_outputs

import logging

class HeadlineBenefit(Lever):

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
                "content" : f'''You are a helpful digital marketing assistant. Generate 5 Benefit copies for the following Brand and Product Benefit. The Benefit Copies should be extremely creative and Between 20-30 Characters. Include keywords from Product Benefit in generations.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''}'''.strip()
                },
            {
                "role": "user", 
                "content": f'''###
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Interest: Cyber
Product Benefit: Protect your business against Data Breach
Write 5 headlines for the given Product Benefit:
Benefit 1: Safeguard Against Data Breaches
Benefit 2: Cyber Insurance For Data Spill
Benefit 3: Protection Against Data Spill
Benefit 4: Defend Your Business From Leaks
Benefit 5: Secure Your Data From Breach
###
Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Interest: London
Product Benefit: Aesthetic and Luxurious
Write 5 headlines for the given Product Benefit:
Benefit 1: London Style Royal Interiors
Benefit 2: Personalized Luxurious Designs
Benefit 3: Unbeatable Aesthetic Styles
Benefit 4: Inspiring Aesthetic Interiors
Benefit 5: Love London's Rich Aesthetics?
###
Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users' doorstep each week. It enables anyone to cook. Quick and healthy meals are designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Interest: Vegan
Product Benefit: Reduce the risk of heart disease
Write 5 headlines for the given Product Benefit:
Benefit 1: Lower The Risk Of Heart Disease
Benefit 2: Yummy Vegan For Happy Heart
Benefit 3: Fresh Heart-Friendly Meals
Benefit 4: Reduce Your Cholesterol Levels
Benefit 5: Vegan Meals For healthy hearts
###
Brand: {self.input_dict['bu_detail']}
Interest: {self.input_dict['interest_keyword']}
Product Benefit: {self.input_dict['benefit_used']}
Write 6 headlines for the given Product Benefit. All Headlines must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}
Benefit 1:'''
            }]

        self.nlg_parameters = {
            "n" : 3,
            "response_length": 300,
            "temperature": 0.75,
            "top_p": 1,
            "frequency_penalty": 0.8,
            "presence_penalty": 0,
            "stop_seq" : ["###", "Brand:"]
        }

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)



    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = [] 
        for generation in self.nlg_generations_list:
            generation = 'Questions:' + generation
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
            max_length=30)
        # TODO: Add ISF filter
        self.filter_generations_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict['reference_headline'],
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
            logging.debug("Google headline_benefit generate started")
            no_of_outputs = self.input_dict['n_generations']
            self.input_dict['n_generations'] *= 2

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            self.filter_generations_list = {
                'benefit': self.performance_generations_dict_list[:no_of_outputs]
            }

            return self.filter_generations_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return {"benefit":[]}, updated_log_json


if __name__ == '__main__':
    # TODO: add prompt temptlate, params, support dict to csv for google

    pt='''Generate 5 Benefit copies for the following Brand and Product Benefit. The Benefit Copies should be extremely creative and Between 20-30 Characters. Include keywords from Product Benefit in generations.
Brand: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Interest: Cyber
Product Benefit: Protect your business against Data Breach
Benefit 1: Safeguard against Data Breaches
Benefit 2: Cyber Insurance for Data Spill
Benefit 3: Protection Against Data Spill
Benefit 4: Defend Your Business from Leaks
Benefit 5: Secure your Data from Breach
###
Brand: HomeLane is a home interior company that helps homeowners do their home interiors in a personalized and pocket-friendly way. Explore thousands of inspiring interior designs or get a free estimate.
Interest: London
Product Benefit: Aesthetic and Luxurious
Benefit 1: London Style Royal Interiors
Benefit 2: Personalized Luxurious Designs
Benefit 3: Unbeatable Aesthetic Styles
Benefit 4: Inspiring Aesthetic Interiors
Benefit 5: Love London's Rich Aesthetics?
###
Brand: HelloFresh is a food subscription company that sends pre-portioned ingredients to users' doorstep each week. It enables anyone to cook. Quick and healthy meals are designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Interest: Vegan
Product Benefit: Reduce the risk of heart disease
Benefit 1: Lower the Risk of Heart Disease
Benefit 2: Yummy Vegan for Happy Heart
Benefit 3: Fresh Heart-Friendly Meals
Benefit 4: Reduce your Cholesterol Levels
Benefit 5: Vegan Meals for healthy hearts
###
Brand: {self.input_dict['bu_detail']}
Interest: {self.input_dict['interest_keyword']}
Product Benefit: {benefit_used}
Benefit 1:'''
    pp = {
        'engine': 'text-davinci-002',
        'response_length': 256,
        'temperature': 0.75,
        'top_p': 1,
        'frequency_penalty': 0.8,
        'presence_penalty': 0,
        'stop_seq' : ["###", "Brand:"],
    }
    sd = {}

    # id = {
    #     "bu_detail": "SwiGGy delivers yummy food to your doorsteps.",
    #     "reference_headline": "Get tasty food at best prices. Delivered in 20 mins. Choose from 500+ restaurants. $20 Off",
    #     "interest_keyword": "Pizza",
    #     "bu_name": "Swiggy",
    #     "benefit_used": "Gluten free",
    #     "n_generations": 5,
    #     "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9"
    # }

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
        "bu_detail": "MamaEarth allows us Explore best-selling safe, natural, and 100% toxin-free baby and beauty products.",
        "reference_headline": "Udforsk bedst sælgende sikre, naturlige og 100 % toksinfri baby- og skønhedsprodukter fra Mamaearth. fantastiske tilbud. start din toksinfri hud-, hår- og babyplejerejse",
        "interest_keyword": "100% TOKIN-fri",
        "bu_name": "MamaEarth",
        "benefit_used": "beauty products",
        "n_generations": 5,
        "brand_id" : "6cdb2607-6c1f-4de2-b0a2-1e82172eccd9_"
    }

    outputs = []

    # for id in [id1, id2, id3]:
    for id in [id3]:

        gens, rej_gens = HeadlineBenefit().run(input_dict=id)
        outputs.append("\n".join([gen['text'] for gen in gens['benefit']]))
        # print(len(gens['benefit']))

    for output in outputs:
        print("*****************************")
        print(output)

    # print(pt.format(**id))

    # t_p = self.postprocess_class(title_case=False, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True)
    # print(t_p.run('Get an Pizza" Delivered. thesis is best. $55 Off on Swiggy', id))