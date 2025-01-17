
from ds.lever import Lever

class UACThemeGeneration(Lever):


    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role" : "system",
                "content": "Extract one word Themes from the Given Reference."},
             {   "role": "user", 
                "content": f'''Extract 3 one word Themes from the Given Reference.

Reference:
{self.input_dict['input_assets']}
Theme 1:'''
            }]

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
                generation_list[i] = generation_list[i].replace('Theme ' + str(i+1) + ':', '')
                generation_list[i] = generation_list[i].strip()
            self.extracted_generations += generation_list
       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=30,
            threshold=80)
        self.filtered_list, self.discarded_list = filter_obj.run(
            self.post_process_list, 
            self.input_dict['adText'],
            input_dict=self.input_dict)

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        # self.filter_generations()
        return list(set(self.post_process_list)), []
        # return self.extracted_generations
   
if __name__ == '__main__':
    pass
# ad_account_id = 2904992326
# ad_group_id = 63963090431
# generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id)