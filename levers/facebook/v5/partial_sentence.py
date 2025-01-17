
#Importing all the python libraries
import sys
import traceback
import re
import os
import yaml

import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

from ds.lever import Lever
from ds.scripts.detect_language import detect_language


class PartialSentenceLever(Lever):

    def preprocess(self) -> None:

        self.text_list = []
        self.min_char_list = []
        self.max_char_list = []

        for key in self.layer_dict:
            self.text_list.append(self.layer_dict[key]["layer_text"])
            self.min_char_list.append(self.layer_dict[key]["min_char_limit"])
            self.max_char_list.append(self.layer_dict[key]["max_char_limit"])

        self.min_length = sum(self.min_char_list)
        self.max_length = sum(self.max_char_list)
        
        self.input_dict["min_limit"] = int( self.min_length/5 )
        self.input_dict["max_limit"] = int( (self.max_length/5) + (len(self.text_list) - 1 ) )

        self.input_layer_text = " [SEP] ".join(self.text_list)

        headline = self.input_dict['reference_headline']
        description = self.input_dict['reference_description']
        primary = self.input_dict['reference_primary_text']
        primary = '. '.join(primary.split('\n'))

        ad_texts = [headline, description, primary]
        reference = ''
        for adtext in ad_texts:
            if(adtext):
                if(adtext[-1] not in ['.','!','?',',']):
                    adtext += '. '
                reference += adtext

        self.input_dict['reference'] = reference

        
    @Lever.log_generate
    def generate(self) -> None:
        self.input_dict['image_text'] = self.input_layer_text
        self.input_dict['language'] = detect_language(" ".join([self.input_dict['image_text'] , self.input_dict['reference']]))

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
                "role": "system", 
                "content": f'''You are a helpful digital marketing assistant for writing creative Facebook ad Image Text.

Create Variations of the Image Text using information from the Image Text and Reference.

Follow the Examples.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''} '''},
            {
                "role": "user", 
                "content": f'''###
Example 1

Reference: Get the best deal today. Style meets comfort. The pant that pairs with every occasion. Find your perfect length in size XS - 3X
Image Text: The flex you need [SEP] in the fabric you love

Image Text consists of Separator [SEP]

Create 3 Variations of the Image Text using information from the Image Text and Reference. Each Variation must be less than 12 words. 
Each Variation must have the Separator [SEP] at the appropriate position after a phrase. All Variations must have the same number of Separators as in the Image Text. 

Variation 1: Get The Perfect Look [SEP] With Comfort & Flexibility
Variation 2: Style Meets Comfort [SEP] In Our Versatile Pants
Variation 3: Find The Perfect Fit [SEP] With Flexible Sizing

###
Example 2

Reference: Personalized treatment, entirely online. Alcohol dependence is a medical condition. Monument provides a medical solution. Work with expert therapists and physicians to change your drinking habits for good. You deserve to feel supported, empowered, and secure.
Image Text: If You Are Ready to Change [SEP] Your Relationship With Alcohol [SEP] Monument is here to help

Image Text consists of Separator [SEP]

Create 4 Variations of the Image Text using information from the Image Text and Reference. Each Variation must be less than 16 words. 
Each Variation must have the Separator [SEP] at the appropriate position after a phrase. All Variations must have the same number of Separators as in the Image Text. 

Variation 1: Work With Expert Therapists [SEP] To Help You Quit Drinking [SEP] And Improve Your Life
Variation 2: Feel Empowered To Change [SEP] Your Relationship With Alcohol [SEP] With Experts At Monument
Variation 3: Get Medical Treatment [SEP] With Expert Therapists Online [SEP] For Alcohol Addiction
Variation 4: Work Toward Sobriety [SEP] With Expert Therapists & Physicians [SEP] From The Comfort of Home

###
Example 3

Reference: {self.input_dict['reference']}
Image Text: {self.input_dict['image_text']}

Image Text consists of Separator [SEP]

Create 6 Variations of the Image Text using information from the Image Text and Reference. Each Variation must be less than {self.input_dict['max_limit']} words. 
Each Variation must have the Separator [SEP] at the appropriate position after a phrase. All Variations must have the same number of Separators as in the Image Text. 
All Variations must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}

Variation 1:'''
            }]

        self.nlg_parameters = {
            "n": 3, 
            "top_p": 1,
            "temperature": 1, 
            "response_length": 500, 
            "presence_penalty": 1, 
            "frequency_penalty": 0.5
            }
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations_list = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for index, generation in enumerate(generation_list):
                replace_list = ['Variation ' + str(index + 1) + ':' , 'variation ' + str(index + 1) + ':' , 'Variation ' + str(index + 1) + ' :','variation ' + str(index + 1) + ' :' ]
                for text in replace_list:
                    generation = re.sub(text, '', generation)
                generation_list[index] = generation
            self.extracted_generations_list += generation_list
        return 
    
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=False, ending_exclusions='.!', exclude_domain=True, exclude_phone_number=True, match_capitalization_with_input=True)
        
        self.post_process_list = []
        for generation in self.extracted_generations_list:
            self.post_process_list.append(post_process_obj.run(generation, reference_input = self.input_dict['image_text'], separator='[SEP]'))
        return 

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        extra_length = len(" [SEP] ") * (len(self.layer_dict) - 1 )
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=self.max_length + extra_length, 
            threshold=95)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict["image_text"],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        cluster_text_obj = self.cluster_text_class(threshold=95)
        self.filter_generations_list, self.log_json['discarded_similar_generations'] = cluster_text_obj.get_unique_sentences(input_assets=self.filtered_list)
        return 

    def remove_separator(self):
        self.removed_sep_list = []
        for generation in self.filter_generations_list:
            # print(generation)
            sep_count = generation.count("[SEP]")
            if sep_count != (len(self.layer_dict) - 1 ): 
                continue
                   
            gen_split = generation.split("[SEP]")
            flag = True 
            for index, gen in enumerate(gen_split):
                if (len(gen) <= self.min_char_list[index]):
                    flag = False
                if (len(gen) >= self.max_char_list[index]):
                    flag = False
            if(flag):
                self.removed_sep_list.append(" * ".join(gen_split))     
        return 

    def output_formatting(self) -> None:
        self.output_list=[]                
        output_dict={}
        output_dict['layer_name'] = []
        output_dict['original_text'] = []
        output_dict['layer_text'] = self.removed_sep_list
        if "frame_name" in self.layer_dict['1'].keys():
            output_dict['frame_name'] = []
        for key in self.layer_dict:          
            output_dict['layer_name'].append(self.layer_dict[key]['layer_name'])
            output_dict['original_text'].append(self.layer_dict[key]['layer_text'])
            if "frame_name" in self.layer_dict[key].keys():
                output_dict['frame_name'].append(self.layer_dict[key]['frame_name'])
        self.output_list.append(output_dict)
        return 

    def run(self, input_dict):
        try:
            self.input_dict=input_dict
            if "image_layer_data" in input_dict:
                self.layer_dict = input_dict['image_layer_data']
            elif "video_layer_data" in input_dict:
                self.layer_dict = input_dict["video_layer_data"]
            else:
                raise Exception("Could not find image_layer_data/video_layer_data field in input_dict in PartialSentenceLever")
            
            self.preprocess()
            logging.debug("fb partial_sentence: preprocess completed")
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            self.remove_separator()
            logging.debug("fb partial_sentence: remove_separator Completed")
            self.output_formatting()
            logging.debug("fb partial_sentence: partial_sentence lever operation Completed")
            
            return self.output_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return [], updated_log_json 
    

