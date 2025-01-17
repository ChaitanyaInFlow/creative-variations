
import sys
import traceback

from ds.lever import Lever

import logging


class PMaxThemeGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
                    {
                        "role": "system", 
                        "content": "You are a helpful digital marketing assistant. Find one or two recurrent Topics from the Keywords."
                    }, 

                    {
                        "role" : "user",
                        "content" : f'''###\nExample 1\n\nFind one or two recurrent Topics from the Keywords.\n
                        Keywords:
how to apply lipstick
Brown Lipstick
natural lip balm
lipstick collection
red lipstick
rose natural lip balm
rose lip balm
colour lipstick
Best Natural Lipstick
rose lip balm
non toxic lipstick
lipstick shades

Topic 1: Lipsticks
Topic 2:  Lip Balms

###
Example 2 

Find one or two recurrent Topics from the Keywords.
Keywords:\n{self.input_dict['keywords']}\n\nTopic 1:'''
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
        self.extracted_generations = []
        for generation in self.nlg_generations_list:
            generation_list = generation.split('\n')
            for i in range(len(generation_list)):
                generation_list[i] = generation_list[i].replace('Topic ' + str(i+1) + ':', '')
                generation_list[i] = generation_list[i].replace('topic ' + str(i+1) + ':', '')
                generation_list[i] = generation_list[i].strip()
            self.extracted_generations += generation_list

    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation))
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
    
    ad_account_id = 2904992326
    ad_group_id = 63963090431
    input_dict = {
        "keywords" : " lipstick , natural lip care"
    }
    output_dict_list, _ = PMaxThemeGeneration().run(input_dict=input_dict)
    print("#######")
    print(output_dict_list)
    print("########")
    print(_)
    print("####")