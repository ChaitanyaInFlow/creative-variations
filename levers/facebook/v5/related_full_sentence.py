

#Importing all the python libraries
import sys
import re
import traceback
import os
import yaml
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

class FullSentenceParaphrasingLever(Lever):

    def preprocess(self) -> None:
        self.min_length = self.layer_dict["min_char_limit"] 
        self.max_length = self.layer_dict["max_char_limit"]
        
        self.input_dict["min_limit"] = int(self.min_length/5)
        self.input_dict["max_limit"] = int((self.max_length/5) + 1)

        headline = self.input_dict['reference_headline']
        description = self.input_dict['reference_description']
        primary = self.input_dict['reference_primary_text']

        ad_texts = [headline, description, primary]
        reference = ''

        for adtext in ad_texts:
            if(adtext):
                if(adtext[-1] not in ['.','!','?',',']):
                    adtext += '. '
                reference += adtext

        self.input_dict['reference'] = reference
        self.log_json['reference'] = self.input_dict['reference']
        return

    @Lever.log_generate
    def generate(self) -> None:
        self.input_dict['image_text'] = self.layer_dict['layer_text']
        self.input_dict['language'] = detect_language(self.input_dict['image_text'] + " " + self.input_dict['reference'])

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
                "content": f'''You are a helpful digital marketing assistant for writing creative Facebook ad Image Text for the given Image Text and Reference.

Create Paraphrased Variations of the Image Text.

Follow the Examples.
{'Make sure Variations follow the following compliance guidelines.' + replacement_instructions if replacement_instructions else ''} '''},
                {"role": "user",
                "content": f'''###
Example 1

Reference: Get meals for only $3.99. Did you hear? HelloFresh is cheaper than grocery shopping (and no checkout lines either!)
Image Text: Cheaper than Grocery shopping

Create 3 Paraphrased Variations of the Image Text. Each Variation must be less than 7 words. 

Variation 1: More Affordable Than The Grocery Store
Variation 2: Save Money On Groceries
Variation 3: Less Expensive Than Grocery Shopping

###
Example 2

Reference: Find Your Advisor Match | SmartAsset.com. Find Yourself a Financial Advisor that's Legally Obligated to Serve In Your Best Interest
Image Text: How much do you have saved for your retirement ?

Create 4 Paraphrased Variations of the Image Text. Each Variation must be less than 10 words. 

Variation 1: How Much Money Have You Set Aside For Retirement? 
Variation 2: What Are Your Retirement Savings Like? 
Variation 3: Do You Have A Retirement Savings Plan?
Variation 4: Do You Have Enough Saved For Retirement?

###
Example 3

Reference: {self.input_dict['reference']}
Image Text: {self.input_dict['image_text']}

Create 4 Paraphrased Variations of the Image Text. Each Variation must be less than {self.input_dict['max_limit']} words.
All Variations must be in {self.input_dict['language']}.
{'Additional Instructions: ' + additional_instructions if additional_instructions else ''}

Variation 1:'''
            }]

        self.nlg_parameters = {"n": 3, "top_p": 1,
                       "temperature": 1, "response_length": 300, "presence_penalty": 0, "frequency_penalty": 0}

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
            self.post_process_list.append(post_process_obj.run(generation, reference_input = self.input_dict['image_text'], separator=''))
        return

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_pipeline_obj = self.filter_generations_class(
            min_length=self.min_length, 
            max_length=self.max_length, 
            threshold=86)
        self.filter_generations_list, _ = filter_pipeline_obj.run(
            self.post_process_list, 
            self.input_dict["image_text"],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True)
        self.log_json['filtered_generations'] = self.filter_generations_list
        cluster_text_obj = self.cluster_text_class(threshold=86)
        self.performance_generations_dict_list, self.log_json['discarded_low_performance_generations'] = cluster_text_obj.get_unique_sentences(input_assets=self.filter_generations_list)
        return
    
    def output_formatting(self) -> None:
        self.output_list=[]
        output_dict={}
        output_dict['layer_name'] = [self.layer_dict['layer_name']]
        output_dict['layer_text'] = self.filter_generations_list
        output_dict['original_text'] = [self.layer_dict['layer_text']]
        
        if "frame_name" in self.layer_dict.keys():
            output_dict['frame_name'] = [self.layer_dict['frame_name']]
        
        self.output_list.append(output_dict)
        self.log_json['output_list'] = self.output_list
        return

    def run(self, input_dict):
        try:
            self.input_dict=input_dict
            if "image_layer_data" in input_dict:
                self.layer_dict = input_dict['image_layer_data']
            elif "video_layer_data" in input_dict:
                self.layer_dict = input_dict["video_layer_data"]
            else:
                raise Exception("Could not find image_layer_data/video_layer_data field in input_dict in FullSentenceParaphrasingLever")
            
            # Retrieve layer data from nested layer_dict
            self.layer_dict = self.layer_dict.get('1')
            self.preprocess()
            logging.debug("fb related_full_sentence: preprocess completed")
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            self.output_formatting()
            logging.debug("fb related_full_sentence: related_full_sentence lever operation Completed")
            return self.output_list, self.log_json
        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace, "exception":str(exc), "info": self.log_json}
            return [], updated_log_json 