if __name__ == '__main__':

#     input_dict = {
#     "bu_name": "swiggy Ginnie",
#     "bu_detail": "Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.",
#     "brand_name": "swiggy",
#     "interest_keyword": "burger",
#     "brand_id": "sample_brand_id",
#     "reference_headline": "Order now to get 30% off",
#     "reference_description": "Delivered at your doorsteps",
#     "reference_primary_text": "Get 30% off on your first order, \n\n delivered to your doorsteps with Swiggy Ginnie",
#     "image_layer_data": {
#         "1": {
#             "is_partial_sentence": True,
#             "is_sentence_related": False,
#             "layer_name": "layer_1",
#             "layer_text": "Now is the time to start",
#             "max_char_limit": 20,
#             "min_char_limit": 10,
#             "related_to": "layer_2"
#         },
#         "2": {
#             "is_partial_sentence": True,
#             "is_sentence_related": False,
#             "layer_name": "layer_2",
#             "layer_text": "our medical jouney",
#             "max_char_limit": 20,
#             "min_char_limit": 10,
#             "related_to": "END"
#         }
#     }
# }

#     input_dict = {'bu_name': 'Klar Credit',
#  'bu_detail': 'Klar is Mexico’s leading online bank, giving people an easy-to-use & commission-free banking experience. Klar gives its users a credit line of up to 10,000 pesos without a credit score. Offering an interest rate of under 10 percent',
#  'brand_name': 'Klar',
#  'interest_keyword': 'Credit, Loan',
#  'image_layer_data': {'1': {'layer_name': 'Text 1',
#    'layer_text': 'The credit card',
#    'related_to': 'START',
#    'max_char_limit': 21,
#    'min_char_limit': 15,
#    'is_partial_sentence': True,
#    'is_sentence_related': True},
#   '2': {'layer_name': 'Text 2',
#    'layer_text': 'no annuity',
#    'related_to': 'Text 1',
#    'max_char_limit': 13,
#    'min_char_limit': 8,
#    'is_partial_sentence': True,
#    'is_sentence_related': True}},
#  'reference_headline': 'Crédito inmediato',
#  'reference_description': '',
#  'reference_primary_text': 'Klar te ofrece una línea de crédito rápida y sin letras chiquitas.'}
#     gens, logs = PartialSentenceLever().run(input_dict)
#     print(gens)

    id1 = {'image_layer_data': 
              {'1': {'layer_name': 'Text 1', 'layer_text': 'TREAT ANXIETY', 'related_to': 'Text 2', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}, 
               '2': {'layer_name': 'Text 2', 'layer_text': 'WITHOUT INSURANCE', 'related_to': 'END', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}}, 
               'reference_headline': 'Get started today', 
               'reference_description': 'We‚Äôre here to help when you‚Äôre ready', 
               'reference_primary_text': 'Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\nWhy Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'bu_name': 'Hims', 
               'brand_id': 'a31704be-7b6d-442a-bf94-bf2bc7084263', 
               'bu_detail': "Hims is a one-stop telehealth service for men's wellness and care, providing treatment options for hair loss, ED & more. They sell prescription and over-the-counter drugs online and personal care products.\n\n\n\n\n\n", 
               'brand_name': 'Hims and Hers', 
               'interest_keyword': "Men's health and wellness", 
               'n_generations': 12, 
               'min_limit': 2, 
               'max_limit': 19, 
               'reference': 'Get started today. We‚Äôre here to help when you‚Äôre ready. Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  . . Why Hims for mental health care?. ‚úÖ No office visits or pharmacy trips required . ‚úÖ Vetted, licensed healthcare providers . ‚úÖ Free shipping from licensed US pharmacies, if prescribed. ‚úÖ Unlimited ongoing check-ins. . *Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'image_text': 'TREAT ANXIETY [SEP] WITHOUT INSURANCE'}
    
    id2 = {'image_layer_data': 
              {'1': {'layer_name': 'Text 1', 'layer_text': 'treat anxiety', 'related_to': 'Text 2', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}, 
               '2': {'layer_name': 'Text 2', 'layer_text': 'without insurance', 'related_to': 'END', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}}, 
               'reference_headline': 'Get started today', 
               'reference_description': 'We‚Äôre here to help when you‚Äôre ready', 
               'reference_primary_text': 'Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\nWhy Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'bu_name': 'Hims', 
               'brand_id': 'f226bd37-db7c-4908-b992-907ff441bcb7', 
               'bu_detail': "Hims is a one-stop telehealth service for men's wellness and care, providing treatment options for hair loss, ED & more. They sell prescription and over-the-counter drugs online and personal care products.\n\n\n\n\n\n", 
               'brand_name': 'Hims and Hers', 
               'interest_keyword': "Men's health and wellness", 
               'n_generations': 12, 
               'min_limit': 2, 
               'max_limit': 19, 
               'reference': 'Get started today. We‚Äôre here to help when you‚Äôre ready. Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  . . Why Hims for mental health care?. ‚úÖ No office visits or pharmacy trips required . ‚úÖ Vetted, licensed healthcare providers . ‚úÖ Free shipping from licensed US pharmacies, if prescribed. ‚úÖ Unlimited ongoing check-ins. . *Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'image_text': 'treat anxiety [SEP] without insurance'}
    id3 = {'image_layer_data': 
              {'1': {'layer_name': 'Text 1', 'layer_text': 'Treat Anxiety', 'related_to': 'Text 2', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}, 
               '2': {'layer_name': 'Text 2', 'layer_text': 'Without Insurance', 'related_to': 'END', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}}, 
               'reference_headline': 'Get started today', 
               'reference_description': 'We‚Äôre here to help when you‚Äôre ready', 
               'reference_primary_text': 'Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\nWhy Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'bu_name': 'Hims', 
               'brand_id': 'f226bd37-db7c-4908-b992-907ff441bcb7_', 
               'bu_detail': "Hims is a one-stop telehealth service for men's wellness and care, providing treatment options for hair loss, ED & more. They sell prescription and over-the-counter drugs online and personal care products.\n\n\n\n\n\n", 
               'brand_name': 'Hims and Hers', 
               'interest_keyword': "Men's health and wellness", 
               'n_generations': 12,
               'min_limit': 2, 
               'max_limit': 19, 
               'reference': 'Get started today. We‚Äôre here to help when you‚Äôre ready. Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  . . Why Hims for mental health care?. ‚úÖ No office visits or pharmacy trips required . ‚úÖ Vetted, licensed healthcare providers . ‚úÖ Free shipping from licensed US pharmacies, if prescribed. ‚úÖ Unlimited ongoing check-ins. . *Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'image_text': 'Treat Anxiety [SEP] Without Insurance'}
    
    id4 = {'image_layer_data': 
              {'1': {'layer_name': 'Text 1', 'layer_text': 'Treat anxiety', 'related_to': 'Text 2', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}, 
               '2': {'layer_name': 'Text 2', 'layer_text': 'without insurance', 'related_to': 'END', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}}, 
               'reference_headline': 'Get started today', 
               'reference_description': 'We‚Äôre here to help when you‚Äôre ready', 
               'reference_primary_text': 'Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\nWhy Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'bu_name': 'Hims', 
               'brand_id': 'f226bd37-db7c-4908-b992-907ff441bcb7_', 
               'bu_detail': "Hims is a one-stop telehealth service for men's wellness and care, providing treatment options for hair loss, ED & more. They sell prescription and over-the-counter drugs online and personal care products.\n\n\n\n\n\n", 
               'brand_name': 'Hims and Hers', 
               'interest_keyword': "Men's health and wellness", 
               'n_generations': 12,
               'min_limit': 2, 
               'max_limit': 19, 
               'reference': 'Get started today. We‚Äôre here to help when you‚Äôre ready. Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  . . Why Hims for mental health care?. ‚úÖ No office visits or pharmacy trips required . ‚úÖ Vetted, licensed healthcare providers . ‚úÖ Free shipping from licensed US pharmacies, if prescribed. ‚úÖ Unlimited ongoing check-ins. . *Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'image_text': 'Treat Anxiety [SEP] Without Insurance'}

    id5 = {'image_layer_data': 
              {'1': {'layer_name': 'Text 1', 'layer_text': 'treat Anxiety', 'related_to': 'Text 2', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}, 
               '2': {'layer_name': 'Text 2', 'layer_text': 'Without insurance', 'related_to': 'END', 'max_char_limit': 20, 'min_char_limit': 10, 'is_partial_sentence': True, 'is_sentence_related': True}}, 
               'reference_headline': 'Get started today', 
               'reference_description': 'We‚Äôre here to help when you‚Äôre ready', 
               'reference_primary_text': 'Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\nWhy Hims for mental health care?\n‚úÖ No office visits or pharmacy trips required \n‚úÖ Vetted, licensed healthcare providers \n‚úÖ Free shipping from licensed US pharmacies, if prescribed\n‚úÖ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'bu_name': 'Hims', 
               'brand_id': 'f226bd37-db7c-4908-b992-907ff441bcb7_', 
               'bu_detail': "Hims is a one-stop telehealth service for men's wellness and care, providing treatment options for hair loss, ED & more. They sell prescription and over-the-counter drugs online and personal care products.\n\n\n\n\n\n", 
               'brand_name': 'Hims and Hers', 
               'interest_keyword': "Men's health and wellness", 
               'n_generations': 12,
               'min_limit': 2, 
               'max_limit': 19, 
               'reference': 'Get started today. We‚Äôre here to help when you‚Äôre ready. Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  . . Why Hims for mental health care?. ‚úÖ No office visits or pharmacy trips required . ‚úÖ Vetted, licensed healthcare providers . ‚úÖ Free shipping from licensed US pharmacies, if prescribed. ‚úÖ Unlimited ongoing check-ins. . *Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.', 
               'image_text': 'Treat Anxiety [SEP] Without Insurance'}
    
    
    id9 = {
        "bu_name": "Claro Shop",
        "brand_id" : "112811d5-d614-40ce-bcec-8d3945262e2f",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,

        "bu_detail": "Claro Shop is an e-commerce website that sells electronic gadgets, kitchen appliances, furniture, apparel, footwear, and gym utilities.", 
        "brand_name": "Claro Shop", 
        "interest_keyword": "e-commerce",
          "reference_headline": "¡Solicítalo ahora!", 
          "reference_description": "¡Solicítalo ahora!", 
          "reference_primary_text": "Estrena millones de productos este Hot Sale a meses, sin tarjeta, sin aval con tu Crédito Claro Shop :fire::fire: Disfruta 15% de descuento adicional en tu primer compra + hasta 24 meses :star-struck:",
        "min_limit": 12, 
        "max_limit": 60, 
        "image_layer_data": {
            '1': {"layer_name": "Text 1", "layer_text": "Compra millones de productos", "related_to": "Text 2", "max_char_limit": 28, "min_char_limit": 15, "is_partial_sentence": True, "is_sentence_related": True}, 
            '2': {"layer_name": "Text 2", "layer_text": "con tu Crédito Claro shop", "related_to": "END", "max_char_limit": 28, "min_char_limit": 15, "is_partial_sentence": True, "is_sentence_related": True}},
               'image_text': 'Compra millones de productos [SEP] con tu Crédito Claro shop'}
    

    ids = [id9]
    # ids = [id5]
    gen_list = []

    for id in ids:
        gens, logs = PartialSentenceLever().run(id)
        gen_list.append(gens)
    print("$$$")
    for gen in gen_list:
        print("\n\n######\n\n")
        print(gen)
