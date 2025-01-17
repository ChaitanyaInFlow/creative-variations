
import sys
import traceback

from ds.lever import Lever
from ds.scripts.detect_language import detect_language
# from ds.driver.pmax.api_archive.pmax_fetch_assets import FetchPMAXAssets

import logging


class PMaxThemeGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.input_dict['reference'] = self.input_dict.get('reference_headline', '') + '\n' + self.input_dict.get('reference_description', '') + '\n' + self.input_dict.get('reference_long_headline', '')
        ## Detect Language
        self.input_dict['language'] = detect_language(self.input_dict['reference'])
        self.prompt = [
                    {
                        "role": "system", 
                        "content": '''You are a helpful digital marketing assistant. Extract one Theme from the Given Reference.

The theme should be of one or two words. It should be a broad theme. 

Avoid using generic themes like deals, discount or the brand name.'''
                    }, 

                    {
                        "role" : "user",
                        "content" : f'''###
Example 1 

Reference:
Mamaearth Face Wash at 25% Off
Instantly cleanse & hydrate with the nourishing Face Wash Range at 20% Off. Code REDEEM20
Mamaearth Natural Face Wash
Get upto 20% Off. Use REDEEM20
Get upto 25% Off. Use SAVE25
Upto 25% Off with Code SAVE25
Apply Code SAVE25 and Avail Upto 25% Off on Mamaearth Toxin-Free Facewash Range
Cleanse & brighten with the natura Face Wash Range without over-drying. Use SAVE25
Shop Our Exclusive Face Wash For Oil Control, Tan Removal, Acne & Pimples.
Protect & Nurture Your Face Naturally With Mamaearth Face Wash For All Face Concerns.
Look & feel fresh with the skin purifying Face Wash Range
Shop the goodness of nature with toxin-free face wash range. Use SAVE25 for Upto 25% Off
Get effortlessly clean with naturally effective ingredients in the Face Wash Range
Leave no skin offenders behind with the soothing & hydrating Face Wash Range. Use REDEEM20
Hurry & Shop Now to Say Goodbye to Toxins. Use Code SAVE25 for Upto 25% Off

Extract one Theme from the Given Reference.
The Theme should be in English.

Theme: Face Wash

###
Example 2 

Reference:
{self.input_dict['reference']}

Extract one Theme from the Given Reference.
The Theme should be in {self.input_dict['language']}.

Theme:'''
                    }
                    
                    ]
        self.nlg_parameters = {
            "response_length": 256,
            "temperature": 0,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop_seq": "[]",
            "n" : 1,
        }     
        self.nlg_generations_list, self.nlg_response = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

    @Lever.log_extract_label
    def extract_label(self) -> None:
        pass

    @Lever.log_postprocess
    def postprocess(self) -> None:
        if self.input_dict['language'] == 'English':
            post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
            self.post_process_list = []
            for generation in self.nlg_generations_list:
                self.post_process_list.append(post_process_obj.run(generation))
        else:
            self.post_process_list = self.nlg_generations_list
        self.log_json['post_process_list'] = self.post_process_list

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        pass

    @Lever.log_run       
    def run(self, input_dict):
        try:
            self.input_dict = input_dict
            self.generate()
            self.extract_label()
            self.postprocess()

            output_dict_list = [{"text": generation.strip()} for generation in list(set(self.post_process_list))]
            self.log_json['output_dict_list'] = output_dict_list

            return output_dict_list, self.log_json


        except Exception as exc:
            _, _, exc_traceback = sys.exc_info()
            trace = traceback.format_tb(exc_traceback)
            updated_log_json = {"trace": trace,
                                "exception": str(exc), "info": self.log_json}
            return [], updated_log_json

   
if __name__ == '__main__':
        # ad_account_id = 5258806593
        # asset_group_id = 6442780289

        # headlines, descriptions, long_headlines = FetchPMAXAssets(ad_account_id, asset_group_id).execute()

        # input_dict = {}

        # input_dict['reference_headline'] = headlines
        # input_dict['reference_description'] = descriptions
        # input_dict['reference_long_headline'] = long_headlines

        # theme, _ = PMaxThemeGeneration().run(input_dict)

        # print("### Theme = ", theme)
        pass