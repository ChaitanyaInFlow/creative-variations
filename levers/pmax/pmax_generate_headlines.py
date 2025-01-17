#Import our own files
import sys
import traceback

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import logging

class PMAXHeadlineGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:

        self.prompt = [
            {
                "role": "system", 
                "content": '''Write creative Google ad Headlines for the given Brand Details and Themes. 
The Headlines should be focused on the Themes.'''},

{ "role": "user",
"content" : f'''###
Generation 1

Brand: Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.

Themes: Natural Lip Care, Lipstick, Lip Masks With Beneficial Ingredients, Cruelty-Free Lipsticks

Write 5 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1: The Best Natural Lipstick
Headline 2: Gentle And Safe Lip Care
Headline 3: Cruelty-Free Lipsticks
Headline 4: Pure And Gentle Lip Masks
Headline 5: Pure And Natural Lipstick

###
Generation 2

Brand: Qanvast is the go-to renovation platform for homeowners to browse local home ideas & get matched with local interior firms. They can connect you with interior designers based on your budget and style requirements for free. They have helped thousands of happy homeowners reach out to the right designers - achieving their dream homes in the process.

Themes: Renovation Ideas, Browse Local Home Ideas, Home Exterior Design, Get Matched With Local Home Renovation Experts, Interior Design

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1: Renovate With Qanvast
Headline 2: Get Matched With Local Experts
Headline 3: Get Inspiration From Qanvast
Headline 4: Browse Local Home Ideas
Headline 5: Browse Exterior Designs
Headline 6: Interior Design Ideas

###
Generation 3

Brand: Betabrand designs amazingly comfortable clothing for women who like to stay active all day long. Dress Pant Yoga Pants, Yoga Denim, travel wear, and more.

Themes: Clothing/Fashion, Betabrand Jeans

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1: Look Great In Betabrand Jeans
Headline 2: Clothing For The Active Woman
Headline 3: Yoga Denim For Women
Headline 4:Travel In Style With Betabrand
Headline 5: Stylish Jeans from Betabrand
Headline 6: Comfortable Clothing For Women

###
Generation 4

Brand: {self.input_dict['bu_detail']}

Themes: {self.input_dict['themes']}

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.
All Headlines must be in {self.input_dict.get('language','English')}.

Headline 1:'''
            }]

        self.nlg_parameters = {
            "response_length": 500,
            "temperature": 1,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1,
            "stop_seq": "[]",
            "n" : 5
        }        
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return
    
    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Headline ' + str(i+1) + ':', '')
            self.extracted_generations += generation_list

       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict.get('language','English') == 'English':
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
            max_length=30, 
            min_length=10, 
            threshold=84)
        self.filtered_list, self.log_json['discard_filter_generations']= filter_obj.run(
            self.post_process_list, 
            reference_ad='',
            input_dict=self.input_dict,
            check_english= False if self.input_dict.get('language','English')!='English' else True) ## Need to add reference ad logic
        self.log_json['filtered_generations'] = self.filtered_list

        cluster_text_obj = self.cluster_text_class(threshold=85)
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
            "themes": "apparel, fashion",
            "n_generations": 6,
            "limit": 40
                    }
    gens, logs = PMAXHeadlineGeneration().run(ids)
    print(gens)
    # print(logs)
    # Headline(prompt_templete=, support_dict=, )