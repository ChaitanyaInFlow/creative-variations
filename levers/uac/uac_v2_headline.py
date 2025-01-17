
from ds.lever import Lever

import logging


class UACHeadlineGeneration(Lever):

    @Lever.log_generate
    def generate(self) -> None:
        self.prompt = [
            {
                "role": "system", 
                "content": f'''
            Write creative Google ad Headlines for the given Brand and Themes. 

###
Generation 1

Brand: Rapido is India's first and fastest-growing Bike taxi app with a whopping 25 Million+ app downloads. Rapido bike taxi provides the best intra-city commuting services and is currently operating in 100+ cities. It is considered as the most affordable choice.

Themes: Shopping, Transportation ,Discounts/Coupons

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1: Shopping plan? Get Rapido Auto
Headline 2: Book Rapido Auto to the Mall
Headline 3: Most Affordable Bike Taxi App
Headline 4: Best Choice for Transportation
Headline 5: Save with Rapido Discounts
Headline 6: Great Discounts on Bike Rides

###
Generation 2

Brand: Swiggy is an online food ordering and delivery platform. It helps users order food from their favorite restaurants near them and track their delivery partner.

Themes: Swiggy, 50% Off, Cricket Season

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1: Order Food Online with Swiggy
Headline 2: Fast Food Delivery with Swiggy
Headline 3: Enjoy 50% Off at Swiggy
Headline 4: Half Price Meals with Swiggy
Headline 5: Watch the match with Swiggy
Headline 6: Cricket Season with Swiggy

###
Generation 3

Brand: {self.input_dict['bu_detail']}

Themes: {self.input_dict['input_themes']}

Write 6 Headlines based on the Themes for the given Brand. Each Headline must be less than 6 words.

Headline 1:'''
            }]

        self.nlg_parameters = {
            "response_length": 500,
            "temperature": 0.77,
            "top_p": 1,
            "frequency_penalty": 1,
            "presence_penalty": 1,
            "stop_seq": "[]",
            "n" : 5
        }

        self.nlg_generations_list, _ = self.chatgpt_generator.execute(self.prompt, **self.nlg_parameters)

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
        post_process_obj = self.postprocess_class(title_case=True, exclude_exclamation=True)
        self.post_process_list = []
        for generation in self.extracted_generations:
            self.post_process_list.append(post_process_obj.run(generation, self.input_dict))

    @Lever.log_filter_generations
    def filter_generations(self) -> None:
        filter_obj = self.filter_generations_class(
            max_length=30, 
            min_length=15, 
            threshold=84)
        self.filtered_list, rejected_list= filter_obj.run(
            self.post_process_list, 
            reference_ad='',
            input_dict=self.input_dict)  # Need to add reference ad logic

    @Lever.log_run       
    def run(self, input_dict):
        self.input_dict = input_dict
        self.generate()
        self.extract_label()
        self.postprocess()
        self.filter_generations()

        return self.filtered_list, []