if __name__ == '__main__':

    id1 = {
    "bu_name": "swiggy Ginnie",
    "bu_detail": "Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.",
    "brand_name": "swiggy",
    "interest_keyword": "burger",
    "brand_id": "a31704be-7b6d-442a-bf94-bf2bc7084263",
    "reference_headline": "Order now to get 30% off",
    "reference_description": "Delivered at your doorsteps",
    "reference_primary_text": "Get 30% off on your first order, delivered to your doorsteps with Swiggy Ginnie",
    "image_layer_data": {
        "1": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_1",
            "layer_text": "Now Is The Time To start",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "layer_2"
        },
        "2": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_2",
            "layer_text": "our medical jouney",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "END"
        }
    }
}
    # gens, logs = FullSentenceParaphrasingLever().run(input_dict)
    # print(gens)

    id2 = {
    "bu_name": "swiggy Ginnie",
    "bu_detail": "Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.",
    "brand_name": "swiggy",
    "interest_keyword": "burger",
    "brand_id": "f226bd37-db7c-4908-b992-907ff441bcb7",
    "reference_headline": "Order now to get 30% off",
    "reference_description": "Delivered at your doorsteps",
    "reference_primary_text": "Get 30% off on your first order, delivered to your doorsteps with Swiggy Ginnie",
    "image_layer_data": {
        "1": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_1",
            "layer_text": "NOW IS THE TIME TO START",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "layer_2"
        },
        "2": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_2",
            "layer_text": "OUR MEDICAL JOUNEY",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "END"
        }
    }
}

    id3 = {
    "bu_name": "swiggy Ginnie",
    "bu_detail": "Swiggy is a food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner till their food is delivered.",
    "brand_name": "swiggy",
    "interest_keyword": "burger",
    "brand_id": "f226bd37-db7c-4908-b992-907ff441bcb7_",
    "reference_headline": "Order now to get 30% off",
    "reference_description": "Delivered at your doorsteps",
    "reference_primary_text": "Get 30% off on your first order, delivered to your doorsteps with Swiggy Ginnie",
    "image_layer_data": {
        "1": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_1",
            "layer_text": "now is the time to start",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "layer_2"
        },
        "2": {
            "is_partial_sentence": True,
            "is_sentence_related": False,
            "layer_name": "layer_2",
            "layer_text": "Our Medical Jouney",
            "max_char_limit": 20,
            "min_char_limit": 10,
            "related_to": "END"
        }
    }
}

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
            '1': {"layer_name": "Text 1", "layer_text": "Compra millones de productos", "related_to": "Text 2", "max_char_limit": 28, "min_char_limit": 15, "is_partial_sentence": True, "is_sentence_related": False}, 
            '2': {"layer_name": "Text 2", "layer_text": "con tu Crédito Claro shop", "related_to": "END", "max_char_limit": 28, "min_char_limit": 15, "is_partial_sentence": True, "is_sentence_related": False}},
               'image_text': 'Compra millones de productos [SEP] con tu Crédito Claro shop'}
    ids = [id9]
    gen_list = []

    for id in ids:
        gens, logs = FullSentenceParaphrasingLever().run(id)
        gen_list.append(gens)
    print("$$$")
    for gen in gen_list:
        print("\n\n######\n\n")
        print(gen)
