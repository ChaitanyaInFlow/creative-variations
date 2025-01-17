import sys
import traceback
import logging
import os
import yaml
from ds.lever import Lever

from ds.scripts.detect_language import detect_language


class ListicleParaphrase(Lever):
    
    # Lever has support_dict, prompt_templete, self.nlg_parameters, min_length
    @Lever.log_generate
    def generate(self) -> None:
        
        additional_instructions, replacement_instructions = '', ''
        brand_id = self.input_dict.get('brand_id', '')
        compliance_file_path = 'ds/process/brand_specific/' + str(brand_id) + '.yaml'
        if os.path.exists(compliance_file_path):
            with open(compliance_file_path, "r") as f:
                data = yaml.safe_load(f) 
            additional_instructions = data.get('additional_instructions')
            replacement_instructions = data.get('replacement_instructions')

        self.input_dict['language'] = detect_language(self.input_dict['reference_listicle'])
           
        self.prompt = [
            {
                "role": "system", 
                "content": f'''You are a helpful digital marketing assistant. Write one Ad in points from the Brand Info and Reference Ad.

Follow the Examples.

{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''} '''},
            {
                "role": "user", 
                "content": f'''Example 1
Brand Info: CoverWallet makes it easy for businesses to understand, buy and manage insurance. All online, in minutes. We make it simple, convenient, and fast for you to get the coverage you need at the right price.
Reference Ad:
🔐 Secure your business
📝 Customizable options
👌 Easy online setup
📈 Affordable rates
😌 Hassle-free claims
###
The Ad must be in English.

Ad:
🔐 Protection against unforeseen risks
📝 Coverage tailored to your business
👌 Streamlined online process
📈 Competitive rates
😌 Timely resolution of claims

Example 2
Brand Info: HelloFresh is a food subscription company that sends pre-portioned ingredients to users doorstep each week. It enables anyone to cook. Quick and healthy meals designed by nutritionists and chefs. Enjoy wholesome home-cooked meals with no planning.
Reference Ad:
🥗 Keto Meals at $4/meal
🥗 fast delivery in 15 minutes
🥗 designed by nutritionists
🥗 no planning required
🥗 Order now on HelloFresh
###
The Ad must be in English.

Ad:
🥗 Super healthy Keto meals at $4
🥗 Wholesome Home-Cooked Meals in 15 minutes
🥗 Nutritionists' Recipes. Delivered.
🥗 Meal Prep Has Never Been Easier
🥗 Get Healthy with HelloFresh! 

Example 3
Brand Info: {self.input_dict['bu_detail']}
Reference Ad:
{self.input_dict['reference_listicle']}
###
The Ad must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}

Ad:
'''
        }]
   
        self.nlg_parameters = {"n": 5,
            "top_p": 1,
            "temperature": 1,
            "response_length": 500,
            "presence_penalty": 1,
            "frequency_penalty": 1.5}

        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
       

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = self.nlg_generations_list

    
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(
            title_case=False, exclude_exclamation=False, ending_exclusions='')
        self.post_process_list = []
        for generation in self.extracted_generations:
            t_generation = post_process_obj.run(generation, self.input_dict)
            self.post_process_list.append(t_generation)
        self.log_json['post_process_list'] = self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:            
        filter_obj = self.filter_generations_class(
            max_length=max(len(self.input_dict['reference_listicle']), 250),
            min_length=50,
            threshold=84,
            similar_to_reference_threshold=75)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list,
            reference_ad=self.input_dict['reference_listicle'],
            input_dict=self.input_dict,
            check_english=False)
        self.log_json['filtered_generations'] = self.filtered_list
        # cluster_text_obj = self.cluster_text_class(threshold=75)
        # self.performance_generations_dict_list, self.log_json['discarded_repetitive_listicle_generations'] = cluster_text_obj.get_unique_sentences(input_assets=self.filtered_list)
            
    @Lever.log_run
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            
            if not self.filtered_list:
                self.filtered_list = ['']

            return self.filtered_list,  self.log_json

        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return [], updated_log_json

if __name__ == '__main__':
#     idi = {
#             "bu_name": "Carsome",
#             "bu_detail": "Carsome is an online car-selling platform that connects customers to used car dealers. The company offers a range of services, including car inspection, ownership transfer, and financing. It also offers a curated selection of cars to individuals who wish to buy pre-owned cars.",
#             "brand_name": "Carsome",
#             "interest_keyword": "Investment",      
#             "reference_headline": "KONFEM LAJU",
#             "reference_primary_text": "Dapat bayaran dalam 24 jam",
#             "reference_listicle": "Dapat bayaran dalam 24 jam",
#             "n_generations": 5
#             }

#     id = {
#             "reference_headline": "You'll wear these daily",
#             "bu_name": "Vuori",
#             "bu_detail": "Vuori is a premium performance apparel brand inspired by the active Coastal California lifestyle. The brand offers apparel that is ethically manufactured and made with durable performance materials.",
#             "brand_name": "Vuori",
#             "interest_keyword": "apparel",
#             "n_generations": 6,
#             "limit": 40,
#             "reference_description": "You'll wear these daily!",
#             "reference_primary_text": "You'll wear these daily.",
#             "additional_reference": "You'll wear these daily!You'll wear these daily.",
#             "language": "English"
#                     }
    
#     id = {
#             "reference_headline": "Choose happiness with Joe & The Juice",
#             "bu_name": "Joe & The Juice",
#             "bu_detail": "Joe & The Juice is a popular Danish chain of juice bars and coffee shops. The company is known for its healthy and affordable juices, shakes, coffee, and sandwiches made with natural and organic ingredients.",
#             "brand_name": "Joe & The Juice",
#             "interest_keyword": "",
#             "n_generations": 6,
#             "limit": 40,
#             "reference_description": "Choose happiness with Joe & The Juice",
#             "reference_primary_text": '''🧃 Fresh pulpy juices
# 🏃🏻 Convenient online ordering & fast delivery
# 🥗 Healthy options available
# 🤯 11% Off on Thursdays. Order now!''',
#             "additional_reference": "Choose happiness with Joe & the Juice! Choose happiness with Joe & the Juice!",
#             "language": "English"
#                     }
    
#     gens, logs = PrimaryTextParaphrase().run(id)
#     print(gens)
#     # print(logs)
#     # Headline(prompt_templete=, support_dict=, )

    id1 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English",
        "reference_listicle": 'Why Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\nGet affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.'
    }

    id2 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English",
        "reference_listicle": 'Why Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\nGet affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.'

    }
    id3 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263__",
        "n_generations" : 6,
        "language": "Spanish",
        "reference_listicle": 'Why Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\nGet affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.'

    }

    ids = [id3]
    gen_list = []

    for id in ids:
        gens, logs = ListicleParaphrase().run(id)
        gen_list.append(gens)

    print("$$$$$$$")
    for gen in gen_list:
        print("\n\n##########\n\n")
        print('\n'.join(gen))
