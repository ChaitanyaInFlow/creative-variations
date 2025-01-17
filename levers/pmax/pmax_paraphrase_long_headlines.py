#Import our own files
import sys
import traceback

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import logging

class PMAXLongHeadlineParaphrase(Lever):

    @Lever.log_generate
    def generate(self) -> None:

        ## Detect Language
        self.input_dict['language'] = detect_language(self.input_dict['reference_long_headline'])

        self.prompt = [
            {
                "role": "system", 
                "content": '''You are a helpful digital marketing assistant for writing creative Variations of the given Reference Headline using the Brand Info, Reference Headline and Reference Theme. 

The Variations should be centred around the Reference Headline and Reference Theme.'''},

{ "role": "user",
"content" : f'''Give Variations for the following Reference Headline.

###
Example 1

Reference Headline: Revive Your Hair With Mamaearth Hair Oil

Brand Info: Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.

Reference Theme: Hair Oil

Additional Reference: Pure And Natural Hair Oil. Get healthy, luscious hair with Mamaearth’s natural hair oil

Write 6 Variations of the Reference Headline. All Variations should have less than 18 words.
All Variations must be in English.

Variation 1: Transform Your Hair with Mamaearth's Natural Hair Oil
Variation 2: Get Healthy Hair with Mamaearth's Toxin-Free Hair Oil
Variation 3: Get Smooth and Silky Hair with Mamaearth's Natural Hair Oil
Variation 4: Nourish Your Hair From Root To Tip With Mamaearth
Variation 5: Pamper Your Scalp And Revitalize Your Hair With Mamaearth
Variation 6: Restore the Health of Your Hair with Mamaearth Hair Oil

###
Example 2

Reference Headline: {self.input_dict['reference_long_headline']}

Brand Info: {self.input_dict['bu_detail']}

Reference Theme: {self.input_dict['theme']}

Write 6 Variations of the Reference Headline. All Variations should have less than 18 words.
All Variations must be in {self.input_dict['language']}.

Variation 1:'''
            }]

        self.nlg_parameters = {
            "response_length": 500,
            "temperature": 1,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop_seq": "[]",
            "n" : 3
        }        
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return
    
    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        ## Strip Generations starting with Variant 1, Variant 2, etc or Variation 1, Variation 2, etc.
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
            post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
            self.post_process_list = []
            for generation in self.extracted_generations:
                self.post_process_list.append(post_process_obj.run(generation, self.input_dict))
            self.log_json['post_process_list'] = self.post_process_list
        else:
            self.post_process_list = self.extracted_generations

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=90, 
            min_length=15, 
            threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations']= filter_obj.run(
            self.post_process_list, 
            reference_ad=self.input_dict['reference_long_headline'],
            input_dict=self.input_dict,
            check_english= False if self.input_dict['language']!='English' else True) ## Need to add reference ad logic
        self.log_json['filtered_generations'] = self.filtered_list

        cluster_text_obj = self.cluster_text_class(threshold=80)
        self.filtered_cluster_list , _ = cluster_text_obj.get_unique_sentences(input_assets=self.filtered_list)
        self.filtered_cluster_list = [{"text": generation.strip()} for generation in self.filtered_cluster_list]
        self.log_json['filtered_cluster_list'] = self.filtered_cluster_list



    @Lever.log_run       
    def run(self, input_dict):

        try:
            self.input_dict = input_dict
            
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()
            
            final_output = self.filtered_cluster_list
            self.log_json['final_output'] = final_output

            return final_output, self.log_json

        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return [], updated_log_json



if __name__ == '__main__':


    ids = {
            "bu_name": "Vuori",
            "bu_detail": "Vuori is a premium performance apparel brand inspired by the active Coastal California lifestyle. The brand offers apparel that is ethically manufactured and made with durable performance materials.",
            "brand_name": "Vuori",
            "theme": "cashback",
            "reference_headline" : "get clothes today",
            "n_generations": 6,
            "limit": 40,
            "reference_description": "You'll wear these daily!",
            # "reference_long_headline": "You'll wear these daily.",
            "reference_long_headline" : "Quer milhas, cashback, desconto na fatura"

                    }
    gens, logs = PMAXLongHeadlineParaphrase().run(ids)
    print(gens)
    # print(logs)
    # Headline(prompt_templete=, support_dict=, )