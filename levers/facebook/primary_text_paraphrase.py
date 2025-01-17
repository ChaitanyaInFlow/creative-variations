import sys
import traceback
import emoji
import re
import logging
import random
import os
import yaml
import copy
import itertools
from ds.lever import Lever

from ds.scripts.detect_language import detect_language
from ds.levers.facebook.primary_text_listicle import ListicleParaphrase


class PrimaryTextParaphrase(Lever):

    def separate_primarytext_and_listicle(self, primarytext):

        def _is_list_element(line):
            listicle_lenght_thres = 120 # 70 characteres

            # if line starts w/ special symbol or emoji and is shorter than threshold
            if len(line) < listicle_lenght_thres \
            and ( emoji.is_emoji(line[0]) or bool(re.search(r'\W', line[0]))):
                return True
            else:
                return False

        def find_number_of_new_lines(primarytext, elements_list):
            # elements_list[0] = ref_primary_text
            # elements_list[1] = listicles
            # elements_list[2] = post_listicle
            if elements_list[1] == []:
                return [1, 1]
            primarytext = primarytext.splitlines()
            primarytext = [line.strip() for line in primarytext]
            elements_list = [[line.strip() for line in element] for element in elements_list]
            # start_indices -> start index of primary_text, listicle, post-listicle respectively
            # end_indices -> end index of primary_text, listicle, post-listicle respectively
            start_indices = [primarytext.index(elements_list[i][0]) if elements_list[i] else '-' for i in range(len(elements_list))]
            end_indices = [primarytext.index(elements_list[i][-1]) if elements_list[i] else '-' for i in range(len(elements_list))]

            # If primarytext exists
            if elements_list[0] != []:
                input_primarytext = primarytext[start_indices[0]:start_indices[1]]
                # getting list of same consecutive elements (looking for '' specifically)
                consecutive_elements_list_0 = [list(x[1]) for x in itertools.groupby(input_primarytext)]
            
            # If all 3 elements exist
            if not any(element == [] for element in elements_list):
                # If primary_text does not contain multiple lines/texts/assets
                if not len(elements_list[0]) > 1:
                    first_new_line = start_indices[1] - start_indices[0]
                else:
                    if end_indices[0] - start_indices[0] > 1:
                        if any('' in asset for asset in consecutive_elements_list_0):
                            first_new_line = len([el for el in consecutive_elements_list_0 if '' in el][0]) + 1
                        else:
                            first_new_line = 1                        
                        second_new_line = start_indices[2] - end_indices[1]
                    else:
                        first_new_line = start_indices[1] - end_indices[0]
                second_new_line = start_indices[2] - end_indices[1]

            # If any one of the element is missing
            else:
                # If listicle element exists
                if elements_list[1] != []:
                    
                    # If listicle pre-text exists and post does not
                    if elements_list[0] != [] and elements_list[2] == []:
                        if any('' in asset for asset in consecutive_elements_list_0):          
                            first_new_line = len([el for el in consecutive_elements_list_0 if '' in el][0]) + 1
                        else:
                            first_new_line = 1
                        second_new_line = 1

                    # Pre-text does not, post does
                    elif elements_list[0] == [] and elements_list[2] != []:
                        first_new_line = 1
                        second_new_line = start_indices[2] - end_indices[1]
                    
                    # Pre-text and post doesn't exist
                    elif elements_list[0] == [] and elements_list[2] == []:
                        first_new_line = 1
                        second_new_line = 1
                
                # If listicle element does not exist
                else:
                    first_new_line = 1
                    second_new_line = 1
            
            # If there are more than 2 lines, use only 2
            if first_new_line > 2:
                first_new_line = 2
            if second_new_line > 2:
                second_new_line = 2

            return [first_new_line, second_new_line]
                
        if (not primarytext) or (not isinstance(primarytext, str)): return '', '', '', [1, 1]

        
        lines_list = [el.strip() for el in primarytext.split('\n') if el.strip()]
        
        listicle_elements = []
        for i, line in enumerate(lines_list):
            # if line starts w/ special symbol or emoji and is shorter than threshold
            if _is_list_element(line):
                # if previous line was also list element
                if i>0 and _is_list_element(lines_list[i-1]):
                    listicle_elements.append(line)
                
                # or next line is list element
                elif i<len(lines_list)-1 and _is_list_element(lines_list[i+1]):
                    listicle_elements.append(line)

        # print('lines:', lines_list)
        # print('listicles:', listicle_elements)
        all_primarytext_elements = []
        
        reference_plain_primarytext_list = []
        for line in lines_list:
            if line not in listicle_elements:
                reference_plain_primarytext_list.append(line)
            else:
                break
                # break when listicle starts
        all_primarytext_elements.append(reference_plain_primarytext_list)
        
        # print(reference_plain_primarytext)
        reference_plain_primarytext = ' '.join(reference_plain_primarytext_list)

        reference_listicle_list = listicle_elements
        all_primarytext_elements.append(reference_listicle_list)
        
        reference_post_listicle_list = [el for el in lines_list if (el not in reference_plain_primarytext) and (el not in reference_listicle_list)]
        all_primarytext_elements.append(reference_post_listicle_list)
        
        reference_listicle = '\n'.join(reference_listicle_list)
        reference_post_listicle = '\n'.join(reference_post_listicle_list)
        
        number_new_lines = find_number_of_new_lines(primarytext, all_primarytext_elements)
        return reference_plain_primarytext, reference_listicle, reference_post_listicle, number_new_lines

    # Lever has support_dict, prompt_templete, self.nlg_parameters, min_length
    @Lever.log_generate
    def generate(self) -> None:
        input_reference_headline = self.input_dict.get('reference_headline','')
        input_reference_description = self.input_dict.get('reference_description','')
        input_additional_reference = ''

        if input_reference_headline:
            if (input_reference_headline[-1] not in ['.', '!', '?']):
                input_reference_headline += '. '
            input_additional_reference += input_reference_headline

        if input_reference_description:
            if (input_reference_description[-1] not in ['.', '!', '?']):
                input_reference_description += '. '
            input_additional_reference += input_reference_description

        self.input_dict['additional_reference'] = input_additional_reference
        
        ## Detect Language
        text = " ".join([self.input_dict['reference_primary_text'], input_additional_reference])
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
            {   "role": "system", 
                "content": f'''You are a helpful digital marketing assistant for writing creative Facebook ad Primary Text for the given Brand Info, Reference Primary Text and Additional Reference
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''} '''},
            {
                "role": "user", 
                "content": f'''###
Example 1
Brand Info: Allbirds, Inc. is a New Zealand-American company that sells footwear and apparel. They crafted a revolutionary wool fabric made specifically for footwear. Products include Shoes, Apparel, Accessories.
Reference Primary Text: Comfy? Check. Planet-friendly? Check. Everyday styles for any kind of day.
Additional Reference: Free Shipping + Free Returns. Made to get outside, move, and be ridiculously comfortable.

Write 5 Variations of the Reference Primary Text using context from the Brand Info and Additional Reference. All Variations must be less than 125 characters.

Variation 1: Allbirds shoes are comfortable and planet-friendly. Get free shipping and returns on your purchase!
Variation 2: Get free shipping + free returns on Allbirds shoes, apparel, and accessories. Shop now!
Variation 3: Get outside and move in comfort with Allbirds. Shop now!
Variation 4: Allbirds has your everyday style needs covered. Check out our latest arrivals!
Variation 5: Allbirds shoes are made for any kind of day. Shop now and get free shipping + free returns!

###
Example 2
Brand Info: HelloFresh is the first global carbon-neutral meal kit company, supporting global and local environmentally-friendly projects you care about.
Reference Primary Text: Stuck on what to have for dinner? Say hello to tasty dishes and farm-fresh ingredients, delivered right to your door!
Additional Reference: Rethink every meal, and save! Come Back for $150 Off. 

Write 5 Variations of the Reference Primary Text using context from the Brand Info and Additional Reference. All Variations must be less than 125 characters.

Variation 1: HelloFresh delivers delicious, farm-fresh ingredients right to your door. Come back for $150 off!
Variation 2: Tired of the same old dinner options? HelloFresh delivers tasty, new dishes every week!
Variation 3: Get out of your dinner rut with HelloFresh. Tasty recipes and fresh ingredients, delivered to your door.
Variation 4: HelloFresh is the first carbon-neutral meal kit company. Try us out today and save $150!
Variation 5: Rethink every meal with HelloFresh. Farm-fresh ingredients and delicious recipes, delivered to you.

###
Example 3
Brand Info: {self.input_dict['bu_detail']}
Reference Primary Text: {self.input_dict['reference_primary_text']}
Additional Reference: {self.input_dict['additional_reference']}

Write 7 Variations of the Reference Primary Text using context from the Brand Info and Additional Reference. All Variations must be less than 125 characters.
All Variations must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}

Variation 1:'''
            }]

        self.nlg_parameters = {
            "n": 5,
            "top_p": 1,
            "temperature": 1,
            "response_length": 500,
            "presence_penalty": 1.35,
            "frequency_penalty": 0.85
        }
        if self.input_dict['language'] != 'English':
            self.nlg_parameters['temperature'] = 1
            self.nlg_parameters['presence_penalty'] = 0
            self.nlg_parameters['frequency_penalty'] = 0
            
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        # Strip Generations starting with Variant 1, Variant 2, etc or Variation 1, Variation 2, etc.
        for generation_str in self.nlg_generations_list:
            generation_list = generation_str.split('\n')

            stripped_generations_list = []
            for generation in generation_list:
                generation = generation.strip()
                if generation.lower().startswith('varia'):
                    stripped_generation = ' '.join(generation.split()[2:])
                    stripped_generations_list.append(stripped_generation)

            self.extracted_generations += stripped_generations_list

    
    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(
                title_case=False, exclude_exclamation=False, ending_exclusions='')
            self.post_process_list = []
            for generation in self.extracted_generations:
                t_generation = post_process_obj.run(generation, self.input_dict)
                self.post_process_list.append(t_generation)
        else:
            self.post_process_list = self.extracted_generations
        self.log_json['post_process_list'] = self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=max(len(self.input_dict['reference_primary_text']), 250),
            min_length=15,
            threshold=84,
            similar_to_reference_threshold=85)
        self.filtered_list, self.log_json['discard_filter_generations'] = filter_obj.run(
            self.post_process_list,
            reference_ad=self.input_dict['reference_primary_text'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        self.log_json['filtered_generations'] = self.filtered_list
        
        score_performance_obj = self.score_performance_class(brand_name=self.input_dict['bu_name'])
        self.performance_list = score_performance_obj.get_performance_scores(generations_list=self.filtered_list)
        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_assets_by_filter_key(input_assets=self.performance_list)

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.input_dict['original_reference_primary_text'] = self.input_dict['reference_primary_text']

            reference_primary_text, reference_listicle, reference_post_listicle, number_of_new_lines = \
                self.separate_primarytext_and_listicle(self.input_dict['reference_primary_text'])

            self.input_dict['reference_primary_text'] = reference_primary_text
            self.input_dict['reference_listicle'] = reference_listicle
            self.input_dict['reference_post_listicle'] = reference_post_listicle

            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            final_outputs_needed = input_dict['n_generations']
            final_output = self.performance_generations_dict_list[:final_outputs_needed]
            
            if reference_listicle and self.input_dict['language'] == 'English':
                listicle_obj = ListicleParaphrase()
                self.top_variation_listicles, listicle_logs = listicle_obj.run(self.input_dict)

                self.input_dict['generated_listicles'] = self.top_variation_listicles if self.top_variation_listicles else ['']
            else:
                self.input_dict['generated_listicles'] = ['']

            final_output_dict = []
            for generations in final_output:
                generations['text'] += ('\n' * number_of_new_lines[0] + random.choice(self.input_dict['generated_listicles']) \
                                            + '\n' * number_of_new_lines[1] + self.input_dict['reference_post_listicle'])
                generations['text'] = generations['text'].strip()
                final_output_dict.append(generations)
            self.log_json['final_output'] = final_output_dict
            
            return final_output_dict, self.log_json

        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return [], updated_log_json

if __name__ == '__main__':
    
    id1 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        # "reference_primary_text": '''Join healthcare professionals, technology providers and government representatives as we look at the transformation of healthcare across the region.''',
        "reference_primary_text": '''Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\n\nWhy Hims for mental health care?\n✅ No office visits or pharmacy trips required \n✅ Vetted, licensed healthcare providers \n✅ Free shipping from licensed US pharmacies, if prescribed\n✅ Unlimited ongoing check-ins\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,
        "language": "English"
    }

    id2 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  \n\n\n\nWhy Hims for mental health care?\n\n✅ No office visits or pharmacy trips required \n✅ Vetted, licensed healthcare providers \n✅ Free shipping from licensed US pharmacies, if prescribed\n✅ Unlimited ongoing check-ins\n\n\n*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263_",
        "n_generations" : 6,
        "language": "English"
    }
    
    id3 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  

✅ No office visits or pharmacy trips required 
✅ Vetted, licensed healthcare providers 
✅ Free shipping from licensed US pharmacies, if prescribed
✅ Unlimited ongoing check-ins

*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.
''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263_",
        "n_generations" : 6,
        "language": "English"
    }

    
    id4 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''Get affordable prescription medication for anxiety and depression from a licensed healthcare provider.  

Whty eonwobnosbcobe?
✅ No office visits or pharmacy trips required 
✅ Vetted, licensed healthcare providers 
✅ Free shipping from licensed US pharmacies, if prescribed
✅ Unlimited ongoing check-ins



*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.
''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263_",
        "n_generations" : 6,
        "language": "English"
    }


    
    id5 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''
        
        
✅ No office visits or pharmacy trips required 
✅ Vetted, licensed healthcare providers 
✅ Free shipping from licensed US pharmacies, if prescribed
✅ Unlimited ongoing check-ins

*Asynchronous visits not available in all states. Prescription products required an online consultation with a healthcare provider who will determine if a prescription is appropriate. Restrictions apply. See website for full details and important safety information. Controlled substances such as Xanax and Adderall are not available through our platform.
''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263_",
        "n_generations" : 6,
        "language": "English"
    }

    id6 = {
        "bu_detail" : '''HIMSS is a healthcare research and advisory firm that specializes in guidance and market intelligence. It has various models that include outpatient electronic medical record adoption, infrastructure adoption, analytics maturity adoption and certified consultant program models.''',
        "reference_primary_text": '''
        
        
✅ No office visits or pharmacy trips required 
✅ Vetted, licensed healthcare providers 
✅ Free shipping from licensed US pharmacies, if prescribed
✅ Unlimited ongoing check-ins''',
        "reference_headline": 'Manifest transformative health tech at HIMSS23.',
        "reference_description": '',
        "brand_name" : 'hims',
        'bu_name': 'hims',
        'interest_keyword': 'Mental Health',
        # "brand_id" : "f226bd37-db7c-4908-b992-907ff441bcb7_",
        "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6
        # "language": "English"
    }
    id3 = {
        "bu_name": "Claro Shop",
        "brand_id" : "112811d5-d614-40ce-bcec-8d3945262e2f",
        # "brand_id" : "a31704be-7b6d-442a-bf94-bf2bc7084263",
        "n_generations" : 6,

        "bu_detail": "Claro Shop is an e-commerce website that sells electronic gadgets, kitchen appliances, furniture, apparel, footwear, and gym utilities.", 
        "brand_name": "Claro Shop", 
        "interest_keyword": "e-commerce",
          "reference_headline": "¡Solicítalo ahora!", 
          "reference_description": "¡Solicítalo ahora!", 
          "reference_primary_text": "Estrena millones de productos este Hot Sale a meses, sin tarjeta, sin aval con tu Crédito Claro Shop :fire::fire: Disfruta 15% de descuento adicional en tu primer compra + hasta 24 meses :star-struck:"
    }

    id4 = {
"brand_id": "3e2e",
"n_generations" : 6,
"bu_name": "Carsome",
"bu_detail": "Carsome is an online car-selling platform that connects customers to used car dealers. The company offers a range of services, including car inspection, ownership transfer, and financing. It also offers a curated selection of cars to individuals who wish to buy pre-owned cars.",
"brand_name": "Carsome",
"interest_keyword": "Cars",
"reference_primary_text": "Vender un auto es fácil y seguro con CARSOME. Reserve una inspección GRATIS ahora.",
"reference_headline" : "",
"reference_description" :""
}
    

    # ids = [id1, id2]
    ids = [id3]
    # ids = [id6]
    s = 0

    for idx, id in enumerate(ids):
        gens, logs = PrimaryTextParaphrase().run(id)

        print(gens)
        
        for gen in gens:
            print("*********************")
            print(gen['text'])
            print("*********************")
            print()
            print()