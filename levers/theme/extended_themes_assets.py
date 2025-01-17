import re
from ds.lever import Lever
from ds.process.cluster_text import ClusterText


import logging



class ExtendedThemeAssetsGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        # remove_words = 'discount deal offer sale'
        # remove_words_regex = '|'.join([f'({el})' for el in remove_words.split()])
        # self.input_dict['theme'] = re.sub(remove_words_regex, '', self.input_dict['theme'])
        
        self.prompt = [
            {
                "role": "system", 
                "content" : '''You are a helpful digital marketing assistant. Extract extended themes for the Reference Theme present in the Reference Text.

extended themes refer to sub themes or niche themes within the broader Reference Theme.

Keep them short.'''} ,
{
    "role" : "user", 
    "content" : f'''###
Example 1 

Reference Text:
Mamaearth Face Wash at 25% Off
Instantly cleanse & hydrate with the nourishing Face Wash Range at 20% Off. Code REDEEM20
Mamaearth Natural Face Wash
Upto 25% Off with Code SAVE25
Apply Code SAVE25 and Avail Upto 25% Off on Mamaearth Toxin-Free Facewash Range
Cleanse & brighten with the natural Face Wash Range without over-drying. Use SAVE25
Shop Our Exclusive Face Wash For Tan Removal
Shop the goodness of nature with toxin-free face wash range. 
Natural Facewash for Tan removal
Use SAVE25 for Upto 25% Off
Get rid of that summer tan with Mamaearth Face Wash
Get effortlessly clean with naturally effective ingredients in the Face Wash Range
Hurry & Shop Now to Say Goodbye to Toxins. Use Code SAVE25 for Upto 25% Off

Reference Theme: Face Wash

Extract extended themes for the Reference Theme present in the Reference Text.

1: Toxin-free face wash
2: Natural face wash
3: Tan removal face wash

###
Example 2 

Reference Text:
{self.input_dict['reference']}

Reference Theme:{self.input_dict['theme']}

Extract extended themes for the Reference Theme present in the Reference Text.

1:'''
}]

        self.nlg_parameters = {
            'temperature': 0,
            'response_length': 256,
            'top_p': 1,
            'frequency_penalty': 0,
            'presence_penalty': 0,
            # 'stop_seq': ["Extract", "6:", "###", "Recommend"],
            'n': 1,
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
        
        if(len(self.filtered_list)>5):
            extended_themes, _ = ClusterText(threshold=86).get_unique_sentences(self.filtered_list)
        else:
            extended_themes = self.filtered_list

        self.output_dict_list = []
        for generations in extended_themes:
            generation_dict = {}
            generation_dict['text'] = generations.strip()
            self.output_dict_list.append(generation_dict)

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()
        return self.output_dict_list, []
   
if __name__ == '__main__':

    reference = '''Naturally Smooth & Thick Hair
Get 20% Off. Use MAMA20
Bid goodbye to bad hair days
The Secret to Flawless Hair
Natural nourishment for hair
Get upto 20% Off. Use REDEEM20
Get upto 25% Off. Use SAVE25
Free of harmful chemicals, it deeply nourishes hair from root to tip. Get Flat 20% Off.
Choose The Best Hair Conditioner Online From Mamaearth
Buy Mamaearth Conditioner For Hair Fall Control. Use Code MAMA20 for 20% Off.
Get healthier hair with nature infused Mamaearth Conditioner range.
Buy Mamaearth's Natural & Toxin Free Conditioner Online.
Buy Mamaearth Conditioner For Hair Fall Control. Get Upto 20% Off. Use REDEEM20.
Free of harmful chemicals, it deeply nourishes hair from root to tip. Get Upto 20% Off.
Free of harmful chemicals, it deeply nourishes hair from root to tip. Get Upto 25% Off.
Buy Mamaearth Conditioner For Hair Fall Control. Get Upto 25% Off. Use SAVE25
Repair, protect & nourish with Mamaearth's Almond & Rice Water Conditioner range.
Step up your hair game with Mamaearth's Natural Conditioners. Code MAMA20 for 20% Off.
Effortlessly grow long, thick & healthy hair with Conditioner Range at 20% Off.
Fight hair damage with Mamaearth's Paraben-Free Conditioner Range.
Get long-lasting results with SLS & toxin free Conditioner Range. Code MAMA20 for 20% Off.
Step up your hair game with Mamaearth's Natural Conditioners. Upto 20% Off. Use REDEEM20.
Get lasting results with SLS & toxin free Conditioner Range. Upto 20% Off. Use REDEEM20.
Step up your hair game with Mamaearth's Natural Conditioners. Upto 25% Off. Use SAVE25
Effortlessly grow long, thick & healthy hair with Conditioner Range at 25% Off.
Get lasting results with SLS & toxin free Conditioner Range. Upto 25% Off. Use SAVE25
    '''.split('\n')
    input_dict = {
        "reference" : reference,
        "theme" : "Hair Conditioner"
    }

    themes, _ = ExtendedThemeAssetsGeneration().run(input_dict)

    print("\n\n THEMES : \n", themes)


# ad_account_id = 2904992326
# ad_group_id = 63963090431
# generations, input_headlines, input_descriptions = generate(ad_account_id, ad_group_id)
