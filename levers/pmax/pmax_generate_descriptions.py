#Import our own files
import sys
import traceback

from ds.lever import Lever
from ds.scripts.detect_language import detect_language

import logging



class PMAXDescriptionGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:

                
        self.prompt = [
            {
                "role": "system", 
                "content": '''Write creative Google ad Descriptions for the given Brand and Themes. 
The Descriptions should be focused on the Themes.'''},
{ "role" : "user",
 "content" :f'''###
Generation 1

Brand: Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.

Themes: Natural Lip Care, Lipstick, Lip Masks With Beneficial Ingredients, Cruelty-Free Lipsticks

Write 5 Descriptions based on the Themes for the given Brand. Each Description must be less than 18 words.

Description 1: The best natural lip care products to keep your lips soft and supple
Description 2: Find the perfect shade of lipstick with mamaearth
Description 3: Get healthy and beautiful lips with mamaearth’s natural lip care
Description 4: The best lip masks with beneficial ingredients for soft, supple lips
Description 5: Cruelty-Free lipsticks that will keep your lips looking amazing

###
Generation 2

Brand: Qanvast is the go-to renovation platform for homeowners to browse local home ideas & get matched with local interior firms. They can connect you with interior designers based on your budget and style requirements for free. They have helped thousands of happy homeowners reach out to the right designers - achieving their dream homes in the process.

Themes: Renovation Ideas For HDB Flats, Browse Local Home Ideas, Home Exterior Design, Get Matched With Local Home Renovation Experts, Interior Design

Write 6 Descriptions based on the Themes for the given Brand. Each Description must be less than 18 words.

Description 1: Get renovation ideas for your HDB flat from Qanvast today
Description 2: Not sure where to start with your renovation? Browse local home ideas on qanvast
Description 3: Not sure where to start with your home exterior design? Let Qanvast help you out
Description 4: Get matched with local home renovation experts on Qanvast today
Description 5: Create your dream home with Qanvast’s interior design ideas
Description 6: Find the perfect home renovation expert for your project on Qanvast

###
Generation 3

Brand: Betabrand designs amazingly comfortable clothing for women who like to stay active all day long. Dress Pant Yoga Pants, Yoga Denim, travel wear, and more.

Themes: Clothing/Fashion, Betabrand Jeans

Write 5 Descriptions based on the Themes for the given Brand. Each Description must be less than 18 words.

Description 1: The most comfortable and fashionable clothing for women. Betabrand has it all
Description 2: Get the perfect fit with Betabrand’s stylish and comfortable clothing
Description 3: Look great and feel even better in betabrand clothing
Description 4: Get a comfortable, stylish fit with Betabrand jeans
Description 5: Look fashionable and stay comfortable with Betabrand jeans

###
Generation 4

Brand: {self.input_dict['bu_detail']}

Themes: {self.input_dict['themes']}

Write 6 Descriptions based on the Themes for the given Brand. Each Description must be less than 18 words.
All Descriptions must be in {self.input_dict.get('language','English')}.

Description 1:'''
            }]

        self.nlg_parameters = {
            "response_length": 500,
            "temperature": 0.77,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1,
            "stop_seq": "[]",
            "n" : 3
        }        
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)
        return

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Description ' + str(i+1) + ':', '')
            self.extracted_generations += generation_list

       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict.get('language','English') == 'English':
            post_process_obj = self.postprocess_class(title_case=False, exclude_exclamation=False)
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
            min_length=30,
            threshold=80)
        self.filtered_list, rejected_list= filter_obj.run(
            self.post_process_list, 
            reference_ad='',
            input_dict=self.input_dict,
            check_english= False if self.input_dict.get('language','English')!='English' else True) ## Need to add reference ad logic
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
            "themes": "apparel, fashion",
            "n_generations": 6,
                    }
    gens, logs = PMAXDescriptionGeneration().run(ids)
    print(gens)
   