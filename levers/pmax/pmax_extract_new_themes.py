
import sys
import traceback

from ds.lever import Lever
from ds.scripts.detect_language import detect_language
# from ds.driver.pmax.api_archive.pmax_fetch_assets import FetchPMAXAssets
from ds.process.cluster_text import ClusterText


import logging


class PMaxNewThemeGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
                    {
                        "role": "system", 
                        "content": '''You are a helpful digital marketing assistant. 

Give 6 new themes for the Brand.
3 themes should not be related to the Reference Theme. 
3 themes should be related to the Reference Theme. 

The themes should be of one or two words. '''
                    }, 

                    {
                        "role" : "user",
                        "content" : f'''For the following Brand, recommend new themes.

###
Example 1

Brand: Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.

Reference Theme: Lipstick

Give 6 new themes for the Brand.
All themes must be in English.

1: Hair Care
2: Skin Care
3: Body Wash
4: Lip Balm 
5: Lip Care
6: Lip Scrub

###
Example 2

Brand: {self.input_dict['brand_detail']}

Reference Theme: {self.input_dict['theme']}

Give 6 new themes for the Brand.
All themes must be in {self.input_dict.get('language','English')}.

1:'''
                    }
                    
                    ]
        self.nlg_parameters = {
            "response_length": 256,
            "temperature": 0.8,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop_seq": "[]",
            "n" : 3,
        }     
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation = '1:' + generation
            t_gens = generation.split('\n')
            t_gens = [':'.join(el.split(':')[1:]).strip() for el in t_gens]
            self.extracted_generations.extend(t_gens)

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict.get('language','English') == 'English':
            post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
            self.post_process_list = []
            for generation in self.extracted_generations:
                self.post_process_list.append(post_process_obj.run(generation))
            self.log_json['post_process_list'] = self.post_process_list
        else:
            self.post_process_list = self.extracted_generations

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            min_length = 8,
            max_length=60,
            threshold=85)
        self.filtered_list, self.discarded_list = filter_obj.run(
            self.post_process_list,
            input_dict=self.input_dict, reference_ad='',
            check_english= False if self.input_dict.get('language','English')!='English' else True)
        if(len(self.filtered_list)>5):
            self.filtered_list, _ = ClusterText(threshold=80).get_unique_sentences(self.filtered_list)

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.generate()
            self.extract_label()
            self.postprocess()
            self.filter_generations()

            output_dict_list = [{"text": generation.strip()} for generation in list(set(self.filtered_list))]
            self.log_json['output_dict_list'] = output_dict_list

            return output_dict_list, self.log_json


        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return [], updated_log_json

   
if __name__ == '__main__':
    pass
    # input_dict = {
    #     "brand_detail" : "Betabrand's clothes are designed to be comfortable and stylish for women who are constantly on the move. With a focus on yoga-inspired designs, the brand offers a variety of pants, denim, travel wear, and more that are perfect for any activity.",
    #     "theme" : "jeans"
    # }

    # themes, _ = PMaxNewThemeGeneration().run(input_dict)

    # print("\n\n NEW THEMES : \n", themes)

    # ## BENCHMARKING 

    # import pandas as pd 

    # df_input = pd.read_csv("ds/driver/PMAX_Benchmarking_output_themes_1.csv")

    # new_themes_list = []

    # for i in range(0, len(df_input)):

    #     print("\n\n########  ", i, " ############\n\n")

    #     input_dict = {
    #     "brand_detail" : df_input.loc[i, 'brand_detail'],
    #     "theme" : df_input.loc[i, 'theme'] }

    #     new_themes, _ = PMaxNewThemeGeneration().run(input_dict)

    #     new_themes_list.append( "\n".join([ theme['text'] for theme in new_themes]))

    # df_input['new_themes'] = new_themes_list

    # df_input.to_csv("ds/driver/PMAX_Benchmarking_output_themes_2.csv", index=False)