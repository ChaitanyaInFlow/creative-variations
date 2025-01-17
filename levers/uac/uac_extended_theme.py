import re
from ds.lever import Lever

import logging



class UACExtendedThemeGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        remove_words = 'discount deal offer sale'
        remove_words_regex = '|'.join([f'({el})' for el in remove_words.split()])
        self.input_dict['theme'] = re.sub(remove_words_regex, '', self.input_dict['theme'])
        
        self.prompt = [
            {
                "role": "system", 
                "content" : '''You are a helpful digital marketing assistant. Give extended themes from the given theme. 

extended themes refer to sub themes or niche themes within the broader theme.

Develop marketing themes that can resonate with the target audience,  aligns with the brand and can generate engaging content.

Keep them short.'''} ,
{
    "role" : "user", 
    "content" : f'''For the following Brand, recommend extended themes from the given Theme.

###
Example 1

Brand: Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.

Theme: Lipstick

Give 6 extended themes for the Brand from the Theme.

1: Natural Lipsticks
2: Long-lasting Lipsticks
3: Matte Finish Lipsticks
4: Hydrating Lipsticks
5: Toxin-free Lipsticks
6: Bold colour Lipsticks

###
Example 2

Brand: {self.input_dict['brand_detail']}

Theme: {self.input_dict['theme']}

Give 6 extended themes for the Brand from the Theme.

1:'''
}]

        self.nlg_parameters = {
            'temperature': 1,
            'response_length': 256,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0,
            # 'stop_seq': ["Extract", "6:", "###", "Recommend"],
            'n': 3,
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
        # print("\n\n extracted : \n", self.extracted_generations)
       
    @Lever.log_postprocess
    def postprocess(self) -> None:
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation))
        # print("\n\n self.post_process_list : \n", self.post_process_list)

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            min_length = 8,
            max_length=60,
            threshold=85)
        self.filtered_list, self.discarded_list = filter_obj.run(
            self.post_process_list,
            input_dict=self.input_dict, reference_ad='')
        # print("\n\n self.filtered_list : \n", self.filtered_list)

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()
        return self.filtered_list, []
   
if __name__ == '__main__':
    input_dict = {
        "brand_detail" : "Mamaearth products are made using safe, pure, gentle, natural, and toxin-free ingredients.They provide various products for beauty, skin, hair, and baby care needs.",
        "theme" : "Shampoo Range"
    }

    themes, _ = UACExtendedThemeGeneration().run(input_dict)

    print("\n\n THEMES : \n", themes)


# ad_account_id = 2904992326
# ad_group_id = 63963090431
# generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id)
